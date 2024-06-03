import cv2
from ultralytics import YOLO
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext as st
import threading
import os
import time
import datetime
import sqlite3
import webbrowser



class Predict():
    def __init__(self, top=None):
        self.top = top

        self.origin_cap = None
        self.cap = None
        self.size = (960, 540)

        # 연속 검출 카운트
        self.continuous_detection_count = 0

        self.model = YOLO('./runs/detect/train/weights/best.pt')

        # IP 카메라 또는 스트리밍 서버의 URL
        self.url = './data/cctv/2024-05-13.mp4'

        # label.txt 에서 label 목록 가져오기
        self.labels=[]
        with open("label.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                self.labels.append(line)

        self.create_gui()
        if self.url:
            self.start_capture_cctv_video()


    def load_cctv(self):
        # play_video의 cap을 캠으로 변환
        if self.cap:
            self.cap.release()

        self.continuous_detection_count = 0
        self.cap = cv2.VideoCapture(self.url)




    def load_video(self):
        video_path = filedialog.askopenfilename(initialdir="", filetypes=[("Video files", "*.mp4;*.avi;*.mov")])
        
        if self.cap:
            self.cap.release()

        self.continuous_detection_count = 0
        self.cap = cv2.VideoCapture(video_path)


    def start_capture_cctv_video(self):
        cctv_thread = threading.Thread(target=self.capture_cctv_video) # cctv 원본 영상 저장
        play_thread = threading.Thread(target=self.play_video) # yolo 예측 영상 재생 및 저장
        cctv_thread.daemon = True
        play_thread.daemon = True
        cctv_thread.start()
        play_thread.start()


    def capture_cctv_video(self):
        # IP 카메라 또는 스트리밍 서버 연결
        self.origin_cap = cv2.VideoCapture(self.url)

        self.cctv_video_playing = True
        # 동영상 프레임의 FPS 설정
        fps = int(self.origin_cap.get(cv2.CAP_PROP_FPS))

        date = datetime.date.today()
        # 디렉토리 경로 생성
        directory = "../static"
        if not os.path.exists(directory):
            os.makedirs(directory)

        # 영상 저장 경로 설정
        filename = date.strftime("%Y-%m-%d") + "_origin.avi"
        filepath = os.path.join(directory, filename)
        # VideoWriter 객체 생성
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.origin_out = cv2.VideoWriter(filepath, fourcc, fps, self.size)

        if not self.cctv_video_playing:
            self.origin_cap.release()

        if not self.origin_cap.isOpened():
            print("Error: Unable to connect to camera")
            return None

        while self.cctv_video_playing:
            ret, frame = self.origin_cap.read()
            resized_frame = cv2.resize(frame, self.size)

            if not ret:
                print("Error: Failed to capture frame")
                break
            
            self.origin_out.write(resized_frame)

            time.sleep(1/30) # 1초에 30프레임


    def start_timer(self): # 결과 출력 여부 타이머 쓰레드
        timer_thread = threading.Thread(target=self.reset_printed_detection)
        timer_thread.daemon = True
        timer_thread.start()

    def reset_printed_detection(self):
        # 1분 후에 결과 출력 여부 초기화
        time.sleep(60)
        self.printed_detection = False

    def play_video(self):
        self.printed_detection = False  # 결과가 이미 출력되었는지 여부를 나타내는 변수

        # IP 카메라 또는 스트리밍 서버 연결
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.url)

        # 동영상 프레임의 FPS 설정
        fps = int(self.cap.get(cv2.CAP_PROP_FPS))

        date = datetime.date.today()
        # 디렉토리 경로 생성
        directory = "../static"
        if not os.path.exists(directory):
            os.makedirs(directory)

        # 영상 저장 경로 설정
        filename = date.strftime("%Y-%m-%d") + "_yolo.avi"
        filepath = os.path.join(directory, filename)
        # VideoWriter 객체 생성
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.yolo_out = cv2.VideoWriter(filepath, fourcc, fps, self.size)


        while True:
            if self.cap is not None:
                ret, frame = self.cap.read()
                resized_frame = cv2.resize(frame, self.size)
                if ret:
                    # 프레임 처리 (예: 재생)
                    plots = self.display_video(resized_frame)

                    bgr_plots = cv2.cvtColor(plots, cv2.COLOR_RGB2BGR)
                    self.yolo_out.write(bgr_plots) # bgr로 변환 하고 저장

            time.sleep(1 / 30)  # 적절한 지연 시간
    

    def display_video(self, frame):
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.model(image)
        plots = results[0].plot()
        self.image_print(plots)

        if results[0].boxes:
            if self.continuous_detection_count < 150:
                self.continuous_detection_count += 1

            # 결과가 이미 출력되지 않았고, 연속 객체 검출 횟수가 150이 되었을 때
            if not self.printed_detection and self.continuous_detection_count == 150:
                # 5초간 지속되면
                self.predict_results(results)
                self.results_to_database()  # db에 저장
                self.printed_detection = True  # 결과 출력 플래그를 설정
                self.start_timer()

        else:
            if self.continuous_detection_count > 0:
                self.continuous_detection_count -= 1
        return plots


    def image_print(self, image):
        # OpenCV 이미지를 PIL 이미지로 변환
        pil_image = Image.fromarray(image)

        # PIL 이미지를 tkinter PhotoImage로 변환
        photo = ImageTk.PhotoImage(image=pil_image)

        # 이미지를 캔버스에 출력합니다.
        self.image_canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        self.image_canvas.image = photo


    def predict_results(self, results):
        # 결과에서 라벨인덱스 검출
        for r in results:
            self.results_label = []
            for cls_value in r.boxes.cls:
                label_index = int(cls_value.item())
                # label 검출
                self.results_label.append(self.labels[label_index])
        
        self.incident = ",".join(self.results_label)

        # 현재 날짜를 가져옵니다.
        self.current_date = datetime.date.today()

        # 년월일 형식으로 날짜를 출력합니다.
        self.formatted_date = self.current_date.strftime("%Y-%m-%d")

        # 재생 시간 얻기
        playback_time_ms = self.cap.get(cv2.CAP_PROP_POS_MSEC)

        # 밀리초(ms)를 시, 분, 초로 변환
        playback_time_sec = playback_time_ms // 1000
        self.hours = int(playback_time_sec // 3600)
        self.minutes = int((playback_time_sec % 3600) // 60)
        self.seconds = int(playback_time_sec % 60)

        self.occurrence_time = "{:02d}:{:02d}:{:02d}".format(self.hours, self.minutes, self.seconds)

        self.my_log(self.formatted_date + " " + self.occurrence_time + " " + ",".join(self.results_label))


    def results_to_database(self):
        db_path = "cctv_manager.sqlite"
        # 데이터베이스 연결 설정
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # 예측 결과를 데이터베이스에 삽입하는 SQL 쿼리
            insert_query = "INSERT INTO cctvlog (date, occurrence_time, incident) VALUES (?, ?, ?)"  # 필요한 만큼 열과 값을 적절히 수정

            # 쿼리 실행
            cursor.execute(insert_query, (self.formatted_date, self.occurrence_time, self.incident))  # 결과 값에 맞게 값을 수정

            # 변경사항 커밋
            conn.commit()



    def model_list_show(self):
        models_path = './runs/detect'

        # "train"으로 시작하는 폴더 경로를 찾아 리스트로 저장
        train_folders = [folder.path for folder in os.scandir(models_path) if folder.is_dir() and folder.name.startswith('train')]

        self.best_model_listbox.delete(0, tk.END)
        self.last_model_listbox.delete(0, tk.END)

        self.best_pt_list = []
        self.last_pt_list = []

        for train_folder in train_folders:
            best_pt = train_folder + '/weights/best.pt'
            last_pt = train_folder + '/weights/last.pt'

            self.best_pt_list.append(best_pt)
            self.last_pt_list.append(last_pt)

            model_name = os.path.basename(train_folder)

            self.best_model_listbox.insert(tk.END, model_name.strip())
            self.last_model_listbox.insert(tk.END, model_name.strip())


    def on_model_select(self, event):
        # 선택된 리스트 박스 가져오기
        selected_listbox = event.widget

        # 선택된 항목의 인덱스 가져오기
        selected_index = event.widget.curselection()
        if selected_index:
            index = selected_index[0]

            # 모델 불러오기
            if selected_listbox is self.best_model_listbox:
                self.model = YOLO(self.best_pt_list[index])

            elif selected_listbox is self.last_model_listbox:
                self.model = YOLO(self.last_pt_list[index])


    def my_log(self, msg):
        # 텍스트 위젯에 하이퍼링크 추가
        link_id = self.formatted_date + "|" + self.occurrence_time

        self.text_log.config(state="normal")  # 텍스트 위젯을 편집 가능한 상태로 설정
        self.text_log.insert(tk.END, msg + "\n", ("hyperlink", link_id))  # 텍스트 삽입
        
        self.text_log.tag_config("hyperlink", foreground="blue", underline=True)  # 링크 스타일 지정
        self.text_log.tag_bind(link_id, "<Button-1>", lambda event, link_id=link_id: self.on_link_click(event, link_id))  # 링크 연결
        self.text_log.tag_bind(link_id, "<Enter>", lambda event: self.text_log.config(cursor="hand2"))  # 마우스 진입 시 커서 변경
        self.text_log.tag_bind(link_id, "<Leave>", lambda event: self.text_log.config(cursor=""))  # 마우스 이탈 시 커서 변경
        
        self.text_log.see("end")  # 스크롤바를 맨 아래로 이동하여 가장 최근에 추가된 텍스트를 표시
        self.text_log.config(state="disabled")  # 텍스트 위젯을 읽기 전용 상태로 다시 설정


    def on_link_click(self, event, link_id):
        formatted_date, occurrence_time = link_id.split("|")
        # 동영상 파일 경로
        video_name = formatted_date + "_origin.avi"
        video_path = os.path.join("../static", video_name)

        # 동영상을 특정 시간으로 이동
        video_url = f"file://{os.path.abspath(video_path)}#t={occurrence_time}"

        # 파일을 기본 웹 브라우저에서 열기
        webbrowser.open(video_url)


    def stop_process(self):
        response = messagebox.askyesno("종료 확인", "프로그램을 종료하시겠습니까?")
        if not response:
            return -1
        
        self.cctv_video_playing = False
        self.origin_cap.release()
        self.cap.release()
        self.origin_out.release()
        self.yolo_out.release()



    def create_gui(self):
        self.models_frame = tk.Frame(self.top)
        self.models_frame.grid(row=0, column=0, padx=10, pady=20)

        self.load_cctv_button = tk.Button(self.models_frame, text="CCTV", width=25, height=2, command=self.load_cctv)
        self.load_cctv_button.pack(padx=10, pady=10)

        self.load_video_button = tk.Button(self.models_frame, text="Load Video", width=25, height=2, command=self.load_video)
        self.load_video_button.pack(padx=10, pady=10)

        self.best_model_label = tk.Label(self.models_frame, text="Best Models")
        self.best_model_label.pack(padx=10)

        self.best_model_listbox = tk.Listbox(self.models_frame, width=25)
        self.best_model_listbox.pack(padx=10, pady=10)


        self.last_model_label = tk.Label(self.models_frame, text="Last Models")
        self.last_model_label.pack(padx=10)

        self.last_model_listbox = tk.Listbox(self.models_frame, width=25)
        self.last_model_listbox.pack(padx=10, pady=10)

        self.model_list_show()

        # 리스트 박스 선택 이벤트에 대한 핸들러 등록
        self.best_model_listbox.bind("<<ListboxSelect>>", self.on_model_select)
        self.last_model_listbox.bind("<<ListboxSelect>>", self.on_model_select)




        self.image_canvas = tk.Canvas(self.top, width=960, height=540, bg="white")
        self.image_canvas.grid(row=0, column=1, padx=10, pady=20)



        # 로그
        self.log_frame = tk.Frame(self.top)
        self.log_frame.grid(row=0, column=2, padx=10, pady=20)

        self.text_log_label = tk.Label(self.log_frame, text="Incident Log")
        self.text_log_label.grid(row=0, column=0, padx=3, pady=3)

        self.text_log = st.ScrolledText(self.log_frame,
                                    width = 60,
                                    height = 34,
                                    font = ("Times New Roman",10),
                                    state="disabled")
        self.text_log.grid(row=1, column=0, padx=3, pady=3)


if __name__ == "__main__":
    top = tk.Tk()

    Predict(top)

    top.mainloop()