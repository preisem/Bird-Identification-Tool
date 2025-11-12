import os, logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from fastapi.responses import RedirectResponse
from nicegui import app, ui

from webui import datacharts #internal package

logger = logging.getLogger(__name__)

''' MAIN ROUTE / '''
def generateRouteMain(authentication: bool, detections_data: list, directory_watcher: Path):
    @ui.page('/')
    def main_page() -> None:
        if authentication:
            def logout() -> None:
                app.storage.user.clear()
                ui.navigate.to('/login')
        
        
        ''' title of page '''
        ui.page_title('Bird Identification Tool')          
    
        ''' call function to generate header bar '''
        with ui.header():
            generate_header(route='/',ui=ui, authentication=authentication) 
            if authentication:
                ui.button(on_click=logout, icon='logout').classes("h-11") # logout button
        
        ''' MAIN DASHBOARD CARDS '''
        with ui.card().classes('absolute-center').style('align-items: center;'):
            with ui.column():
                with ui.row():
                    ''' today's date card '''
                    with ui.card():
                        ui.label(datetime.now().strftime("%A, %B %-d, %Y")).style('font-size: 36px; font-weight: bold;')
            
            with ui.column():
                with ui.row():
                    ''' total detections today card '''
                    with ui.card():
                        with ui.column().style('align-items: center;'):
                            ui.label('Audio Detections').style('font-weight: bold')
                            ui.label(str(len(detections_data))).style('font-size: 36px; font-weight: bold; color: #6E93D6;')
                            # .style('color: #6E93D6; font-size: 200%; font-weight: 300').classes('absolute-center')
                
                    ''' recent identification card '''
                    with ui.card():
                        with ui.column().style('align-items: center;'):
                            ui.label('Most Recent Identification').style('font-weight: bold')
                            try:
                                ui.label(detections_data[-1]["common_name"]).style('font-size: 36px; font-weight: bold; color: #6E93D6;')
                                ui.audio(detections_data[-1]["filename"])# later use .seek() to start 1s before the start of detection
                                #ui.markdown(str(detections_data[-1]["start_ts"]))
                            except:
                                ui.label("None").style('font-size: 36px; font-weight: bold; color: #6E93D6;')
                            
                    ''' average model confidence card '''
                    with ui.card():
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
                    
                    ''' directory watcher card '''
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
                                    ui.icon('folder_open', color=color_usage).classes('text-5xl')
                                    ui.markdown(str(dir_size) + "GB Used" )           
                            
        ''' queries '''
        ui.query('header').style(f'background-color: #292f48')
        ui.query('body').style(f'background-color: #42849b')


''' FULL ANALYSIS ROUTE /analysis '''
def generateRouteAnalysis(authentication: bool, detections_data: list):
    @ui.page('/analysis')
    def analysis_page() -> None:
        def logout() -> None:
            app.storage.user.clear()
            ui.navigate.to('/login')
            
        ui.page_title('Bird Identification Tool') 
        
        ''' call function to generate header bar '''
        with ui.header():
            generate_header(route='/analysis',ui=ui, authentication=authentication) 
            if authentication:
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
                        piechart =  datacharts.generate_pie_chart_object(pie_type="species-distro", input_data=detections_data)
                    with ui.tab_panel(three):
                        ''' avg model confidence bar chart '''
                        barchart = datacharts.generate_bar_chart_object(bar_type="species-confidence", input_data=detections_data)
                    with ui.tab_panel(four):
                        linechart = datacharts.generate_line_chart_object(input_data=detections_data)
           
        #queries 
        ui.query('header').style(f'background-color: #292f48')
        ui.query('body').style(f'background-color: #42849b')


''' VIDEO STREAM ROUTE ''' 
def generateVideoRoute(authentication: bool, video_streams):
    @ui.page('/video')
    def video_page() -> None:
        def logout() -> None:
            app.storage.user.clear()
            ui.navigate.to('/login')
            
        ui.page_title('Bird Identification Tool') 
        
        ''' call function to generate header bar '''
        with ui.header():
            generate_header(route='/video',ui=ui, authentication=authentication)
            if authentication: 
                ui.button(on_click=logout, icon='logout').classes("h-11") # logout button


        ''' load streams from input as urls into a card with buttons at the bottom to chose the active stream to display '''
        with ui.card().style('align-items: center; width: 50%; margin: auto;').classes('absolute-center'):
            with ui.column().style('width: 100%; align-items: center;'):
                # Create a placeholder for the stream display
                if video_streams:
                    # Set a larger width and height for the video display
                    stream_display = ui.image(video_streams[0]).style('width: 100%; max-width: 800px; height: auto;')

                    # Define a function to update the displayed stream
                    def change_stream(stream_url):
                        stream_display.set_source(stream_url)  # Update the image source

                    # Create buttons for each stream
                    with ui.row().style('justify-content: center; margin-top: 20px;'):
                        for stream in video_streams:
                            ui.button(stream.split("/")[-1], on_click=lambda s=stream: change_stream(s))
                else:  # Default page if no streams provided
                    with ui.column():
                        ui.label("No Active Streams").style('font-size: 36px; font-weight: bold; color: #6E93D6;')
                        ui.label("Add streams with the --video-streams argument").style('font-weight: bold;')
        
        #queries 
        ui.query('header').style(f'background-color: #292f48')
        ui.query('body').style(f'background-color: #42849b')


''' MARKDOWN README ROUTE '''
def generateReadmeRoute(authentication: bool):
    @ui.page('/readme')
    def readme_page() -> None:
        def logout() -> None:
            app.storage.user.clear()
            ui.navigate.to('/login')
            
        ui.page_title('Bird Identification Tool') 
        
        ''' call function to generate header bar '''
        with ui.header():
            generate_header(route='/readme',ui=ui, authentication=authentication) 
            if authentication:
                ui.button(on_click=logout, icon='logout').classes("h-11") # logout button
        
        ''' load the readme file into a markdown element '''
        with ui.card():
            with open('../README.md', 'r') as readme_in:
                ui.markdown(readme_in.read())
        
            
        #queries 
        ui.query('header').style(f'background-color: #292f48')
        ui.query('body').style(f'background-color: #42849b')

''' LOGIN ROUTE /login '''
def generateLoginRoute(passwords: dict):
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


''' HELPER FUNCTIONS'''
def generate_header(route: str, ui, authentication: bool):
        ''' all pages get the welcome banner '''
        ui.image("img/icon.png").classes("h-12 w-12") #logo icon
        if authentication:
            username = app.storage.user["username"][0].upper() + app.storage.user["username"][1:] #uppercase the first letter
            ui.label(f'Hello {username}!').style('color: #FFFFFF; font-size: 200%; font-weight: 300') # header banner
        ui.space() # creates space between left justified and right justified items
        
        ''' create buttons to other pages depending on what page the header is on '''
        if route == "/":
            ui.button('Analysis', on_click=lambda: ui.navigate.to('/analysis')).classes("h-11") # button link to /analysis
            ui.button('Live Video', on_click=lambda: ui.navigate.to('/video')).classes("h-11") # button link to /video
            ui.button('Readme', on_click=lambda: ui.navigate.to('/readme')).classes("h-11") # button link to /readme
        elif route == "/analysis":
            ui.button('Dashboard', on_click=lambda: ui.navigate.to('/')).classes("h-11")
            ui.button('Live Video', on_click=lambda: ui.navigate.to('/video')).classes("h-11") # button link to /video
            ui.button('Readme', on_click=lambda: ui.navigate.to('/readme')).classes("h-11")
        elif route == "/readme":
            ui.button('Dashboard', on_click=lambda: ui.navigate.to('/')).classes("h-11")
            ui.button('Analysis', on_click=lambda: ui.navigate.to('/analysis')).classes("h-11")
            ui.button('Live Video', on_click=lambda: ui.navigate.to('/video')).classes("h-11") # button link to /video
        elif route == "/video":
            ui.button('Dashboard', on_click=lambda: ui.navigate.to('/')).classes("h-11")
            ui.button('Analysis', on_click=lambda: ui.navigate.to('/analysis')).classes("h-11")
            ui.button('Readme', on_click=lambda: ui.navigate.to('/readme')).classes("h-11")

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

