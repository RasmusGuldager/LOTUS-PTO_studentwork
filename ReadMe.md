# LOTUS-PTO: Basler ace 2 python controller

## Python venv
1. ```python3 -m venv venv```
2. ```source venv/bin/activate```
3. ```pip install -r requirements.txt```


## Execution of code

1. Headless Control (CLI Only)
Use this for simple command-line interaction with the camera

```python3 -m Camera.camera_control```

2. Full Dashboard
Launches the full interactive terminal interface with live logs

```python3 main.py```

3. Automated Snapper Mode
To start the script with the auto-snapping background task enabled, use the -a or --auto flag (defaulted to 60 sec intervals)

```python3 main.py -a 60```


## If CV2 can't open on ubuntu wayland:

```export QT_QPA_PLATFORM=xcb```
