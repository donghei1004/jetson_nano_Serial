import argparse
import cv2
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import model_from_json
import serial
import helper

Optimize_number = 0.14

# 카메라 이니셜라이징
print("Camera Initializing...")
cap = cv2.VideoCapture(0)
if (cap.isOpened() == False):
    print("Unable to read camera feed")
key = 0


print("Ready... Go?")
input()
print("Program Started...!")

# 시리얼 포트 연결
ser = serial.Serial("COM5", 115200)

# 딥러닝 용 코드, 딱히 시리얼 과정에서 쓸모있는 코드는 아니다
parser = argparse.ArgumentParser(description='Remote Driving')
parser.add_argument('model', type=str,
                    help='Path to model definition json. Model weights should be on the same path.')
args = parser.parse_args()
with open(args.model, 'r') as jfile:
    model = model_from_json(json.load(jfile))

model.compile("adam", "mse")
weights_file = args.model.replace('json', 'h5')
model.load_weights(weights_file)

# 초반 60개의 명령 메시지로 이니셜라이징 => 초기 조정과정이 없어졌다면 사라질 부분
# 파이썬 string.encode()함수는 파이썬 문자열을 바이트형식으로 엔코딩함 -> 현재 디폴트값으로 변환되는 형태는 utf-8 형태
for i in range(60):
    dataFormat = "<250,255,0>"
    # =======================Serial Write===========================
    ser.write(dataFormat.encode())
    print(dataFormat)
    key = cv2.waitKey(30)

# 기본 루프 시작
while True:
    ret, frame = cap.read()
    key = cv2.waitKey(30)
    image_array = np.asarray(frame)
    image_array = helper.crop(image_array, 0.5, 0.2)

    image_array = helper.resize(image_array, new_dim=(64, 64))
    HSV_image_array = cv2.cvtColor(image_array, cv2.COLOR_BGR2HSV)
    transformed_image_array = HSV_image_array[None, :, :, :]
    transformed_image_array = tf.cast(transformed_image_array, tf.float32)
    steering_angle = float(model.predict(transformed_image_array, batch_size=1))

    cv2.imshow("keytest", image_array)
    cv2.imshow("keytest2", HSV_image_array)

    # steering_angle INT transform
    INT_steering = int(steering_angle * 320)
    if INT_steering > 250:
        INT_steering = 250
    elif INT_steering < -250:
        INT_steering = -250
    INT_steering += 250

    # =======================Serial Write===========================
    dataFormat = "<{},510,1>".format(INT_steering)
    ser.write(dataFormat.encode())
    print(dataFormat)

    # KeyBoard X key Pressed
    if key is 120:
        dataFormat = "<250,255,3>"
        # =======================Serial Write===========================
        ser.write(dataFormat.encode())
        print(dataFormat)
        break
    # KeyBoard Y key Pressed
    if key is 121:
        cv2.waitKey(5000)
        for i in range(60):
            dataFormat = "<250,255,0>"
            # =======================Serial Write===========================
            ser.write(dataFormat.encode())
            print(dataFormat)
            key = cv2.waitKey(30)
print("Program Exit...")




