# OdeAudio
### Minimal setup
In the folder you've downloaded the code (the folder containing this readme file)

`cd MathAudio/`

Setup a virtual environment

`python -m venv .venv`

Activate that virtual environment - run one of the scripts in `.venv/Scripts`, depending on your OS, 
e.g.: `.\.venv\Scripts\Activate.ps1` on Windows Powershell

If using python 3.11, install Kivy development branch

```
python -m pip install kivy --pre --no-deps --index-url  https://kivy.org/downloads/simple/
python -m pip install "kivy[base]" --pre --extra-index-url https://kivy.org/downloads/simple/
```

Install requirements

`pip install -r requirements.txt`

Run the app

`python -m ODEAAudio.main`

### Controls
Spacebar: pause/play, the app starts paused

r: reset, pauses the app and resets y to y_init

click: sets lambda_c/lambda_e according to where you clicked

p: plot signal in background (note that this is very unstable, and will crash in under a minute)

escape: closes the app
