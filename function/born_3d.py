import numpy as np
import cv2

def create_bone_structure(bone_list, file_name, file_path):
    """
    ボーン構築し、情報を保存する。

    Args:
        bone_list (list): ボーンリスト。形式: [[親[x, y, z], 関節[x1, y1, z1], 部位[x2, y2, z2]], ...]
        file_name (str): 保存するファイル名（拡張子なし）。
        file_path (str): 保存するディレクトリ
    """
    bone_data = []  # ボーンの情報を格納
    parent_map = {}  # 親の位置の一致を管理する辞書
    unique_bone_set = set()  # 出力の重複を防ぐためのセット

    for bone_index, bone in enumerate(bone_list):
        parent_position = tuple(bone[0])  # 親の位置
        joint_position = tuple(bone[1])  # 関節の位置（タプルに変換）
        part_position = tuple(bone[2])  # 部位の位置（タプルに変換）

        # 親の登録と取得
        if parent_position not in parent_map:
            parent_name = f"Bone_{len(parent_map)}_Parent"
            parent_map[parent_position] = parent_name
            bone_data.append((parent_name, parent_position, None))  # 親情報追加

        parent_name = parent_map[parent_position]

        # 子（関節と部位）のボーンデータを追加
        joint_name = f"Bone_{bone_index}_Joint"
        part_name = f"Bone_{bone_index}_Part"

        # 重複を防いで追加
        if (joint_name, joint_position, parent_name) not in unique_bone_set:
            bone_data.append((joint_name, joint_position, parent_name))
            unique_bone_set.add((joint_name, joint_position, parent_name))

        if (part_name, part_position, joint_name) not in unique_bone_set:
            bone_data.append((part_name, part_position, joint_name))
            unique_bone_set.add((part_name, part_position, joint_name))

    # 保存先のパスを結合
    txt_path = f"{file_path}{file_name}.txt"
    print(txt_path)

    # ボーン情報をtxtに保存
    with open(txt_path, "w") as f:
        for child_name, world_position, parent_name in bone_data:
            # 座標値に空白を追加
            formatted_position = f"[ {world_position[0]} , {world_position[1]} , {world_position[2]} ]"
            if parent_name:  # 子ボーン
                f.write(
                    f"Bone: {child_name}, World Position: {formatted_position}, Parent: {parent_name}\n"
                )
            else:  # 親ボーン
                f.write(
                    f"Bone: {child_name}, World Position: {formatted_position}, Parent: None\n"
                )

    print(f"ボーン情報を保存しました: {txt_path}")



    
    
def calculate_centroids(image_path, radius=10, showFlag=False):
    """
    二値化された画像において、各白領域の最初の重心を計算する関数。
    
    Args:
        image_path (str): 二値化画像のファイルパス
    
    Returns:
        list: 最初の重心の座標 [x1, y1] 形式
    """
    # 画像を読み込む
    binary_image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    
    if binary_image is None:
        raise ValueError(f"画像の読み込みに失敗しました: {image_path}")
    
    # 画像が二値化されていない場合、二値化処理を行う
    _, binary_image = cv2.threshold(binary_image, 127, 255, cv2.THRESH_BINARY)

    # 連結成分をラベリング
    num_labels, labels = cv2.connectedComponents(binary_image)

    # 画像をカラー画像に変換（赤色を表示するため）
    color_image = cv2.cvtColor(binary_image, cv2.COLOR_GRAY2BGR)
    
    for label in range(1, num_labels):  # 0は背景なので除外
        # ラベルごとの座標を抽出
        coords = np.column_stack(np.where(labels == label))
        
        # 最初の重心を計算
        centroid = np.mean(coords, axis=0)
        x, y = centroid[1], centroid[0]  # [x, y] 形式に変換

        # 重心を中心に円を描く
        cv2.circle(color_image, (int(x), int(y)), radius, (0, 0, 255), 2)  # 赤色の円を描く
        
        if showFlag:
            # 画像を表示
            cv2.imshow("Marked Image", color_image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        return [x, y]  # 最初の重心を返す

    # 重心が見つからない場合、デフォルト値を返す
    return [0, 0]


def MakeBornList(file_name, mask_num, mask_directory="output/ss/", height=100, scaleFactor=0.0004):
    """関節の数を基にボーンリストを作成（相対参照とスケール変換付き）

    Args:
        file_name: 拡張子なしのファイル名
        mask_num: マスクの数
        mask_directory: マスクが格納されているディレクトリ. Defaults to "output/ss/".
        height: 魚が生成される高さ. Defaults to 100.
        scaleFactor: スケール変換用の係数. Defaults to 0.0004.

    Returns:
        born_list: ボーンの情報（全体[1stボーン[親[],関節[],部位[]],2ndボーン[...]]）
    """
    def add_z_coordinate(point, z_value):
        """[x, y]形式のポイントにz座標を追加して[x, y, z]形式に変換"""
        if not point or len(point) < 2:
            print(f"警告: 無効なポイント {point} を検出しました。デフォルト値を使用します。")
            return [0, 0, z_value]  # デフォルト値
        return [point[0], point[1], z_value]

    def apply_relative_and_scale_transform(base_point, target_point):
        """基準点を基に相対座標化し、スケール変換を適用"""
        relative_point = [
            (target_point[0] - base_point[0]) * scaleFactor,
            (target_point[1] - base_point[1]) * scaleFactor,
            (target_point[2] - base_point[2]) * scaleFactor,
        ]
        return relative_point

    born_list = []
    z_value = height / 2

    # 最も大きい部分(親・胴体)のポイント
    mask_path = mask_directory + "2_regrow_" + file_name + "_" + str(mask_num - 1) + ".png"
    body_point = add_z_coordinate(calculate_centroids(mask_path), z_value)
    relative_body_point = apply_relative_and_scale_transform([0,0,0],body_point)

    # 例外処理
    if mask_num <= 0:
        return [[0, 0, 0]]  # ルート座標のみ

    # マスクがなくなるまで
    for i in range(0, mask_num):
        # 重複部分(関節)のポイント
        mask_path = mask_directory + "2_regrow" + file_name + "_common_" + str(i) + ".png"
        joint_point = add_z_coordinate(calculate_centroids(mask_path), z_value)

        # 部位部分のポイント
        mask_path = mask_directory + "2_regrow" + file_name + "_small_" + str(i) + ".png"
        part_point = add_z_coordinate(calculate_centroids(mask_path), z_value)

        # 相対参照 + スケール変換
        relative_joint_point = apply_relative_and_scale_transform(body_point, joint_point)
        relative_part_point = apply_relative_and_scale_transform(body_point, part_point)

        # 全体[1stボーン[親[],関節[],部位[]],2ndボーン[...]] になるようリストを作成
        # 〇番目のボーン
        born_list.append([relative_body_point, relative_joint_point, relative_part_point])
    
    return born_list




def main(obj_path, file_name):
    # サンプルデータ
    bone_list = [
        [[0, 0, 0], [1, 1, 1], [2, 2, 0]],
        [[1, 1, 1], [1, 2, 2], [0, 3, 1]],
        [[0, 0, 0], [2, 2, 2], [9, 9, 0]],
    ]

    # 実行
    create_bone_structure(bone_list, obj_path, file_name)


if __name__ == "__main__":
    main("output/mesh/me_template(1).obj", "output_bone_mesh")
