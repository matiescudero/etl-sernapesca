import requests
import sys
import os
import json
import pandas as pd
import logging
from shapely.geometry import Polygon
from sqlalchemy import create_engine
from sqlalchemy import text
from datetime import datetime



def execute_sql_query(mapstore_engine, sql_query, logger):
    """Execute the given sql query on mapstore database.

    Args:
        mapstore_engine (sqlalchemy.engine.base.Engine): Mapstore DB sqlalchemy engine.
        sql_query (sqlalchemy.sql.elements.TextClause): SQL file query
    """

    with mapstore_engine.connect().execution_options(autocommit=True) as con:
        con.execute(sql_query)
    print("[OK] - SQL query successfully executed")
    logger.debug("[OK] - EXECUTE_SQL_QUERY")

def open_sql_query(sql_file, logger):
    """Open the SQL query to add the geometry type to the IDE tables on mapstore database.

    Args:
        sql_file (str): Name of the .sql file to execute

    Returns:
        sqlalchemy.sql.elements.TextClause
    """

    with open("./sql_queries/" + sql_file, encoding = "utf8") as file:
        sql_query = text(file.read())
    print("[OK] - " + sql_file + " SQL file successfully opened")
    logger.debug("[OK] - " + sql_file.upper() + " OPEN_SQL_QUERY")
    return sql_query
 
def df_to_db(df, config_data, mapstore_engine, table_name, logger):
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
                schema = config_data['mapstore']['schema'], 
                index = False)

    print("[OK] - " + table_name + " dataframe successfully copied to Mapstore database")
    logger.debug("[OK] - " + table_name.upper() + " DF_TO_DB")

def create_mapstore_engine(mapstore_connection, logger):
    """Create sqlalchemy mapstore engine based on the mapstore connection string.

    Args:
        mapstore_connection (str): string with the mapstore databse connection.

    Returns:
        sqlalchemy.engine.base.Engine
    """
    try:
        mapstore_engine = create_engine(mapstore_connection)
        print("[OK] - SQLAlchemy engine succesfully generated")
        logger.debug("[OK] - CREATE_MAPSTORE_ENGINE")
        return mapstore_engine

    except Exception as e:
        print('[ERROR] - Creating DB engine')
        print(e)
        logger.error('[ERROR] - CREATE_MAPSTORE_ENGINE')
        sys.exit(2)

def create_mapstore_connection(config_data, logger):
    """Create mapstore connection string based on the config file parameters.

    Args:
        config_data (dict): config.json parameters.

    Returns:
        str
    """

    mapstore_connection = 'postgresql://{}:{}@{}:{}/{}'.format(
        config_data['mapstore']['user'],
        config_data['mapstore']['passwd'], 
        config_data['mapstore']['host'], 
        config_data['mapstore']['port'], 
        config_data['mapstore']['db'])
    print("[OK] - Connection string successfully generated")
    logger.debug("[OK] - CREATE_MAPSTORE_CONNECTION")
    return mapstore_connection   

def drop_str_geometry(df, logger):
    """Drop the previous geometry column.

    Args:
        df (pandas.core.frame.DataFrame): Dataframe from IDE service.

    Returns:
        pandas.core.frame.DataFrame
    """

    df.drop('geometry.rings', axis=1, inplace=True)
    print("[OK] - Old geometry column successfully dropped")
    logger.debug("[OK] - DROP_STR_GEOMETRY")
    return df

def transform_geometry_column(df, logger):
    """Transform the geometry column to a SQL readable format.

    Args:
        df (pandas.core.frame.DataFrame): Dataframe from IDE service.

    Returns:
        pandas.core.frame.DataFrame
    """

    df["geometry"] = df["geometry"].apply(Polygon).apply(str)
    print("[OK] - Geometry column format successfully converted")
    logger.debug("[OK] - TRANSFORM GEOMETRY COLUMN")
    return df

def polygon_coords_to_df(df, coord_list, logger):
    """Appends the list of coordinates to the centros_df DataFrame as a column.

    Args:
        df (pandas.core.frame.DataFrame): Dataframe from IDE service.
        coord_list (list): list of lists with the coodinates of each farming center.

    Returns:
        pandas.core.frame.DataFrame
    """

    df["geometry"] = coord_list
    print("[OK] - New geometry column successfully appended")
    logger.debug("[OK] - POLYGON_COORDS_TO_DF")
    return df

def list_to_tuples(df, logger):
    """Transforms the "geometry.rings" column from list of lists to a list of tuples. 

    Args:
        df (pandas.core.frame.DataFrame): Dataframe from IDE service.

    Returns:
        list.
    """

    coord_list = [[*map(tuple, row[0])] for row in df["geometry.rings"].values]
    print("[OK] - List of lists successfully converted to list of tuples")
    logger.debug("[OK] - LIST_TO_TUPLES")
    return coord_list

def rename_df_columns(df, logger):
    """Removes the word 'attributes' from the Pandas DataFrame's columns.

    Args:
        df (pandas.core.frame.DataFrame): Dataframe from IDE service.

    Returns:
        pandas.core.frame.DataFrame.
    """

    df = df.rename(columns = lambda row: row.lstrip('attributes.'))
    print("[OK] - DataFrame columns successfully renamed")
    logger.debug("[OK] - RENAME_DF_COLUMNS")
    return df

def json_to_df(json_response, logger):
    """Transforms the json dictionary to a Pandas DataFrame.

    Args:
        json_response (dict): Dictionary of the json response.

    Returns:
        pandas.core.frame.DataFrame.
    """
    df = pd.json_normalize(json_response['features'])
    print("[OK] - JSON successfully transformed to DataFrame")
    logger.debug("[OK] - JSON_TO_DF")

    return df

def response_to_json(ide_response, logger):
    """Transforms the subpesca's request to a python dictionary.

    Args:
        ide_response (requests.models.Response): response to subpesca's rest api request.

    Returns:
        dict.
    """

    json_response = ide_response.json()
    print("[OK] - IDE rest api service succesfully transformed")
    logger.debug("[OK] - RESPONSE_TO_JSON")
    return json_response

def get_ide_response(config_data, service, logger):
    """Gets the response of subpesca's rest api service request based on the config data parameters.

    Args:
        config_data (dict): config.json parameters.
        service (str) : name of the arcgis service on the local config file.

    Returns:
        requests.models.Response.
    """

    ide_response = requests.get(config_data["ide_subpesca"]["request_url"][service], headers = config_data["ide_subpesca"]["headers"])
    print("[OK] - ArcGIS rest API " + service + " service succesfully requested")
    logger.debug("[OK] - GET_IDE_RESPONSE FROM " + service.upper() + " SERVICE")
    return ide_response

def create_logger(log_file):
    """Create a logger based on the passed log file.

    Args:
        log_file (str): Path of the log file.

    Returns:
        class logging.RootLogger.
    """
    logging.basicConfig(filename = log_file,
                    format='%(asctime)s %(message)s',
                    filemode='a')

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    return logger

def delete_log_file(log_file):
    """Deletes the log file if it's too big.
    Args:
        log_file (str): Path of the log file.
    """    
    # Check if log file exists
    if os.path.exists(log_file):
        
        # Get the size of the log path
        log_size = os.path.getsize(log_file)
        
        if log_size > 0:
            # Deletes the log file if too big
            if log_size > 80 * 1024:
                os.remove(log_file)
                print("[OK] - Log file removed")

def create_log_file(log_path):
    """Create the log folder if not exists. Get the log file name.

    Args:
        log_path (str): Path of the log folder.

    Returns:
        str
    """
    if not os.path.exists(log_path):
        os.makedirs(log_path)

    log_file = log_path + "/ide_subpesca_conector.log"
    return log_file  

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


def main(argv):
    start = datetime.now()

    # Get parameters
    config_filepath = get_parameters(argv)

    # Get service config parameters
    config_data = get_config(config_filepath)

    # Create the log file if not exists
    log_file = create_log_file(config_data["log_path"])

    # Deletes the previous log file if too big
    delete_log_file(log_file)

    # Create the logger
    logger = create_logger(log_file)

    # Get responses from arcgis rest services
    centros_response = get_ide_response(config_data, "centros", logger)
    areas_response = get_ide_response(config_data, "areas_colecta", logger)
    ecmpo_response = get_ide_response(config_data, "ecmpo", logger)
    amerb_response = get_ide_response(config_data, "amerb", logger)
    acuiamerb_response = get_ide_response(config_data, "acui_en_amerb", logger)


    # Tranform responses to dictionary
    centros_json = response_to_json(centros_response, logger)
    areas_json = response_to_json(areas_response, logger)
    ecmpo_json = response_to_json(ecmpo_response, logger)
    amerb_json = response_to_json(amerb_response, logger)
    acuiamerb_json = response_to_json(acuiamerb_response, logger)

    # Transform dictionarys to DataFrames
    centros_df = json_to_df(centros_json, logger)
    areas_df = json_to_df(areas_json, logger)
    ecmpo_df = json_to_df(ecmpo_json, logger)
    amerb_df = json_to_df(amerb_json, logger)
    acuiamerb_df = json_to_df(acuiamerb_json, logger)
    
    # Rename DataFrame's columns
    centros_df = rename_df_columns(centros_df, logger)
    areas_df = rename_df_columns(areas_df, logger)
    ecmpo_df = rename_df_columns(ecmpo_df, logger)
    amerb_df = rename_df_columns(amerb_df, logger)
    acuiamerb_df = rename_df_columns(acuiamerb_df, logger)

    # Transform the list of list of coordinates to list of tuples
    centros_df_coord_list = list_to_tuples(centros_df, logger)
    areas_df_coord_list = list_to_tuples(areas_df, logger)
    ecmpo_df_coord_list = list_to_tuples(ecmpo_df, logger)
    amerb_df_coord_list = list_to_tuples(amerb_df, logger)
    acuiamerb_coord_list = list_to_tuples(acuiamerb_df, logger)

    # Append new column to DataFrame
    centros_df = polygon_coords_to_df(centros_df, centros_df_coord_list, logger)
    areas_df = polygon_coords_to_df(areas_df, areas_df_coord_list, logger)
    ecmpo_df = polygon_coords_to_df(ecmpo_df, ecmpo_df_coord_list, logger)
    amerb_df = polygon_coords_to_df(amerb_df, amerb_df_coord_list, logger)
    acuiamerb_df = polygon_coords_to_df(acuiamerb_df, acuiamerb_coord_list, logger)

    # Change format of the geometry column
    centros_df = transform_geometry_column(centros_df, logger)
    areas_df = transform_geometry_column(areas_df, logger)
    ecmpo_df = transform_geometry_column(ecmpo_df, logger)
    amerb_df = transform_geometry_column(amerb_df, logger)
    acuiamerb_df = transform_geometry_column(acuiamerb_df, logger)

    # Drop the old geometry column
    centros_df = drop_str_geometry(centros_df, logger)
    areas_df = drop_str_geometry(areas_df, logger)
    ecmpo_df = drop_str_geometry(ecmpo_df, logger)
    amerb_df = drop_str_geometry(amerb_df, logger)
    acuiamerb_df = drop_str_geometry(acuiamerb_df, logger)

    # Create string with the db mapstore parameters
    mapstore_connection = create_mapstore_connection(config_data, logger)

    # Create sqlalchemy engine based on the mapstore db paramters
    mapstore_engine = create_mapstore_engine(mapstore_connection, logger)

    # Copy the DataFrame to the mapstore database
    df_to_db(centros_df, config_data, mapstore_engine, "concesiones_acuicultura", logger)
    df_to_db(areas_df, config_data, mapstore_engine, "areas_colecta", logger)
    df_to_db(ecmpo_df, config_data, mapstore_engine, "ecmpo", logger)
    df_to_db(amerb_df, config_data, mapstore_engine, "amerb", logger)
    df_to_db(acuiamerb_df, config_data, mapstore_engine, "acuiamerb", logger)

    # Open the 'add_geometry_to_services.sql' file
    geom_sql_query = open_sql_query("add_geometry_to_services.sql", logger)

    # Execute the SQL query to transform the geometry type of the new tables
    execute_sql_query(mapstore_engine, geom_sql_query, logger)

    # Open the 'ide_layers_processing.sql' file
    ide_process_sql_query = open_sql_query("ide_layers_processing.sql", logger)

    # Execute the SQL query to change the column names of the IDE tables
    execute_sql_query(mapstore_engine, ide_process_sql_query, logger)

    end = datetime.now()

    print(f"[OK] - Tables successfully copied to mapstore's database. Time elapsed: {end - start}")

if __name__ == "__main__":
    main(sys.argv)

