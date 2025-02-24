from ultralytics import YOLO
import cv2
import os
import time
import paho.mqtt.client as mqtt

MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_CHANNEL_STOP_SIGN = "lab/stop_sign"

def process_image(model_path, image_path, traffic_sign_classes):
    """
    Process a single image, detecting traffic signs and returning True if any appear.

    Parameters:
    - model_path (str): Path to the YOLO model weights file.
    - image_path (str): Path to the image file.
    - traffic_sign_classes (list): List of class names corresponding to traffic signs.

    Returns:
    - bool: True if a traffic sign is detected, False otherwise.
    """
    
    model = YOLO(model_path)
    img = cv2.imread(image_path)
    results = model(img)
    
    detected = False
    for result in results:
        for detection in result.boxes.data:
            class_name = model.names[int(detection.tolist()[5])]
            if class_name in traffic_sign_classes:
                detected = True
                break
    return detected


#Example
if __name__ == "__main__":
    traffic_sign_classes = ["different-traffic-sign",
        "prohibition-sign", "speed-limit-sign", "warning-sign"]
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    while(True):
        result = process_image("fine_tuned_yolov8s.pt", "/home/jetson/Documents/DACH_robot/src/image_yolo_detection/yolo_image.jpg", traffic_sign_classes)
        print(f"Stop sign on image: {result}")
        client.publish(MQTT_CHANNEL_STOP_SIGN, str(result))
        time.sleep(0.1)
