import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment
from sshtunnel import SSHTunnelForwarder
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import sys


# Funcion que lee el archivo de configuracion con extension .json
def read_config_file(filename):
    dirname = os.path.dirname(__file__)
    filepath = os.path.join(dirname, filename)
    try:
        config = None
        with open(filepath) as json_file:
            print(json_file)
            config = json.load(json_file)

        return config
    except:
        return None


# Funcion que realiza el envio de un correo con los datos obtenidos sobre los cambios de estado
# en los valores de toxicidad
def send_email(config, toxic_values):
    logging.info("Comienza el envio de correos")
    try:
        dirname = os.path.dirname(__file__)
        filepath = os.path.join(dirname, config["output_html"])
        with open(filepath, "r") as f:
            base_message = f.read()
            f.close()
            # Se completa el html con los datos obtenidos sobre los cambios de estado en los valores de 
            # toxicidad 
            message = MIMEText(
                Environment().from_string(base_message).render(
                    rows=toxic_values,
                    link_visor=config["link_visor"],
                    contacto=config["contacto"]
                ), "html"
            )

            # Se configura el mensaje
            msg = MIMEMultipart()
            msg['From'] = config["smtp_username"]
            msg['Subject'] = config["smtp_subject"]
            msg.attach(message)
            msg['To'] = config["to_email"]

            # Se realiza la conexión con el servidor SMTP
            mailserver = smtplib.SMTP(
                config["smtp_server"], config["smtp_port"])
            mailserver.ehlo()
            mailserver.starttls()
            mailserver.ehlo()
            mailserver.login(config["smtp_username"],
                             config["smtp_password"])
            # Se envia el email
            mailserver.sendmail(
                config["smtp_username"], config["to_email"], msg.as_string())
            logging.info(f"Se envio el correo a {config['to_email']}")

            mailserver.quit()

    except Exception as e:
        logging.error(f"Se produjo un error al enviar el correo. Error: {str(e)}")
        sys.exit("Se produjo un error al enviar el correo")
    finally:
        logging.info("Ha finalizado el envio de correos")

# Funcion que revisa si existen cambios de estado en la toxicidad de las areas
def find_toxic_values_rows(conn):
    toxic_value = {}
    results = []
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    # Se recorren todas las areas en la tabla areas_contingencia del esquema capas_estaticas
    cursor.execute("""SELECT * FROM capas_estaticas.areas_contingencia""")
    rows = cursor.fetchall()
    for area_cont in rows:
        # Cada area se busca en la tabla estados del esquema notificaciones
        cursor.execute(
            f"SELECT * FROM notificaciones.estados WHERE codigoarea = {area_cont['codigoarea']}")
        area_est = cursor.fetchone()
        # Si el area no existe en esta tabla, se inserta con su estado actual
        if area_est == None:
            cursor.execute(
                f"INSERT INTO notificaciones.estados (codigoarea, ultimo_estado) VALUES({area_cont['codigoarea']}, '{area_cont['accion']}')")
            conn.commit()
        # Si el area existe en esta tabla, se consulta si el ultimo estado registrado es diferente al actual
        # Si lo es, se agrega a la lista de resultados y se actualiza el ultimo estado en la base de datos
        elif area_cont["accion"] != area_est["ultimo_estado"]:
            toxic_value["area_name"] = area_cont["nombrearea"]
            toxic_value["area_code"] = area_cont["codigoarea"]
            toxic_value["value"] = area_cont["accion"]
            toxic_value["causal"] = area_cont["causal"]
            if toxic_value["causal"] == None:
                toxic_value["causal"] = "-"
            results.append(toxic_value)
            toxic_value = {}
            cursor.execute(
                f"UPDATE notificaciones.estados SET ultimo_estado = '{area_cont['accion']}' WHERE codigoarea = {area_cont['codigoarea']}")
            conn.commit()
    cursor.close()
    return results


# Funcion que realiza la conexion a la base de datos por un tunel ssh
# y obtiene los datos datos sobre los cambios de estado en los valores de toxicidad
def find_toxic_values_ssh_tunnel(config):
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
                # Se buscan los cambios de estado en los valores de toxicidad
                toxic_values = find_toxic_values_rows(conn)
                logging.info("Se termino de ejecutar la busqueda de cambios de estados en valores toxicos")
                return toxic_values
            except Exception as e:
                logging.error(f"No se puede realizar la conexion con la base de datos. Error: {str(e)}")
                sys.exit("No se puede realizar la conexion con la base de datos")
            finally:
                # Se cierra la conexion
                if conn:
                    conn.close()
                    logging.info("Se ha cerrado la conexion con la base de datos")
    except Exception as e:
        logging.error(f"No se ha podido crear el tunel ssh. Error: {str(e)}")
        sys.exit("No se ha podido crear el tunel ssh")


# Funcion que realiza la conexion a la base de datos por un tunel ssh
# y obtiene los datos datos sobre los cambios de estado en los valores de toxicidad
def find_toxic_values(config):
    conn = False
    try:
        # Se realiza la conexion a la base de datos
        conn = psycopg2.connect(host=config["db_host"], dbname=config["db_name"],
                                user=config["db_username"], password=config["db_password"], port=config["db_port"])
        # Se buscan los cambios de estado en los valores de toxicidad
        toxic_values = find_toxic_values_rows(conn)
        logging.info("Se termino de ejecutar la busqueda de cambios de estados en valores toxicos")
        return toxic_values
    except Exception as e:
        logging.error(f"No se puede realizar la conexion con la base de datos. Error: {str(e)}")
        sys.exit("No se puede realizar la conexion con la base de datos")
    finally:
        # Se cierra la conexion
        if conn:
            conn.close()
            logging.info("Se ha cerrado la conexion con la base de datos")

# Funcion que obtiene los resultados y envia el correo si existen cambios de estados en los 
# valores de toxicidad
def check_and_send(config):
    # Si la bd esta en la misma maquina desde donde se hace la conexion no se usa tunel ssh
    if config["is_local_db"] == 1:
        toxic_values = find_toxic_values(config)
    # Si la bd esta en una maquina diferente desde donde se hace la conexion, es decir, se accede 
    # externamente, se usa tunel ssh
    else:
        toxic_values = find_toxic_values_ssh_tunnel(config)
    if toxic_values != []:
        send_email(config, toxic_values)
    else:
        logging.info("No existen cambios en los estados de toxicidad en ningun area")


if __name__ == '__main__':
    # Se crea el logger
    dirname_log = os.path.dirname(__file__)
    filepath_log = os.path.join(dirname_log, "mailer.log")
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
        # Si el archivo de configuracion se lee correctamente se buscan los cambios de estado
        # en los valores de toxicidad y se envia el correo
        check_and_send(config)

