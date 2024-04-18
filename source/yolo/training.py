import os

# Darknet 설치 경로
darknet_path = "/path/to/darknet"

# 데이터셋 경로
dataset_path = "/path/to/dataset"

# Darknet 경로로 이동
os.chdir(darknet_path)

# 설정 파일 복사
os.system("cp cfg/yolov4-custom.cfg cfg/yolov4-training.cfg")

# 데이터셋 경로 설정
os.system("sed -i 's/batch=64/batch=1/' cfg/yolov4-training.cfg")
os.system("sed -i 's/subdivisions=16/subdivisions=1/' cfg/yolov4-training.cfg")
os.system("sed -i 's/max_batches = 500200/max_batches = 4000/' cfg/yolov4-training.cfg")
os.system("sed -i '610 s@classes=80@classes=1@' cfg/yolov4-training.cfg")
os.system("sed -i '696 s@classes=80@classes=1@' cfg/yolov4-training.cfg")
os.system("sed -i '783 s@classes=80@classes=1@' cfg/yolov4-training.cfg")
os.system("sed -i '603 s@filters=255@filters=18@' cfg/yolov4-training.cfg")
os.system("sed -i '689 s@filters=255@filters=18@' cfg/yolov4-training.cfg")
os.system("sed -i '776 s@filters=255@filters=18@' cfg/yolov4-training.cfg")

# obj.names 파일 생성
with open("obj.names", "w") as f:
    f.write("person\n")

# obj.data 파일 생성
with open("obj.data", "w") as f:
    f.write("classes = 1\n")
    f.write("train = data/train.txt\n")
    f.write("valid = data/test.txt\n")
    f.write("names = obj.names\n")
    f.write("backup = backup/\n")

# 데이터셋 폴더 생성 및 이미지 파일 이동
os.makedirs("data/obj", exist_ok=True)
os.system(f"cp {dataset_path}/*.jpg data/obj")
os.system(f"find data/obj -name '*.jpg' -exec sh -c 'convert \"$0\" \"${{0%.jpg}}.png\"' {{}} \\;")

# 학습 시작
os.system("./darknet detector train obj.data cfg/yolov4-training.cfg yolov4.conv.137")
