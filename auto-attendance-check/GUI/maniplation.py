# GUI sub file ボタンクリック時の操作

import tkinter as tk
import toml
import paramiko
from PIL import Image
from tkinter import messagebox
import timetable_frame
import look_timetable
import owner
import configuration_frame
import subjects_frame
import send_tables_frame
import set_calendar_frame
import reference_attend_frame


def reference_attend_data():
    """
    「出席状況」button was pushed
    Notes
    powershellを開き、出席データを格納している機器へアクセス

    """
    new_window = tk.Toplevel()
    new_window.geometry("750x600")

    reference_attend_frame.ReferenceAttendFrame(new_window)


def take_photo_command(background: tk.PhotoImage):
    """
    「教室撮影」button was pushed
    """

    # raspberrypiのファイルのパスワードファイルの読み込み
    with open("./raspberrypi_key.toml", mode="rt", encoding="UTF-8") as fp:
        data = toml.load(fp)

    # 呼び出すコマンド
    cmd = "aac take_photo gui"

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
        # take_photo実行
        client.exec_command(cmd)

        # 撮影した画像を読み込む
        sftp_connection = client.open_sftp()
        sftp_connection.get(
            "/home/pi/aac/Photos/out_gui.jpg", "./photo_raspi/out_gui.jpg"
        )
    except Exception:
        messagebox.showerror("エラー", "画像を取得できませんでした")
        client.close()
        return

    messagebox.showinfo("完了", "画像を取得しました")

    # jpg画像をtkinterで表示させられるようpng画像に変換
    im = Image.open("./photo_raspi/out_gui.jpg")
    im.save("./photo_raspi/out_gui.png")

    im = Image.open("./photo_raspi/out_gui.png")
    w = im.width
    h = im.height
    im = im.resize((int(w * (754 / w)), int(h * (754 / w))))
    im.save("./photo_raspi/out_gui.png")
    background.config(file="./photo_raspi/out_gui.png")


def set_timetable():
    """
    「タイムテーブルの新規作成」button was pushed

    Notes
        新しく時間割を作成する
        「タイムテーブルの名前」と「タイムテーブル」を新たなウィンドウで入力させ、
        指定したフォーマットでテキストファイルに出力する。
    """

    new_window = tk.Toplevel()
    new_window.geometry("750x600")

    timetable_frame.TimetableFrame(new_window)


def set_calender():
    """
    「タイムテーブルの指定」button was pushed
    """
    new_window = tk.Toplevel()
    new_window.geometry("750x680")

    set_calendar_frame.DateFrame(new_window)


def looktimetable():
    """
    「タイムテーブル」を見る
    """
    new_window = tk.Toplevel()
    new_window.geometry("750x680")

    look_timetable.LookTimetable(new_window)


def configuration(mysettings: owner.Owner):
    """
    「設定」button was pushed
    Notes
    """
    new_window = tk.Toplevel()
    new_window.geometry("500x550")

    configuration_frame.ConfigurationFrame(new_window, mysettings)


def set_subjects():
    """
    「時間割」の科目名を設定
    """
    new_window = tk.Toplevel()
    new_window.geometry("750x600")

    subjects_frame.SubjectFrame(new_window)


def send_tables():
    """
    作成したタイムテーブルや時間割のラズパイへの送信
    """
    new_window = tk.Toplevel()
    new_window.geometry("750x600")

    send_tables_frame.SendFrame(new_window)
