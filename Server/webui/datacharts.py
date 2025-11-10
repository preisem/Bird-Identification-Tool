import json, logging
from datetime import datetime
from pathlib import Path
from nicegui import ui

logger = logging.getLogger(__name__)

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