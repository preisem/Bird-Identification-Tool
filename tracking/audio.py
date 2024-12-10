import logging, time, sys, signal, json

from pathlib import Path
from subprocess import Popen
from datetime import datetime, timedelta

from birdnetlib.watcher import DirectoryWatcher
from birdnetlib.analyzer_lite import LiteAnalyzer
from birdnetlib.analyzer import Analyzer

logger = logging.getLogger(__name__)

def format_and_save_detections_to_file(detections, recording_path: Path, detections_directory: Path, location: tuple, node_name: str):
    ''' Get start date of recording from filename '''
    datetime_str = str(recording_path).split("/")[-1] #remove subfolder from filename (still has .wav)
    rec_start_time_obj = datetime.strptime(datetime_str, "%Y-%m-%d-birdnet-%H:%M:%S.wav")
    
    with open(detections_directory / Path("detections-" + datetime_str.split("-birdnet")[0] +".jsonl"), "a") as fileout:
        for detection in detections:
            json_out = {}
            json_out["start_ts"] = (rec_start_time_obj + timedelta(seconds=detection['start_time']) ).strftime("%Y-%m-%dT%H:%M:%S")
            json_out["end_ts"] = (rec_start_time_obj + timedelta(seconds=detection['end_time']) ).strftime("%Y-%m-%dT%H:%M:%S")
            json_out["common_name"] = detection['common_name']
            json_out["scientific_name"] = detection['scientific_name']
            json_out["confidence"] = detection['confidence']
            json_out["location"] = str(location)
            json_out["node_name"] = node_name
            json_out["filename"] = str(recording_path)
            
            print(json_out)
            fileout.write(json.dumps(json_out)+"\n")


def main(mic_name: str, recording_dir: Path, detections_directory: Path, location: tuple, node_name: str):

    duration_secs = 15
    RECORD_PROCESS = None
    
    ''' Create Analyzer Functions '''
    def on_analyze_complete(recording):
    # after each analyze is complete
        if recording.detections:
            ''' Send each detection to be formatted and written out to json file '''
            format_and_save_detections_to_file(recording.detections, recording.path, detections_directory, location, node_name)
            
    def on_error(recording, error):
        logger.error("An exception occurred: {}".format(error))
        logger.error(recording.path)

    ''' Create Signal Handler '''
    def signal_handler(sig, frame):
        RECORD_PROCESS.terminate()
        RECORD_PROCESS.wait()
        logger.info("Gracefully exiting process ...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    ''' Create Arecord command '''
    arecord_command_list = [
        "arecord",
        "-f",
        "S16_LE",
        "-c2",
        "-r48000",
        "-t",
        "wav",
        "-D",
        mic_name,
        "--max-file-time",
        f"{duration_secs}",
        "--use-strftime",
        f"{recording_dir}/%F-birdnet-%H:%M:%S.wav",
    ]

    ''' Start recording process '''
    logger.info("Starting to record audio with arecord now.")
    RECORD_PROCESS = Popen(arecord_command_list)
    
    ''' Start Analyzer '''
    try:
        analyzer = Analyzer()
        analyzers = [analyzer,]
        logger.info("Analyzer started")
    except Exception as e:
        logger.error(f"Error while starting the analyzer: {e}")
    
    ''' Start directory watcher to analyze new audio files '''
    directory = recording_dir
    watcher = DirectoryWatcher(
        directory,
        analyzers=analyzers,
        lon=location[1],
        lat=location[0],
        min_conf=0.2,
    )
    
    ''' Set function call after analyze of each recording is completed '''
    watcher.on_analyze_complete = on_analyze_complete
    watcher.on_error = on_error
    
    ''' Watch '''
    watcher.watch()


def listen_for_birds(mic: str, recording_directory: Path, detections_directory: Path, location: tuple, node_name: str):
    logger.info(f"Starting Bird Audio Listener with Microphone: {mic}")
    try:
        main(mic, recording_directory, detections_directory, location, node_name)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt")
    except Exception as e:
        logger.error(f"Error while listening for birds: {e}")
    return
