import os
import cv2
import numpy as np
from sklearn.model_selection import train_test_split
import tensorflow as tf


data_path = "./data/train_data_set"
hdf5_file = "./models/cnn_model.hdf5"

def cnn_model_train(data_path, epochs=10, batch=32, imgsz=128):
    images = []
    labels = []
    # data_path 안의 파일들 불러오기
    for filename in os.listdir(data_path):
        # 이미지 파일경로 설정
        img_path = os.path.join(data_path, filename)

        # 이미지 파일 이름에서 라벨 분리
        base, _ = os.path.splitext(filename)
        label = base.split("_")[0]

        # 이미지 불러와서 사이즈 조절
        cv_image = cv2.imread(img_path)
        resized_image = cv2.resize(cv_image, (imgsz, imgsz))

        if resized_image is not None:
            images.append(resized_image)
            labels.append(label)
                    
    images = np.array(images)
    labels = np.array(labels)
    
    X_train, X_test, y_train, y_test = train_test_split(images, labels, test_size=0.2, random_state=42)
    # 라벨을 정수로 변환
    label_to_index = {label: idx for idx, label in enumerate(np.unique(labels))}
    y_train = np.array([label_to_index[label] for label in y_train])
    y_test = np.array([label_to_index[label] for label in y_test])
    
    # 데이터 정규화
    X_train = X_train.astype('float32') / 255.0
    X_test = X_test.astype('float32') / 255.0
    
    # 새로운 모델 생성
    model = tf.keras.models.Sequential([
        tf.keras.layers.Conv2D(64, (3, 3), padding='same', activation='relu', input_shape=(imgsz, imgsz, 3)),
        tf.keras.layers.MaxPooling2D((2, 2)),
        tf.keras.layers.Conv2D(128, (3, 3), padding='same', activation='relu'),
        tf.keras.layers.MaxPooling2D((2, 2)),
        tf.keras.layers.Conv2D(256, (3, 3), padding='same', activation='relu'),
        tf.keras.layers.MaxPooling2D((2, 2)),
        tf.keras.layers.Conv2D(512, (3, 3), padding='same', activation='relu'),
        tf.keras.layers.MaxPooling2D((2, 2)),
    
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(512, activation='relu'),
        tf.keras.layers.Dense(len(label_to_index), activation='softmax')
    ])
    
    # 모델 컴파일
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    
    # 모델 요약 확인
    print(model.summary())
    
    # 모델 학습
    model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=epochs, batch_size=batch)
    
    # 모델 저장하기
    model.save(hdf5_file)
    
    # 모델 평가
    score = model.evaluate(X_test, y_test)
    print('loss=', score[0])        # loss
    print('accuracy=', score[1])    # acc
    

if __name__=="__main__":
    cnn_model_train(data_path)