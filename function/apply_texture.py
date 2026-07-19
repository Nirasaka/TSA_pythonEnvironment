import numpy as np
from PIL import Image
import cv2

def load_obj(file_path):
    """OBJを読み込む

    Args:
        file_path (str): OBJのパス

    Returns:
        Tuple: vertices(頂点), faces(メッシュ), normals(法線)
    """
    # 変数宣言
    vertices = []
    faces = []
    normals = []
    
    # ファイルオープン
    with open(file_path, 'r') as file:
        
        # 1行読み込む
        for line in file:
            
            # 頂点なら頂点リストに追加
            if line.startswith('v '):
                vertices.append(list(map(float, line.strip().split()[1:])))
            
            # 法線なら法線リストに追加
            elif line.startswith('vn '):
                normals.append(list(map(float, line.strip().split()[1:])))
            
            # メッシュならメッシュリストに追加
            elif line.startswith('f '):
                face = [list(map(int, v.split('/'))) for v in line.strip().split()[1:]]
                faces.append(face)
                
    return np.array(vertices), faces, np.array(normals)

def save_obj(file_path, vertices, faces, uvs, normals=None):
    """objを出力する

    Args:
        file_path (str): ファイルパス
        vertices (List): 頂点
        faces (List): メッシュ
        uvs (List): UV
        normals (List): 法線ベクトル
    """
    
    file = open(file_path, 'w')
    
    # 設定文章
    file.write("######\n")
    file.write("#\n")
    file.write("# Made by TomitaAkito\n")
    file.write("# For Resurch 2024-2025\n")
    file.write("# Info: VisualComputingLab.\n")
    file.write("# URL : https://lss.oit.ac.jp/~t2013033/vcl/\n")
    file.write("# AT  : https://atdigital.cloudfree.jp/oit/vcl/index.html\n")
    file.write("#\n")
    file.write("######\n")

    with open(file_path, 'a') as file:
        file.write("# -----Vertex-----\n")
        for vertex in vertices:
            file.write(f"v {vertex[0]} {vertex[1]} {vertex[2]}\n")
            
        if normals is not None:
            file.write("\n# -----Normals-----\n")
            for normal in normals:
                file.write(f"vn {normal[0]} {normal[1]} {normal[2]}\n")
                # file.write(f"vn -0.5 -0.5 -0.5\n")
            
        file.write("\n# -----UV-----\n")
        for uv in uvs:
            file.write(f"vt {uv[0]} {uv[1]}\n")
            
        file.write("\n# -----face-----\n")
        for face in faces:
            face_str = ' '.join([f"{v[0]}/{i+1}" for i, v in enumerate(face)])
            file.write(f"f {face_str}\n")

def create_uvs_from_image(vertices, image_path):
    """画像からUV展開を施し，UVリストを出力する

    Args:
        vertices (List): 頂点
        image_path (str): 画像のパス

    Returns:
        List: UV座標のリスト
    """
    # 画像を読み込んでサイズを取得
    image = Image.open(image_path)
    width, height = image.size
    
    uvs = []
    
    # vertexの座標を[0-1]に収まるよう正規化
    # ->UV座標系に変換
    for vertex in vertices:
        u = vertex[0] / width
        v = 1 - (vertex[1] / height)
        uvs.append([u, v])
    return np.array(uvs)

def makeUVs(obj_file_path,image_file_path,output_file_path,file):
    """UV展開する

    Args:
        obj_file_path (str): OBJのパス
        image_file_path (str): imgのパス
        output_file_path (str): 出力のパス
        file (str): 拡張子を除いたファイル名
    """
    # OBJファイルの読み込み
    vertices, faces,normal = load_obj(obj_file_path)

    # UV座標の作成
    uvs = create_uvs_from_image(vertices, image_file_path)

    # 新しいOBJファイルの保存
    save_obj(output_file_path, vertices, faces, uvs,normal)
    
    # テクスチャ用に画像を反転
    img = cv2.imread(image_file_path)
    rotateImg = cv2.flip(img, 0)
    newImgPath = './upload/only' + file + '.png'
    cv2.imwrite(newImgPath,rotateImg)
    

if __name__ == "__main__":
    print('main.pyを実行してください')