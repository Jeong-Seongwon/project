import tkinter as tk
from tkinter import filedialog
from ultralytics import settings
from PIL import Image, ImageTk
import os



class Select_project():
    def __init__(self, top, instance):
        self.top = top
        self.instance = instance # 메인 클래스의 인스턴스

        self.create_gui()


    def change_project(self):
        # MainApp 클래스의 인스턴스 속성값 변경
        self.instance.project_path = self.project_dir_entry.get()
        self.instance.dataset_path = self.dataset_dir_entry.get()
        self.instance.runs_path = self.runs_dir_entry.get()

        self.change_yolo_settings()


    def change_yolo_settings(self):
        # settings.yaml 파일 수정
        settings.update({'datasets_dir': self.instance.dataset_path})
        settings.update({'runs_dir': self.instance.runs_path})


    def change_project_dir(self):
        dir_path = filedialog.askdirectory(initialdir="./")

        if dir_path and dir_path != self.instance.project_path: # 디렉토리 경로가 없거나 안 바뀌면 실행하지 않음
            # 프로젝트 디렉토리 엔트리 수정
            self.project_dir_entry.delete(0, tk.END)
            self.project_dir_entry.insert(tk.END, dir_path)

            # dataset, runs 디렉토리 엔트리 초기화
            self.dataset_dir_entry.delete(0, tk.END)
            dataset_path = os.path.join(dir_path, "data", "dataset")
            self.dataset_dir_entry.insert(tk.END, dataset_path)

            self.runs_dir_entry.delete(0, tk.END)
            runs_path = os.path.join(dir_path, "runs")
            self.runs_dir_entry.insert(tk.END, runs_path)


    def change_dataset_dir(self):
        dir_path = filedialog.askdirectory(initialdir="./")

        if dir_path and dir_path != self.instance.dataset_path: # 디렉토리 경로가 없거나 안 바뀌면 실행하지 않음
            # dataset 디렉토리 엔트리 수정
            self.dataset_dir_entry.delete(0, tk.END)
            self.dataset_dir_entry.insert(tk.END, dir_path)

    
    def change_runs_dir(self):
        dir_path = filedialog.askdirectory(initialdir="./")

        if dir_path and dir_path != self.instance.runs_path: # 디렉토리 경로가 없거나 안 바뀌면 실행하지 않음
            # runs 디렉토리 엔트리 수정
            self.runs_dir_entry.delete(0, tk.END)
            self.runs_dir_entry.insert(tk.END, dir_path)


    def create_gui(self):
        # 폴더 이미지 열기 및 리사이즈
        img = Image.open("./images/folder.png")
        img = img.resize((42, 28), Image.Resampling.LANCZOS)  # 원하는 크기로 리사이즈 (가로, 세로)
        # Tkinter에서 사용할 수 있는 이미지로 변환
        self.folder_image = ImageTk.PhotoImage(img)

        # 첫 번째 행과 열이 윈도우 크기에 맞춰 확장
        self.top.grid_rowconfigure(0, weight=1)
        self.top.grid_columnconfigure(0, weight=1)


        label_font = ("Helvetica", 12, "bold") # 라벨 폰트 지정

        # 전체 프레임 >> 중앙 정렬을 위해서
        self.main_frame = tk.Frame(self.top, bg="white")
        self.main_frame.grid(row=0, column=0)

        self.main_label = tk.Label(self.main_frame, text="Project", bg="white", font=("Helvetica", 40, 'bold italic'))
        self.main_label.grid(row=0, column=0, columnspan=3, padx=10, pady=50)

        # 프로젝트 디렉토리 프레임
        self.project_dir_label = tk.Label(self.main_frame, text="Project Dir: ", bg="white", font=label_font)
        self.project_dir_label.grid(row=1, column=0, padx=10, pady=10)

        self.project_dir_entry = tk.Entry(self.main_frame, width=80)
        self.project_dir_entry.grid(row=1, column=1, pady=10)
        self.project_dir_entry.insert(tk.END, self.instance.project_path) # 기본값 입력

        self.change_project_dir_button = tk.Button(self.main_frame, image=self.folder_image, command=self.change_project_dir)
        self.change_project_dir_button.grid(row=1, column=2, padx=10, pady=10)


        # dataset 경로
        self.dataset_dir_label = tk.Label(self.main_frame, text="Dataset Dir: ", bg="white", font=label_font)
        self.dataset_dir_label.grid(row=2, column=0, padx=10, pady=10)

        self.dataset_dir_entry = tk.Entry(self.main_frame, width=80)
        self.dataset_dir_entry.grid(row=2, column=1, pady=10)
        self.dataset_dir_entry.insert(tk.END, self.instance.dataset_path) # 기본값 입력

        self.change_dataset_dir_button = tk.Button(self.main_frame, image=self.folder_image, command=self.change_dataset_dir)
        self.change_dataset_dir_button.grid(row=2, column=2, padx=10, pady=10)


        # 학습결과 runs 경로
        self.runs_dir_label = tk.Label(self.main_frame, text="Runs Dir: ", bg="white", font=label_font)
        self.runs_dir_label.grid(row=3, column=0, padx=10, pady=10)

        self.runs_dir_entry = tk.Entry(self.main_frame, width=80)
        self.runs_dir_entry.grid(row=3, column=1, pady=10)
        self.runs_dir_entry.insert(tk.END, self.instance.runs_path) # 기본값 입력

        self.change_runs_dir_button = tk.Button(self.main_frame, image=self.folder_image, command=self.change_runs_dir)
        self.change_runs_dir_button.grid(row=3, column=2, padx=10, pady=10)


        # 프로젝트 설정 버튼
        self.change_project_button = tk.Button(self.main_frame, text="Change Project", width=30, height=2, font=label_font, command=self.change_project)
        self.change_project_button.grid(row=4, column=0, columnspan=3, padx=10, pady=30)






class Instance: # 코드 디버깅을 위한 인스턴스 클래스
    def __init__(self, project_path="C:/path/project", dataset_path="data/dataset", runs_path="runs"):
        self.project_path = project_path
        self.dataset_path = dataset_path
        self.runs_path = runs_path



if __name__ == "__main__":
    top = tk.Tk()

    instance = Instance() # 코드 디버깅을 위한 인스턴스

    Select_project(top, instance)

    top.mainloop()