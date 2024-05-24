import subprocess

# requirements.txt에서 필요한 패키지 목록 가져와 설치
def install_dependencies():
    try:
        # requirements.txt 파일에 명시된 패키지 목록 가져오기
        with open('requirements.txt', 'r') as f:
            required_packages = [line.strip() for line in f if not line.startswith('#') and line.strip()]

        # 패키지를 requirements.txt 파일에 명시된 버전 이상으로 설치
        subprocess.check_call(['pip', 'install'] + required_packages)
        print("Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print("Failed to install dependencies:", e)

install_dependencies()

import tkinter as tk
from tkinter import ttk

import yolov8_dataset_preprocessing as preprocess
import yolo_model_train as train
import yolo_predict as predict


class MainApp():
    def __init__(self):
        self.run()


    def create_tab1_gui(self, tab):
        # 탭 1의 GUI 생성
        self.preprocess_tab = preprocess.Preprocess(tab)


    def create_tab2_gui(self, tab):
        # 탭 2의 GUI 생성
        self.train_tab = train.Train(tab)


    def create_tab3_gui(self, tab):
        # 탭 3의 GUI 생성
        self.predict_tab = predict.Predict(tab)


    def on_close(self):
        # 각 탭에서 실행 중인 프로세스를 종료하고 GUI를 닫음
        stop_process2 = self.train_tab.stop_process()
        if stop_process2 == -1:
            return
        stop_process3 = self.predict_tab.stop_process()
        if stop_process3 == -1:
            return
        self.preprocess_tab.stop_process()

        # 쓰레드가 실행 중이 아니면 윈도우를 종료
        self.root.destroy()


    def run(self):
        # 메인 윈도우 생성
        self.root = tk.Tk()
        self.root.title("Yolov8 Training Program")

        # 노트북 위젯 생성
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True)

        # 탭 스타일 설정
        style = ttk.Style()
        style.configure('TNotebook', background='light yellow')  # 탭 전체의 배경색 설정
        style.configure('TNotebook.Tab', font=('Helvetica', 12, 'bold'), padding=[10, 5])  # 글꼴 및 텍스트 스타일 변경

        # 탭 1 생성
        self.tab1 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab1, text='Dataset Preprocessing')

        # 탭 2 생성
        self.tab2 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab2, text='Yolo Training')

        # 탭 3 생성
        self.tab3 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab3, text="Yolo Predict")

        # 각 탭에 대한 GUI 생성
        self.create_tab1_gui(self.tab1)
        self.create_tab2_gui(self.tab2)
        self.create_tab3_gui(self.tab3)


        # GUI를 닫을 때 추가 작업을 수행하기 위한 이벤트 바인딩
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)


        self.root.mainloop()


if __name__ == "__main__":
    MainApp()