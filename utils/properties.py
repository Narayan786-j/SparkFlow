import os, json
from .cryptlib import *


class Properties:
    def __init__(self):
        pass

    cms_url = os.environ['cms_url']
'''
    decryption_password = os.environ['UI_PASSWORD']
    oracle_database_credentials = {
        "dialect": os.environ["db_dialect"],
        "sql_driver": os.environ["db_sql_driver"],
        "username": os.environ["ORACLE_DE_USER"],
        "password": decrypt(os.environ["ORACLE_DE_PASSWORD_ENC"]),
        "host": os.environ["ORACLE_HOST"],
        "port": os.environ["ORACLE_PORT"],
        "service": os.environ["ORACLE_DE_SERVICE_NAME"],
    }

    core_services = json.loads(os.environ['services'])
    job_instance_url = os.environ['job_instance_url']
    '''
