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
    ui.page_title('Bird Identification Tool')
    #ui.markdown("##Birds Detected Today")
    
    ''' load data from jsonl file into detections_data'''
    detections_file = detections_directory / Path("detections-"+ datetime.now().strftime("%Y-%m-%d") + ".jsonl")
    detections_data = generate_table_data_from_file(detections_file)
    
    ''' PLACE OBJECTS ON SCREEN '''
    
    with ui.splitter(value=35) as splitter:
        with splitter.before: # LEFT SIDE OBJECTS
        
            ''' create table object using data and headers '''
            table = ui.table(rows=detections_data, title='Birds Detected Today', pagination={'rowsPerPage': 10, 'descending': True, 'sortBy': 'start_ts'},).classes('w-full')
                                                   
              
        with splitter.after: # RIGHT SIDE
            ''' create tabs to display graphs '''
            with ui.tabs() as tabs:
                one = ui.tab('Species Distribution')
                two = ui.tab('Model Confidence')
            with ui.tab_panels(tabs, value=one):
                with ui.tab_panel(one):
                    ''' distribution by species pie chart '''
                    piechart = generate_pie_chart_object(pie_type="species-distro", input_data=detections_data)
                with ui.tab_panel(two):
                    ''' avg model confidence bar chart '''
                    barchart = generate_bar_chart_object(bar_type="species-confidence", input_data=detections_data)
            
                 
    ''' run server, reload when files are modified '''
    ui.run(uvicorn_reload_includes='*.py, *.jsonl', favicon='🐦')

def generate_table_data_from_file(file_path: Path):
    rows = []
    try:
        with open(file_path, "r") as filein:
            for line in filein:
                data = json.loads(line.strip("\n"))
                rows.append(data)
    except Exception as e:
        logger.error("Exception while generating table: " + str(e))            
    
    return rows
    
def generate_pie_chart_object(pie_type: str, input_data):
    ''' create data, then series, then chart '''
    if pie_type=="species-distro":
        ''' create data '''
        bird_counts = [] #each item will be name, count json objects
        bird_names = [] # keep track of all bird names so far 
        for entry in input_data:
            if entry['common_name'] not in bird_names:
                ''' new bird, so add object with 1 count to bird counts '''
                bird_counts.append({'name': entry['common_name'], 'y': 1 })
                bird_names.append(entry['common_name'])
            else:
                for n in bird_counts:
                    if n['name'] == entry['common_name']:
                        old_y = n['y'] # get y
                        bird_counts.remove(n)#remove old from list
                        bird_counts.append({'name': entry['common_name'], 'y': old_y + 1 }) # add new to list
                    
        data = bird_counts
        ''' static test data 
        data = [
                {'name': 'Northern Cardinal', 'y': 34 },
                {'name': 'Carbohydrates', 'y': 10},
                {'name': 'Protein', 'y': 15},
                {'name': 'Ash', 'y': 21}
            ]
         '''   
            
        ''' create series using data '''
        series = [{ 'name': 'Count',  'data': data}]
        
        '''create chart using series '''
        chart = ui.highchart({
            'title': {'text': 'Distribution of Birds by Species'},
            'chart': {'type': 'pie'},
            #'tooltip': {'valueSuffix': '%'},
            'series': series,
            })
        
        return chart
        
def generate_bar_chart_object(bar_type: str, input_data):
    ''' create data, then series, then chart '''
    if bar_type=="species-confidence":
        ''' create data '''
        bird_counts = [] #each item will be name, count json objects
        bird_confidence_total = [] #each item will be the confidence of each detection
        bird_names = [] # keep track of all bird names so far 
        for entry in input_data:
            if entry['common_name'] not in bird_names:
                ''' new bird, so add object with 1 count to bird counts '''
                bird_counts.append({'name': entry['common_name'], 'y': 1 })
                bird_names.append(entry['common_name'])
                bird_confidence_total.append({'name': entry['common_name'], 'y': entry['confidence'] })
            else:
                for n in bird_counts:
                    if n['name'] == entry['common_name']:
                        old_y = n['y'] # get y
                        bird_counts.remove(n)#remove old from list
                        bird_counts.append({'name': entry['common_name'], 'y': old_y + 1 }) # add new to list
                for n in bird_confidence_total:
                    if n['name'] == entry['common_name']:    
                        old_conf = n['y']
                        bird_confidence_total.remove(n)
                        bird_confidence_total.append({'name': entry['common_name'], 'y': entry['confidence'] + old_conf})
        avg_confidence = []
        for a,b in zip(bird_confidence_total, bird_counts):
            avg_confidence.append({'name': a['name'], 'y': a['y'] / b['y'] })
        
        data = avg_confidence
            
        ''' create series using data '''
        series = [{ 'name': 'Avg Confidence',  'data': data}]
        
        '''create chart using series '''
        chart = ui.highchart({
            'title': {'text': 'Average Model Confidence by Species'},
            'chart': {'type': 'column'},
            'xAxis': {'type': 'category', 'labels': { 'autoRotation': [-45, -90]}},
            'yAxis': {'ceiling': 1, 'title': {'text': 'Confidence'} },
            'legend': {'enabled': False},
            'plotOptions': {'column': {'colorByPoint': True}},
            'series': series,
            })
        
        return chart
        
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
