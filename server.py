'''Server for Bird Migration Tool'''

import json, time, argparse, logging, os, sys

from nicegui import events, ui
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

def main(detections_directory: Path):
    ''' START '''
    date_today_str = datetime.now().strftime("%Y-%m-%d")
    logger.info("Starting Bird Server: " + str(date_today_str))
    
    ''' title of page '''
    ui.markdown("##Birds Detected Today")
    
    ''' generate table data and headers from file '''
    detections_file = detections_directory / Path("detections-"+ datetime.now().strftime("%Y-%m-%d") + ".jsonl")
    rows = []
    try:
        rows = generate_table_data_from_file(detections_file)
        ''' create table object using data and headers '''
        table = ui.table(rows=rows)
    except Exception as e:
        logger.error("Exception while generating table: " + str(e))
        
    ''' run server, reload when files are modified '''
    ui.run(uvicorn_reload_includes='*.py, *.jsonl')

def generate_table_data_from_file(file_path: Path):
    rows = []
    with open(file_path, "r") as filein:
        for line in filein:
            data = json.loads(line.strip("\n"))
            rows.append(data)
    return(rows)
  
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
    input_group.add_argument("--detections-directory",type=Path,required=False,default=Path("./detections/"),help="Path to directory where detections from node analyzers are saved")

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


if __name__ in {"__main__", "__mp_main__"}: #to allow server to run within mp
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
            ],
            log_level=args.log_level,
            log_file=Path(args.log_file_path / Path(f'{datetime.today().year}-{str(datetime.today().month).zfill(2)}-server.log'))
        )
        
        ''' run main '''
        main(args.detections_directory)
    except Exception as e:
        logger.error(f'Unknown exception of type: {type(e)} - {e}')
        raise e

