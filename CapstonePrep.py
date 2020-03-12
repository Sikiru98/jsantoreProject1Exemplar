import requests
import time
from typing import Dict, List
import sqlite3
from typing import Tuple
import feedparser
from geopy.geocoders import Nominatim
from urllib.request import urlopen
import json
import dash
import dash_core_components as dcc
import dash_html_components as html


d = feedparser.parse('https://stackoverflow.com/jobs/feed')
listOfDictionaries = []
newDictionary = {}

for post in d.entries:
    newDictionary['id'] = post['id']
    newDictionary['type'] = None
    newDictionary['url'] = post['link']
    newDictionary['created_at'] = post['published']
    newDictionary['company'] = post['author']
    newDictionary['company_url'] = None

    if 'location' in post.keys():
        newDictionary['location'] = post['location']
    else:
        newDictionary['location'] = None

    newDictionary['title'] = post['title']
    newDictionary['description'] = post['summary']
    newDictionary['how_to_apply'] = None
    newDictionary['company_logo'] = None

    listOfDictionaries.append(newDictionary)
    newDictionary = {}

for dictionary in listOfDictionaries:
    print(dictionary)


def get_github_jobs_data() -> List[Dict]:
    """retrieve github jobs data in form of a list of dictionaries after json processing"""
    all_data = []
    page = 1
    more_data = True
    while more_data:
        url = f"https://jobs.github.com/positions.json?page={page}"
        raw_data = requests.get(url)
        if "GitHubber!" in raw_data:  # sometimes if I ask for pages too quickly I get an error; only happens in testing
            continue  # trying continue, but might want break
        partial_jobs_list = raw_data.json()
        all_data.extend(partial_jobs_list)
        if len(partial_jobs_list) < 50:
            more_data = False
        time.sleep(.1)  # short sleep between requests so I dont wear out my welcome.
        page += 1
    return all_data


def save_data(data, filename='data.txt'):
    with open(filename, 'a') as file:
        for item in data:
            print(item, file=file)


def save_to_db(jobs, cursor, connection):
    """:keyword data is a list of dictionaries. Each dictionary is a JSON object with a bit of jobs data"""
    for data in jobs:
        cursor.execute(f'''INSERT OR IGNORE INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);''', (
            data['id'],
            data['type'],
            data['url'],
            data['created_at'],
            data['company'],
            data['company_url'],
            data['location'],
            data['title'],
            data['description'],
            data['how_to_apply'],
            data['company_logo']))

        connection.commit()


def main():
    data = get_github_jobs_data()
    save_data(data)
    filename = 'demo_db.sqlite'
    connection, cursor = open_db(filename)
    setup_db(cursor, connection)
    save_to_db(data, cursor, connection)
    save_to_db(listOfDictionaries, cursor, connection)
    close_db(connection)


def open_db(filename: str) -> Tuple[sqlite3.Connection,sqlite3.Cursor]:
    db_connection = sqlite3.connect(filename)  # connect to existing DB or create new one
    cursor = db_connection.cursor()  # get ready to read/write data
    return db_connection,cursor


def close_db(connection: sqlite3.Connection):
    connection.commit()  # make sure any changes get saved
    connection.close()


def setup_db(cursor: sqlite3.Cursor,connection):
    cursor.execute('''CREATE TABLE IF NOT EXISTS jobs(
                        id TEXT PRIMARY KEY, 
                        Position_Type TEXT, 
                        url TEXT, 
                        created_at TEXT, 
                        company TEXT, 
                        company_url TEXT, 
                        Location TEXT, Title TEXT, 
                        Description TEXT, 
                        How_to_Apply TEXT, 
                        Company_Logo TEXT);''')
    connection.commit()


geolocator = Nominatim(user_agent=" my-application ")
location = geolocator.geocode("Boston, Ma")
Latitude = location.latitude
Longitude = location.longitude
print(location.latitude, location.longitude)

with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)

import pandas as pd
df = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/fips-unemp-16.csv",
                   dtype={"fips": str})

import plotly.express as px

fig = px.choropleth_mapbox(df, geojson=counties, locations='fips', color='unemp',
                           color_continuous_scale="Viridis",
                           range_color=(0, 12),
                           mapbox_style="carto-positron",
                           zoom=3, center = {"lat": 37.0902, "lon": -95.7129},
                           opacity=0.5,
                           labels={'unemp':'unemployment rate'}
                          )
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig.show()


import pandas as pd

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

df = pd.read_csv('https://gist.githubusercontent.com/chriddyp/5d1ea79569ed194d432e56108a04d188/raw/a9f9e8076b837d541398e999dcbac2b2826a81f8/gdp-life-exp-2007.csv')


app.layout = html.Div([
    dcc.Graph(
        id='life-exp-vs-gdp',
        figure={
            'data': [
                dict(
                    x=df[df['continent'] == i]['gdp per capita'],
                    y=df[df['continent'] == i]['life expectancy'],
                    text=df[df['continent'] == i]['country'],
                    mode='markers',
                    opacity=0.7,
                    marker={
                        'size': 15,
                        'line': {'width': 0.5, 'color': 'white'}
                    },
                    name=i
                ) for i in df.continent.unique()
            ],
            'layout': dict(
                xaxis={'type': 'log', 'title': 'GDP Per Capita'},
                yaxis={'title': 'Life Expectancy'},
                margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
                legend={'x': 0, 'y': 1},
                hovermode='closest'
            )
        }
    )
])


if __name__ == '__main__':
    main()
