# Bird Identification Tool
[![Python](https://img.shields.io/static/v1?&message=Python%203.12.3&logo=python&labelColor=gray&color=1182c3&logoColor=white&label=%20)](https://www.python.org/downloads/release/python-3123/) 
[![Python application](https://github.com/preisem/Bird-Identification-Tool/actions/workflows/python-app.yml/badge.svg)](https://github.com/preisem/Bird-Identification-Tool/actions/workflows/python-app.yml)
[![BirdNetLib](https://img.shields.io/static/v1?&message=birdnetlib&logo=pypi&labelColor=5c5c5c&color=f27b3a&logoColor=white&label=%20)](https://pypi.org/project/birdnetlib/)
[![NiceGUI](https://img.shields.io/static/v1?&message=NiceGUI&logo=pypi&labelColor=5c5c5c&color=609867&logoColor=white&label=%20)](https://pypi.org/project/nicegui/)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-E95420?style=for-the-badge&logo=Ubuntu&logoColor=white)](https://ubuntu.com/blog/tag/ubuntu-24-04-lts)

This tool is split into 2 main parts:
- Node (main.py): Nodes collect and analyze audio (and eventually video) and save bird detections to daily jsonl files
- Server (server.py): Webserver reads jsonl bird detection files created by nodes, displays data
## Install
```
sudo apt-get install v4l-utils -y
sudo apt-get install python3-pip -y
sudo apt-get install python3-virtualenv -y
python3 -m venv myvenv
source ./myvenv/bin/activate
python -m pip install -r requirements.txt
```

## QuickStart
### Node
  ```
  (myvenv) python main.py --camera 0 --mic sysdefault --location 42.0051 -74.2660 --recordings-directory path/to/folder --detections-directory path/to/folder --log-file-path path/to/folder 
  ```
### Server
  ```
  (myvenv) python server.py --detections-directory path/to/folder --log-file-path path/to/folder
  ```
## Import Notes
- check the audio device names using ```arecord -L```
- check the video device names using ```v4l2-ctl --list-devices```

## CMD Line Args
### Node
- ```--camera```: ```int``` X of camera device where device name = ```/dev/videoX```
- ```--mic```: ```str``` name of microphone device, can be found using command ```arecord -L```
- ```--location ```: ```float, tuple``` GPS location of devices using tuple such like: lat lon
- ```--node-name ```: ```str``` Name of node
- ```--min-confidence ```: ```float``` Minimum confidence of model for audio detection (default=0.2, range=0.0<x<1.0)
- ```--recordings-directory```: ```pathlib.Path``` path of directory to save audio recordings to
- ```--detections-directory```: ```pathlib.Path``` path of directory to save jsonl data of detected birds
- ```--log-file-path```: ```pathlib.Path``` parth to directory to save log files
### Server
- ```--detections_directory```: ```pathlib.Path``` path of directory to load jsonl data of detected birds
- ```--directory_wathcer```: ```pathlib.Path``` path to directory that the size in GB will be reported to the dashboard (optional)
- ```--log-file-path```: ```pathlib.Path``` parth to directory to save log files

## JSON Output Data Schema 
|field-name|data-type|description|example|
|----------|---------|-----------|-------|
|start_ts|datetime string|datetime string indicating start of detection|2024-12-02T11:43:41|
|end_ts|datetime string|datetime string indicating end of detection|2024-12-02T11:43:50|
|common_name|string|common name of detected bird|American Crow|
|scientific_name|string|scientific name of detected bird|Corvus brachyrhynchos|
|confidence|float|confidince of the detection|0.85435|
|location|string tuple '(float,float)'|location of the detection, expressed as a string tuple in format '(lat,lon)'|(42.01,-74.28)|
|node_name|string|name of node|backyard-1|
|filename|string pathlib.Path|filepath to audio file that the detection was made|sounds/2024-12-02-birdnet-11:43:35.wav|
