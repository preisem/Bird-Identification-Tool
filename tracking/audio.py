import logging
import time

from pathlib import Path
from subprocess import Popen
import sys
import signal
from datetime import datetime
from pprint import pprint

from birdnetlib.watcher import DirectoryWatcher
from birdnetlib.analyzer_lite import LiteAnalyzer
from birdnetlib.analyzer import Analyzer

logger = logging.getLogger(__name__)

def on_analyze_complete(recording):
    print("on_analyze_complete")
    # Each analyzation as it is completed.
    print(recording.path, recording.analyzer.name)
    pprint(recording.detections)


def on_analyze_file_complete(recording_list):
    print("---------------------------")
    print("on_analyze_file_complete")
    print("---------------------------")
    # All analyzations are completed. Results passed as a list of Recording objects.
    for recording in recording_list:
        print(recording.filename, recording.date, recording.analyzer.name)
        pprint(recording.detections)
        print("---------------------------")


def on_error(recording, error):
    print("An exception occurred: {}".format(error))
    print(recording.path)


def preanalyze(recording):
    # Used to modify the recording object before analyzing.
    filename = recording.filename
    # 2022-08-15-birdnet-21:05:51.wav, as an example, use BirdNET-Pi's preferred format for testing.
    dt = datetime.strptime(filename, "%Y-%m-%d-birdnet-%H:%M:%S.wav")
    # Modify the recording object here as needed.
    # For testing, we're changing the date. We could also modify lat/long here.
    recording.date = dt


def main(mic_name: str, recording_dir: Path, location: tuple):

    duration_secs = 15

    RECORD_PROCESS = None

    def signal_handler(sig, frame):
        RECORD_PROCESS.terminate()
        RECORD_PROCESS.wait()
        print("Gracefully exitting process ...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

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

    # Start arecord in a separate process ...
    RECORD_PROCESS = Popen(arecord_command_list)

    print("Starting Analyzer")

    analyzer = Analyzer()
    analyzers = [analyzer,]

    print("Starting Watcher")

    directory = recording_dir
    watcher = DirectoryWatcher(
        directory,
        analyzers=analyzers,
        lon=location[1],
        lat=location[0],
        min_conf=0.1,
    )
    watcher.recording_preanalyze = preanalyze
    watcher.on_analyze_complete = on_analyze_complete
    watcher.on_analyze_file_complete = on_analyze_file_complete
    watcher.on_error = on_error
    watcher.watch()


def listen_for_birds(mic: str, recording_directory: Path, location: tuple):
    logger.info(f"Starting Bird Audio Listener with Microphone: {mic}")
    logger.info(f"Microphone Location: {location}")
    try:
        main(mic, recording_directory, location)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt")
    except Exception as e:
        logger.error(f"Error while listening for birds: {e}")
    return
