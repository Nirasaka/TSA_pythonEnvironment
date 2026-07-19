import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk
import numpy as np
import time
import sys
import os
# 現在のディレクトリをシステムパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from function import module  # カメラを使う

global g_directory
global g_cameraFlag

class Application(tk.Frame):
    global g_directory
    
    def __init__(self, master, video_source=0):
        """コンストラクタ

        Args:
            master (): 自分自身(キャンバス)
            video_source (int, optional): カメラの番号
        """
        super().__init__(master)

        self.master.geometry("700x700")
        self.master.title("[Sketch Aquarium]Camera App with GUI")
        self.master.iconbitmap('./icon.ico')

        # カメラ初期化
        self.vcap = cv2.VideoCapture(video_source)
        self.width = int(self.vcap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.vcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        # self.width = int(650)
        # self.height = int(350)
        
        # ウィジェット作成
        self.create_widgets()

        # 更新間隔（ms）
        self.delay = 15
        self.update()

    def create_widgets(self):
        """ウィジェット(ボタン)を作成
        """
        # カメラ表示フレーム
        self.frame_cam = tk.LabelFrame(self.master, text='Camera')
        self.frame_cam.place(x=10, y=10, width=self.width + 20, height=self.height + 50)
        
        # キャンバス
        self.canvas = tk.Canvas(self.frame_cam, width=self.width, height=self.height)
        self.canvas.grid(column=0, row=0, padx=10, pady=10)

        # ボタンフレーム
        self.frame_btn = tk.LabelFrame(self.master, text='Control')
        self.frame_btn.place(x=10, y=self.height + 70, width=self.width + 20, height=100)

        # スナップショットボタン
        self.btn_snapshot = tk.Button(self.frame_btn, text='Snapshot', font=('Helvetica', 14), command=self.snapshot)
        self.btn_snapshot.grid(column=0, row=0, padx=10, pady=10)

        # 閉じるボタン
        self.btn_close = tk.Button(self.frame_btn, text='Close', font=('Helvetica', 14), command=self.close_app)
        self.btn_close.grid(column=1, row=0, padx=10, pady=10)

    def update(self):
        """アップデート
        """
        # カメラからフレーム取得
        ret, frame = self.vcap.read()
        if ret:
            self.frame = frame
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(frame_rgb))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
        self.master.after(self.delay, self.update)

    def snapshot(self):
        """写真をとる
        """
        global g_directory
        # フレームを保存
        if hasattr(self, 'frame'):
            filename = f"frame-{time.strftime('%Y%m%d-%H%M%S')}.png"
            cv2.imwrite(g_directory+filename, self.frame)
            print(f"Saved snapshot as {filename}")
            # 画像を加工する
            self.process_image(self.frame)
        
    def process_image(self, frame):
        """画像を加工

        Args:
            frame : 画像(フレーム)
        """
        global g_directory
        global g_cameraFlag
        
        # クロッピング処理
        clipped_img = self.croppingIMG(frame)
        
        if clipped_img is not None:
        
            # 影除去処理
            result_img = self.removeShade(clipped_img)
            filename = f"camera.png"
            cv2.imwrite(g_directory+filename, result_img)
            print(f"Saved processed image as {filename}")
        
            self.regitFish()
            self.display_image('./output/onlyfish/onlycamera.png')
            
        # if g_cameraFlag:
            
        #         # 写真を入力として保存
        #         filename = module.namingFile("fish_data",".png","./inputimg")
        #         filepath = "./inputimg/"+filename
        #         cv2.imwrite(filepath,result_img)
        #         # Web用写真として保存
        #         cv2.imwrite('./static/images/paint.png',result_img)
                
        #         return

    def regitFish(self):
        """カメラ画像の魚を生成アルゴリズムに反映させる
        """
        # ライブラリを読み込む
        import function.extraction_fish as extraction_fish
        
        # file名を取得する
        file = "camera.png"
        filePath = "./output/camera/" + file

        # 魚を抽出
        only_img = extraction_fish.findFishParts(filePath, file)

    def croppingIMG(self, img):
        """画像から最大の四角形領域を抽出して保存する関数"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 50, 100)
        contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        warp = None

        for c in contours:
            arclen = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * arclen, True)

            if len(approx) == 4:
                warp = approx
                break

        if warp is not None:
            warped = self.transform_by4(img, warp[:, 0, :])
            warped_resized = cv2.resize(warped, (640, 640), interpolation=cv2.INTER_LINEAR)
            cv2.imwrite("./output/camera/cropping.png",warped_resized)
            return warped_resized
        else:
            print("四角形の輪郭が見つかりませんでした")
            return None

    def transform_by4(self, img, points,offset=10):
        """画像を透視変換を用いて切り抜く"""
        points = sorted(points, key=lambda x: x[1])
        top = sorted(points[:2], key=lambda x: x[0])
        bottom = sorted(points[2:], key=lambda x: x[0], reverse=True)
        points = np.array(top + bottom, dtype="float32")

        # 各点を内側に少しオフセットして黒枠が映らないように調整
        points[0] += [offset, offset]
        points[1] += [-offset, offset]
        points[2] += [-offset, -offset]
        points[3] += [offset, -offset]

        width = max(
            np.linalg.norm(points[0] - points[1]),
            np.linalg.norm(points[2] - points[3])
        )
        height = max(
            np.linalg.norm(points[0] - points[3]),
            np.linalg.norm(points[1] - points[2])
        )

        dst = np.array(
            [
                [0, 0],
                [width - 1, 0],
                [width - 1, height - 1],
                [0, height - 1]
            ],
            dtype="float32"
        )

        trans = cv2.getPerspectiveTransform(points, dst)
        return cv2.warpPerspective(img, trans, (int(width), int(height)))

    def removeShade(self, img):
        """画像から影を除去する"""
        rgb_planes = cv2.split(img)
        result_planes = []

        for plane in rgb_planes:
            dilated_img = cv2.dilate(plane, np.ones((7, 7), np.uint8))
            bg_img = cv2.medianBlur(dilated_img, 21)
            diff_img = 255 - cv2.absdiff(plane, bg_img)
            result_planes.append(diff_img)

        im_shadow = cv2.merge(result_planes)
        return im_shadow

    def close_app(self):
        """アプリを終了
        """
        self.vcap.release()
        self.master.destroy()
        
    def display_image(self, image_path, title="[Sketch Aquarium]Select Images"):
        """画像を表示する

        Args:
            image_path (str): 画像のパス
        """
        global g_cameraFlag

        # 現在のTkウィンドウを閉じる
        self.master.destroy()

        # 新しいTkウィンドウを作成
        new_root = tk.Tk()
        new_root.title(title)
        new_root.iconbitmap('./icon.ico')

        # 画像を開く
        img = Image.open(image_path)
        img = img.resize((300, 300), Image.Resampling.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)

        # 画像を表示
        img_label = tk.Label(new_root, image=img_tk)
        img_label.image = img_tk  # 参照を保持するために属性に保存
        img_label.pack()

        # Yesボタンの処理
        def on_yes():
            global g_cameraFlag
            g_cameraFlag = True
            
            # 写真を入力として保存
            filename = module.namingFile("fish_data",".png","./inputimg")
            filepath = "./inputimg/"+filename
            result_img = cv2.imread("./output/camera/camera.png")
            cv2.imwrite(filepath,result_img)
            # Web用写真として保存
            cv2.imwrite('./static/images/paint.png',result_img)
            
            new_root.quit()  # Yesを選択したらウィンドウを閉じる
            new_root.destroy()


        # Noボタンの処理
        def on_no():
            global g_cameraFlag
            g_cameraFlag = False  # フラグをリセット
            new_root.quit()  # Noを選択したらウィンドウを閉じる
            new_root.destroy()
            start()  # アプリを再起動

        # Yes/Noボタンを作成
        yes_button = tk.Button(new_root, text="Yes", command=on_yes)
        yes_button.pack(side=tk.LEFT, padx=10, pady=10)

        no_button = tk.Button(new_root, text="No", command=on_no)
        no_button.pack(side=tk.RIGHT, padx=10, pady=10)

        new_root.mainloop()

def start():
    global g_directory
    
    g_directory = "./output/camera/"
    root = tk.Tk()
    app = Application(root)
    root.mainloop()


if __name__ == "__main__":
    start()