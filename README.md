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

Launch Julia and install a few modules we need - these would be installed automatically later, but the app will appear to hang for several minutes.

```julia
using Pkg
Pkg.add("DifferentialEquations")
Pkg.add("LinearAlgebra")
```

If you get any errors about Julia not being found - double check that it's on your path, and restart your machine.

#### Run the app

`python -m ODEAudio.main`

### Controls
Spacebar: pause/play, the app starts paused

r: reset, pauses the app and resets y to y_init

click: sets lambda_c/lambda_e according to where you clicked

p: plot signal in background (note that this is very unstable, and will crash in under a minute)

escape: closes the app
