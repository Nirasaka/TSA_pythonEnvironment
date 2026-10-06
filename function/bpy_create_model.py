import bpy
import bmesh
import math
import os
from mathutils import Vector

def calculate_dynamic_scale(ratio, base_value, min_ratio=0.25):
    if ratio >= 0.5:
        return base_value

    scale = 2.0 * ratio
    
    scale = max(min(scale, 2.0), min_ratio)
    
    dynamic_value = base_value * scale
    return dynamic_value

def fill_concave_with_grid(obj, grid_size=0.005):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    
    if len(bm.verts) < 3:
        return
        
    if bm.faces:
        bmesh.ops.delete(bm, geom=bm.faces, context="FACES_ONLY")
        
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    
    all_loops = []
    visited_edges = set() # 頂点ではなく「辺」で訪問履歴を管理
    max_steps = len(bm.edges) # 無限ループ防止用の最大ステップ数
    
    for v in bm.verts:
        # ループを形成できない（繋がっている辺が2本未満の）頂点はスキップ
        if len(v.link_edges) < 2:
            continue
            
        for start_edge in v.link_edges:
            if start_edge in visited_edges:
                continue
                
            loop_verts = [v]
            curr_v = v
            curr_e = start_edge
            is_closed = False
            steps = 0
            
            while steps < max_steps:
                steps += 1
                visited_edges.add(curr_e)
                
                # 次の頂点を取得
                next_v = curr_e.other_vert(curr_v)
                
                # スタート地点に戻ってきたらループ完成
                if next_v == v:
                    is_closed = True
                    break
                    
                loop_verts.append(next_v)
                
                # 次の頂点に繋がっている辺のうち，未訪問の辺を探す
                next_edges = [e for e in next_v.link_edges if e != curr_e and e not in visited_edges]
                
                if not next_edges:
                    break # 行き止まり，またはすべて訪問済みなら探索終了
                    
                # 複数ある場合は最初の辺を選ぶ（交差している形状への簡易対応）
                curr_e = next_edges[0]
                curr_v = next_v
                
            if is_closed and len(loop_verts) >= 3:
                all_loops.append(loop_verts)
                
    if not all_loops:
        print("閉じた多角形が見つかりませんでした．線が途切れている可能性があります．")
        bm.free()
        return

    # 面を張る
    for loop_verts in all_loops:
        try:
            bm.faces.new(loop_verts)
        except ValueError:
            pass
            
    # 法線を+Y方向に統一
    for f in bm.faces:
        if f.normal.y > 0:
            f.normal_flip()

    min_x = min(v.co.x for v in bm.verts)
    max_x = max(v.co.x for v in bm.verts)
    min_z = min(v.co.z for v in bm.verts)
    max_z = max(v.co.z for v in bm.verts)

    # 異常な回数のスライスを防止するセーフティ（1万回を超えたら処理しない）
    cut_count_x = (max_x - min_x) / grid_size
    cut_count_z = (max_z - min_z) / grid_size
    if cut_count_x > 10000 or cut_count_z > 10000:
        print(f"エラー: オブジェクトに対して grid_size ({grid_size}) が小さすぎます．")
        bm.free()
        return
    
    start_x = math.floor(min_x / grid_size) * grid_size
    start_z = math.floor(min_z / grid_size) * grid_size
    
    # 4. X軸方向のカット
    x = start_x
    while x <= max_x + 1e-4:
        bmesh.ops.bisect_plane(
            bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
            dist=1e-6, plane_co=(x, 0, 0), plane_no=(1, 0, 0),
            clear_inner=False, clear_outer=False
        )
        x += grid_size
        
    # 5. Z軸方向のカット
    z = start_z
    while z <= max_z + 1e-4:
        bmesh.ops.bisect_plane(
            bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
            dist=1e-6, plane_co=(0, 0, z), plane_no=(0, 0, 1),
            clear_inner=False, clear_outer=False
        )
        z += grid_size
        
    bm.to_mesh(obj.data)
    bm.free()

def thickening(obj, thickness=0.03, proportion_size=0.06):
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


def main(obj, file_name, ratio = 1.0, isOutput = False):
    fill_concave_with_grid(obj, calculate_dynamic_scale(ratio, 0.005))
    thickening(obj, calculate_dynamic_scale(ratio, 0.03), calculate_dynamic_scale(ratio, 0.06))

    if isOutput:
        path = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), r"../output/blend/" + file_name + "_withoutBorn.blend"))
        bpy.ops.wm.save_as_mainfile(filepath=path)
        print("ボーン挿入前モデルを出力しました：", f"{obj.name}")

    return obj
