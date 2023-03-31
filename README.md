# Instalación Conectores

El repositorio a continuación contiene el set de códigos encargados de automatizar la extracción, procesamiento y carga de tablas y capas espaciales provenientes de distintas bases de datos y servicios de mapas mediante lenguaje Python y SQL. En base a la información extraída se generan nuevas capas espaciales en una BD Postgres, la cual se conecta a Geoserver y se despliegan sus servicios de mapas en mapstore.

## Prerequisitos de instalación

A continuación se especifican los prerequisitos mínimos que debe poseer la VM en la que se instalan los conectores:

**IMPORTANTE: LA INSTALACIÓN DE ESTOS CONECTORES DEBE REALIZARSE EN LA MISMA VM EN DÓNDE SE ENCUENTREN INSTALADOS EL SERVIDOR Y VISOR DE MAPAS**, ya que la carga de las distintas tablas y capas espaciales se realiza en la BD Postgres que se conecta al servidor de mapas, la cual se genera al momento de instalar el servidor y visor de mapas. 

### Sistema Operativo

Debian 11

### Bases de Datos

La ejecución de los scripts contempla la conexión a tres bases de datos: BD SQL Server del reporteador, BD SQL Server que contiene información toxicológica y BD PostgreSQL conectada al servidor de mapas. **Los parámetros de conexión a las distintas bases de datos se especifican en el archivo config.json**. A continuación se detallan las especificaciones técnicas de cada una de ellas:

#### BD Reporteador

- Versión SQL Server 2017
- Debe existir el esquema **"dbo"** en donde se almacenan los siguientes procedimientos almacenados:
    - Sp_Acui_no_PSMB
    - sp_acui_PSMB_Centros
    - sp_usach_existencia_no_salmonidos
    - sp_usach_existencia_salmonidos
    - sp_Acui_estaciones_areasPSMB
    - sp_usach_caleta_detalle_Rpa_Emb_Org

#### BD con datos mrSAT

- Versión SQL Server 2017
- Debe existir una tabla con la información toxicológica de los últimos 60 días. En el manual de instalación del conector del mrSAT se específica el formato de esta tabla con mayor detalle.

#### BD Mapstore

- Versión Postgres 10

**Acá no deberían cambiarse los parámetros de conexión, ya que la instalación del servidor y visor de mapas deja lista esta BD.**

### Paquetes previamente instalados

- sudo
- git
- Python 3.9
- pip
- [Driver ODBC para SQL Server 2017 de Debian](https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server?view=sql-server-ver16) 

## Flujo de información

A continuación se especifica el flujo general de los distintos scripts a ejecutar:

[![](https://mermaid.ink/img/pako:eNplkEtOwzAQhq8y8qqVWg6QBSivIhYgpMAqQdHEHtpIiW35sShJjsQpuBh2KN10Nxp9_zePiXEliCXsaFCf4K1oJEC6SbnzOPRfaICjRgsjauuUoS3s9_eQTTdAh5bgqSihes9eyypPH5aoyiI_Vz_fM-R1L6i1vtNkObZcSeJBeafPH5HMV3NRG9LKOEKhTCu6GywKo_JFzbAuW6y5Q30kSQZdmKDR9Ti0yjvtnf0PHlbucZOv6z5f7oHrIQLtlu3YSGbEXoSPTDHVMHeikRqWhFKSdwaHhjVyCajXIswrRR9ELPnEwdKOoXeqOkt-bfxRRY_hw-Olu_wCGSV_5Q)](https://mermaid-js.github.io/mermaid-live-editor/edit#pako:eNplkEtOwzAQhq8y8qqVWg6QBSivIhYgpMAqQdHEHtpIiW35sShJjsQpuBh2KN10Nxp9_zePiXEliCXsaFCf4K1oJEC6SbnzOPRfaICjRgsjauuUoS3s9_eQTTdAh5bgqSihes9eyypPH5aoyiI_Vz_fM-R1L6i1vtNkObZcSeJBeafPH5HMV3NRG9LKOEKhTCu6GywKo_JFzbAuW6y5Q30kSQZdmKDR9Ti0yjvtnf0PHlbucZOv6z5f7oHrIQLtlu3YSGbEXoSPTDHVMHeikRqWhFKSdwaHhjVyCajXIswrRR9ELPnEwdKOoXeqOkt-bfxRRY_hw-Olu_wCGSV_5Q)

### 1. ide_subpesca_conector.py

Extrae las capa espaciales provenientes de servicios de mapas mediante la API REST de ArcGIS Server:

- [Concesiones de Acuicultura por estado de trámite](https://geoportal.subpesca.cl/server/rest/services/IDE_PUBLICO/SRMPUB_ACUICULTURA/MapServer/0)
- [Acuicultura en AMERB](https://geoportal.subpesca.cl/server/rest/services/IDE_PUBLICO/SRMPUB_ACUIAMERB/MapServer/0)
- [AMERB](https://geoportal.subpesca.cl/server/rest/services/TESTING/SRMTEST_AMERB/MapServer/0)
- [Áreas de Colecta](https://geoportal.subpesca.cl/server/rest/services/IDE_INTERNO/SRMINT_AREASDECOLECTA/MapServer/0)
- [ECMPO](https://geoportal.subpesca.cl/server/rest/services/IDE_PUBLICO/SRMPUB_ECMPO/MapServer/0)

Estas capas son procesadas mediante Python y SQL y posteriormente son almacenadas en la BD Postgres conectada a Geoserver. 

**Se ejecuta sólo en caso de querer actualizar la información base a desplegar en Mapstore.**

### 2. reporteador_db_conector.py

Genera una conexión a la la BD SQL Server de SERNAPESCA y ejecuta procedimientos almacenados para extraer las tablas:

- Existencias Moluscos
- Existencias Salmónidos
- Áreas PSMB
- Centros PSMB
- Estaciones de Monitoreo

Estas tablas son copiadas a la BD Postgres conectada a Geoserver y son pre-procesadas dentro de esta misma BD. 

**IMPORTANTE: Para poder generar la conexión a la BD de SERNAPESCA hay que estar conectado a su VPN o bien ejecutar el script desde su servidor.**

### 3. generate_spatial_outputs.py

Se conecta a la BD de SERNAPESCA que contiene la información toxicológica proveniente del mrSAT y la almacena en la BD Postgres.
Posterior a esto, se ejecuta un script SQL en la BD Postgres conectada a Geoserver para generar las capas espaciales de salida que están desplegadas en mapstore:

- areas_contingencia
- areas_psmb
- bancos_contingencia
- centros_acuicultura
- centro_causal
- centros_no_psmb
- centros_psmb
- centros_tara
- centros_salmonidos

## Instalación

A continuación se especifican los pasos a seguir para automatizar la ejecución de los distintos scripts:

### 1. Clonar Repositorio
Se clona el proyecto con el siguiente comando:
```bash
git clone https://gitlab.sernapesca.cl/acuicultura/GRDSN/SIG/sig-backend.git
```

### 2. Instalación librerías 
Una vez instalado Python, se deben instalar las librerías necesarias para el correcto funcionamiento de los scripts, las cuales se encuentran especificadas dentro del archivo requirements.txt. Dentro del directorio raíz se ejecuta por consola el comando:
```bash
pip3 install -r requirements.txt
```

### 3. Configuración archivo config.json
Una vez instaladas las librerías de Python requeridas se deben especificar dentro del archivo `config.json` los parámetros de conexión a las distintas BDs a las que se conectarán los scripts. Dentros de los distintos objetos que se muestran en este archivo, se deben editar (de ser necesario) principalmente dos: **los parámetros especificados en 'mrsat' y 'reporteador'**.

A continuación se especifican los parámetros que interesaría cambiar dentro de estos objetos:

```bash
{
    "reporteador": {
        "db_type": "mssql+pyodbc", # Driver que se utiliza para conectarse a la BD, NO CAMBIAR
        "db": "VistasdeNegocio", # Nombre de la BD que contiene los SP's a ejecutar
        "port": "1433", # Puerto en el que se encuentra la BD
        "host": "10.5.1.35", # IP del servidor
        "passwd": "T_T54ch201", # Contraseña del usuario que se conecta
        "user": "usr_usach" # Usuario que se conecta a la BD
    },
    "mrsat": {
        "db_type": "mssql+pyodbc", # Driver que se utiliza para conectarse a la BD, NO CAMBIAR
        "db": "SNPA", # Nombre de la BD que contiene la información toxicológica
        "schema": "mrsat", # Esquema en donde se encuentra alojada la tabla toxicológica de interés
        "last_days_table": "mrsat_60days", # Nombre de la tabla que contiene la información toxicológica de los últimos 60 días.
        "historic_table": "mrsat", # Nombre de la tabla que contiene la información toxicológica histórica. No es necesario especificarla.
        "host": "10.5.1.18", # IP del servidor
        "port": "1433", # Puerto en el que se encuentra la BD
        "passwd": "C1_7Y02aps", # Contraseña del usuario que se conecta
        "user": "citiaps" # Usuario que se conecta a la BD
    }
}
```

### 4. Carga de capas base
El procesamiento automatizado de las distintas capas a desplegar en el visor de mapas contempla cómo información de entrada algunas tablas y capas espaciales estáticas. Estas tablas y capas se encuentran almacenadas dentro del repositorio en la carpeta `entradas`, las cuales serán cargadas a la BD PostgreSQL local. Para cargar estas capas se deben seguir los siguientes pasos:

#### 4.1 Edición archivo generate_static_inputs.sh
El archivo `generate_static_inputs.sh` se encarga de realizar la carga mencionada anteriormente. Antes de ejecutar este archivo, se debe editar la ruta de la carpeta 'entradas' del repositorio; para lo cual se debe abrir con un editor de texto el archivo `generate_static_inputs.sh` y especificar la ruta de la carpeta entradas al lado de `PATH_ENTRADAS`.

Las credenciales de conexión a la BD no deberían cambiarse entendiendo que la instalación se está generando en la misma VM en dónde ya se encuentra desplegada la BD PostgreSQL.

#### 4.2 Ejecución archivo generate_static_inputs.sh
Una vez editado el archivo, este debe ejecutarse en el directorio raíz del proyecto:
```bash
sh ./generate_static_inputs.sh
```
De esta forma, se debe haber generado el esquema 'entradas' dentro de la BD postgreSQL y cargado las capas la carpeta entradas dentro de este.

### 5. Edición cronjobs
Los archivos `cronjobs.sh` son los que contienen los comandos para ejecutar los distintos scripts. Antes de automatizar su ejecución se debe cambiar la ruta de ejecución de cada uno de los scripts. Para esto, se debe abrir en un editor de texto cada uno de los archivos (`cronjob_ide.sh, cronjob_reporteador.sh, cronjob_mrsat_to_db.sh `) por separado y en la línea 2, al lado de cd indicar la ruta raíz del proyecto:

```bash
#!/bin/bash
cd <ruta directorio raíz del proyecto>
python3 <archivo python a ejecutar> config.json
```

### 6. Automatización ejecución de scripts

Finalmente, se debe inicializar la ejecución automatizada de los distintos scripts del proyecto. Los pasos a seguir son los siguientes:

- Inicializar el servicio de cron con el comando `sudo systemctl start cron`.
- Ejecutar por línea de comando `crontab -e` Acá se abre un editor de texto en donde se indican los archivos a ejecutar y su respectiva frecuencia de ejecución. Al final del editor de texto que se abre, se debe pegar lo siguiente:

```bash
# Ruta del proyecto
REPORTEADOR_PATH="/home/usach/sig-backend" # CAMBIAR POR LA RUTA DEL PROYECTO DENTRO DE LA VM

# Ejecuta cada una hora el archivo generate_spatial_outputs.py, a las HH:05 hrs.
5 * * * * sh ${REPORTEADOR_PATH}/cronjob_mrsat_to_db.sh

# Ejecuta el archivo ide_subpesca_conector.py a las 00:30 en el día 1 de cada mes.
30 0 1 * * sh ${REPORTEADOR_PATH}/cronjob_ide.sh

# Ejecuta el archivo reporteador_db_conector.py en el minuto 1 cada 12 horas
1 */12 * * * sh ${REPORTEADOR_PATH}/cronjob_reporteador.sh
```
Nota: Si se desea cambiar la frecuencia de ejecución de estos scripts según se indica en la página de [crontab guru](https://crontab.guru/)

- El daemon de cron debió haber instalado el proceso automáticamente. Si no lo hizo, realizar nuevamente el paso anterior.


# Servicio de correos

Para ejecutar el servicio de correos se deben configurar primero las variables del archivo config.json de la carpeta mailer. A continuación, se explica
cada una de ellas.
- "output_html": Corresponde al nombre del archivo base del html que compone el correo que se enviará. Debe tener valor "mail.html" (como se ve en config.json-example).
- "link_visor": Es el link al visor de mapas.
- "contacto": Corresponde a un contacto para mayor información y/o consultas.
- "smtp_server": Es el servidor SMTP.
- "smtp_port": Es el puerto del servidor SMTP (número).
- "smtp_username": Corresponde al usuario SMTP.
- "smtp_password": Corresponde a la contraseña SMTP.
- "smtp_subject": Es el asunto que poseerá el correo que se enviará.
- "to_email": Corresponde al email al que se enviará el correo, está pensado para ser una lista de correos.
- "db_host": Corresponde al servidor de la base de datos.
- "db_port": Es el puerto de la base de datos (número).
- "db_username": Es el usuario de la base de datos.
- "db_password": Corresponde a la contraseña de la base de datos.
- "db_name": Es el nombre de la base de datos en donde se encuentra el esquema capas_estaticas y la tabla areas_contingencia.
- "ssh_username": Corresponde al usuario ssh.
- "ssh_password": Corresponde a la constraseña ssh.
- "ssh_ip": Corresponde a la ip del servidor en donde se encuentra la base de datos.
- "ssh_port": Es el puerto ssh (número).
- "is_local_db": Corresponde a un variable que indica si el servicio de correos se ejecuta en la misma máquina que la base de datos. Para indicar que se encuentran en la misma máquina, esta variable debe tener valor 1. Y para indicar que no se encuentran en la misma máquina, debe tener valor 0.

Cabe mencionar que las variables que se reacionan con ssh son necesarias solo si el servicio de correos se ejecuta en una máquina distinta a donde se encuentra la base de datos.

Luego de configurar las variables, para instalar las dependencias utilizadas por el servicio de correos, y crear el esquema y tabla que utiliza el servicio de correos se debe ejecutar el archivo init.sh que se encuentra en la carpeta mailer.
```bash
cd /home/usach/sig-backend/mailer # ADAPTAR A LA RUTA DEL PROYECTO DENTRO DE LA VM
sh init.sh
```

Por último, para ejecutar el servicio de correos, se debe agregar la siguiente línea en el crontab:

```bash
# Ejecuta el archivo mailer_daemon.py a las 22:00 hrs todos los días
0 22 * * * python3 ${REPORTEADOR_PATH}/mailer/mailer_daemon.py
```
Con esto el servicio de correos se ejecutará todos los días a las 22:00 hrs.
