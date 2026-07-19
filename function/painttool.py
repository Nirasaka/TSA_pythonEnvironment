import tkinter as tk
from tkinter import colorchooser, filedialog, ttk,messagebox
from PIL import Image, ImageDraw, ImageTk
import cv2
import hashlib

# ライブラリのインポート
import sys
import os

# 現在のディレクトリをシステムパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import module

# キャンバスサイズを設定する変数
CANVAS_WIDTH = 640
CANVAS_HEIGHT = 640
g_Flag = False

class PaintApp:
    def __init__(self, root):
        """
        PaintAppクラスの初期化メソッド。メインフレーム、メニューバー、ツールバー、キャンバスを設定し、
        描画ツールや色の初期設定を行います。

        Args:
            root (Tk): メインウィンドウオブジェクト。
        """
        self.root = root
        self.root.title("[Sketch Aquarium]Paint Tool")
        self.root.iconbitmap('./icon.ico')
        
        # 初期設定
        self.pen_color = "black"  # 初期ペンカラー
        self.pen_size = 5  # 初期ペンサイズ
        self.current_tool = "Pen"
        self.eraser_on = False
        self.fill_mode = False
        self.drawing_shape = False  # 図形描画中かどうかを示すフラグ
        self.history = []  # 描画履歴を保存するためのリスト

        self.last_x = None
        self.last_y = None

        # メインフレームの作成と配置
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # メニューバーの作成と設定
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="ファイル", menu=file_menu)
        file_menu.add_command(label="画像を保存", command=self.save_image)  # 画像保存メニューの追加
        file_menu.add_command(label="画像を開く", command=self.open_image)  # 画像を開くメニューの追加
        
        color_menu = tk.Menu(menu_bar, tearoff=0)                                   # パレット以外の色選択メニューの追加
        menu_bar.add_command(label="パレット外の色選択", command=self.choose_color)

        edit_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="編集", menu=edit_menu)
        edit_menu.add_command(label="全削除",command=self.clear_all) # すべて削除を追加
        edit_menu.add_command(label="元に戻す", command=self.undo)  # 元に戻すメニューの追加
        
        regit_fish = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_command(label="魚を登録する", command=self.regitFish)  # 魚を登録するコマンドを追加

        # ツールバーの作成と配置
        toolbar_frame = ttk.Frame(main_frame, padding="2 2 2 2")
        toolbar_frame.pack(side=tk.TOP, fill=tk.X)
        
        tool_button_frame = ttk.Frame(toolbar_frame)
        tool_button_frame.pack(side=tk.LEFT)

        self.tool_text_label = tk.Label(tool_button_frame, text="現在のツール:ペン")
        self.tool_text_label.pack(padx=5)

        self.pen_button = ttk.Button(tool_button_frame, text="ペン", command=self.use_pen)
        self.pen_button.pack(side=tk.LEFT)  # ペンボタンの配置

        self.eraser_button = ttk.Button(tool_button_frame, text="消しゴム", command=self.use_eraser)
        self.eraser_button.pack(side=tk.LEFT)  # 消しゴムボタンの配置

        self.fill_button = ttk.Button(tool_button_frame, text="塗りつぶし", command=self.use_fill)
        self.fill_button.pack(side=tk.LEFT)  # 塗りつぶしボタンの配置
        
        self.undo_button = ttk.Button(tool_button_frame, text="元に戻す", command=self.undo)
        self.undo_button.pack(side=tk.LEFT)  # 元に戻すボタンの配置

        self.set_tool_active()

        # 初期設定
        self.pen_color = "black"  # 初期ペンカラー

        # カラーパレットの作成と配置
        color_palette_frame = ttk.Frame(toolbar_frame)
        color_palette_frame.pack(side=tk.TOP, padx=10)

        self.colors = ["black", "white", "red", "green", "blue", "yellow", "orange", "purple", "brown"]
        self.color_buttons = {}
        for color in self.colors:
            btn = tk.Button(color_palette_frame, bg=color, width=2, height=1, command=lambda c=color: self.set_color(c))
            btn.pack(side=tk.LEFT, padx=3, pady=3)  # カラーボタンの配置
            self.color_buttons[color] = btn
            
        # 現在の色ラベルのテキスト部分
        color_text_label = tk.Label(toolbar_frame, text="選択されている色:")
        color_text_label.pack(side=tk.LEFT, padx=5)

        # 現在の色を表示するラベルを追加
        self.current_color_label = tk.Label(toolbar_frame, text=" ", width=2, height=1, bg=self.pen_color)
        self.current_color_label.pack(side=tk.LEFT, padx=10)
        
        # ペンの太さを調整するスケールバーを追加
        pen_size_frame = ttk.Frame(toolbar_frame)
        pen_size_frame.pack(side=tk.LEFT, padx=10)
        
        pen_size_label = tk.Label(pen_size_frame, text="ペンの太さ:")
        pen_size_label.pack(side=tk.LEFT)
        
        self.pen_size_scale = tk.Scale(pen_size_frame, from_=1, to=10, orient=tk.HORIZONTAL, command=self.change_pen_size)
        self.pen_size_scale.set(self.pen_size)
        self.pen_size_scale.pack(side=tk.LEFT)

        # キャンバスの作成と配置
        self.canvas = tk.Canvas(main_frame, bg="white", width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # キャンバスにイベントバインド
        self.canvas.bind("<B1-Motion>", self.paint)  # ドラッグ時の描画処理
        self.canvas.bind("<Button-1>", self.start_action)  # 描画の開始処理
        self.canvas.bind("<ButtonRelease-1>", self.reset_coords)  # 描画終了時の座標リセット

        # 画像と描画オブジェクトの初期設定
        self.image = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), "white")
        self.draw = ImageDraw.Draw(self.image)
        self.last_tk_image = ImageTk.PhotoImage(self.image)
        self.canvas.create_image(0, 0, image=self.last_tk_image, anchor=tk.NW)

        showExsample()
        
    def choose_color(self):
        """メニュー外の色を選択する
        """
        self.pen_color = colorchooser.askcolor(color=self.pen_color)[1]
        self.current_color_label.config(bg=self.pen_color)
        # self.update_color_indicator()
        
    def change_pen_size(self, value):
        """
        ペンの太さを変更します。

        Args:
            value (str): スケールバーからの選択された値。
        """
        self.pen_size = int(value)

    def reset_coords(self, event):
        """
        描画終了時に座標をリセットします。
        """
        self.last_x, self.last_y = None, None

    def add_tool(self, parent, label, icon, command=None):
        """
        ツールバーにアイコンボタンを追加するヘルパー関数。

        Args:
            parent (Widget): ボタンを追加する親ウィジェット。
            label (str): ボタンに表示するテキスト。
            icon (str): アイコンのパス。
            command (function): ボタンがクリックされたときに実行される関数。
        """
        btn = tk.Button(parent, text=label, relief=tk.FLAT, command=command)
        btn.pack(side=tk.LEFT, padx=2, pady=2)

    def open_image(self):
        """
        画像ファイルを開き、キャンバスに表示します。
        """
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp")])
        if file_path:
            self.image = Image.open(file_path).resize((CANVAS_WIDTH, CANVAS_HEIGHT))
            self.draw = ImageDraw.Draw(self.image)
            self.last_tk_image = ImageTk.PhotoImage(self.image)
            self.canvas.create_image(0, 0, image=self.last_tk_image, anchor=tk.NW)

    def start_action(self, event):
        """
        描画アクションの開始時に呼び出され、必要に応じて塗りつぶしや図形描画を開始します。

        Args:
            event (Event): マウスイベントオブジェクト。
        """
        self.history.append(self.image.copy())  # 現在の画像の状態を履歴に保存
        self.last_x, self.last_y = event.x, event.y  # 描画開始点を初期化
        if self.fill_mode:
            self.bucket_fill(event)
        elif self.current_tool == "Circle":
            self.drawing_shape = True  # 円を描き始める
            self.temp_circle = self.canvas.create_oval(event.x, event.y, event.x, event.y, outline=self.pen_color, width=self.pen_size)

    def paint(self, event):
        """
        ドラッグ中の描画処理を行います。

        Args:
            event (Event): マウスイベントオブジェクト。
        """
        if self.fill_mode or self.drawing_shape:
            return  # Fillモードまたは円描画中は通常の描画をしない
        
        x1, y1 = (event.x - self.pen_size // 2), (event.y - self.pen_size // 2)
        x2, y2 = (event.x + self.pen_size // 2), (event.y + self.pen_size // 2)
        color = "white" if self.eraser_on else self.pen_color

        if self.last_x and self.last_y:
            # 前回の位置から現在の位置まで線を描画
            self.canvas.create_line(self.last_x, self.last_y, event.x, event.y, fill=color, width=self.pen_size)
            self.draw.line([self.last_x, self.last_y, event.x, event.y], fill=color, width=self.pen_size)

        # 現在の位置に●を描画
        self.canvas.create_oval(x1, y1, x2, y2, fill=color, outline=color)
        self.draw.ellipse([x1, y1, x2, y2], fill=color, outline=color)

        self.last_x, self.last_y = event.x, event.y

    def finish_action(self, event):
        """
        図形描画の終了時に呼び出され、最終的な図形を描画します。

        Args:
            event (Event): マウスイベントオブジェクト。
        """
        if self.drawing_shape:
            if self.temp_circle:
                self.canvas.delete(self.temp_circle)  # 仮の円を削除
            x1, y1 = self.last_x, self.last_y
            x2, y2 = event.x, event.y
            if x1 > x2:  # x2がx1より小さい場合は交換
                x1, x2 = x2, x1
            if y1 > y2:  # y2がy1より小さい場合は交換
                y1, y2 = y2, y1
            self.canvas.create_oval(x1, y1, x2, y2, outline=self.pen_color, width=self.pen_size)
            self.draw.ellipse([x1, y1, x2, y2], outline=self.pen_color, width=self.pen_size)
            self.drawing_shape = False  # 円描画終了
            self.temp_circle = None  # 仮の円をリセット

    def bucket_fill(self, event):
        """
        指定された位置を塗りつぶす処理を行います。

        Args:
            event (Event): マウスイベントオブジェクト。
        """
        x, y = event.x, event.y

        # 座標が画像範囲内にあるか確認
        if not (0 <= x < self.image.width and 0 <= y < self.image.height):
            return  # 範囲外なら処理を中断

        # クリック位置の色を取得
        target_color = self.image.getpixel((x, y))
        fill_color = self.canvas.winfo_rgb(self.pen_color)
        fill_color = (fill_color[0] // 256, fill_color[1] // 256, fill_color[2] // 256)

        if target_color == fill_color:
            return  # 既に同じ色の場合は処理しない

        # 塗りつぶしの実行
        ImageDraw.floodfill(self.image, (x, y), fill_color, thresh=50)
        self.last_tk_image = ImageTk.PhotoImage(self.image)
        self.canvas.create_image(0, 0, image=self.last_tk_image, anchor=tk.NW)

    def use_pen(self):
        """
        ペンツールを選択します。
        """
        self.current_tool = "Pen"
        self.eraser_on = False
        self.fill_mode = False
        self.tool_text_label.config(text="現在のツール:ペン")
        self.set_tool_active()

    def use_eraser(self):
        """
        消しゴムツールを選択します。
        """
        self.current_tool = "Eraser"
        self.eraser_on = True
        self.fill_mode = False
        self.tool_text_label.config(text="現在のツール:消しゴム")
        self.set_tool_active()

    def use_fill(self):
        """
        塗りつぶしツールを選択します。
        """
        self.current_tool = "Fill"
        self.eraser_on = False
        self.fill_mode = True
        self.tool_text_label.config(text="現在のツール:塗りつぶし")
        self.set_tool_active()

    def set_tool_active(self):
        self.pen_button.config(state="disabled" if self.current_tool == "Pen" else "normal")
        self.eraser_button.config(state="disabled" if self.eraser_on else "normal")
        self.fill_button.config(state="disabled" if self.fill_mode else "normal")

    def set_color(self, color):
        """
        描画に使用する色を設定します。

        Args:
            color (str): 設定する色の名前。
        """
        self.pen_color = color
        self.current_color_label.config(bg=color)  # ラベルの背景色を変更

        # すべての色ボタンの枠線をリセット
        for btn in self.color_buttons.values():
            btn.config(relief=tk.FLAT)

        # 選択された色のボタンに枠線を追加
        self.color_buttons[color].config(relief=tk.SUNKEN)

    def save_image(self):
        """
        キャンバス上の画像を保存します。
        """
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if file_path:
            self.image.save(file_path)

    def undo(self):
        """
        最後の描画操作を元に戻します。
        """
        if self.history:
            self.image = self.history.pop()  # 最後の履歴を取り出して復元
            self.draw = ImageDraw.Draw(self.image)
            self.last_tk_image = ImageTk.PhotoImage(self.image)
            self.canvas.create_image(0, 0, image=self.last_tk_image, anchor=tk.NW)
    
    def clear_all(self):
        """
        描画した線をすべて削除します。
        """
        self.history.append(self.image.copy())  # 現在の画像の状態を履歴に保存
        self.image = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), "white")
        self.draw = ImageDraw.Draw(self.image)
        self.canvas.delete("all")
        self.last_tk_image = ImageTk.PhotoImage(self.image)
        self.canvas.create_image(0, 0, image=self.last_tk_image, anchor=tk.NW)
    
    def regitFish(self):
        """キャンパス上の魚を生成アルゴリズムに反映させる
        """
        # ライブラリを読み込む
        import function.extraction_fish as extraction_fish
        
        # file名を取得する
        file = "paint"
        filePath = "./output/paint/" + file + ".png"
        
        # 魚をいったん保存する
        if filePath:
            self.image.save(filePath)

        # 魚を抽出
        only_img = extraction_fish.findFishParts(filePath, file)
        # cv2.imshow("hello",only_img)
        # cv2.waitKey(0)
        
        # これで問題ないか確認する
        # 結果はg_Flagに格納
        display_image("./output/onlyfish/only" + file + ".png","魚を抽出")
        
        # g_Flagをみて閉じるか検討する
        if g_Flag:
            exit_msgbox(self.root)

def showExsample():
    """例を表示"""
    display_image('./inputimg/template(1).png',"[Sketch Aquarium]Paint Tool_example",False)

def exit_msgbox(root):
    """メッセージボックスを終了する

    Args:
        root : メッセージボックス本体
    """
    global g_Flag
    
    root.quit()  # Yesの場合、root.quit()を呼び出してイベントループを終了
    root.destroy()  # Yesの場合、すべてのウィンドウを閉じる
    
    g_Flag = True

def No_msgbox(root):
    """メッセージでNoが選択される

    Args:
        root : メッセージボックス本体
    """
    global g_Flag
    
    root.quit()  # Yesの場合、root.quit()を呼び出してイベントループを終了
    root.destroy()  # Yesの場合、すべてのウィンドウを閉じる
    g_Flag = False

def display_image(image_path,title="[Sketch Aquarium]Select Images" ,flag=True,root=None):
    """imgを表示する

    Args:
        image_path (str): 画像のパス
        root :メッセージボックス
    """
    global g_Flag
    
    
    if root is None:
        root = tk.Toplevel()  # 新しいTkウィンドウの代わりにToplevelを使用
    else:
        root = tk.Toplevel(root)  # 既存のTkインスタンスを親にする

    root.title(title)
    root.iconbitmap('./icon.ico')

    # 画像を開く
    img = Image.open(image_path)
    img = img.resize((300, 300), Image.Resampling.LANCZOS)
    img_tk = ImageTk.PhotoImage(img)

    # 画像を表示
    img_label = tk.Label(root, image=img_tk)
    img_label.image = img_tk  # 参照を保持するために属性に保存
    img_label.pack()
    
    if flag:
        # Yes/Noボタン
        yes_button = tk.Button(root, text="Yes", command=lambda: exit_msgbox(root))
        yes_button.pack(side=tk.LEFT, padx=10, pady=10)

        no_button = tk.Button(root, text="No", command=lambda: No_msgbox(root))  # Noボタンには何も追加処理を行わない
        no_button.pack(side=tk.RIGHT, padx=10, pady=10)

    root.mainloop()
    
    
def main():
    # ウインドウ作成
    root = tk.Tk()
    
    # ウィンドウのアイコンを設定
    # root.iconbitmap(r"note_icon.ico")
    
    # サイズを固定
    root.resizable(False, False)
    
    # アプリ作成
    app = PaintApp(root)

    # アプリ内をずーーーーとルーーーープする
    root.mainloop()
    
    # paintにある画像をinputimgに移動させる
    img = cv2.imread("./output/paint/paint.png")

    if(img is None):
        return

    #filename = module.namingFile("fish_data",".png","./inputimg")
    filename = hashlib.sha256(img).hexdigest()
    filepath = "./inputimg/" + filename + ".png"
    cv2.imwrite(filepath,img)
    
    # index.html用に同じ処理を施す
    filepath = "./static/images/paint.png"
    cv2.imwrite(filepath,img)

    return filename
    
if __name__ == "__main__":
    main()