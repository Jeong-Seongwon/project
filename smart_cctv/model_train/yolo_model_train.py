from ultralytics import YOLO
import yaml
from tkinter import filedialog

dataset_dir = ""

def yolov8n_train(model='yolov8n.pt', epochs=100, imgsz=640):
    global dataset_dir
    # setting.yaml 파일 datasets_dir 경로 수정
    setting_yaml_file_path = "C:/Users/602-24/AppData/Roaming/Ultralytics/settings.yaml"
    
    if not dataset_dir:
        # 새로운 dataset_dir 경로
        dataset_dir = filedialog.askdirectory(initialdir="", title="dataset 경로")

        yolov8n_train(model=model, epochs=epochs, imgsz=imgsz)
        return

    else:
        # YAML 파일 읽기
        with open(setting_yaml_file_path, 'r') as file:
            data = yaml.safe_load(file)

        # datasets_dir 수정
        data['datasets_dir'] = dataset_dir

        # 변경된 YAML 파일 쓰기
        with open(setting_yaml_file_path, 'w') as file:
            yaml.dump(data, file)


        # Load a pretrained YOLO model (recommended for training)
        model = YOLO(model)

        results = model.train(data='label.yaml', epochs=epochs, imgsz=imgsz)

        return results

if __name__ == '__main__':
    results = yolov8n_train(epochs=3)
    