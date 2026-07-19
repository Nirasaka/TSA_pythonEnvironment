import bpy
import mathutils
import os
import bmesh
from mathutils import Vector

def fix_mesh_normal(obj: bpy.types.Object):
    bpy.ops.object.mode_set(mode='EDIT')

    mesh = bmesh.from_edit_mesh(obj.data)

    # 見る方向（+Y軸方向から見て裏向きを探す場合）
    view_dir = Vector((0, 0, 1))

    # === オブジェクトの重心（ローカル座標系）を計算 ===
    verts = [v.co for v in mesh.verts]
    center_y = sum(v.z for v in verts) / len(verts)

    # 裏向き面を格納
    faces_to_flip = []

    # === 面を選択 ===
    for f in mesh.faces:
        n = f.normal.normalized()
        avg_y = sum(v.co.z for v in f.verts) / len(f.verts)
        if avg_y > center_y:
            if n.dot(view_dir) < 0:
                faces_to_flip.append(f)

    # 見る方向（-Y軸方向から見て裏向きを探す場合）
    view_dir = Vector((0, 0, -1))

    # === 面を選択 ===
    for f in mesh.faces:
        n = f.normal.normalized()
        avg_y = sum(v.co.z for v in f.verts) / len(f.verts)
        if avg_y < center_y:
            if n.dot(view_dir) < 0:
                faces_to_flip.append(f)

    # 対象面を反転
    for f in faces_to_flip:
        f.normal_flip()

    # メッシュ更新
    bmesh.update_edit_mesh(obj.data, loop_triangles=True)
    bpy.ops.object.mode_set(mode='OBJECT')

    # print(f"[完了] {obj.name} のメッシュのノーマルを補正しました ")


def create_material(obj: bpy.types.Object, imgName):
    # マテリアル作成
    mat = bpy.data.materials.new(name="ImageMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # テクスチャノード
    texture_node = nodes.new(type='ShaderNodeTexImage')
    texture_node.name = "texture"

    # print("テクスチャをロード：" + os.getcwd() + "/output/onlyfish/normalized_" + imgName + ".png")
    texture_node.image = bpy.data.images.load(os.getcwd() + "/output/onlyfish/normalized_" + imgName + ".png")

    # プリンシプルBSDF
    bsdf = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)

    # ノードを接続
    links.new(texture_node.outputs["Color"], bsdf.inputs["Base Color"])

    # マテリアルスロット作成
    obj.data.materials.append(mat)

    # print(f"[完了] {obj.name} に画像マテリアルを適用しました: ")


def deploy_uv(obj: bpy.types.Object):
    # メッシュアクセス
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    # UVレイヤー取得または作成
    uv_layer = bm.loops.layers.uv.verify()

    # 投影方向: +Y方向から見た正面
    proj_axis = Vector((0, 0, 1))

    # 投影座標を格納
    uvs = []

    for face in bm.faces:
        for loop in face.loops:
            v = loop.vert.co
            # X-Z平面に投影
            uv = Vector((v.x, v.y))
            loop[uv_layer].uv = uv
            uvs.append(uv)

    # ============================
    #   UVを [0, 1] に正規化
    # ============================

    if uvs:
        # 最小・最大を求める
        min_u = min(v.x for v in uvs)
        max_u = max(v.x for v in uvs)
        min_v = min(v.y for v in uvs)
        max_v = max(v.y for v in uvs)

        size_u = max_u - min_u
        size_v = max_v - min_v

        # サイズゼロ除外（防止）
        if size_u == 0: size_u = 1.0
        if size_v == 0: size_v = 1.0

        # 正規化（0〜1範囲に収める）
        for face in bm.faces:
            for loop in face.loops:
                uv = loop[uv_layer].uv
                uv.x = (uv.x - min_u) / size_u
                uv.y = (uv.y - min_v) / size_v

    bm.to_mesh(mesh)
    bm.free()

    # print(f'[完了]{obj.name}UV展開完了')

# アーマチュア挿入処理
def insert_bones_and_bind(obj: bpy.types.Object):
    if obj.type != 'MESH':
        raise TypeError("対象はMESHオブジェクトである必要があります。")

    mesh_obj = obj
    mesh_name = mesh_obj.name

    # 重心とx方向の分割点計算
    bbox_world = [mesh_obj.matrix_world @ mathutils.Vector(corner) for corner in mesh_obj.bound_box]
    center = sum(bbox_world, mathutils.Vector()) / 8.0

    x_coords = [v.x for v in bbox_world]
    x_min = min(x_coords)
    x_max = max(x_coords)
    x_length = x_max - x_min

    z_coords = [v.z for v in bbox_world]
    z_min = min(z_coords)
    z_max = max(z_coords)
    z_length = z_max - z_min

    # 分割数
    splits = 3
    if x_length >= z_length * 2:
        splits = 4

    x_split1 = x_min + (1 / splits) * x_length
    x_split2 = x_min + (2 / splits) * x_length
    x_split3 = x_min + (3 / splits) * x_length

    # アーマチュア作成
    bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
    armature = bpy.context.object
    armature.name = "Armature"
    armature.data.name = "Armature"

    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = armature.data.edit_bones
    edit_bones.remove(edit_bones[0])

    bone1 = edit_bones.new("Bone1")
    bone1.head = mathutils.Vector((x_min, center.y, center.z))
    bone1.tail = mathutils.Vector((x_split1, center.y, center.z))

    bone2 = edit_bones.new("Bone2")
    bone2.head = bone1.tail
    bone2.tail = mathutils.Vector((x_split2, center.y, center.z))
    bone2.parent = bone1
    bone2.use_connect = True

    bone3 = edit_bones.new("Bone3")
    bone3.head = bone2.tail
    bone3.tail = mathutils.Vector((x_split3, center.y, center.z))
    bone3.parent = bone2
    bone3.use_connect = True

    if splits == 4:
        bone4 = edit_bones.new("Bone4")
        bone4.head = bone3.tail
        bone4.tail = mathutils.Vector((x_max, center.y, center.z))
        bone4.parent = bone3
        bone4.use_connect = True
        
    bpy.ops.object.mode_set(mode='OBJECT')
    armature.location = mesh_obj.location

    bpy.ops.object.select_all(action='DESELECT')
    mesh_obj.select_set(True)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature

    bpy.ops.object.parent_set(type='ARMATURE_AUTO')

    armature.scale *= 0.0005

    # print(f"[完了] {mesh_name} にボーン挿入＆自動ウェイト完了。")

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # bpy.ops.wm.read_factory_settings(use_empty=True)


# --- OBJファイルの読み込みと処理 ---
def main(obj_path, file_name, save_path = r"./output/"):
    clear_scene()
    
    # print(os.path.dirname(os.path.realpath(__file__)))

    # OBJ読み込み
    bpy.ops.wm.obj_import(filepath=obj_path)

    # 読み込んだメッシュを取得（通常は最後に読み込まれたもの）
    mesh_obj = next((obj for obj in reversed(bpy.context.selected_objects) if obj.type == 'MESH'), None)
    if not mesh_obj:
        raise RuntimeError("OBJから有効なMESHオブジェクトが見つかりません。")

    # メッシュのノーマルを補正
    fix_mesh_normal(mesh_obj)

    # UV展開
    deploy_uv(mesh_obj)

    # マテリアル適用
    create_material(mesh_obj, file_name)

    # アーマチュア挿入処理
    insert_bones_and_bind(mesh_obj)

    # 任意で.blendとして保存
    if save_path:
        bpy.ops.wm.save_as_mainfile(filepath=save_path + f"blend/blend_{file_name}.blend")
        # print(f"[保存完了] Blendを書き出しました： {save_path}blend/blend_{file_name}.blend")

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

        # print(f"[完了] FBXを書き出しました：{save_path}fbx/fbx_{file_name}.fbx")

# テスト実行
if __name__ == "__main__":
    obj_path = r"./output/mesh/me_213c03589eecc79ec44be9a7add6b6bdc0e366652a20d5af48bb078947a7eacf.obj"
    save_path = r"./output/"
    main(obj_path, "213c03589eecc79ec44be9a7add6b6bdc0e366652a20d5af48bb078947a7eacf", save_path)
