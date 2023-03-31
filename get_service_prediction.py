import sys
import json
import os
import logging
import requests
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text
from datetime import datetime

def get_config(filepath=""):
    """Reads the config.json file.

    Args:
        filepath (string):  config.json file path.
    
    Returns:
        dict.
    """

    if filepath == "":
        sys.exit("[ERROR] - Config filepath empty.")

    with open(filepath) as json_file:
        config_data = json.load(json_file)

    if config_data == {}:
        sys.exit("[ERROR] - Config file is empty.")

    return config_data


def get_parameters(argv):
    """Stores the input parameters.

    Args:
        argv (list):  input parameters.
    
    Returns:
        string: config.json path.
    """

    config_filepath = argv[1]
    return config_filepath

def create_db_string(config_data, db_object):
    """Create database connection string based on the config file parameters.

    Args:
        config_data (dict): config.json parameters.
        db_object (str): Name of the DB object specified on the config.json file.

    Returns:
        str
    """

    db_string = '{}://{}:{}@{}:{}/{}'.format(
        config_data[db_object]['db_type'],
        config_data[db_object]['user'],
        config_data[db_object]['passwd'], 
        config_data[db_object]['host'], 
        config_data[db_object]['port'], 
        config_data[db_object]['db'])

    # Case if the DB is SQL Server
    if config_data[db_object]['db_type'] == 'mssql+pyodbc':
        db_string = db_string + '?driver=ODBC+Driver+17+for+SQL+Server'
    
    print("[OK] - Connection string successfully generated")
    return db_string 

def create_db_engine(config_data, db_object, db_string):
    """Creates the SQL Alchemy db engine. 

    Args:
        config_data (dict): config.json parameters.
        db_object (str): Name of the DB object specified on the config.json file.
        db_string (str):  Mapstore database connection string.
    
    Returns:
        sqlalchemy.engine.base.Engine.
    """

    try:
        # Type of the DB 
        db_type = config_data[db_object]['db_type']

        if db_type == 'postgresql':
            db_engine = create_engine(db_string)
            print("[OK] - SQLAlchemy engine successfully created")
            return db_engine

        else:
            conn_args={
                "TrustServerCertificate": "yes",
                "Echo": "True",
                "MARS_Connection": "yes"
                }

            db_engine = create_engine(db_string, connect_args=conn_args)
            print("[OK] - SQLAlchemy engine succesfully generated")
            return db_engine

    except Exception as e:
        print("[ERROR] - Creating the database connection engine")
        print(e)
        sys.exit(2)


def get_json_response(url):
    """ Gets json response from an URL
    
    Args:
        url (str): URL of REST service
        
    Returns:
        json_data (dict): JSON response.
    """
    json_data = requests.get(url).json()

    print("[OK] - " + url + " service succesfully requested")
    
    return json_data

def get_list_areas(areas_response):
    """ Gets the list of areas from the REST service
    
    Args:
        areas_response (dict): JSON response of the available areas
        
    Returns:
        areas_list (list): List of areas
    """
    
    areas_list = [area['id'] for area in areas_response]

    print("[OK] - List of areas succesfully getted")
    
    return areas_list

def format_toxin_url(toxins_url, n_area):
    """Generates the url from a given n_area
    
    Args:
        toxins_url (str): URL of REST service of available toxins from an area.
        n_area (int): ID from an area
        
    Returns:
        toxin_area_url (str): Formatted URL of the REST service of available toxins from an area
    """
    
    toxin_area_url = toxins_url.format(n_area)
    
    return toxin_area_url

def get_areas_urls(toxins_url, areas_list):
    """ Gets the formatted urls of all the available areas
    
    Args:
        toxins_url (str): URL of REST service of available toxins from an area.
        areas_list (list): List of the available areas.
    
    Returns:
        areas_url_list (list): List of all the URL's.
    """

    areas_url_list = [format_toxin_url(toxins_url, area) for area in areas_list]

    print("[OK] - Formatted URL's of areas succesfully getted")
    
    return areas_url_list

def remove_unavailable_areas(areas_url_list):
    available_areas = [url for url in areas_url_list if str(requests.get(url)) == '<Response [200]>']
    
    print("[OK] - Unavailable areas succesfully removed")

    return available_areas   

def create_areas_dict(areas_url_list):
    """Creates a dictionary with the area's id and their respective available toxins.
    
    Args:
        areas_url_list (list): List of all the URL's of the areas.
    
    Returns:
        areas_dict (dict): Dictionary with the area's id and their respective available toxins.
    """
    
    areas_dict = {int(url.split('=')[1]) : get_json_response(url) for url in areas_url_list}
    
    print("[OK] - Areas dictionary succesfully generated")

    return areas_dict

def create_df_list(areas_dict, service_url):
    """Creates a list with all the requested areas and toxins.

    Args:
        areas_dict (dict): Dictionary with the area's id and their respective available toxins.
        config_data (dict): config.json parameters.
        service_name (str): name of the URL of the REST service on the config.json file.
    
    Returns: 
        df_list (list): List of multiple area-toxin DF's
    """ 
    
    df_list = []

    for area, toxinas in areas_dict.items():

        for toxina in toxinas:
            url = service_url.format(area, toxina)
            json_response = get_json_response(url)
            df = pd.DataFrame.from_dict(json_response['original']['points'])
            df['area'] = area
            df['analisis'] = toxina

            df_list.append(df)

    print("[OK] - List of DF's succesfully generated")

    return df_list

def df_to_db(df, mapstore_engine, table_name):
    """Copy the IDE DataFrames to the mapstore database.

    Args:
        df (pandas.core.frame.DataFrame): Dataframe from IDE service.
        config_data (dict): config.json parameters.
        mapstore_engine (sqlalchemy.engine.base.Engine): Mapstore DB sqlalchemy engine.
        table_name (str): Name of the output table on the mapstore's database.
    
    Raises:
        SAWarning: Did not recognize type 'geometry' of column 'geom'
    """

    df.to_sql(table_name, 
              mapstore_engine, 
              if_exists = 'replace', 
              schema = 'entradas', 
              index = False)


def main(argv):

    start = datetime.now()

    # Gets parameters
    config_filepath = get_parameters(argv)

    # Gets dbs config parameters
    config = get_config(config_filepath)

    # Gets the service URL's from the config file
    service_url = config["pred_service"]["service_url"]
    areas_url = config["pred_service"]["areas_url"]
    toxins_url = config["pred_service"]["toxins_url"]

    # Generates 'mapstore' database coonection string
    mapstore_con_string = create_db_string(config, 'mapstore')

    # Creates mapstore's database engine
    mapstore_engine = create_db_engine(config, 'mapstore', mapstore_con_string)

    # Gets json response from the available areas service
    areas_response = get_json_response(areas_url)

    # Gets the list of areas from the REST service
    areas_list = get_list_areas(areas_response)

    # Gets the formatted urls of all the available areas
    areas_url_list = get_areas_urls(toxins_url, areas_list)

    # Removes the unavilable areas from the areas list
    areas_url_list = remove_unavailable_areas(areas_url_list)

    # Creates a dictionary with tha areas and their toxins.
    areas_dict = create_areas_dict(areas_url_list)

    # Generates list of area-toxin DF's
    df_list = create_df_list(areas_dict, service_url)

    # Concatenates the final DF
    df_final = pd.concat(df_list)

    # Copies the final DF to the mapstore DB
    df_to_db(df_final, mapstore_engine, "mrsat_pred")

    end = datetime.now()

    print(f"[OK] - Tables successfully copied to mapstore's database. Time elapsed: {end - start}")

if __name__ == "__main__":
    main(sys.argv)