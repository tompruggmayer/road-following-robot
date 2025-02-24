"""
    The Actuation block class that receives control signals
    from the controller and sends commands to the robot body.
"""

from jetracer.nvidia_racecar import NvidiaRacecar
from typing import Any

class Actuation:
    """
        Implements the Actuation module.
    """
    _steering_gain : float
    _steering_bias : float
    _car : Any

    def __init__(self, steering_gain : float, steering_bias : float):
        self._steering_gain = steering_gain
        self._steering_bias = steering_bias
        self._car = NvidiaRacecar()
        self._car.steering = 0.0
        print("Actuation module initialized.")
        
    def control_robot(self, steering : float, throttle : float)->None:
        """
            Receives a command and controls the movement of the robot according to it.
        """
        self._car.steering = steering * self._steering_gain + self._steering_bias
        self._car.throttle = throttle
        return
        