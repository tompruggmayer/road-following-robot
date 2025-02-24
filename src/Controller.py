"""
    The class that controls the robot behaviour
    We can consider this to be the "BRAIN" of our robot
"""

from typing import Any
import logging
import numpy as np
import torch
from torch2trt import TRTModule
import sys
import time
from Sense import Sense
from Actuation import Actuation
import threading
import paho.mqtt.client as mqtt
import io
from PIL import Image

MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_CHANNEL_SUBSCRIBE = "lab/orders"
MQTT_CHANNEL_DATA = "lab/sensor_data"
MQTT_CHANNEL_IMAGES = "lab/images"
MQTT_CHANNEL_STOP_SIGN = "lab/stop_sign"
stop_thread = False

logger = logging.getLogger(__name__)
logging.basicConfig(filename='logging.log', level=logging.DEBUG)

# DO NOT CHANGE THE FOLLOWING VALUES!
STEERING_GAIN = 0.7
STEERING_BIAS = 0.26

class Controller:

    _sense : Any
    _actuation : Any
    _road_following_model : Any
    _image_front : Any
    _running : bool
    _kill : bool
    _stop_sign_ignore : bool
    _stop_sign_count : Any

    def __init__(self):
        self._sense = Sense()
        self._actuation = Actuation(steering_gain=STEERING_GAIN, steering_bias=STEERING_BIAS)
        self._road_following_model = TRTModule()
        self._road_following_model.load_state_dict(torch.load('/home/jetson/Documents/DACH_robot/models/improved_road_following_model_trt.pth'))
        self._image_front = []
        self._running = True
        self._kill = False
        self._stop_sign_ignore = False
        self._stop_sign_count = 0
        print("Controller module initialized.")
        logger.debug("Finished initialization.")
        
    def loop(self)->bool:
        """
            Executes the main functionality of the robot and gets called in every tick.
        """
        # Getting the image from the camera
        self._image_front, image_front_preprocessed = self._sense.get_images(logger)
        
        # analyze the sensors value and determine the new command to execute
        steering_road_following, throttle = self._think(image_front_preprocessed)

        logger.debug(f"New Steering: {steering_road_following} New Throttle: {throttle}")
        
        # take action with new commands
        self._actuation.control_robot(float(steering_road_following[0]), throttle)
        
        # send current data to GUI
        self.send_robot_data_via_mqtt(float(steering_road_following[0]), throttle)
        return True
    
    def _think(self, image):
        """
            Makes the decision for the next move and returns it.
        """
        steering_road_following = self._road_following_model(image).detach().cpu().numpy().flatten()
        if self._running:
            throttle = 0.15
        else:
            throttle = 0.0
        return steering_road_following, throttle
    
    def send_robot_data_via_mqtt(self, steering, throttle):
        """
            Publishes the steering and throttle value via MQTT.
        """
        steering = steering * STEERING_GAIN + STEERING_BIAS
        client.publish(MQTT_CHANNEL_DATA, f"{steering}:{throttle}")
        
def on_message(client, userdata, msg):
    """
        Decodes the new message and changes the behaviour variables.
    """
    if msg.topic == MQTT_CHANNEL_SUBSCRIBE:
        message = msg.payload.decode()
        print(f"Received message on MQTT_CHANNEL_SUBSCRIBE: {message}")
        logger.debug(f"Received message on MQTT_CHANNEL_SUBSCRIBE: {message}")
        if message=="Go":
            controller._running = True
            print("Robot running!")
            logger.debug("Robot running!")
        elif message=="Stop":
            controller._running = False
            print("Robot stopped!")
            logger.debug("Robot stopped!")
        elif message=="Kill":
            controller._kill = True
            print("Robot killed!")
            logger.debug("Robot killed!")
        else:
            print("Received wrong message from mqtt!")
            logger.error("Received wrong message from mqtt!")
    elif msg.topic == MQTT_CHANNEL_STOP_SIGN:
        message = msg.payload.decode()
        print(f"Received message on MQTT_CHANNEL_STOP_SIGN: {message}")
        logger.debug(f"Received message on MQTT_CHANNEL_STOP_SIGN: {message}")
        if message=="Detected" and controller._stop_sign_ignore == False:
            controller._stop_sign_count = controller._stop_sign_count + 1
            print("Detected Stop sign!")
            logger.debug("Detected Stop sign!")
        if message=="Detected" and controller._stop_sign_ignore == False and controller._stop_sign_count>2:
            print("Stop at stop sign!")
            logger.debug("Stop at stop sign!")
            controller._running = False
            controller._stop_sign_count = 0
            
            # starting a new thread for stopping at the stop sign
            stop_thread = threading.Thread(target=stop_at_stop_sign)
            stop_thread.start()    

def stop_at_stop_sign():
    """
        Will turn on the robot again after 5 seconds of waiting and starts the ignoring threat.
    """
    time.sleep(5)
    controller._running = True
    controller._stop_sign_ignore = True
    
    # starting a new thread for ignoring the stop sign
    ignoring_thread = threading.Thread(target=ignore_stop_sign)
    ignoring_thread.start()

def ignore_stop_sign():
    """
        Waits 10 seconds and then stops to ignore the stop sign
    """
    time.sleep(10)
    controller._stop_sign_ignore = False
    
def getting_values_via_mqtt():
    """
        Subscribes to the given MQTT channel and starts the loop.
    """
    client.on_message = on_message
    client.subscribe(MQTT_CHANNEL_SUBSCRIBE)
    client.subscribe(MQTT_CHANNEL_STOP_SIGN)
    client.loop_forever()
    
def send_camera_images():
    """
        This function is called in a new thread and periodically sends 
        images of the camera via MQTT to the channel MQTT_CHANNEL_IMAGES.
    """
    while(True):
        image = controller._image_front
        if image != []:
            # convert the RGB image to grayscale using the luminance formula
            image_gray = np.dot(image[...,:3], [0.2989, 0.5870, 0.1140])

            # ensure that the resulting grayscale image is in uint8 format
            image_gray = image_gray.astype(np.uint8)

            # convert to bytestream to reduce the amount of data
            byte_stream = io.BytesIO()
            np.save(byte_stream, image_gray)
            bytearray_data = byte_stream.getvalue()
            client.publish(MQTT_CHANNEL_IMAGES, bytearray_data)
        time.sleep(0.25)
        if stop_thread == True:
            break


if __name__ == "__main__":
    print("Start Simulation!")
    logger.info("Start Simulation!")

    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    # starting a new thread for the mqtt listening
    listener_thread = threading.Thread(target=getting_values_via_mqtt)
    listener_thread.start()

    controller = Controller()
    start_time = time.time()
    
    # starting a new thread for sending the camera images
    camera_thread = threading.Thread(target=send_camera_images)
    camera_thread.start()
    
    while True:
        continue_simulation = controller.loop()

        if controller._kill:
            print("Exiting...")
            logger.debug("Exiting...")
            break
            
        if time.time() - start_time > 600:
            break
    
    # stopping camera thread, close mqtt connection and stop robot
    stop_thread = True
    controller._actuation.control_robot(0.0, 0.0)
    client.disconnect()
    sys.exit("Stopping the program")