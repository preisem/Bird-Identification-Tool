
## Install
```python -m pip install -r requirements.txt```

## QuickStart
```
python3 -m venv myvenv
source ./myvenv/bin/activate
python main.py --camera 0 --mic sysdefault --recordings-directory path/to/folder --location 42.0051 -74.2660
```
## Import Notes
- check the audio device names using ```arecord -L```
- check the video device names using ```v4l2-ctl --list-devices```

## CMD Line Args
- ```--camera```: ```int``` X of camera device where device name = ```/dev/videoX```
- ```--mic```: ```str``` name of microphone device, can be found using command ```arecord -L```
- ```--recordings_directory```: ```pathlib.Path``` path of directory to save audio recordings to
- ```--location ```: ```float, tuple``` GPS location of devices using tuple such like: lat lon
- ```--detections_directory```: ```pathlib.Path``` path of directory to save jsonl data of detected birds
- ```--log-file-path```: ```pathlib.Path``` parth to directory to save log files

## JSON Output Data Schema 
|field-name|data-type|description|example|
|----------|---------|-----------|-------|
|start_ts|datetime string|datetime string indicating start of detection|2024-12-02T11:43:41|
|end_ts|datetime string|datetime string indicating end of detection|2024-12-02T11:43:50|
|common_name|string|common name of detected bird||
|scientific_name|string|scientific name of detected bird||
|confidence|float|confidince of the detection|0.85435|
|location|string tuple '(float,float)'|location of the detection, expressed as a string tuple in format '(lat,lon)'|(42.01,-74.28)|
|filename|string pathlib.Path|filepath to audio file that the detection was made|sounds/2024-12-02-birdnet-11:43:35.wav|
