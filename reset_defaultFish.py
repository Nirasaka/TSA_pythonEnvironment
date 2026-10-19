from pathlib import Path

from function import module # 共通するモジュール
import main


if __name__ == "__main__":
    module.printTerminal("デフォルトの魚を再生成します．（出力はuploadフォルダ）")

    folder_path = Path(r"./defaultfish")
    
    default_fish_list = [p.stem for p in folder_path.rglob("*.zip")].copy()

    for zip_name in default_fish_list:
        main.generateFish(zip_name)