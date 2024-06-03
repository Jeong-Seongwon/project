import cv2
from ultralytics import YOLO
import datetime
import os
import sqlite3

class Predict:
    def __init__(self):
        self.size = (960, 540)
        self.model = YOLO('./model_train/runs/detect/train/weights/best.pt')
        self.labels = []  # Add your labels here, e.g., ['person', 'car', ...]

    def detect_objects(self, video_path):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error opening video file or camera: {video_path}")
            return None
        
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        date = datetime.date.today()
        directory = "static/results"
        if not os.path.exists(directory):
            os.makedirs(directory)

        filename = f"{date.strftime('%Y-%m-%d')}_yolo.avi"
        filepath = os.path.join(directory, filename)
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(filepath, fourcc, fps, self.size)

        # SQLite 데이터베이스 연결
        conn = sqlite3.connect('/cctv_manager.sqlite')
        cursor = conn.cursor()

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            resized_frame = cv2.resize(frame, self.size)
            results = self.model(resized_frame)
            plots = results[0].plot()
            
            # Convert RGB plot to BGR
            rgb_plots = cv2.cvtColor(plots, cv2.COLOR_RGB2BGR)
            out.write(rgb_plots)

            # 검출된 객체 정보를 데이터베이스에 저장
            for detection in results.xyxy[0]:
                label = int(detection[5].item())
                box = [int(coord) for coord in detection[:4].tolist()]
                occurrence_time = datetime.datetime.now().strftime('%H:%M:%S')
                incident = self.labels[label] if label < len(self.labels) else "Unknown"
                cursor.execute("INSERT INTO cctvlog (date, occurrence_time, incident) VALUES (?, ?, ?)", (date, occurrence_time, incident))

        # 데이터베이스에 변경 사항 저장
        conn.commit()
        conn.close()

        cap.release()
        out.release()
        return filepath
