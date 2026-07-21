import threading
from flask import Flask, send_file, jsonify,render_template,redirect,url_for,request
import sys
import os
from colorama import Fore, Back, Style
import zipfile
from pathlib import Path

from function import painttool as paint  # ペイントツール
from function import module # 共通するモジュール
from function import settimer  # 時間測定
from function import extraction_fish  # さかなの輪郭を使った処理(抽出・部位推定)
from function import createobj as obj  # 3DOBJを作る
from function import create_armature as ca    # ボーンを生成する

app = Flask(__name__)

# 現在のディレクトリをシステムパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

#* ======================================================================================== 
#* グローバル変数と魚の管理
#* ======================================================================================== 
is_sever_shutdown = False       # サーバーのシャットダウンフラグ
is_painttool_running = False    # ペイントツールが起動中かどうかのフラグ
server_fish_store = []          # サーバで管理している魚のハッシュリスト
default_fish_list = []          # デフォルトでいる魚のリスト

@app.route('/')
def index():
    """ホームページを表示

    Returns:
       html : Webサイト
    """
    module.printTerminal("HPを表示します")
    return render_template('index.html')

#! 魚生成
def generateFish(file_name):
    if os.path.exists(f"./upload/{file_name}.zip"):
        module.printTerminal("既に生成されているモデルです：" + file_name, 3)
        return

    module.printTerminal("魚を生成")
    print(file_name)

    #? ------------------------------------------------------
    #? 画像から魚抽出->輪郭抽出
    #? ------------------------------------------------------
    module.printTerminal("画像から魚を抽出",2)
    preproTimer = settimer.timer("-->Preprocessing-Timer")

    filePath = "./inputimg/" + file_name + ".png"
    img = extraction_fish.findFishParts(filePath, file_name)
    import cv2
    cv2.imwrite("./static/images/new.png", img)

    preproTimer.stop()

    #? ------------------------------------------------------
    #? 3DOBJに変換
    #? ------------------------------------------------------
    module.printTerminal("3DOBJを作成",2)
    
    createTimer = settimer.timer("-->create-Timer")

    filePath = "./output/mask/" + file_name + "_mask3.png"
    maskPath = "./output/mask/" + file_name + "_mask3.png"
    obj.creating3D(filePath, maskPath, file_name, 100, False)
    
    meshpath = "./output/mesh/me_" + file_name + ".obj"
    
    createTimer.stop()

    # ? ------------------------------------------------------
    # ? ボーンを生成
    # ? ------------------------------------------------------
    module.printTerminal("ボーンを生成(ついでにUV展開)", 2)

    bornTimer = settimer.timer("-->born-Timer")

    ca.main(meshpath, file_name)

    fbxpath = "./output/fbx/fbx_" + file_name + ".fbx"

    bornTimer.stop()

    # ? ------------------------------------------------------
    # ? サーバの魚辞書に登録
    # ? ------------------------------------------------------

    zipFish(file_name)

    module.printTerminal("モデルの生成が終了しました：" + file_name, 2)

#! 魚をZIP化する
def zipFish(file_name):
    """魚をZIP化します"""
    # パスを取得
    fbx_path = f"./output/fbx/fbx_{file_name}.fbx"
    png_path = f"./output/onlyfish/normalized_{file_name}.png"
    zipPath = f"./upload/{file_name}.zip"
    
    # 情報をターミナルに出力
    print(file_name)
    
    # 必須ファイルの存在を確認
    if not os.path.exists(fbx_path) or not os.path.exists(png_path):
        return jsonify({"error": "File not found"}), 404
    
    # ZIPファイルを作成
    with zipfile.ZipFile(zipPath, 'w') as zipf:
        zipf.write(fbx_path, os.path.basename(fbx_path))  # 魚のfbx
        zipf.write(png_path, os.path.basename(png_path))  # 魚の画像

#! 魚をダウンロードするリクエストを受け取った場合の処理
@app.route('/download',methods=['POST'])
def uploadFish():
    data = request.get_json()
    # data = {"fish_list":[]}

    # print(data)
    client_fish_list = data["fish_list"]
    # print(client_fish_list)

    return newFish(client_fish_list)

@app.route('/download/new',methods=['GET'])
def newFish(client_fish_list=[]):
    if server_fish_store == []:
        return jsonify({"error": "Server has no fish"}), 404
    
    for file_name in reversed(server_fish_store):
        if not file_name in client_fish_list:
            zip_path = f"./upload/{file_name}.zip"

            if not os.path.exists(zip_path):
                server_fish_store.remove(file_name)
                continue

            return send_file(
                zip_path,
                mimetype="application/zip",
                as_attachment=True,
                download_name=f"{file_name}.zip"
                )

    #? 新しい魚がいない
    return {}, 204
        
    


@app.route('/paint')
def pushedPaintButton():
    global is_painttool_running
    if is_painttool_running:
        return redirect(url_for('index'))
    
    is_painttool_running = True
    
    return redirect(url_for('index'))


#! ペイントツールを起動
def launchPaintTool():
    global is_painttool_running, generation_queue
    module.printTerminal("ペイントツールを起動します")
    
    file_name = paint.main()
    generateFish(file_name)

    server_fish_store.append(file_name)


#! 接続確認
@app.route('/download/defaultlist', methods=['GET'])
def sendDefaultList():
    data = {"defaultlist":default_fish_list}
    return jsonify(data)

@app.route('/hello', methods=['GET'])
def hello():
    return {}, 200

#! シャットダウン
@app.route('/shutdown', methods=['GET'])
def shutdown():
    """システムをシャットダウン

    Returns:
        str : メッセージ
    """
    global is_sever_shutdown
    module.printTerminal("シャットダウンします")
    is_sever_shutdown = True

#! flaskサーバを別スレッドで起動
def runServer():
    """サーバー起動関係

    Args:
        ip (str): サーバのIPアドレス. Defaultは '150.89.239.35'.
        flag : デバッグモードを使用するか判定するフラグ
    """
    # 全く意味がないアスキーアートを表示する
    print(Fore.LIGHTCYAN_EX + '               __   __')
    print(Fore.LIGHTCYAN_EX + '              __ \ / __')
    print(Fore.LIGHTCYAN_EX + '             /  \ | /  ')
    print(Fore.LIGHTCYAN_EX + '                 \|/')
    print(Fore.LIGHTCYAN_EX + '            _,.---v---._')
    print(Fore.LIGHTCYAN_EX + '   /\__/\  /            |')
    print(Fore.LIGHTCYAN_EX + '   \_  _/ /              |')
    print(Fore.LIGHTCYAN_EX + '     \ \_|           @ __|')
    print(Fore.LIGHTCYAN_EX + '  hjw \                \_')
    print(Fore.LIGHTCYAN_EX + '  `97  \     ,__/       /')
    print(Fore.LIGHTCYAN_EX + '     ~~~`~~~~~~~~~~~~~~/~~~~')

    print(Fore.LIGHTYELLOW_EX + '以下のURLにログインしてください')
    print(Fore.LIGHTYELLOW_EX + "-> http://127.0.0.1:5000")
    print(Fore.WHITE)
    print(Style.RESET_ALL+"",end="")

    app.run(host="0.0.0.0",port=5000, debug=True, use_reloader=False, threaded=True)


#! 生成されている魚を取得する初期化
def initServer():
    module.printTerminal("初期化：生成済みの魚を取得(”*”はデフォルト)")
    global server_fish_store, default_fish_list

    # 検索したいフォルダのパス
    folder_path = Path(r"./upload")

    # フォルダ内のzipファイルを取得
    server_fish_store = [p.stem for p in folder_path.rglob("*.zip")].copy()

    # デフォルトの魚を取得
    folder_path = Path(r"./defaultfish")

    default_fish_list = [p.stem for p in folder_path.rglob("*.zip")].copy()

    # 表示
    for zip_name in server_fish_store:
        if zip_name in default_fish_list:
            zip_name += "*"
        print(zip_name)


if __name__ == '__main__':
    initServer()

    thread = threading.Thread(target=runServer, daemon=True)
    thread.start()

    try:
        while not is_sever_shutdown:
            if is_painttool_running:
                launchPaintTool()
                is_painttool_running = False

    except KeyboardInterrupt:
        print('Ctrl + C によって終了します')
