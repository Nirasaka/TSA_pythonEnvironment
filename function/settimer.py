import time


class timer:
    """時間測定用クラス"""

    def __init__(self, string="NULL"):
        """コンストラクタ

        Args:
            string: 名前を格納
        """
        self.name = string
        self.start = time.time()
        print(self.name + " start!")

    def stop(self):
        """時間を終了して経過時間を出力する"""
        time_deff = time.time() - self.start
        h, m, s, ms = self.calctime(time_deff)
        print(
            "\n  time : {0:02}:{1:02}:{2:02}:{3:02} [HH:MM:SS:mSmS]\n".format(
                h, m, s, ms
            )
        )
        print(self.name + " finish!")

        return time_deff

    def nowTime(self):
        """現在の時間を出力する"""
        time_deff = time.time() - self.start
        h, m, s, ms = self.calctime(time_deff)
        print(
            "\n  time : {0:02}:{1:02}:{2:02}:{3:02} [HH:MM:SS:mSmS]\n".format(
                h, m, s, ms
            )
        )

    def calctime(self, time_deff):
        """与えられた時間から単位ごとに計算する

        Args:
            time_deff : 経過時間

        Returns:
            時，分，秒の順番で出力
        """
        time_h = int(time_deff / (60 * 60))
        time_m = int((time_deff % (60 * 60)) / 60)
        time_s = int(time_deff % 60)
        time_ms = int((time_deff - int(time_deff)) * 10)

        return time_h, time_m, time_s, time_ms

if __name__ == "__main__":
    print('main.pyを実行してください')