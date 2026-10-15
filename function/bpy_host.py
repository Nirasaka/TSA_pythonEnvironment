import bpy 
from function import bpy_outline_from_mask
from function import bpy_create_model
from function import bpy_insert_bone
import os

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # bpy.ops.wm.read_factory_settings(use_empty=True)

def calculate_dynamic_white_width(img):
    """
    マスク画像の横幅に対する白領域の割合
    """
    width, height = img.size
    pixels = tuple(img.pixels)
    
    # マスク画像の白領域を取得
    min_px = width
    max_px = 0
    has_white = False
    
    for y in range(height):
        for x in range(width):
            idx = (y * width + x) * 4
            if pixels[idx] >= 0.5: # 白領域
                if x < min_px: min_px = x
                if x > max_px: max_px = x
                has_white = True
                
    if not has_white:
        return None
        
    white_width = max_px - min_px + 1
    ratio = white_width / width # 画像の横幅に対する白領域の割合 (0.0 ~ 1.0)
    return ratio

def main(file_name, save_path = r"./output/"):
    clear_scene()
    # print(os.path.dirname(os.path.realpath(__file__)))
    mask_path = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), r"../output/mask/" + file_name + "_mask3.png"))

    loaded_img = bpy.data.images.load(mask_path, check_existing=True)
    target_image_name = loaded_img.name
    
    if target_image_name not in bpy.data.images:
        print(f"エラー: 画像 '{target_image_name}' が見つかりません．")
        return None
        
    img = bpy.data.images[target_image_name]

    ratio = calculate_dynamic_white_width(img)

    if ratio is None:
        print(f"エラー: 画像 '{target_image_name}' に何も描かれていないか，マスク生成が失敗しています．")
        return None

    outline_model = bpy_outline_from_mask.main(img,file_name, ratio)

    no_born_model = bpy_create_model.main(outline_model, file_name, ratio)

    bpy_insert_bone.main(no_born_model, file_name)

    # 任意で.blendとして保存
    if save_path:
        bpy.ops.wm.save_as_mainfile(filepath=save_path + f"blend/blend_{file_name}.blend")
        print(f"[保存完了] Blendを書き出しました： {save_path}blend/blend_{file_name}.blend")

    #FBX出力
    if save_path:
        # 全オブジェクト選択
        bpy.ops.object.select_all(action='SELECT')

        # スケールと位置を適用（トランスフォーム適用）
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        
        # エクスポート
        bpy.ops.export_scene.fbx(
            filepath=save_path + f"fbx/fbx_{file_name}.fbx",
            use_selection=True,              # 選択オブジェクトのみ
            apply_unit_scale=True,           # FBX単位スケールを適用
            apply_scale_options='FBX_SCALE_ALL',  # Unityに合わせたスケーリング
            object_types={'MESH', 'ARMATURE'},    # メッシュとアーマチュアのみ
            bake_space_transform=True,       # トランスフォームを焼き付け（Unityとの軸合わせ）
            add_leaf_bones=False,            # Unityと互換性のためにLeafボーンを無効
            armature_nodetype='NULL',        # Unity互換のノードタイプ
            axis_forward='-Z',               # Unityの前方（-Z）
            axis_up='Y'                      # Unityの上方向（Y）
        )

        print(f"[完了] FBXを書き出しました：{save_path}fbx/fbx_{file_name}.fbx")