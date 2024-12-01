''' Matt P Server for Bird Migration Tool'''

import argparse
import logging
import multiprocessing as mp
import sys
import os

from pathlib import Path
from datetime import datetime
from random import shuffle, choice

import webserver #bird webserver frontend 
import tracking #bird audio and video tracking

logger = logging.getLogger(__name__)


def main(camera: int, mic: str, recordings_directory: Path):    
    
    ''' START '''
    date_today_str = datetime.now().strftime("%Y-%m-%d")
    logger.info("Starting Bird Server: " + str(date_today_str))
    
    ''' Create audio recordings directory if doesn't exist '''
    os.makedirs(recordings_directory, exist_ok=True) 
    
    ''' create worker instances for webserver and bird tracking '''
    bird_server_workers = [
        mp.Process(target=webserver.start_web_server,args=()),
        mp.Process(target=tracking.listen_for_birds,args=(mic,recordings_directory,)),
        mp.Process(target=tracking.look_for_birds,args=(camera,))
    ]
    
    ''' start each collection worker '''
    for worker in bird_server_workers:
        worker.start()

    ''' wait for each collection worker to finish. '''
    for worker in bird_server_workers:
        worker.join()
    
    ''' End of Sever, Shutdown '''
    logger.info("Closing Bird Server @ " + datetime.now().strftime("%H:%M:%S"))   

def empty_queue(queue):
    try:
        while True:
            _ = queue.get_nowait()
    except mp.queues.Empty:
        pass
        
  
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
    input_group.add_argument("--camera",type=int,required=True,help="Integer of camera device for video tracking")
    input_group.add_argument("--mic",type=str,required=True,help="Name of microphone device for audio tracking")
    
    output_group = parser.add_argument_group("Output")
    output_group.add_argument("--recordings-directory",type=Path,required=False,default=Path("./audio_recordings/"),help="Path to directory to save audio recordings")

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
    logging_group.add_argument("--log-file-path",required=False,default=Path("."),type=Path,help="log file path. (deafult is cwd)")
    
    #multiproccessing
    multiprocessing_group = parser.add_argument_group('Multiprocessing')
    #multiprocessing_group.add_argument('--workers',default=1,type=int)

    return parser.parse_args()


if __name__ == '__main__':
    try:
        ''' parse args '''
        args = parse_args()
        print(args)
        
        ''' set up logging, add packages (class files that need to be included for logging) '''
        set_up_logging(
            packages=[
                __name__, # always
                'webserver',
                'tracking'
            ],
            log_level=args.log_level,
            log_file=Path(args.log_file_path / Path(f'{datetime.today().year}-{str(datetime.today().month).zfill(2)}.log'))
        )
        
        ''' run main '''
        main(args.camera, args.mic, args.recordings_directory)
    except Exception as e:
        logger.error(f'Unknown exception of type: {type(e)} - {e}')
        raise e
