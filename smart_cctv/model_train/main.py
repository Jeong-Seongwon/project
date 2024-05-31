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
import os

import yolov8_dataset_preprocessing as preprocess
import yolo_model_train as train
# import yolo_predict as predict
import select_project
import state



class MainApp():
    def __init__(self):
        # 상태 관리 객체 생성
        self.state = state.State()
        self.state.project_path = os.getcwd() # 현 디렉토리로 기본값 설정
        self.state.dataset_path = os.path.join(self.state.project_path, "data", "dataset")
        self.state.runs_path = os.path.join(self.state.project_path, "runs")

        self.run()


    # 각 탭별 gui 생성
    def create_select_project_tab_gui(self, tab):
        self.select_project_tab = select_project.Select_project(tab, self.state)

    def create_preprocess_tab_gui(self, tab):
        self.preprocess_tab = preprocess.Preprocess(tab, self.state)

    def create_train_tab_gui(self, tab):
        self.train_tab = train.Train(tab, self.state)

    # def create_predict_tab_gui(self, tab):
    #     self.predict_tab = predict.Predict(tab)


    def on_close(self):
        # 각 탭에서 실행 중인 프로세스를 종료하고 GUI를 닫음
        stop_process2 = self.train_tab.stop_process()
        if stop_process2 == -1:
            return
        # stop_process3 = self.predict_tab.stop_process()
        # if stop_process3 == -1:
        #     return
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

        # select_project 탭 생성
        self.select_project_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.select_project_tab, text='Select Project')

        # preprocess 탭 생성
        self.preprocess_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.preprocess_tab, text='Dataset Preprocessing')

        # train 탭 생성
        self.train_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.train_tab, text='Yolo Training')

        # predict 탭 생성
        # self.predict_tab = ttk.Frame(self.notebook)
        # self.notebook.add(self.predict_tab, text="Yolo Predict")

        # 각 탭에 대한 GUI 생성
        self.create_select_project_tab_gui(self.select_project_tab)
        self.create_preprocess_tab_gui(self.preprocess_tab)
        self.create_train_tab_gui(self.train_tab)
        # self.create_predict_tab_gui(self.predict_tab)


        # GUI를 닫을 때 추가 작업을 수행하기 위한 이벤트 바인딩
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)


        self.root.mainloop()


if __name__ == "__main__":
    MainApp()