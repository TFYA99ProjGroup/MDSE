# MDSE - Molecular Dynamics Simulation Environment

## Licensing
This repository is primarily licensed under the MIT License. See root LICENSE for full details.

### **Important License Exception**
The code and files contained within **`httklib/`** are governed by the GNU Affero General Public License. A copy of this license can be found within that directory at `httklib/LICENSE`.

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
