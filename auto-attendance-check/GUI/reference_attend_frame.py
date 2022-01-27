# maniplation.py > reference_attend_frame() により呼び出されるフレーム

import tkinter as tk
from tkinter.constants import (
    NE,
    NW,
    X,
    Y,
)
from tkinter import ttk
from tkinter import messagebox
from typing import List
import toml
import json
import paramiko


class ReferenceAttendFrame(tk.Frame):
    """
    mainframeの「時間割」 -> subframeの「時間割の新規登録」
    ボタンが押された時に作成するフレーム
    """

    def __init__(self, new_window: tk.Toplevel):
        super().__init__(new_window, width=754, height=680)
        # main window の作成

        self.toplevel = new_window

        self.toplevel.grid_rowconfigure(0, weight=1)
        self.toplevel.grid_columnconfigure(0, weight=1)

        # main frame の作成
        self.frame = tk.Frame(self.toplevel)
        self.frame.grid(row=0, column=0, sticky="nsew")

        # app frameの作成
        self.frame_chose = tk.Frame(self.frame)
        self.frame_chose.pack(fill=tk.BOTH)

        # 科目名のコンボボックスの作成
        self.subjects = self.read_subjects()
        self.chose_subject = ttk.Combobox(
            self.frame_chose,
            height=8,
            width=30,
            values=self.subjects,
            font=("Times", 14),
        )
        self.chose_subject.pack(padx=5, pady=10, side=tk.LEFT)

        # 出席状況を見るボタン
        self.show_button = tk.Button(
            self.frame_chose,
            text="出席状況表示",
            borderwidth=10,
            padx=15,
            pady=5,
            width=12,
            height=2,
            relief=tk.RAISED,
            cursor="hand2",
            command=lambda: self.show_data(self.chose_subject.get()),
        )
        self.show_button.pack(padx=5, pady=10, side=tk.LEFT)

        self.complete_button = tk.Button(
            self.frame_chose,
            text="終了",
            borderwidth=10,
            padx=15,
            pady=5,
            width=12,
            height=2,
            relief=tk.RAISED,
            cursor="hand2",
            command=self.toplevel.destroy,
        )
        self.complete_button.pack(padx=5, pady=10, side=tk.RIGHT)

        # Canvas の作成
        self.canvas = tk.Canvas(
            self.frame, width=754, height=1080, scrollregion=(0, 0, 1080, 1260)
        )

        # Canvas上に配置するframeの作成
        self.frame_canvas = tk.Frame(self.canvas, background="#000000")
        self.canvas.create_window((0, 0), window=self.frame_canvas, anchor=tk.NW)

        # 水平方向のスクロールバーを作成
        self.xbar = tk.Scrollbar(self.frame, orient=tk.HORIZONTAL)

        # 垂直方向のスクロールバーを作成
        self.ybar = tk.Scrollbar(self.frame, orient=tk.VERTICAL)

        # キャンバスの下に水平方向のスクロールバーを配置
        self.xbar.pack(anchor=NW, fill=X, side=tk.BOTTOM)

        # キャンバスの右に垂直方向のスクロールバーを配置
        self.ybar.pack(anchor=NE, fill=Y, side=tk.RIGHT)

        # canvasの配置
        self.canvas.pack()

        self.grid(row=0, column=0, sticky="nsew")


    def read_subjects(self) -> List[str]:
        """
        時間割ファイルから科目名一覧を求めリストにする
        """
        try:
            with open("./subjects/subjects.toml", "rt", encoding="UTF-8") as fp:
                data = toml.load(fp)
        except FileNotFoundError:
            data = {}

        # subjects.tomlファイルが存在しない場合
        if not data:
            messagebox.showerror("エラー", "時間割が登録されていません")
            self.toplevel.destroy()
            return

        subjects: List[str] = []

        # 科目名をすべて求める
        i = ""
        for day in data:
            for num in data[day]:
                for i in subjects:
                    if data[day][num] == i:
                        break
                # まだsubjects[]に入っていない科目の場合
                if data[day][num] != i and data[day][num] != "":
                    subjects.append(data[day][num])

        return subjects

    def show_data(self, subject: str):
        if not subject:
            messagebox.showerror("エラー", "表示させる科目名を選択してください")

        # treeviewの作成
        self.column = (
            "num",
            "name",
            "attend",
            "absent",
            "late",
            "authorized absence",
            "none",
            "error",
        )
        self.tree = ttk.Treeview(self.canvas, columns=self.column, show="headings", height=600)

        # 列の設定
        self.tree.column("num", width=40, anchor="w", stretch=False)
        self.tree.column("name", anchor="w", width=150)
        self.tree.column("attend", anchor="w", width=60)
        self.tree.column("absent", anchor="w", width=60)
        self.tree.column("late", anchor="w", width=60)
        self.tree.column("authorized absence", anchor="w", width=60)
        self.tree.column("none", anchor="w", width=60)
        self.tree.column("error", anchor="w", width=60)

        # 列の見出し設定
        self.tree.heading("num", text="番号")
        self.tree.heading("name", text="名前")
        self.tree.heading("attend", text="出席")
        self.tree.heading("absent", text="欠席")
        self.tree.heading("late", text="遅刻")
        self.tree.heading("authorized absence", text="公欠")
        self.tree.heading("none", text="初期状態")
        self.tree.heading("error", text="エラー")
        
        # sshでラズパイから「科目名.json」ファイルを読み込む
        # raspberrypiのファイルのパスワードファイルの読み込み
        with open("./raspberrypi_key.toml", mode="rt", encoding="UTF-8") as fp:
            data = toml.load(fp)

        # SSH接続
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            client.connect(
                data["IP_ADDRESS"],
                username=data["USER_NAME"],
                password=data["PASS_WORD"],
                timeout=3.9,
            )
        except Exception:
            messagebox.showerror("エラー", "ラズパイに接続できませんでした")
            return
        
        try:
            # 指定した科目のファイルを読み込む
            sftp_connection = client.open_sftp()
            sftp_connection.get(
                f"/home/pi/aac/attend_data/json/{subject}.json",
                f"./attend_data/{subject}.json",
            )
        except Exception:
            messagebox.showerror("エラー", "ファイルを取得できませんでした")
            client.close()
            return
        
        # 出席・欠席...の回数を計算
        attend_data = self.culcu_num(subject)
        i = 0
        for list in attend_data:
            self.tree.insert(parent="", index="end", iid=i, values=list)
            i += 1

        # スクロールバーのスライダーが動かされた時の処理
        self.xbar.config(command=self.tree.xview)
        self.ybar.config(command=self.tree.yview)

        # スクロールバーをCanvasに関連付け
        self.tree.config(xscrollcommand=self.xbar.set)
        self.tree.config(yscrollcommand=self.ybar.set)

        # Canvasの位置の初期化
        self.tree.yview_moveto(0)
        self.tree.xview_moveto(0)

        self.tree.pack(pady=20, side=tk.LEFT)

    def culcu_num(self, subject: str) -> list:
        """
        出席・欠席・遅刻・...の回数を計算

        出席の正体を表す列挙体
        Attributs
        ---------
        ATTEND : str
            出席
        ABSENCE : str
            欠席
        LATENESS : str
            遅刻
        AUTHORIZEED_ABSENCE : str
            公欠
        NONE : str
            初期状態、未確認状態
        ERROR : str
            エラー
        """

        ATTEND = "attend"
        ABSENCE = "absence"
        LATENESS = "lateness"
        AUTHORIZEED_ABSENCE = "authorized absence"
        NONE = "none"
        ERROR = "error"

        # 読み込んだファイルから出席数・欠席数・等を計算
        try:
            with open(f"./attend_data/{subject}.json", mode="rt", encoding="UTF-8") as fp:
                data = json.load(fp)
        except FileNotFoundError:
            messagebox.showerror("エラー", "指定科目のファイルが見つかりません")

        attend_data = []

        for item in range(0, len(data)):
            count = [0] * 6
            for num in data[item]["attendance states"]:
                if num == ATTEND:
                    count[0] += 1
                if num == ABSENCE:
                    count[1] += 1
                if num == LATENESS:
                    count[2] += 1
                if num == AUTHORIZEED_ABSENCE:
                    count[3] += 1
                if num == NONE:
                    count[4] += 1
                if num == ERROR:
                    count[5] += 1
            attend_data.append(
                (data[item]["student number"], data[item]["name"], *count)
            )

        return attend_data
