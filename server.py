#!/usr/bin/env python3
"""
Bird Identification Tool Web Server
- Simple authentication is based on NiceGUI example
- Not production ready, oauth and password hashing are not implemented
- resources:
    <https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/>
    <https://docs.authlib.org/en/v0.13/client/starlette.html#using-fastapi>
"""
import json, time, argparse, logging, os, sys
from typing import Optional
from pathlib import Path
from datetime import datetime

from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from nicegui import events, app, ui

logger = logging.getLogger(__name__)


def main(detections_directory: Path, directory_watcher: Path):
    ''' START '''
    date_today_str = datetime.now().strftime("%Y-%m-%d")
    logger.info("Starting Bird Server: " + str(date_today_str))
        
    ''' load data from jsonl file into detections_data'''
    detections_file = detections_directory / Path("detections-"+ datetime.now().strftime("%Y-%m-%d") + ".jsonl")
    detections_data = generate_table_data_from_file(detections_file)
       
    ''' Authentication (WIP)'''
    passwords = {'admin': 'password'}

    unrestricted_page_routes = {'/login'}

    ''' define classes and functions for each route '''
    class AuthMiddleware(BaseHTTPMiddleware):
        """
        This middleware restricts access to all NiceGUI pages.
        It redirects the user to the login page if they are not authenticated.
        """
        async def dispatch(self, request: Request, call_next):
            if not app.storage.user.get('authenticated', False):
                if not request.url.path.startswith('/_nicegui') and request.url.path not in unrestricted_page_routes:
                    app.storage.user['referrer_path'] = request.url.path  # remember where the user wanted to go
                    return RedirectResponse('/login')
            return await call_next(request)

    app.add_middleware(AuthMiddleware)

    ''' MAIN ROUTE / '''
    @ui.page('/')
    def main_page() -> None:
        def logout() -> None:
            app.storage.user.clear()
            ui.navigate.to('/login')
        
        
        ''' title of page '''
        ui.page_title('Bird Identification Tool')          
    
        with ui.header():
            username = app.storage.user["username"][0].upper() + app.storage.user["username"][1:] #uppercase the first letter
            ui.image("img/icon.png").classes("h-12 w-12") #logo icon
            ui.label(f'Hello {username}!').style('color: #FFFFFF; font-size: 200%; font-weight: 300') # header banner
            ui.space() # creates space between left justified and right justified items
            ui.button('Analysis', on_click=lambda: ui.navigate.to('/analysis')).classes("h-11") # button link to /analysis
            ui.button('Readme', on_click=lambda: ui.navigate.to('/readme')).classes("h-11") # button link to /readme
            ui.button(on_click=logout, icon='logout').classes("h-11") # logout button
        
        ''' MAIN DASHBOARD CARDS '''
        with ui.card().classes('absolute-center'):
            with ui.column():
                with ui.row():
                    with ui.card().classes('w-full'):
                        ''' Top label with date: Sunday, January 1st, 2025 '''
                        ui.label(datetime.now().strftime("%A, %B %-d, %Y")).style('font-size: 36px; font-weight: bold;')
            
            with ui.column():
                with ui.row():
                    with ui.card().style('text-align: center;'):
                        with ui.column().style('align-items: center;'):
                            ui.label('Audio Detections').style('font-weight: bold')
                            ui.label(str(len(detections_data))).style('font-size: 36px; font-weight: bold; color: #6E93D6;')
                            # .style('color: #6E93D6; font-size: 200%; font-weight: 300').classes('absolute-center')
                
                    with ui.card().style('text-align: center;'):
                        with ui.column().style('align-items: center;'):
                            ui.label('Most Recent Identification').style('font-weight: bold')
                            try:
                                ui.label(detections_data[-1]["common_name"]).style('font-size: 36px; font-weight: bold; color: #6E93D6;')
                            except:
                                ui.label("None").style('font-size: 36px; font-weight: bold; color: #6E93D6;')
                    
                    with ui.card().style('text-align: center;'):
                        with ui.column().style('align-items: center;'):
                            ui.label('Model Confidence').style('font-weight: bold')
                            ''' calculate average '''
                            if detections_data:
                                conf = 0
                                for entry in detections_data:
                                    conf = conf + float(entry["confidence"])                        
                                model_conf = round(conf/len(detections_data),2)
                                ''' conditional formatting color for model confidence '''
                                if model_conf < .25:
                                    model_color = "red"
                                elif model_conf < .5:
                                    model_color = "orange"
                                elif model_conf < .75:
                                    model_color = "orange"
                                else:
                                    model_color = "green"
                    
                                #ui.label(str(model_conf)).style(f'font-size: 36px; font-weight: bold; color: {model_color};')
                                ui.circular_progress(value=model_conf,color=model_color)
                            else:
                                ''' default style for model confidence '''
                                ui.label("-").style('font-size: 36px; font-weight: bold; color: #6E93D6;')
                                
                    if directory_watcher:    
                        with ui.card():
                            with ui.row():
                                ''' get dir size, color icon depending on disk usage '''
                                dir_size = get_directory_size(directory_watcher)
                                if dir_size > 5: #critical 5gb used
                                    color_usage = 'red'
                                elif dir_size > 3: #warning 3gb used
                                    color_usage = 'orange'
                                else:
                                    color_usage = 'green'
                                    
                                with ui.column().style('align-items: center;'):
                                    ui.label('Storage Usage').style('font-weight: bold')
                                    ui.icon('folder_open', color=color_usage).classes('text-4xl')
                                    ui.markdown(str(dir_size) + "GB Used" )           
        #queries 
        ui.query('header').style(f'background-color: #292f48')
        ui.query('body').style(f'background-color: #42849b')
    
    
    ''' FULL ANALYSIS ROUTE /analysis '''
    @ui.page('/analysis')
    def analysis_page() -> None:
        def logout() -> None:
            app.storage.user.clear()
            ui.navigate.to('/login')
            
        ui.page_title('Bird Identification Tool') 
        
        with ui.header():
            username = app.storage.user["username"][0].upper() + app.storage.user["username"][1:]
            ui.image("img/icon.png").classes("h-12 w-12")
            ui.label(f'Hello {username}!').style('color: #FFFFFF; font-size: 200%; font-weight: 300')
            ui.space()
            ui.button('Dashboard', on_click=lambda: ui.navigate.to('/')).classes("h-11")
            ui.button('Readme', on_click=lambda: ui.navigate.to('/readme')).classes("h-11")
            ui.button(on_click=logout, icon='logout').classes("h-11") # logout button
            
        with ui.card().classes('overflow-auto fixed-center'):
            with ui.card():
                with ui.tabs() as tabs:
                    one = ui.tab('Detections Today')
                    two = ui.tab('Species Distribution')
                    three = ui.tab('Model Confidence')
                    four = ui.tab('Detections over Time')
                with ui.tab_panels(tabs, value=one):
                    with ui.tab_panel(one):
                        ''' create table object using data and headers '''
                        table = ui.table(rows=detections_data, pagination={'rowsPerPage': 10, 'descending': True, 'sortBy': 'start_ts'},)
                        ''' add quasar conditional formatting for model confidence '''
                        table.add_slot('body-cell-confidence', '''
                        <q-td key="confidence" :props="props">
                            <q-badge :color="props.value < 0.25 ? 'red' : props.value < 0.5 ? 'orange' : props.value < 0.75 ? 'yellow' : 'green'">
                                {{ props.value }}
                            </q-badge>
                        </q-td>
                        ''')
                    with ui.tab_panel(two):
                        ''' distribution by species pie chart '''
                        piechart = generate_pie_chart_object(pie_type="species-distro", input_data=detections_data)
                    with ui.tab_panel(three):
                        ''' avg model confidence bar chart '''
                        barchart = generate_bar_chart_object(bar_type="species-confidence", input_data=detections_data)
                    with ui.tab_panel(four):
                        linechart = generate_line_chart_object(input_data=detections_data)
           
        #queries 
        ui.query('header').style(f'background-color: #292f48')
        ui.query('body').style(f'background-color: #42849b')
        
    ''' MARKDOWN README ROUTE '''
    @ui.page('/readme')
    def readme_page() -> None:
        def logout() -> None:
            app.storage.user.clear()
            ui.navigate.to('/login')
            
        ui.page_title('Bird Identification Tool') 
        
        with ui.header():
            username = app.storage.user["username"][0].upper() + app.storage.user["username"][1:]
            ui.image("img/icon.png").classes("h-12 w-12")
            ui.label(f'Hello {username}!').style('color: #FFFFFF; font-size: 200%; font-weight: 300')
            ui.space()
            ui.button('Dashboard', on_click=lambda: ui.navigate.to('/')).classes("h-11")
            ui.button('Analysis', on_click=lambda: ui.navigate.to('/analysis')).classes("h-11")
            ui.button(on_click=logout, icon='logout').classes("h-11") # logout button
        
        ''' load the readme file into a markdown element '''
        with open('README.md', 'r') as readme_in:
            ui.markdown(readme_in.read())
        
            
        #queries 
        ui.query('header').style(f'background-color: #292f48')
        ui.query('body').style(f'background-color: #42849b')
            
            
    ''' LOGIN ROUTE /login '''
    @ui.page('/login')
    def login() -> Optional[RedirectResponse]:
        ui.page_title('Hickory Lane Bird Watchers')
        def try_login() -> None:  # local function to avoid passing username and password as arguments
            if passwords.get(username.value) == password.value:
                app.storage.user.update({'username': username.value, 'authenticated': True})
                ui.navigate.to(app.storage.user.get('referrer_path', '/'))  # go back to where the user wanted to go
            else:
                ui.notify('Wrong username or password', color='negative')

        if app.storage.user.get('authenticated', False):
            return RedirectResponse('/')
        with ui.card().classes('absolute-center'):
            ui.image('img/logo.png')
            username = ui.input('Username').on('keydown.enter', try_login)
            password = ui.input('Password', password=True, password_toggle_button=True).on('keydown.enter', try_login)
            ui.button('Log in', on_click=try_login)
        #queries
        ui.query('body').style(f'background-color: #42849b')
        return None
        

    ''' RUN ''' 
    ui.run(uvicorn_reload_includes='*.py, *.jsonl', storage_secret='THIS_NEEDS_TO_BE_CHANGED', show=False, favicon='🐦')


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
             
        ''' create series using data '''
        series = [{ 'name': 'Count',  'data': data}]
        
        '''create chart using series '''
        chart = ui.highchart({
            'title': {'text': 'Distribution of Birds by Species'},
            'chart': {'type': 'pie'},
            #'tooltip': {'valueSuffix': '%'},
            'series': series,
            'credits': False,
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
            avg_confidence.append({'name': a['name'], 'y': round(a['y'] / b['y'],2) })
        
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
            'credits': False,
            })
        
        return chart
        
def generate_line_chart_object(input_data):
    ''' create data, then series, then chart '''
    bird_counts = [] 
    total_birds = 0
    for entry in input_data:
        num = str(entry['start_ts']) 
        total_birds = total_birds + 1
        bird_counts.append([num,total_birds])
                    
    ''' create series using data '''
    series_data = [[int(datetime.fromisoformat(timestamp).timestamp() * 1000), value] for timestamp, value in bird_counts]
    
    ''' create chart '''
    chart = ui.highchart(
        {
        'chart': {'type': 'line'},
        'title': {'text': 'Total Detections Over Time'},
        'xAxis': {'type': 'datetime', 'title': {'text': 'Timestamp'}},
        'yAxis': {'title': {'text': 'Detections'}},
        'credits': False,
        'series': [{'name': 'Total Detections','data': series_data}]
        },
    )

    return chart


def get_directory_size(path: Path):
    path = str(path)
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    size_gb = round(float(total_size / 1000000000),2)
    return size_gb

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
        main(args.detections_directory, args.directory_watcher)
    except Exception as e:
        logger.error(f'Unknown exception of type: {type(e)} - {e}')
        raise e
