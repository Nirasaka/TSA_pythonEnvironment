import bpy
import bmesh
from mathutils import Vector
import os

def calculate_dynamic_resolution(img, ratio, base_resolution):
    """
    マスク画像の横幅と白領域のサイズを考慮し、白領域が画像の横幅の半分(0.5)に満たない場合、少しずつ増大
    """
    
    # 割合に応じた動的解像度の計算
    if ratio < 0.5:
        multiplier = 0.8 / max(ratio, 0.05)
        dynamic_res = int(base_resolution * multiplier)
        # あまりに大きくなりすぎて処理が重くなるのを防ぐための上限を設定
        dynamic_res = min(dynamic_res, 700)
    else:
        dynamic_res = base_resolution
    print("サンプリング解像度：" + str(dynamic_res))
    return dynamic_res

def create_outline_from_mask(img, obj_name="MaskOutline", ratio = 1.0, resolution=150, physical_size=0.3, smooth_repeat=10, smooth_factor=0.5):
    """
    img : 画像
    obj_name : 出力モデルの名前
    ratio : マスク画像の横幅に対する白領域の横幅の割合
    resolution : 画像のサンプリング解像度（大きいほど計算量が増大，マスクの白部分が画像の横幅の半分に満たない場合は増幅される）
    physical_size : 画像一辺（x方向）を3D空間上でどれくらいの大きさととらえるか（メートル単位）
    smooth_repeat : 輪郭頂点に適用するスムージングのリピート数（大きいほど滑らか）
    smooth_factor : スムージング強度
    """

    resolution = calculate_dynamic_resolution(img,ratio,resolution)
    
    width, height = img.size
    if width == 0 or height == 0:
        print("エラー: 画像データが空です．")
        return None
        
    pixels = tuple(img.pixels) 
    bm = bmesh.new()
    
    aspect = width / height
    res_x = resolution
    res_z = max(1, int(resolution / aspect))
    
    # X-Z平面に頂点グリッドを生成
    verts = []
    for z in range(res_z + 1):
        for x in range(res_x + 1):
            px = (x / res_x) * physical_size
            pz = (z / res_z) * (physical_size / aspect)
            verts.append(bm.verts.new((px, 0.0, pz)))
            
    bm.verts.ensure_lookup_table()
    
    # 面を張りながら，画像の色を判定
    faces_to_delete = []
    for z in range(res_z):
        for x in range(res_x):
            v1 = verts[z * (res_x + 1) + x]
            v2 = verts[z * (res_x + 1) + (x + 1)]
            v3 = verts[(z + 1) * (res_x + 1) + (x + 1)]
            v4 = verts[(z + 1) * (res_x + 1) + x]
            
            face = bm.faces.new((v1, v2, v3, v4))
            
            u = (x + 0.5) / res_x
            v_coord = (z + 0.5) / res_z
            
            pixel_x = int(u * width)
            pixel_y = int(v_coord * height)
            idx = (pixel_y * width + pixel_x) * 4
            
            if pixels[idx] < 0.5:
                faces_to_delete.append(face)
                
    # 黒い部分の面を削除
    bmesh.ops.delete(bm, geom=faces_to_delete, context="FACES")
    bm.edges.ensure_lookup_table()
    
    # 境界以外の辺（内部の辺）をすべて取得して削除する
    # e.is_boundary は「両側の面が揃っていない（外周の）辺」を返す．
    # これの逆（反転）を取得するため，is_boundary ではない辺を削除対象にする．
    edges_to_delete = [e for e in bm.edges if not e.is_boundary]
    if edges_to_delete:
        bmesh.ops.delete(bm, geom=edges_to_delete, context="EDGES_FACES")
        
    # 残った面をすべて削除し，純粋な「辺のループ」だけにする
    faces_all = bm.faces[:]
    if faces_all:
        bmesh.ops.delete(bm, geom=faces_all, context="FACES_ONLY")
        
    # 孤立した頂点をクリーンアップ
    verts_to_delete = [v for v in bm.verts if len(v.link_edges) == 0]
    if verts_to_delete:
        bmesh.ops.delete(bm, geom=verts_to_delete, context="VERTS")
    
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    
    # 頂点をスムーズにする (スムージング係数 0.5, リピート回数 10)
    for _ in range(smooth_repeat):
        new_coords = {}
        for v in bm.verts:
            # 繋がっている隣接頂点の位置の平均を計算
            linked_verts = [e.other_vert(v) for e in v.link_edges]
            if not linked_verts:
                continue
            avg_co = sum((nv.co for nv in linked_verts), Vector((0, 0, 0))) / len(linked_verts)
            # 現在の位置と隣接平均の間を smooth_factor で補間
            new_coords[v] = v.co.lerp(avg_co, smooth_factor)
            
        # 一括して座標を更新
        for v, co in new_coords.items():
            v.co = co

    # 口のあたりをz=0に
    if len(bm.verts) > 0:
        min_x_vert = min(bm.verts, key=lambda v: v.co.x)
        z_offset = min_x_vert.co.z
        x_offset = min_x_vert.co.x
        for v in bm.verts:
            v.co.z -= z_offset
            v.co.x -= x_offset
    
    # メッシュを生成してシーンに追加
    mesh = bpy.data.meshes.new(obj_name)
    bm.to_mesh(mesh)
    bm.free()
    
    obj = bpy.data.objects.new(obj_name, mesh)
    collection = bpy.context.collection if bpy.context.collection else bpy.data.collections[0]
    collection.objects.link(obj)
    
    return obj

def main(img, file_name, ratio, isOutput = False):
    #print(os.path.dirname(os.path.realpath(__file__)))

    new_obj = create_outline_from_mask(
            img = img, 
            obj_name="me_" + file_name, 
            ratio = ratio,
            resolution=450, 
            physical_size=0.32,
            smooth_repeat=10,  # リピート回数 10
            smooth_factor=0.5  # スムージング係数 0.5
        )

    if isOutput and new_obj:
        path = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), r"../output/blend/" + file_name + "_outline.blend"))
        bpy.ops.wm.save_as_mainfile(filepath=path)
        print("アウトラインモデルを出力しました：", f"{new_obj.name}")
    
    return new_obj


if __name__ == "__main__":
    print(os.path.dirname(os.path.realpath(__file__)))
    new_obj = main("8b0a5e257613fd25d4b4d0d82ea1c7fe73ea9e3a81cb213ea46859d0b86e7fa7")
    
    if new_obj:
        print(f"{new_obj.name} の生成が完了しました！")