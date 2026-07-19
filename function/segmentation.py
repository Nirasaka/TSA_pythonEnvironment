# ライブラリのインポート
import cv2
from skimage import measure
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

#? ---------------------------------------------------------------------------------------------------
#? 成田智史，井尻敬，“最小切断面を利用した2値画像の意味的領域分割”，画像電子学会誌，第47巻,
#? 第4号通巻246号，pp.433-439，(2018)．
#? 上記のアルゴリズムを参考に再現したもの
#? ---------------------------------------------------------------------------------------------------

#* ======================================================================================== 
#* グローバル変数
#* ======================================================================================== 
g_splitNum = []  # 収縮回数を記載


def split(img,filename):
    """結合領域を大まかに分割する

    Args:
        img (画像): マスク画像
        filename: ファイルの名前
        
    Returns:
        分割した枚数
    """
    global g_splitNum
    
    # 収縮処理用カーネル
    # 半径2画素の円形カーネルを作成
    radius = 2
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (radius*2+1, radius*2+1))
    
    # 縮小用画像をコピーする
    img_erosion2 = img.copy()
    i = 0
    spNum = 0
    print()
    
    while True:
        # 画像を収縮する
        img_erosion2 = cv2.erode(img_erosion2, kernel, iterations=2)
        spNum += 1
        
        # 結合部分をラベリング
        labeled_regions, num_labels = measure.label(img_erosion2, return_num=True, connectivity=2)
        
        if num_labels >= 2:
            # 各領域のプロパティを計算
            regions = measure.regionprops(labeled_regions)
            
            # 面積の小さい領域と最大の領域を抽出
            min_region = min(regions, key=lambda r: r.area)
            max_region = max(regions, key=lambda r: r.area)
            
            print("max:",min_region.area," min:",max_region.area)
            
            # 小さい領域のみ抽出（ラベリングされた領域をマスクとして使用）
            min_mask = np.zeros_like(img)
            min_mask[labeled_regions == min_region.label] = 255
            
            # 最大の白領域面積が一定以下であれば処理を終了
            if max_region.area > 10:             
                # 小さい領域を保存
                file_small = './output/ss/'+ '1_split_'+  filename +'_small_' + str(i) + '.png'
                cv2.imwrite(file_small, min_mask)
                
                # 元の画像から小さい領域を削除
                img_erosion2[labeled_regions == min_region.label] = 0
                
                # マスクを保存
                file_mask = './output/ss/'+ '1_split_'+  filename +'_'+ str(i) + '.png'
                cv2.imwrite(file_mask, img_erosion2)
                
                # 回数の設定
                i += 1
                g_splitNum.append(spNum)
                
            else:
                break
        
        elif num_labels == 0:
            break
        
    return i


def regrow(img,num,filename):
    """Split処理で分断された領域を膨張する

    Args:
        img (画像): マスク画像
        num (int): 分断枚数
        filename: ファイルの名前
    """
    global g_splitNum
    
    # 膨張用カーネル
    # 半径2画素の円形カーネルを作成
    radius = 2
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (radius*2+1, radius*2+1))
    
    for i in range(num):
        # 大きい画素を持っている画像を読み込む
        file = './output/ss/'+ '1_split_'+ filename +'_'+ str(i) + '.png'
        largeImg = cv2.imread(file)
        
        # 小さい画素を持っている画像を読み込む
        file = './output/ss/'+ '1_split_'+  filename +'_small_' + str(i) + '.png'
        smallImg = cv2.imread(file)
        
        # 二つのマスク画像を論理和 (OR) 演算で合成する
        combined_mask = cv2.bitwise_or(largeImg, smallImg)
        
        # 何回収縮処理をしたかリストからとってくる
        splitNum = g_splitNum[i]
        
        dilateLargeImg = largeImg.copy()
        dilateSmallImg = smallImg.copy()
        
        for j in range(splitNum):
            dilateLargeImg = cv2.dilate(dilateLargeImg, kernel, iterations=2)
            dilateSmallImg = cv2.dilate(dilateSmallImg, kernel, iterations=2)
            
        
        file_mask = './output/ss/'+ '2_regrow_' + filename +'_'+ str(i) + '.png'
        cv2.imwrite(file_mask, dilateLargeImg)
        file_mask = './output/ss/'+ '2_regrow' + filename +'_small_'+ str(i) + '.png'
        cv2.imwrite(file_mask, dilateSmallImg)
        
        # 共通部分の計算（論理積 AND）
        common_mask = cv2.bitwise_and(dilateLargeImg, dilateSmallImg)
        file_mask = './output/ss/'+ '2_regrow' + filename +'_common_'+ str(i) + '.png'
        cv2.imwrite(file_mask, common_mask)
    

def minCut(baseimg, maskNum, filename):
    """Regrow処理の結果を用いて連結領域における面積最少の切断面(くびれ)を検索する

    Args:
        baseimg (img): 基になるマスク画像
        maskNum (int): 分割した枚数
        filename (str): ファイルの名前
    """
    # 入力画像のサイズ
    rows, cols = baseimg.shape
    segmented_images = []
    
    # グラフ構築用関数
    def build_graph(image):
        G = nx.DiGraph()
        source = "source"
        sink = "sink"
        G.add_node(source)
        G.add_node(sink)
        
        for i in range(rows):
            for j in range(cols):
                node = (i, j)
                # 前景ピクセルをソースに、背景ピクセルをシンクに接続
                if image[i, j] == 1:
                    G.add_edge(source, node, capacity=float("inf"))
                else:
                    G.add_edge(node, sink, capacity=float("inf"))

                # 隣接ピクセルへのエッジを追加
                for di, dj in [(0, 1), (1, 0)]:  # 右と下のピクセルを隣接として設定
                    ni, nj = i + di, j + dj
                    if 0 <= ni < rows and 0 <= nj < cols:
                        G.add_edge(node, (ni, nj), capacity=1)
                        G.add_edge((ni, nj), node, capacity=1)
        
        return G

    # 画像を指定した回数で分割
    current_img = baseimg.copy()
    for part in range(maskNum):
        G = build_graph(current_img)
        source = "source"
        sink = "sink"
        
        # 最大フロー最小切断を実行
        cut_value, partition = nx.minimum_cut(G, source, sink)
        reachable, non_reachable = partition

        # 分割結果を格納するための画像を作成
        segmented_part = np.zeros_like(baseimg)
        for node in reachable:
            if isinstance(node, tuple) and len(node) == 2:  # ピクセル座標のみ処理
                x, y = node
                segmented_part[x, y] = 255
        
        # 分割結果をファイルとして保存
        part_filename = f"{filename}_part_{part+1}.png"
        cv2.imwrite(part_filename, segmented_part)
        segmented_images.append(segmented_part)
        
        # 次の分割のために現在の画像から切断した領域を除外
        for node in reachable:
            if isinstance(node, tuple) and len(node) == 2:
                x, y = node
                current_img[x, y] = 0

    # 分割結果の表示
    plt.figure(figsize=(10, maskNum))
    for i, img in enumerate(segmented_images):
        plt.subplot(1, maskNum, i + 1)
        plt.imshow(img, cmap="gray")
        plt.title(f"Part {i+1}")
        plt.axis("off")
    plt.show()


def SSFromIMG(maskimg,filename):
    """マスク画像から意味的分割(セマンティックセグメンテーション)を行う

    Args:
        maskimg (画像): マスク画像
        filename: 拡張子なしのファイル名
    Returns:
        maskNum: 共有部位の枚数
    """
    # 結合領域を大まかに分割するsplit処理
    maskNum = split(maskimg,filename)
    
    # もし結合結果が0であれば終了する
    if maskNum == 0:
        return
    
    # Split処理で分断された領域を膨張するRegrow処理
    regrow(maskimg,maskNum,filename)
    
    # # Regrow処理の結果を用いて連結領域における面積最少の切断面(くびれ)を検索するMinCut処理
    # minCut(maskimg,maskNum,filename)
    
    return maskNum
    

if __name__ == "__main__":
    imgPath = "./output/mask/template(1)_mask3.png"
    img=cv2.imread(imgPath,cv2.IMREAD_GRAYSCALE)
    filename = "template(1)"
    SSFromIMG(img,filename)
