import os
import cv2
import numpy as np


def contourDetection(imgPath, filename):
    """画像から魚のみを抽出し、透明版も作成する

    Args:
        imgPath: 画像のpath
        filename: ファイルの名前

    Returns:
        img_cut: 抽出した魚画像
        img_cut_with_alpha: 抽出した魚画像（黒領域を透明化したもの）
    """

    # 画像をグレースケールで読み込む
    img = cv2.imread(imgPath, cv2.IMREAD_GRAYSCALE)

    # 二値化処理を行う
    ret, img_2 = cv2.threshold(img, 0, 255, cv2.THRESH_OTSU)
    cv2.imwrite("./output/mask/" + filename + "_mask1.png", img_2)

    # 二値化画像の色を反転
    img_2re = cv2.bitwise_not(img_2)

    # 輪郭を抽出する
    contours, hierarchy = cv2.findContours(
        img_2re, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )

    # マスク画像を作成し、輪郭部分を塗りつぶす
    mask = np.zeros_like(img)
    cv2.drawContours(mask, contours, -1, (255), thickness=cv2.FILLED)
    cv2.imwrite("./output/mask/" + filename + "_mask2.png", mask)

    # カラー画像を読み込む
    img_color = cv2.imread(imgPath)

    # 最大の輪郭を見つける
    max_contour = max(contours, key=cv2.contourArea)

    # 輪郭の内部を白で塗りつぶす
    cv2.drawContours(mask, [max_contour], -1, (255), thickness=cv2.FILLED)

    # マスクをカラー画像に変換
    mask_color = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    cv2.imwrite("./output/mask/" + filename + "_mask3.png", mask_color)

    # マスクを使って元の画像から輪郭部分を抽出
    img_cut = cv2.bitwise_and(img_color, mask_color)

    # 黒領域を透明にするためアルファチャンネルを追加
    b, g, r = cv2.split(img_cut)
    alpha = mask  # マスクをそのままアルファチャンネルに使用
    img_cut_with_alpha = cv2.merge((b, g, r, alpha))


    #画像サイズに合わせて正規化
    # 元画像のサイズを取得
    h0, w0 = img_cut_with_alpha.shape[:2]

    # 不透明部分のバウンディングボックスを取得
    coords = np.column_stack(np.where(alpha))
    y_min, x_min = coords.min(axis=0)
    y_max, x_max = coords.max(axis=0)

    # トリミング
    cropped = img_cut_with_alpha[y_min:y_max + 1, x_min:x_max + 1]
    h, w = cropped.shape[:2]

    # バウンド領域を元の画像サイズにスケーリング
    img_alpha_normalized = cv2.resize(cropped, (w0, h0), interpolation=cv2.INTER_AREA)

    return img_cut, img_alpha_normalized


def findWidestPoint(contour):
    """輪郭から最も幅の広い箇所のx座標を返す

    Args:
        contour: 輪郭(body)

    Returns:
        x : x座標
    """

    # 輪郭のx座標の最小値と最大値を取得
    x_min, x_max = contour[:, :, 0].min(), contour[:, :, 0].max()

    widest_x = x_min + (x_max - x_min) // 2
    return widest_x


def findNarrowestPointAfter(contour, start_x):
    """指定されたx座標以降の最も幅が狭くなる部分を特定する

    Args:
        contour: 輪郭(body)
        start_x: x座標

    Returns:
        x : x座標
    """

    # 探索範囲をx座標の最大値までに設定
    x_max = contour[:, :, 0].max()

    min_width = float("inf")
    split_x = start_x

    # 最も幅が広い部分から始めて、最も幅が狭くなる部分を特定する
    # なお，途中から前の幅より大きくなった場合はそこを返す
    for x in range(start_x, x_max):
        y_values = contour[contour[:, :, 0] == x][:, 1]
        if len(y_values) > 1:
            width = y_values.max() - y_values.min()
            if width < min_width and width > 100:
                min_width = width
                split_x = x

    return split_x


def findFishParts(imgPath, filename, saveOption = True):
    """画像から魚のパーツを推定する

    Args:
        imgPath: 画像のパス
        filename: 保存する名前

    Returns:
        img : パーツ分割を施した画像を出力
    """

    # 拡張子を除くファイル名を作る
    #exFile = os.path.splitext(filename)[0]

    # 輪郭を抽出して画像を切り抜く
    img_cut,img_alpha_normalized ,= contourDetection(imgPath, filename)

    # 結果を保存
    if saveOption:
        cv2.imwrite("./output/onlyfish/only" + filename + ".png", img_cut)
        cv2.imwrite("./output/onlyfish/normalized_" + filename + ".png", img_alpha_normalized)

    return img_cut

if __name__ == "__main__":
    print('main.pyを実行してください')
