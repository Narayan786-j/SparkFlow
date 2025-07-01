import os
import base64
import json


class AuthProperties:
    def __init__(self):
        pass
    redis_password: str = os.getenv('REDIS-RW-PASSWD')
    redis_startup_nodes_from_config= os.getenv('redis_startup_nodes')
    redis_startup_nodes=json.loads(redis_startup_nodes_from_config)
    SECRET_KEY: str = os.environ['BFF_AES_SECRET']
    ALGORITHM: str = os.environ['ALGORITHM']
    issuer_name:str=os.getenv('issuer_name')
    admin_issuer_name:str=os.getenv('admin_issuer_name')
    jwt_key = base64.b64decode(SECRET_KEY)
    issuer_name=issuer_name.split(',')
    admin_issuer_name=admin_issuer_name.split(',')
    public_token_name:str=os.getenv('public_token_name')       
    admin_token_name:str=os.getenv('admin_token_name')
    activity_logging_url:str = os.environ['activity_logging_url']
    namespace = os.getenv('NAMESPACE', '')