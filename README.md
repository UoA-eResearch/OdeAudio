# OdeAudio
### Minimal setup
In the folder you've downloaded the code (the folder containing this readme file)

`cd MathAudio/`

Setup a virtual environment

`python -m venv .venv`

Activate that virtual environment - run one of the scripts in `.venv/Scripts`, depending on your OS, 
e.g.: `.\.venv\Scripts\Activate.ps1` on Windows Powershell

Install requirements

```
pip install kivy[full] --pre --extra-index-url https://kivy.org/downloads/simple/
pip install -r requirements.txt
```

#### Julia setup
We use Julia for integration, first install it from the website

https://julialang.org/downloads/

Make sure the check 'add Julia to PATH' during installation, and restart your machine.

Using this package's venv, install julia dependencies in a python interpretter:
    
```python
import julia
julia.install()

import diffeqpy
diffeqpy.install()
```

#### Run the app

`python -m ODEAudio.main`

### Controls
Spacebar: pause/play, the app starts paused

n: reset, pauses the app and resets y to y_init
m: specify parameters exactly

q/w/e/r/t: nudge u[0-5] up
a/s/d/f/g: nudge u[0-5] down

1/2/3/4/5: select which axis to listen to on the left audio channel
6/7/8/9/0: select which axis to listen to on the right audio channel

click & drag in the left window: select the region of parameter space shown in the right window
click in the right window: sets lambda_c according to where you clicked

escape: closes the app
