from ultralytics import YOLO, settings
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import tkinter.scrolledtext as st
from PIL import Image, ImageTk
import os
import threading


import yolo_predict



class Train():
    def __init__(self, top):
        self.top = top
        self.train_thread = None  # train_thread 속성 초기화
        self.dataset_dir = settings['datasets_dir'] # 데이터셋 기본 경로
        self.runs_dir = settings['runs_dir'] # 학습 결과 기본 경로

        self.create_gui()

    # setting.yaml 파일 datasets_dir 경로 수정
    def dataset_path(self):
        # 새로운 dataset_dir 경로
        initial_dir = os.path.dirname(self.dataset_dir) # 데이터셋 경로 상위 폴더
        dataset_dir = filedialog.askdirectory(initialdir=initial_dir, title="dataset 경로 설정")

        if not os.path.exists(os.path.join(dataset_dir, "train")) or not os.path.exists(os.path.join(dataset_dir, "valid")):
            messagebox.showerror("경고", "데이터셋 경로를 확인하세요.")
            return

        self.dataset_dir = dataset_dir

        settings.update({'datasets_dir': self.dataset_dir})

        self.update_data_dir_entry()

    # runs_dir 경로 수정
    def runs_path(self):
        initial_dir = os.getcwd() # 현재 작업 디렉토리를 가져옴
        runs_dir = filedialog.askdirectory(initialdir=initial_dir, title="학습 결과 경로 설정")

        self.runs_dir = runs_dir

        settings.update({'runs_dir': self.runs_dir})

        self.update_runs_dir_entry()


    def update_data_dir_entry(self):
        self.data_dir_entry.config(state="normal")
        self.data_dir_entry.delete(0, tk.END)
        self.data_dir_entry.insert(0, self.dataset_dir)
        self.data_dir_entry.config(state="readonly")


    def update_runs_dir_entry(self):
        self.runs_dir_entry.config(state="normal")
        self.runs_dir_entry.delete(0, tk.END)
        self.runs_dir_entry.insert(0, self.runs_dir)
        self.runs_dir_entry.config(state="readonly")


    def start_training(self):
        # 쓰레드 생성 및 실행
        self.train_thread = threading.Thread(target=self.train)
        self.train_thread.start()


    def train(self):
        model = self.model_option.get() + ".pt"
        epochs = int(self.epochs_entry.get())

        if not os.path.exists(os.path.join(self.dataset_dir, "train")) or not os.path.exists(os.path.join(self.dataset_dir, "valid")):
            messagebox.showerror("경고", "데이터셋 경로를 확인하세요.")
            return

        # 학습 시작
        if self.dataset_dir:
            # 학습 중인 정보를 텍스트 로그에 추가
            self.my_log("학습 시작")
            self.my_log("-----------------")
            self.my_log(f"모델  :  {model}")
            self.my_log(f"에폭  :  {epochs}")

            results = self.yolo_train(model=model, epochs=epochs)

            if results:
                # 학습 결과 가져오기
                results_dict = results.results_dict
                save_dir = results.save_dir
                names = results.names
                speed = results.speed

                # 결과를 한국어로 보기 쉽게 변환
                korean_labels = {
                    "metrics/precision(B)": "정밀도",
                    "metrics/recall(B)": "재현율",
                    "metrics/mAP50(B)": "평균 정밀도 (AP@0.5)",
                    "metrics/mAP50-95(B)": "평균 정밀도 (AP@0.5-0.95)",
                    "fitness": "적합도"
                }
                # 결과를 보기 좋게 정리하여 문자열로 생성
                formatted_results = "\n".join([f"{korean_labels[key]}  :  {value}" for key, value in results_dict.items()])

                # speed 키에 대한 한국어 레이블
                korean_speed = {
                    "preprocess": "전처리 시간",
                    "inference": "추론 시간",
                    "loss": "손실 계산 시간",
                    "postprocess": "후처리 시간"
                }
                # speed 값을 보기 좋게 정리하여 문자열로 생성
                formatted_speed = "\n".join([f"{korean_speed[key]} : {value} ms" for key, value in speed.items()])

                # 학습 결과 메세지 표시
                self.my_log(f"레이블  :  {names}")
                self.my_log(formatted_results)
                self.my_log(formatted_speed)
                self.my_log(f"학습 모델 경로  :  {save_dir}")

                # 학습 완료 메시지 표시
                self.my_log("-----------------")
                self.my_log("학습 완료")

                # 결과 이미지 표시
                result_folder_path = self.get_results_path()
                self.update_results_image(result_folder_path)

                # yolo_predict의 모델리스트 업데이트
                yolo_predict.Predict().model_list_show()

            else:
                self.my_log("-----------------")
                self.my_log("학습 실패")



    def yolo_train(self, model='yolov8n.pt', epochs=100, imgsz=640):
        # Load a pretrained YOLO model (recommended for training)
        model = YOLO(model)
        results = model.train(data='label.yaml', epochs=epochs, imgsz=imgsz)
        return results


    def get_results_path(self):
        # 폴더 경로
        folder_path = './runs/detect'
        # 폴더 내의 모든 폴더 목록 가져오기
        folders = [f.path for f in os.scandir(folder_path) if f.is_dir()]
        # 폴더를 생성된 시간 기준으로 정렬
        latest_folder = max(folders, key=os.path.getctime)

        return latest_folder


    def update_results_image(self, folder_path="./runs/detect/train"):
        # P_curve 이미지
        p_curve_image_path = os.path.join(folder_path, "P_curve.png")

        self.p_curve_img = tk.PhotoImage(file=p_curve_image_path)
        self.p_curve_img = self.p_curve_img.subsample(4)

        self.p_curve_label.config(image=self.p_curve_img)

        # R_curve 이미지
        r_curve_image_path = os.path.join(folder_path, "R_curve.png")

        self.r_curve_img = tk.PhotoImage(file=r_curve_image_path)
        self.r_curve_img = self.r_curve_img.subsample(4)

        self.r_curve_label.config(image=self.r_curve_img)

        # labels 이미지
        # 이미지 파일 열기
        labels_image_path = os.path.join(folder_path, "labels.jpg")
        image = Image.open(labels_image_path)

        # 이미지의 좌상단 1/4 부분 추출
        cropped_image = image.crop((0, 0, image.width // 2, image.height // 2))

        # 1/2 크기로 줄이기
        cropped_image = cropped_image.resize((image.width // 4, image.height // 4))

        # Tkinter용 PhotoImage로 변환
        self.labels_img = ImageTk.PhotoImage(cropped_image)

        self.labels_label.config(image=self.labels_img)

        # results 이미지
        results_image_path = os.path.join(folder_path, "results.png")

        self.results_img = tk.PhotoImage(file=results_image_path)
        self.results_img = self.results_img.subsample(3)  # 가로 및 세로 크기를 1/3으로 줄임

        self.results_label.config(image=self.results_img)


    def my_log(self, msg):
        self.text_log.config(state="normal")  # 텍스트 위젯을 편집 가능한 상태로 설정
        self.text_log.insert(tk.INSERT, msg + "\n")  # 텍스트 삽입
        self.text_log.see("end")  # 스크롤바를 맨 아래로 이동하여 가장 최근에 추가된 텍스트를 표시
        self.text_log.config(state="disabled")  # 텍스트 위젯을 읽기 전용 상태로 다시 설정


    def stop_process(self):
        if self.train_thread and self.train_thread.is_alive():
            response = messagebox.askyesno("경고", "학습 진행중입니다. 종료 하시겠습니까?")
            if not response:
                return -1
        
        settings.update({'datasets_dir': 'data/dataset'})
        settings.update({'runs_dir': 'runs'})


    def create_gui(self):
        self.train_frame = tk.Frame(self.top)
        self.train_frame.grid(row=0, column=0, padx=5, pady=5)

        self.model_label = tk.Label(self.train_frame, text="model:")
        self.model_label.grid(row=0, column=0, padx=3, pady=3, sticky="e")

        self.model_option = tk.StringVar()

        self.model_option_combobox = ttk.Combobox(self.train_frame, textvariable=self.model_option, width=37, state="readonly")
        self.model_option_combobox['value'] = ('Yolov8n','Yolov8s') #콤보박스 요소 삽입
        self.model_option_combobox.current(0) #0번째로 콤보박스 초기화
        self.model_option_combobox.grid(row=0, column=1, padx=3, pady=3, sticky="w") #콤보박스 배치


        self.epochs_label = tk.Label(self.train_frame, text="epochs:")
        self.epochs_label.grid(row=1, column=0, padx=3, pady=3, sticky="e")

        self.epochs_entry = tk.Entry(self.train_frame, width=40)
        self.epochs_entry.insert(tk.END, 100)
        self.epochs_entry.grid(row=1, column=1, padx=3, pady=3, sticky="w")

        self.data_dir_label = tk.Label(self.train_frame, text="data_dir")
        self.data_dir_label.grid(row=2, column=0, padx=3, pady=3, sticky="e")

        self.data_dir_entry = tk.Entry(self.train_frame, width=40, state="readonly")
        self.data_dir_entry.grid(row=2, column=1, padx=3, pady=3, sticky="w")
        self.update_data_dir_entry()


        self.runs_dir_label = tk.Label(self.train_frame, text="runs_dir")
        self.runs_dir_label.grid(row=3, column=0, padx=3, pady=3, sticky="e")

        self.runs_dir_entry = tk.Entry(self.train_frame, width=40, state="readonly")
        self.runs_dir_entry.grid(row=3, column=1, padx=3, pady=3, sticky="w")
        self.update_runs_dir_entry()


        self.change_data_dir_button = tk.Button(self.train_frame, text="change_data_dir", width=25, height=2, command=self.dataset_path)
        self.change_data_dir_button.grid(row=4, column=0, columnspan=2, padx=3, pady=3)

        self.change_runs_dir_button = tk.Button(self.train_frame, text="Change_runs_dir", width=25, height=2, command=self.runs_path)
        self.change_runs_dir_button.grid(row=5, column=0, columnspan=2, padx=3, pady=3)

        self.train_button = tk.Button(self.train_frame, text="Yolo Train", bg="light gray", width=25, height=2, command=self.start_training)
        self.train_button.grid(row=6, column=0, columnspan=2, padx=3, pady=3)

        # 로그
        self.text_log_label = tk.Label(self.train_frame, text="Text Log")
        self.text_log_label.grid(row=7, column=0, padx=3, pady=3)

        self.text_log = st.ScrolledText(self.train_frame,
                                    width = 60,
                                    height = 35,
                                    font = ("Times New Roman",10),
                                    state="disabled")
        self.text_log.grid(row=8, column=0, columnspan=2, padx=3, pady=3)



        self.results_frame = tk.Frame(self.top)
        self.results_frame.grid(row=0, column=1, padx=5, pady=5)


        self.curve_frame = tk.Frame(self.results_frame)
        self.curve_frame.pack()

        self.p_curve_label = tk.Label(self.curve_frame)
        self.p_curve_label.pack(side="left")

        self.r_curve_label = tk.Label(self.curve_frame)
        self.r_curve_label.pack(side="left")


        self.result_frame = tk.Frame(self.results_frame)
        self.result_frame.pack()

        self.labels_label = tk.Label(self.result_frame)
        self.labels_label.pack(side="left")

        self.results_label = tk.Label(self.result_frame)
        self.results_label.pack(side="left")

        self.update_results_image()


if __name__ == "__main__":
    top = tk.Tk()

    Train(top)

    top.mainloop()