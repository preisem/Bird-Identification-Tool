'''Node for Bird Migration Tool'''

import argparse
import logging
import multiprocessing as mp
import sys
import os

from pathlib import Path
from datetime import datetime
from geopy.geocoders import Nominatim

import tracking #bird audio and video tracking

logger = logging.getLogger(__name__)


def main(camera: int, mic: str, recordings_directory: Path, detections_directory: Path, location: tuple, node_name: str, min_confidence: float, save_audio: str):    
    
    ''' START '''
    date_today_str = datetime.now().strftime("%Y-%m-%d")
    logger.info("Starting Bird Node ("+ node_name +"): " + str(date_today_str))
    
    ''' Interpret Location '''
    interpret_geolocation(location)

    ''' Create audio recordings  and detections directory if doesn't exist '''
    os.makedirs(recordings_directory, exist_ok=True) 
    os.makedirs(detections_directory, exist_ok=True)
    
    ''' create worker instances for bird tracking '''
    bird_server_workers = []
    # add audio worker
    bird_server_workers.append(
        mp.Process(target=tracking.listen_for_birds,args=(mic, recordings_directory, detections_directory, location, node_name, min_confidence, save_audio, ))
        )
    # add video worker if --camera exists
    if camera is not None:
        bird_server_workers.append(mp.Process(target=tracking.look_for_birds,args=(camera, )))
    
    ''' start each collection worker '''
    for worker in bird_server_workers:
        worker.start()

    ''' wait for each collection worker to finish. '''
    for worker in bird_server_workers:
        worker.join()
    
    ''' End of Sever, Shutdown '''
    logger.info("Closing Bird Node @ " + datetime.now().strftime("%H:%M:%S"))   

def empty_queue(queue):
    try:
        while True:
            _ = queue.get_nowait()
    except mp.queues.Empty:
        pass
        
def interpret_geolocation(location: tuple):
    geolocator = Nominatim(user_agent="my_geocoder")
    retries = 0
    max_retries = 5
    while retries <= max_retries:
        try:
            location_geo = geolocator.reverse((location[0], location[1]), exactly_one=True)
            if location_geo:
                address = location_geo.raw['address']
                town = address.get('town', '')
                state = address.get('state', '')
                logger.info(f"Location set to {town}, {state} ({location[0]},{location[1]})")
            else:
                logger.warning(f"Location set to UNKNOWN ({location[0]},{location[1]})")
            return 
        except Exception as e:
            logger.warning(f"Error while trying to geolocate coordinates: {e}")
            retries = retries + 1 
            if retries > max_retries:
                logger.error(f"Max retries ({max_retries}) hit, skipping geolocation coordinates")
                logger.warning(f"Location set to UNKNOWN ({location[0]},{location[1]})")
                return
            else: #retry limit not hit so wait before retry 
                logger.warning(f"Retry({retries}) in 10s...") 
                time.sleep(10)
            
  
def set_up_logging(packages, log_level, log_file):
    '''Set up logging for specific packages/modules.'''
    formatter = logging.Formatter('%(asctime)s - %(process)d - %(levelname)s - %(message)s')
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    for package in packages:
        package_logger = logging.getLogger(package)
        package_logger.addHandler(stream_handler)
        package_logger.addHandler(file_handler)
        package_logger.setLevel(log_level)
  
def parse_args():
    '''Parse command line arguments.'''
    parser = argparse.ArgumentParser()

    # Command line arguments for input.
    input_group = parser.add_argument_group("Input")
    input_group.add_argument("--camera",type=int,required=False,help="Integer of camera device for video tracking")
    input_group.add_argument("--mic",type=str,required=True,help="Name of microphone device for audio tracking")
    input_group.add_argument("--location",type=float,nargs=2,required=True,help="GPS location tuple such like: lat lon")
    input_group.add_argument("--node-name",type=str,required=False,default="default",help="Name for node")
    input_group.add_argument("--min-confidence",type=float,required=False,default=0.2,help="Minimum confidence of model for audio detection (default=0.2, range=0.0<x<1.0)")
    
    output_group = parser.add_argument_group("Output")
    output_group.add_argument("--recordings-directory",type=Path,required=False,default=Path("./audio_recordings/"),help="Path to directory to save audio recordings")
    output_group.add_argument("--detections-directory",type=Path,required=False,default=Path("./detections/"),help="Path to directory to save detections from analyzers")
    output_group.add_argument("--save-audio",type=str,choices=["always", "detections-only", "never"], default="detections-only", required=False, help="Options for saving audio files after processing (always, detections-only, or never)")

    # Command line arguments for logging configuration.
    logging_group = parser.add_argument_group('Logging')
    log_choices = ['DEBUG', 'CRITICAL', 'FATAL', 'ERROR', 'WARNING', 'WARN', 'INFO', 'NOTSET']
    logging_group.add_argument(
        '--log-level',
        required=False,
        default='INFO',
        metavar='LEVEL',
        type=str.upper, # nice trick to catch ERROR, error, Error, etc.
        choices=log_choices,
        help=f'log level {log_choices}'
    )
    logging_group.add_argument("--log-file-path",required=False,default=Path("./logs/"),type=Path,help="log file path. (deafult is cwd)")
    
    return parser.parse_args()


if __name__ == '__main__':
    try:
        ''' parse args '''
        args = parse_args()
        print(args)
        
        ''' create log dir if doesn't already exist '''
        os.makedirs(args.log_file_path, exist_ok=True)
        
        ''' set up logging, add packages (class files that need to be included for logging) '''
        set_up_logging(
            packages=[
                __name__, # always
                'tracking'
            ],
            log_level=args.log_level,
            log_file=Path(args.log_file_path / Path(f'{datetime.today().year}-{str(datetime.today().month).zfill(2)}-node-{args.node_name}.log'))
        )
        
        ''' run main '''
        main(args.camera, args.mic, args.recordings_directory, args.detections_directory, tuple(args.location), args.node_name, args.min_confidence, args.save_audio)
    except Exception as e:
        logger.error(f'Unknown exception of type: {type(e)} - {e}')
        raise e
