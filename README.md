
## Install
```python -m pip install -r requirements.txt```

## QuickStart
```
python3 -m venv myvenv
source ./myvenv/bin/activate
python main.py --camera 0 --mic sysdefault --recordings-directory path/to/folder --location 42.0051 74.2660
```

## CMD Line Args
- ```--camera```: ```int``` X of camera device where device name = ```/dev/videoX```
- ```--mic```: ```str``` name of microphone device, can be found using command ```arecord -L```
- ```--recordings_directory```: ```pathlib.Path``` path of directory to save audio recordings to
- ```--location ```: ```float, tuple``` GPS location of devices using tuple such like: lat lon 
