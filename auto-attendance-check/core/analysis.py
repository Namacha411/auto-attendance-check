from typing import List, Tuple
import mediapipe as mp
import cv2
import numpy as np
import toml

# 画像を表す型エイリアス
Image = np.ndarray
# opencvがアクセスするウェブカメラのID
WEBCAM_ID = 0


def take_photo() -> Image:
    """
    ウェブカメラを使って画像の撮影を行う

    Returns
    -------
    image : np.ndarray
        撮影した画像

    Raises
    ------
    ValueError
        画像の撮影に失敗した
    """
    cap = cv2.VideoCapture(WEBCAM_ID)
    success, image = cap.read()
    if not success:
        raise ValueError("画像の撮影に失敗")
    cap.release()
    return image


class Area:
    """
    それぞれの学生の領域を管理するクラス

    Attribute
    ---------
        id : int
            学生番号
        area : List[List[int]]
            学生番号に対応した学生の顔のあるであろう領域
            画像のうち四角形を構成する左上の座標と右下のピクセル座標を保持
            ```py
            [[0, 0], [200, 300]]
            ```
    """
    def __init__(self, id: int, area: List[List[int]]) -> None:
        self.id = id
        self.area = area

    def __str__(self) -> str:
        return f"'id': {self.id}, 'area': {self.area}"


def read_areas(path: str) -> List[Area]:
    """
    各学生の学生番号とその領域のある座標を読み込む

    tomlファイルは以下のようなフォーマットで書く
    ```toml
    [[area]]
    id = 1
    area = [[0, 0], [200, 200]]
    ```
    """
    datas: List[Area] = []
    areas_file = toml.load(open(path))
    for area in areas_file["area"]:
        datas.append(Area(area["id"], area["area"]))
    return datas


def split_image(image: Image, areas: List[Area]) -> List[Tuple[int, Image]]:
    """
    画像を領域ごとに切り出して分割

    Parameters
    ----------
    image : np.ndarray
        画像データ
    areas : list[Area]
        領域データ、以下のように指定する
        ```py
        areas = [
            Area(1, [[0, 0], [width // 2, height // 2]]),
            Area(2, [[width // 2, 0], [width, height // 2]]),
            Area(3, [[0, height // 2], [width // 2, height]]),
            Area(4, [[width // 2, height // 2], [width, height]])
        ]
        ```

    Return
    ------
    切り出した複数枚の画像データ
    """
    students_list: List[Tuple[int, Image]] = []
    for area in areas:
        [[sx, sy], [ex, ey]] = area.area
        cut = image[sx:ex, sy:ey]
        students_list.append((area.id, cut))
    return students_list


def face_detection(image: Image) -> bool:
    """
    mediapipeによる顔検出を行う

    Parameters
    ----------
    image : np.ndarray
        解析を行う画像

    Returns
    -------
    bool : 顔が検出されたらtrue、されなかったらfalse

    Note
    ----
    複数の顔を認識して個人を識別することが難しいため、
    写真を一人分に分割してその写真から顔が検出できれば出席というふうに判定
    """
    mp_face_detection = mp.solutions.face_detection
    mp_drawing = mp.solutions.drawing_utils

    with mp_face_detection.FaceDetection(
        model_selection=0, min_detection_confidence=0.5
    ) as face_detection:
        image.flags.writeable = False
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = face_detection.process(image)

        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        if results.detections:
            if __debug__:
                # 認識した顔を画像に描画
                for detection in results.detections:
                    mp_drawing.draw_detection(image, detection)
                # pytestでwindowを立ち上げるとエラーが起きるため、コメントアウト
                # cv2.imshow("img", image)
                # cv2.waitKey(0)
            return True
        return False


def desk_analysis(image: Image):
    """
    opencvによる机の解析を用いた出席判定解析を行う

    Parameters
    ----------
    image : np.ndarray
        解析を行う画像

    Returns
    -------
    result
        解析した結果

    Note
    ----
    - Dead code
    - 使用非推奨
    """
    pass


def analysis(image: Image, area_data_path: str) -> List[Tuple[int, bool]]:
    """
    各学生の領域情報データのパスと撮影した画像を受け取り解析を行う

    Parameters
    ----------
    image : Image
        画像データ
    area_data_path : str
        各学生の領域データをもったtomlファイルのパス

    Return
    ------
    data : List[Tuple[int, bool]]
        それぞれの学生の学籍番号と出席状況のペア
    """
    result: List[Tuple[int, bool]] = []
    areas: List[Area] = read_areas(area_data_path)
    students = split_image(image, areas)
    for student in students:
        id, img = student
        result.append((id, face_detection(img)))
    return result


if __name__ == "__main__":
    # this is testcode
    def test_split_image():
        image: str = "auto-attendance-check/tests/core/images/test.JPG"
        image: np.ndarray = cv2.imread(image)
        width, height, _ =  image.shape
        areas = [
            Area(22, [[0, 0], [width // 3, height // 2]]),
            Area(1, [[width // 3, 0], [width, height // 2]]),
            Area(20, [[0, height // 2], [width // 3, height]]),
            Area(2, [[width // 3, height // 2], [width, height]])
        ]
        res = split_image(image, areas)
        for i, t in res:
            cv2.imshow("img", cv2.resize(t, (200, 200)))
            print(f"no.{i}\t{face_detection(t)}")
            cv2.waitKey(0)
    test_split_image()
