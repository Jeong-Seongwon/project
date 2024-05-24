import cv2
from ultralytics import YOLO
import datetime
import os

class Predict:
    def __init__(self):
        self.size = (960, 540)
        self.model = YOLO('./model_train/runs/detect/train/weights/best.pt')
        self.labels = []
        #with open("C:/Users/602-13/k/label.txt", "r", encoding="utf-8") as f:
            #self.labels = [line.strip() for line in f.readlines()]

    def detect_objects(self, video_path):
        cap = cv2.VideoCapture(video_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        date = datetime.date.today()
        directory = "static/results"
        if not os.path.exists(directory):
            os.makedirs(directory)

        filename = f"{date.strftime('%Y-%m-%d')}_yolo.avi"
        filepath = os.path.join(directory, filename)
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(filepath, fourcc, fps, self.size)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            resized_frame = cv2.resize(frame, self.size)
            results = self.model(resized_frame)
            plots = results[0].plot()
            bgr_plots = cv2.cvtColor(plots, cv2.COLOR_RGB2BGR)
            out.write(bgr_plots)

        cap.release()
        out.release()
        return filepath

pre = Predict()

pre.detect_objects(0)