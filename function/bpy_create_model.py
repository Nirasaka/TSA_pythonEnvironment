import bpy
import bmesh
import os
from mathutils import Vector
from function import bpy_host


def thickening(obj, thickness=0.03, proportion_size=0.06, buffer=0.0006):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    
    # 原点を動かさず，全ての頂点を -y 方向に thickness 分だけ移動
    for v in obj.data.vertices:
        v.co.y -= thickness
        
    # 編集モードに移行し，外郭頂点を選択して +y 方向に移動
    bpy.ops.object.mode_set(mode='EDIT')
    bm_edit = bmesh.from_edit_mesh(obj.data)
    bm_edit.verts.ensure_lookup_table()
    
    # 外郭（境界）の頂点のみを選択状態にする
    for v in bm_edit.verts:
        v.select = v.is_boundary
    bm_edit.select_flush(True)
    
    # プロポーショナル編集適用（シャープ，サイズ0.03，接続あり）で +y 方向に移動
    bpy.ops.transform.translate(
        value=(0, thickness, 0),
        use_proportional_edit=True,
        proportional_edit_falloff='SHARP',
        proportional_size=proportion_size,
        use_proportional_connected = True
    )

    bpy.ops.object.mode_set(mode='OBJECT')

    # スムージング
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    
    for _ in range(5):
        new_coords = {}
        for v in bm.verts:
            # 輪郭（境界）の頂点は動かさない
            if v.is_boundary:
                continue
                
            linked_verts = [e.other_vert(v) for e in v.link_edges]
            if not linked_verts:
                continue
                
            avg_co = sum((nv.co for nv in linked_verts), Vector((0, 0, 0))) / len(linked_verts)
            new_coords[v] = v.co.lerp(avg_co, 0.5)
            
        for v, co in new_coords.items():
            v.co = co

    # y0に近すぎる頂点をクランプ
    for v in bm.verts:
        if not v.is_boundary:
            if v.co.y > -buffer:
                v.co.y = -buffer

    bm.to_mesh(obj.data)
    bm.free()


    # モディファイアを新規追加
    mirror_mod = obj.modifiers.new(name="AutoMirror", type='MIRROR')
    
    # Y軸基準でミラーし、重なる部分をマージ（結合）する
    mirror_mod.use_axis[0] = False # X軸ミラーはオフ
    mirror_mod.use_axis[1] = True  # Y軸ミラーをオン
    mirror_mod.use_axis[2] = False # Z軸ミラーはオフ
    
    mirror_mod.use_clip = True     # 境界の頂点がミラー面を越えて離れないようにクリップ
    mirror_mod.use_mirror_merge = True    # y=0 で重なる頂点を自動結合
    mirror_mod.merge_threshold = 0.001 # 結合のしきい値
    
    # オブジェクトモードの状態でモディファイアを実体化（メッシュに適用）する
    bpy.ops.object.modifier_apply(modifier="AutoMirror")

    
    # メッシュを軽量化
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.dissolve_limited(use_dissolve_boundaries=True)
    bpy.ops.mesh.dissolve_degenerate()

    bpy.ops.object.mode_set(mode='OBJECT')


def main(obj, file_name, ratio = 1.0, isOutput = False):
    thickening(obj, bpy_host.calculate_dynamic_scale(ratio, 0.03), bpy_host.calculate_dynamic_scale(ratio, 0.06))

    if isOutput:
        path = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), r"../output/blend/" + file_name + "_withoutBorn.blend"))
        bpy.ops.wm.save_as_mainfile(filepath=path)
        print("ボーン挿入前モデルを出力しました：", f"{obj.name}")

    return obj
