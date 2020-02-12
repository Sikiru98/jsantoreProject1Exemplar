import requests
import time
from typing import Dict, List
import sqlite3
from typing import Tuple

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
        cursor.execute(f'''INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);''', [
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
            data['company_logo']
            ])

    connection.commit()


def main():
    data = get_github_jobs_data()
    save_data(data)
    filename = 'demo_db.sqlite'
    connection, cursor = open_db(filename)
    setup_db(cursor, connection)
    save_to_db(data, cursor, connection)
    close_db(connection)


def open_db(filename:str) ->Tuple[sqlite3.Connection, sqlite3.Cursor]:
    db_connection = sqlite3.connect(filename)  # connect to existing DB or create new one
    cursor = db_connection.cursor()  # get ready to read/write data
    return db_connection,cursor


def close_db(connection:sqlite3.Connection):
    connection.commit()#make sure any changes get saved
    connection.close()


def setup_db(cursor:sqlite3.Cursor, connection):
    cursor.execute('''CREATE TABLE IF NOT EXISTS jobs( id TEXT PRIMARY KEY, Position_Type TEXT NOT NULL,url TEXT NOT NULL,created_at TEXT NOT NULL, company TEXT NOT NULL , company_url TEXT, Location TEXT NOT NULL, Title TEXT NOT NULL, Description TEXT NOT NULL, How_to_Apply TEXT NOT NULL, Company_Logo TEXT);''')
    connection.commit()
    
if __name__ == '__main__':
    main()
