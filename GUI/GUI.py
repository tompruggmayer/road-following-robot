"""
    This script contains the code of the UI. With the help of the UI the commands can be given to the robot. 
    It publishes the commands to an MQTT chanel from which the Control module reads from. 
    Also it subscribes to the lab/sensor_data and lab/images and displays them. 
"""
# Python program to create a basic GUI 
# application using the customtkinter module

import customtkinter as ctk
import threading
import paho.mqtt.client as mqtt
from PIL import Image, ImageTk, ImageEnhance
import numpy as np
import tkinter as tk
import io

MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_CHANNEL_PUBLISH = "lab/orders"
MQTT_CHANNEL_DATA = "lab/sensor_data"
MQTT_CHANNEL_IMAGES = "lab/images"

# Basic parameters and initializations
# Supported modes : Light, Dark, System
ctk.set_appearance_mode("System") 

# Supported themes : green, dark-blue, blue
ctk.set_default_color_theme("green") 

appWidth, appHeight = 600, 700


# App Class
class App(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # set initial value
        self.Behave = "Go"

        self.title("Robot control panel")
        self.geometry(f"{appWidth}x{appHeight}")

        # Top label
        self.occupationLabel = ctk.CTkLabel(self,
                                            text="Robot control panel", font=("Arial", 20))
        self.occupationLabel.grid(row=0, column=0, columnspan=2,
                                padx=20, pady=20,
                                sticky="w")

        # Go Button
        self.generateResultsButton = ctk.CTkButton(self,
                                        text="Go", command=self.go_behave)
        self.generateResultsButton.grid(row=1, column=0,
                                        columnspan=1,
                                        padx=20, pady=20,
                                        sticky="ew")
        
        # Stop Button
        self.generateResultsButton = ctk.CTkButton(self,
                                        text="Stop", command=self.stop_behave)
        self.generateResultsButton.grid(row=1, column=1,
                                        columnspan=1,
                                        padx=20, pady=20,
                                        sticky="ew")
        
        # Kill Button
        self.generateResultsButton = ctk.CTkButton(self,
                                        text="Kill", command=self.kill_behave)
        self.generateResultsButton.grid(row=1, column=2,
                                        columnspan=1,
                                        padx=20, pady=20,
                                        sticky="ew")
        
        # Current robot data label
        self.command_history_Label = ctk.CTkLabel(self,
                                            text="Current robot data",font=("Arial", 15))
        self.command_history_Label.grid(row=2, column=0, padx=20,
                                sticky="w")
        
        # steering value label
        self.steering_Label = ctk.CTkLabel(self,
                                            text="Steering:")
        self.steering_Label.grid(row=3, column=0, padx=20,
                                sticky="w")
        
        # steering value textbox
        self.steering_textbox = ctk.CTkTextbox(master=self, width=150, height=15, corner_radius=5)
        self.steering_textbox.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
        
        # Throttle value label
        self.throttle_Label = ctk.CTkLabel(self,
                                            text="Throttle:")
        self.throttle_Label.grid(row=4, column=0, padx=20,
                                sticky="w")
        
        # Throttle value textbox
        self.throttle_textbox = ctk.CTkTextbox(master=self, width=150, height=15, corner_radius=5)
        self.throttle_textbox.grid(row=4, column=1, padx=10, pady=10, sticky="ew")

        # Camera view label
        self.camera_view_Label = ctk.CTkLabel(self,
                                            text="Camera view", font=("Arial", 15))
        self.camera_view_Label.grid(row=5, column=0, padx=20,
                                sticky="w")
        
        # Camera view image
        self.camera_view_canvas = ctk.CTkCanvas(self, width=400, height=400)
        self.camera_view_canvas.grid(row=6, column=0, padx=20, columnspan=3,
                                sticky="w")

    def change_textbox_value(self, input : str):
        self.throttle_textbox.insert("1.0", str(input))


    def stop_behave(self):
        """
            Changes the value of the behave variable to Stop.
        """
        self.Behave = "Stop"
        print(self.Behave)
        client.publish(MQTT_CHANNEL_PUBLISH, str(self.Behave))

    def go_behave(self):
        """
            Changes the value of the behave variable to Go.
        """
        self.Behave = "Go"
        print(self.Behave)
        client.publish(MQTT_CHANNEL_PUBLISH, str(self.Behave))

    def kill_behave(self):
        """
            Changes the value of the behave variable to Kill.
        """
        self.Behave = "Kill"
        print(self.Behave)
        client.publish(MQTT_CHANNEL_PUBLISH, str(self.Behave))

def on_message(client, userdata, msg):
    """
        Receiving the new messages and adds displaying them on the UI
    """
    if msg.topic == "lab/sensor_data":
        message = msg.payload.decode()
        values = message.split(":")
        app.steering_textbox.delete("1.0", "end")
        app.steering_textbox.insert("1.0", str(values[0]))
        app.throttle_textbox.delete("1.0", "end")
        app.throttle_textbox.insert("1.0", str(values[1]))
    elif msg.topic == "lab/images":
        # get image as bytestream 
        byte_stream = io.BytesIO(msg.payload)
        restored_array = np.load(byte_stream)
        image_pil = Image.fromarray(restored_array.astype('uint8'))

        # Enhance brightness
        enhancer = ImageEnhance.Brightness(image_pil)
        image_pil = enhancer.enhance(1.5)

        # resize image
        resized_pil_image = image_pil.resize((400, 400), Image.Resampling.LANCZOS)

        # show image on GUI
        tk_image = ImageTk.PhotoImage(resized_pil_image)
        app.camera_view_canvas.delete("all")
        app.camera_view_canvas.create_image(0, 0, anchor=tk.NW, image=tk_image)
        app.camera_view_canvas.image = tk_image


def getting_values_via_mqtt():
    """
        Fetches new order from the channel and adds them to the list of orders.
        Returns True if there is a new order in the channel and False if there is none.
    """
    client.subscribe(MQTT_CHANNEL_DATA)
    client.subscribe(MQTT_CHANNEL_IMAGES)
    client.loop_forever()


if __name__ == "__main__":
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    client.on_message = on_message

    # starting a new thread for the mqtt listening
    listener_thread = threading.Thread(target=getting_values_via_mqtt)
    listener_thread.start()

    app = App()
    app.mainloop()
