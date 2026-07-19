:おまじない
chcp 65001

:アクティベート
call ..\anaconda3\Scripts\activate.bat

:ThirdSketchAquariumという名前の仮想環境をAnacondaで作った場合
call conda activate ThirdSketchAquarium

:実行
python main.py

:ウィンドウが勝手に閉じないようにする
cmd \k