"""
    The Sense class read the sensor arrays
    from the Robot physical body
"""

import numpy as np
import cv2
from lib.utils import preprocess
from jetcam.csi_camera import CSICamera
from typing import Any
import matplotlib.pyplot as plt
from IPython.display import display, clear_output
from PIL import Image

class Sense:

    _camera : Any

    def __init__(self):
        self._camera = CSICamera(width=224, height=224, capture_fps=65)
        print("Sense module initialized.")
        
    def get_images(self, logger : Any):
        """ 
            Returns an image and a preprocessed image from the camera
        """
        image = cv2.cvtColor(self._camera.read(), cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
        image_preprocessed = preprocess(image).half()
        return image, image_preprocessed
        
    