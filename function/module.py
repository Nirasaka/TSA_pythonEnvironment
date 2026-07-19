# ライブラリのインポート
import sys
import os
import colorama
from colorama import Fore, Back, Style
import cv2
import numpy as np
import random

#?----------------------------------------------------
#? 自作の便利そうなモジュール
#?----------------------------------------------------

def namingFile(name,extension,dirPath):
    """ディレクトリ内に格納されているnameの番号を決める
    fish(1).pngがあればfish(2).pngを返す

    Args:
        name (str): ファイルの名前
        extension (str): 拡張子
        dirPath (str): directoryのパス

    Returns:
        str: ファイル名
    """
    num = 1
    while True:
        # 探索するファイル名を検索
        filePath = dirPath + "/" + name + "(" + str(num) + ")" + extension
        # directoryになければ終了
        if not os.path.isfile(filePath):
            return name + "(" + str(num) + ")" + extension
        else:
            num += 1
        
def makeFile(filePath):
    """ディレクトリがあるかを判定する．なければ作る．

    Args:
        filePath : ファイルパス
    """
    if not os.path.isdir(filePath):
        os.makedirs(filePath)
        
def initmain():
    """プログラム起動をする際の設定"""
    makeFile("./inputimg")
    makeFile("./output/mask")
    makeFile("./output/mesh")
    makeFile("./output/onlyfish")
    makeFile("./output/split")
    makeFile("./output/ss")
    makeFile("./output/paint")
    makeFile("./output/camera")
    makeFile("./output/born")
    makeFile("./output/blend")
    makeFile("./output/fbx")
    makeFile("./upload")
    
def regitFishPath(nowNum,templateNum):
    """登録する魚を決定する

    Args:
        nowNum (int): fish_dataの番号
        templateNum (int): templateの番号

    Returns:
        パス，flag : Trueならテンプレート使用
    """
    fileBase = "./inputimg/"
    
    serchPath = fileBase + "fish_data(" + str(nowNum) + ").png"
    
    if os.path.isfile(serchPath):
        return "fish_data(" + str(nowNum) + ").png",False
    else:
        return "template(" + str(templateNum) + ").png",True
    
def getFish(fishNum,templateNum):
    """指定された番号のパスを返す

    Args:
        num (int):番号. Defaultsはg_fishNum.

    Returns:
        パス
    """
    serchPath = "./output/mesh/me_fish_data("+str(fishNum)+").obj"
    
    if os.path.isfile(serchPath):
        return serchPath
    else:
        return "./output/mesh/me_template(" + str(templateNum) + ").obj"
    
def getImgFish(fishNum,templateNum):
    """指定された番号のパスを返す

    Args:
        num (int):番号. Defaultsはg_fishNum.

    Returns:
        パス
    """
    serchPath = "./output/onlyfish/up2down_fish_data("+str(fishNum)+").png"
    
    if os.path.isfile(serchPath):
        return serchPath
    else:
        return "./output/onlyfish/up2down_template("+str(templateNum)+").png"


def calculate_longest_line_through_centroid(image_path):
    """
    二値化された画像の白領域において、重心を通り最も長い直線を持つ白領域の輪郭の頂点ペアを求め、そのペアで直線を描画する関数。
    
    すべての直線が同じ距離の場合、その旨を出力する。

    引数:
    image_path (str): 二値化画像のファイルパス

    戻り値:
    tuple: 最も長い直線を持つ頂点ペア ((x1, y1), (x2, y2)) またはすべての直線が同じ距離の場合、その旨を表示
    """
    # 画像を読み込む
    binary_image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    if binary_image is None:
        raise ValueError(f"画像の読み込みに失敗しました: {image_path}")

    # 二値化がされていない場合、二値化処理を行う
    _, binary_image = cv2.threshold(binary_image, 127, 255, cv2.THRESH_BINARY)

    # 画像をカラー画像に変換
    color_image = cv2.cvtColor(binary_image, cv2.COLOR_GRAY2BGR)

    # 白領域の輪郭を検出
    contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 白領域のピクセル座標を取得
    white_pixels = np.column_stack(np.where(binary_image == 255))

    # 重心を計算
    centroid = np.mean(white_pixels, axis=0)
    centroid = tuple(centroid)

    # 最大の距離を求める
    max_distance = 0
    best_pair = None
    same_distance = True  # 同じ距離かどうかをチェック

    # 輪郭内の各点を通る直線を計算し、重心を通る直線の中で最も長い距離を求める
    for contour in contours:
        for i in range(len(contour)):
            p1 = contour[i][0]  # 輪郭の1つ目の点
            for j in range(i + 1, len(contour)):
                p2 = contour[j][0]  # 輪郭の2つ目の点

                # 重心を通る直線の方程式を求める
                if p2[0] != p1[0]:  # x座標が異なる場合、傾きが計算可能
                    m = (p2[1] - p1[1]) / (p2[0] - p1[0])
                    b = p1[1] - m * p1[0]  # y切片を計算

                    # 重心を通る直線がこの直線の式を満たすかを確認
                    # 直線の方程式に重心のx座標を代入して、y座標が重心のy座標と一致するかを確認
                    if abs(centroid[1] - (m * centroid[0] + b)) < 1e-5:
                        # 重心を通る直線として採用
                        # この直線の長さを計算
                        distance = np.linalg.norm(np.array(p1) - np.array(p2))
                        if distance > max_distance:
                            max_distance = distance
                            best_pair = (tuple(p1), tuple(p2))
                            same_distance = True  # 最大距離が更新されたので、同じ距離ではない

                        elif distance == max_distance:
                            # 距離が最大と同じならば、同じ距離とフラグを維持
                            continue

    # 結果を表示
    if best_pair:
        p1, p2 = best_pair
        cv2.line(color_image, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), (0, 255, 0), 2)  # 緑色の線を描画
        print(f"最も長い直線を持つ頂点ペア: {best_pair} 距離: {max_distance}")
    else:
        print("直線が見つかりませんでした")

    if same_distance:
        print("すべての直線の長さが同じです。")

    # 結果を表示
    cv2.imshow("Line Drawn on Image", color_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return best_pair


def printTerminal(string,color = 1):
    """何の処理をしているか表示させる

    Args:
        string (str): 表示させるもの
    """
    colorama.init()
    if color == 1:
        print(Fore.LIGHTBLUE_EX + "\n======================================================")
        print(Fore.LIGHTBLUE_EX + "  " + string)
        print(Fore.LIGHTBLUE_EX + "======================================================")

    elif color == 2:
        print(Fore.LIGHTGREEN_EX + "======================================================")
        print(Fore.LIGHTGREEN_EX + "  " + string)
        print(Fore.LIGHTGREEN_EX + "======================================================")
    elif color == 3:
        print(Fore.LIGHTRED_EX + "  " + string)

        
    print(Fore.WHITE)
    print(Style.RESET_ALL+"",end="")
    
def rand_rete(max=1.5,min=0.8):
    """ランダムな数字を返す

    Args:
        max: 最大値. Defaults to 1.5.
        min: 最小値. Defaults to 0.8.
    """
    return round(random.uniform(min,max),1)
    

    
if __name__ == "__main__":
    print(namingFile("fish_data",".png","./inputimg"))