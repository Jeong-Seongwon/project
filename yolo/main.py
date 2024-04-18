import cv2
from ultralytics import YOLO

CONFIDENCE_THRESHOLD = 0.7

#cam_index = 0 #내장 캠
cam_index = "./data/video/street.mp4"

cap = cv2.VideoCapture(cam_index)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)   

GREEN = (0, 255, 0)
WHITE = (255, 255, 255)

with open('coco128.txt', 'r', encoding='utf8') as coco128:
    data = coco128.read()
    class_list = data.split('\n')

while True:
    ret, frame = cap.read()
    if not ret:
        print('Cam Error')
        break

    model = YOLO('yolov8n.pt')
    detection = model(frame)[0]
    
    for data in detection.boxes.data.tolist():
        confidence = float(data[4])
        if confidence < CONFIDENCE_THRESHOLD:
            continue
    
        xmin, ymin, xmax, ymax = int(data[0]), int(data[1]), int(data[2]), int(data[3])
        label = int(data[5])
        cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), GREEN, 2)
        cv2.putText(frame, class_list[label]+' '+str(round(confidence, 2))+'%', (xmin, ymin), cv2.FONT_ITALIC, 1, WHITE, 2)

    cv2.imshow('frame', frame)

    if cv2.waitKey(1) == ord('q'):
        break