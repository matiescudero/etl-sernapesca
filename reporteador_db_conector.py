import sys
import os
import logging
import json
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text
from datetime import datetime

#python file with SP's querys
import sql_querys as querys


def execute_sql_query(mapstore_engine, sql_query, logger):
    """Execute the 'reporteador_preprocessing.sql' query on mapstore database.

    Args:
        mapstore_engine (sqlalchemy.engine.base.Engine): Mapstore DB sqlalchemy engine.
        sql_query (sqlalchemy.sql.elements.TextClause): 'reporteador_preprocessing' query
    """

    try:
        with mapstore_engine.connect().execution_options(autocommit=True) as con:
            con.execute(sql_query)
        print("[OK] - SQL query successfully executed")
        logger.debug("[OK] - EXECUTE_SQL_QUERY")

    except Exception as e:
        print('[ERROR] - Executing SQL Query on Mapstore DB')
        logger.error('[ERROR] - EXECUTE_SQL_QUERY')
        sys.exit(2)

def open_sql_query(sql_query, logger):
    """Open the SQL query to process the 'existencias' table.

    Returns:
        sqlalchemy.sql.elements.TextClause
    """

    with open("./sql_queries/" + sql_query) as file:
        sql_query = text(file.read())
    print("[OK] - SQL file successfully opened")
    logger.debug("[OK] - OPEN_SQL_QUERY")
    return sql_query


def df_to_bd(config, mapstore_engine, df, table_name, logger):
    """Copy the pandas Dataframes to the 'entradas' schema in the mapstore database.

    Args:
        config (dict): Dictionary with the config.json file information.
        mapstore_engine (sqlalchemy.engine.base.Engine.): SQL Alchemy connection engine.
        df (pandas DataFrame): Dataframe to copy to the Mapstore DB.
        table_name (str): Name of the table in the DB.

    """

    try:
        df.to_sql(table_name, mapstore_engine, schema = config['mapstore']['schema'], if_exists = 'replace', index = False)

        print("[OK] - " + table_name + " table successfully copied to the DB")
        logger.debug("[OK] - DFS_TO_BD")

    except Exception as e:
        print('[ERROR] - Copying ' + table_name + ' table to DB')
        logger.error('[ERROR] - ' + table_name + ' DF_TO_BD')
        sys.exit(2)

def tables_to_df(db_engine, query_file, logger):
    """Read the input SQL querys and execute 'reporteador' database SP's and store them as pandas DFs. 

    Args:
        db_engine (sqlalchemy.engine.base.Engine): SQL Alchemy connection engine
        query_file (.py file): Python file with the executable querys 
    
    Returns:
        pandas Dataframes.

    Raises:
        UserWarning: pandas only support SQLAlchemy connectable(engine/connection) ordatabase string URI or sqlite3 DBAPI2 connectionother 
        DBAPI2 objects are not tested, please consider using SQLAlchemy
    """

    df_areas_psmb = pd.read_sql(query_file.areas_psmb, db_engine)
    df_centros_psmb = pd.read_sql(query_file.centros_psmb, db_engine)
    df_existencias = pd.read_sql(query_file.existencias, db_engine)
    df_salmonidos = pd.read_sql(query_file.salmonidos, db_engine)
    df_estaciones = pd.read_sql(query_file.estaciones, db_engine)
    df_caletas = pd.read_sql(query_file.detalle_caletas, db_engine)

    print("[OK] - SP's executed and stored successfully")
    logger.debug("[OK] - TABLES_TO_DF")

    return df_areas_psmb, df_centros_psmb, df_existencias, df_salmonidos, df_estaciones, df_caletas

def create_db_engine(config_data, db_object, db_string, logger):
    """Creates the SQL Alchemy db engine. 

    Args:
        config_data (dict): config.json parameters.
        db_object (str): Name of the DB object specified on the config.json file.
        db_string (str):  Mapstore database connection string.
    
    Returns:
        sqlalchemy.engine.base.Engine.
    """

    try:
        db_type = config_data[db_object]['db_type']

        if db_type == 'postgresql':
            db_engine = create_engine(db_string)
            print("[OK] - SQLAlchemy engine successfully created")
            logger.debug("[OK] - CREATE_DB_ENGINE")
            return db_engine

        else:
            conn_args={
                "TrustServerCertificate": "yes",
                "Echo": "True",
                "MARS_Connection": "yes"
                }

            db_engine = create_engine(db_string, connect_args=conn_args)
            print("[OK] - SQLAlchemy engine succesfully generated")
            logger.debug("[OK] - CREATE_DB_ENGINE")
            return db_engine

    except Exception as e:
        print("[ERROR] - Creating the database connection engine")
        print(e)
        logger.error('[ERROR] - CREATE_DB_ENGINE')
        sys.exit(2)

def create_db_string(config_data, db_object, logger):
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
    logger.debug("[OK] - CREATE_DB_STRING")
    return db_string 

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

    log_file = log_path + "/reporteador_db_conector.log"
    return log_file 

def get_config(filepath=""):
    """Read the config.json file.

    Args:
        filepath (string):  config.json file path
    
    Returns:
        dict
    """

    if filepath == "":
        sys.exit("[ERROR] - Config filepath empty.")

    with open(filepath) as json_file:
        data = json.load(json_file)

    if data == {}:
        sys.exit("[ERROR] - Config file is empty.")

    return data

def get_parameters(argv):
    """Store the input parameters.

    Args:
        argv (list):  input parameters
    
    Returns:
        string: config.json path
    """

    config_filepath = argv[1]
    return config_filepath

def main(argv):
    start = datetime.now()

    # Gets parameters
    config_filepath = get_parameters(argv)

    # Gets config parameters
    config = get_config(config_filepath)

    # Creates the log file if not exists
    log_file = create_log_file(config["log_path"])

    # Deletes the previous log file if too big
    delete_log_file(log_file)

    # Creates the logger
    logger = create_logger(log_file)

    # Connects to 'reporteador' database
    reporteador_string = create_db_string(config, 'reporteador', logger)

    # Connects to 'mapstore' database
    mapstore_string = create_db_string(config, 'mapstore', logger)

    # Creates mapstore's database engine
    mapstore_engine = create_db_engine(config, 'mapstore', mapstore_string, logger)

    # Creates reporteador's database engine
    reporteador_engine = create_db_engine(config, 'reporteador', reporteador_string, logger)
    
    # Execute 'reporteador' database SP's and store them as pandas DFs
    df_areas_psmb, df_centros_psmb, df_existencias, df_salmonidos, df_estaciones, df_caletas = tables_to_df(reporteador_engine, querys, logger)

    # Pandas DFs to mapstore database
    df_to_bd(config, mapstore_engine, df_areas_psmb, "areas_psmb", logger)
    df_to_bd(config, mapstore_engine, df_centros_psmb, "centros_psmb", logger)
    df_to_bd(config, mapstore_engine, df_existencias, "existencias_moluscos", logger)
    df_to_bd(config, mapstore_engine, df_salmonidos, "existencias_salmonidos", logger)
    df_to_bd(config, mapstore_engine, df_estaciones, "estaciones", logger)
    df_to_bd(config, mapstore_engine, df_caletas, "detalle_caletas", logger)

    # Open the 'reporteador_preprocessing.sql' file
    sql_query = open_sql_query('reporteador_preprocessing.sql', logger)

    # Execute the SQL to preprocces the input tables
    execute_sql_query(mapstore_engine, sql_query, logger)
    
    end = datetime.now()

    print(f"[OK] - Tables successfully copied to mapstore's database. Time elapsed: {end - start}")

if __name__ == "__main__":
    main(sys.argv)