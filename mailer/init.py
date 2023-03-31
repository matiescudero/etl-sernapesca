from sshtunnel import SSHTunnelForwarder
import psycopg2
import logging
import sys
from mailer_daemon import read_config_file
import os


# Funcion que permite crear en la base de datos un esquema y una tabla si no existen
def schema_table_create_if_not_exists(conn, schema, table):
    logging.info("Se crea el schema 'notificaciones' y la tabla 'estados' si no existen")
    cursor = conn.cursor()
    cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    cursor.execute(
        f"CREATE TABLE IF NOT EXISTS {schema}.{table} (id serial PRIMARY KEY, codigoarea BIGINT, ultimo_estado VARCHAR(80))")
    conn.commit()
    cursor.close()
    return

# Funcion que realiza la conexion a la base de datos por un tunel ssh
# y crea el schema notificaciones y la tabla estados
def create_if_not_exists_ssh_tunnel(config):
    try:
    # Se crea el tunel ssh
        with SSHTunnelForwarder(
            (config["ssh_ip"], config['ssh_port']),
            ssh_username=config["ssh_username"],
            ssh_password=config["ssh_password"],
                remote_bind_address=(config["db_host"], config["db_port"])) as tunnel:
            conn = False
            try:
                # Con el tunel ssh, se realiza la conexion a la base de datos
                port = tunnel.local_bind_port
                conn = psycopg2.connect(host=config["db_host"], dbname=config["db_name"],
                                        user=config["db_username"], password=config["db_password"], port=port)
                schema_table_create_if_not_exists(
                        conn, "notificaciones", "estados")
            except Exception as e:
                logging.error(f"No se puede realizar la conexion con la base de datos. Error: {str(e)}")
            finally:
                # Se cierra la conexion
                if conn:
                    conn.close()
                    logging.info("Se ha cerrado la conexion con la base de datos")
    except Exception as e:
        logging.error(f"No se ha podido crear el tunel ssh. Error: {str(e)}")


# Funcion que realiza la conexion a la base de datos por un tunel ssh
# y crea el schema notificaciones y la tabla estados
def create_if_not_exists(config):
    conn = False
    try:
        # Se realiza la conexion a la base de datos
        conn = psycopg2.connect(host=config["db_host"], dbname=config["db_name"],
                                user=config["db_username"], password=config["db_password"], port=config["db_port"])
        schema_table_create_if_not_exists(
                conn, "notificaciones", "estados")
    except Exception as e:
        logging.error(f"No se puede realizar la conexion con la base de datos. Error: {str(e)}")
    finally:
        # Se cierra la conexion
        if conn:
            conn.close()
            logging.info("Se ha cerrado la conexion con la base de datos")


if __name__ == '__main__':
    # Se crea el logger
    dirname_log = os.path.dirname(__file__)
    filepath_log = os.path.join(dirname_log, "mailer_init.log")
    logging.basicConfig(
        format='%(asctime)-5s %(name)-5s %(levelname)-5s %(message)s',
        level=logging.INFO,
        filename=filepath_log,
        filemode="a"
    )
    logging.info("Comienza la ejecucion")

    # Se lee el archivo de configuracion
    config = read_config_file("config.json")
    if config == None:
        logging.error("El archivo de configuracion no se leyo correctamente")
        sys.exit("El archivo de configuracion no se leyo correctamente")
    else:
        # Si la bd esta en la misma maquina desde donde se hace la conexion no se usa tunel ssh
        if config["is_local_db"] == 1:
            create_if_not_exists(config)
        # Si la bd esta en una maquina diferente desde donde se hace la conexion, es decir, se accede 
        # externamente, se usa tunel ssh
        else:
            create_if_not_exists_ssh_tunnel(config)
        
