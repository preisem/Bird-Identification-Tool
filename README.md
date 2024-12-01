
## Install
```python -m pip install -r requirements.txt```

## QuickStart
```
python3 -m venv myvenv
source ./myvenv/bin/activate
python main.py --camera 0 --mic sysdefault --recordings-directory path/to/folder
```

## CMD Line Args
- ```--camera```: ```int``` X of camera device where device name = ```/dev/videoX```
- ```--mic```: ```str``` name of microphone device, can be found using command ```arecord -L```
- ```--recordings_directory```: ```pathlib.Path``` path of directory to save audio recordings to
