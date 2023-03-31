import sys
import json
import os
import logging
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text
from datetime import datetime

def execute_sql_query(mapstore_engine, sql_query, logger):
    """Executes the 'tables_processing.sql' query on mapstore database.

    Args:
        mapstore_engine (sqlalchemy.engine.base.Engine): Mapstore DB sqlalchemy engine.
        sql_query (sqlalchemy.sql.elements.TextClause): 'tables_processing.sql' query
    """
    try:
        with mapstore_engine.connect().execution_options(autocommit=True) as con:
            con.execute(sql_query)
        print("[OK] - SQL query successfully executed")
        logger.debug("[OK] - EXECUTE_SQL_QUERY")

    except Exception as e:
        print('[ERROR] - Executing SQL query')
        print(e)
        logger.error('[ERROR] - EXECUTE_SQL_QUERY')
        sys.exit(2)


def df_to_db(df, config_data, db_engine, logger):
    """Replace the existing 'mrsat_60days' table on the mapstore DB.
    
    Args:
        df (pandas.core.frame.DataFrame): Dataframe with the new records.
        config_data (dict): config.json parameters.
        db_engine (sqlalchemy.engine.base.Engine): Database sqlalchemy engine.
        
    """
    table = 'mrsat_60days'
    schema = config_data['mapstore']['schema']
    
    try:
        df.to_sql(table,
                    db_engine, 
                    if_exists = 'replace', 
                    schema = schema, 
                    index = False)

        print("[OK] - mrSAT table successfully replaced on mapstore DB")
        logger.debug("[OK] - DF_TO_DB")

    except Exception as e:
        print(e)
        print("[ERROR] - Replacing mrSAT table")
        logger.error('[ERROR] - APPEND_NEW_RECORDS')
        sys.exit(2)


def open_sql_query(logger):
    """Opens the SQL query to generate the outputs tables on mapstore database.

    Returns:
        sqlalchemy.sql.elements.TextClause
    """

    try:
        with open("./sql_queries/tables_processing.sql", encoding="utf8") as file:
            sql_query = text(file.read())
        print("[OK] - SQL file successfully opened")
        logger.debug("[OK] - OPEN_SQL_QUERY")
        return sql_query

    except Exception as e:
        print('[ERROR] - Opening SQL Query')
        logger.error('[ERROR] - OPEN_SQL_QUERY')
        sys.exit(2)



def table_to_df(config_data, db_connection, logger):
    """Transforms the mrsat db's 'mrsat_60days' table to a Pandas DataFrame.

    Args:
        config_data (dict): config.json parameters.
        db_connection (sqlalchemy.engine.Connection.connect): SQLAlchemy connection object.

    Returns:
        pandas.core.frame.DataFrame
    """

    table = config_data['mrsat']['last_days_table']
    schema = config_data['mrsat']['schema']
    
    df = pd.read_sql_table(table, db_connection, schema)
    print("[OK] - " + table + " table succesfully transformed to Pandas DataFrame.")
    logger.debug("[OK] - TABLE_TO_DF")
    return df

def connect_to_engine(db_engine, config_data, db_object, logger):
    """Connects to sqlalchemy database engine.

    Args:
        db_engine (sqlalchemy.engine.base.Engine): SQLAlchemy database engine.
        config_data (dict): config.json parameters.
        db_object (str): Name of the DB object specified on the config.json file.

    Returns:
        sqlalchemy.engine.Connection.connect
    """

    db_type = config_data[db_object]['db_type']

    if db_type == 'postgresql':
        db_con = db_engine.connect()

    else:
        db_con = db_engine.connect().execution_options(autocommit=False)
    
    print('[OK] - SQLAlchemy connection succesfully generated')
    logger.debug("[OK] - CONNECT_TO_ENGINE")
    return db_con

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
        # Type of the DB 
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

    log_file = log_path + "/generate_spatial_outputs.log"
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

    # Gets parameters
    config_filepath = get_parameters(argv)

    # Gets dbs config parameters
    config = get_config(config_filepath)

    # Creates the log file if not exists
    log_file = create_log_file(config["log_path"])

    # Deletes the previous log file if too big
    delete_log_file(log_file)

    # Creates the logger
    logger = create_logger(log_file)

    # Generates 'mapstore' database coonection string
    mrsat_string = create_db_string(config, 'mrsat', logger)

    # Creates mrsat's database engine
    mrsat_engine = create_db_engine(config, 'mrsat', mrsat_string, logger)

    # Connects to mrsat's database engine
    mrsat_connection = connect_to_engine(mrsat_engine, config, 'mrsat', logger)

    # Transforms the 'mrsat_60days' table to Pandas DataFrame 
    mrsat_df = table_to_df(config, mrsat_connection, logger)
    
    # Generates 'mapstore' database coonection string
    mapstore_string = create_db_string(config, 'mapstore', logger)

    # Creates mapstore's database engine
    mapstore_engine = create_db_engine(config, 'mapstore', mapstore_string, logger)

    # Replaces the 'mrsat_60days' table on the mapstore DB
    df_to_db(mrsat_df, config, mapstore_engine, logger)

    # Opens the 'tables_processing.sql' file
    sql_query = open_sql_query(logger)

    # Executes the SQL to preprocces the input tables
    execute_sql_query(mapstore_engine, sql_query, logger)
    
    end = datetime.now()

    print(f"[OK] - Tables successfully copied to mapstore's database. Time elapsed: {end - start}")


if __name__ == "__main__":
    main(sys.argv)