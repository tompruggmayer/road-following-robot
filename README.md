# Road following robot

## Requirements
* Jetracer Pro AI fully set up (details for setup: https://www.waveshare.com/wiki/JetRacer_Pro_AI_Kit#interactive-regression)
* Python 3.6.9 or higher on the Jetracer

## Quick start guide on the Jetracer

* Pull the repository with:
```
    git clone https://github.com/tompruggmayer/road-following-robot.git
```
* go into the reposity with:
```
    cd road-following-robot
```
* Install the required python libraries with:
```
    pip install -r requirements.txt
```
* In an other terminal start Controller.py with:
```
    python Controller.py
```

## Quick start guide GUI
* On an other PC, pull the repository with:
```
    git clone https://github.com/tompruggmayer/road-following-robot.git
```
* go into the reposity with:
```
    cd road-following-robot/GUI
```
* Install the required python libraries with:
```
    pip install -r requirements_GUI.txt
```
* Start the GUI with:
```
    python GUI.py
```
* Now commands can be given in the GUI and the robot executes them. The execution can be stopped by pressing the stop button.

## Important Notes
* Sometimes the camera is causing errors, it has to be restarted with this command: sudo systemctl restart nvargus-daemon