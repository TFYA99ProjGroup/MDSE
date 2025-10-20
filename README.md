# MDSE - Molecular Dynamics Simulation Environment

## Install dependencies
Use your virtual environment of choice, either venv or Anaconda, then run:
```
python -m pip install --upgrade pip
pip install -e .
```

## Run your first simulation
When the dependencies are installed you can try to run
```
mdse simulate --filepath examples/multiple_md.yaml
```
So called .traj-files will appear in the current working directory. These can be viewed with:
```
mdse view
```
The .traj files can be removed with:
```
mdse clean
```

Both view and clean can specify filepath with --filepath. 