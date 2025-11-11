#!/usr/bin/env python3
"""
Bird Identification Tool Web Server
- Simple authentication is based on NiceGUI example
- Not production ready, oauth and password hashing are not implemented
- resources:
    <https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/>
    <https://docs.authlib.org/en/v0.13/client/starlette.html#using-fastapi>
"""
import argparse, logging, os, sys
from pathlib import Path
from datetime import datetime
from nicegui import ui
import webui #internal pacakage

logger = logging.getLogger(__name__)


def main(detections_directory: Path, directory_watcher: Path, video_streams, authentication: bool, analyze_video: bool):
    ''' START '''
    date_today_str = datetime.now().strftime("%Y-%m-%d")
    logger.info("Starting Bird Server: " + str(date_today_str))
    
    ''' Load detections data '''
    detections_file = detections_directory / Path("detections-"+ datetime.now().strftime("%Y-%m-%d") + ".jsonl")
    detections_data = webui.generate_table_data_from_file(detections_file)

    ''' Start Video Analyzer (If Enabeled)'''
    if analyze_video:
        # override video_streams with processed endpoints
        video_streams = webui.start_yolo_stream_server(
            stream_urls=video_streams,
            port=8001,
            model_path="yolov8n.pt",  # or your custom-trained model
            skip_frames=5
        )

    ''' Authentication (WIP) with Login Route'''
    if authentication:
        webui.initAuthentication()

    ''' Generate Main Route '''
    webui.generateRouteMain(
        authentication=authentication,
        detections_data=detections_data,
        directory_watcher=directory_watcher
        )
    
    ''' Generate Analysis Route '''
    webui.generateRouteAnalysis(
        authentication=authentication,
        detections_data=detections_data
        )
    
    ''' Generate Video Route '''
    webui.generateVideoRoute(
        authentication=authentication,
        video_streams=video_streams
        )
    
    ''' Generate Readme Route '''
    webui.generateReadmeRoute(
        authentication=authentication
        )        
         
    ''' RUN ''' 
    ui.run(uvicorn_reload_includes='*.py, *.jsonl', storage_secret='THIS_NEEDS_TO_BE_CHANGED', show=False, favicon='🐦')
    
            
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
    input_group.add_argument("--directory-watcher",type=Path,required=False,help="Path to directory that the size in GB will be reported to the dashboard")
    input_group.add_argument("--video-streams",type=str,nargs="*",required=False,help="List of live stream urls to display on /video endpoint") # 1 or more stream urls with nargs="*"
    input_group.add_argument("--authentication",action="store_true", help="Enable authentication (omit to keep it False)")
    input_group.add_argument("--analyze-video",action="store_true", help=" Enable yolo processing on video streams, draws boxes around birds (omit to display raw video)")
    
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
        main(args.detections_directory, args.directory_watcher, args.video_streams, args.authentication, args.analyze_video)
    except Exception as e:
        logger.error(f'Unknown exception of type: {type(e)} - {e}')
        raise e
