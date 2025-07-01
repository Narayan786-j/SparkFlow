from functools import wraps
from json import JSONDecodeError
from fastapi import Request
from ..exceptions import Error
from .auth_properties import AuthProperties
from ..logger import logger
import requests
import json
import traceback
from jose import jwt
import base64
from rediscluster import RedisCluster
from rediscluster.exceptions import RedisClusterException
from urllib.parse import urlparse, parse_qs, urlunparse
from datetime import datetime
import sys
import pprint
import os
import socket
import uuid
import time
import pytz
import asyncio

cfg = AuthProperties()
#config_url = cfg.core_services
SECRET_KEY=cfg.SECRET_KEY
ALGORITHM=cfg.ALGORITHM
issuer_name=cfg.issuer_name
jwt_key=cfg.jwt_key
redis_startup_nodes=cfg.redis_startup_nodes
redis_password=cfg.redis_password
public_token_name=cfg.public_token_name
admin_token_name=cfg.admin_token_name
activity_logging_url=cfg.activity_logging_url
namespace=cfg.namespace
pp = pprint.PrettyPrinter(indent=4)

from cxpactlogging import ActivityEmitter
emitter = ActivityEmitter()

def run_in_background(task_func):
    @wraps(task_func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        task = loop.create_task(task_func(*args, **kwargs))
        task.add_done_callback(handle_task_result)
        return task
    return wrapper

def handle_task_result(task):
    try:
        task.result()
    except Exception as e:
        logger.error(f"Exception in background task: {e}")

@run_in_background
async def log_activity_call(log_data):
    try:
        flattened_data = {
            'schema_version': 1,
            'action_status_code': log_data['status_code_event'],
            'platform_only': True,
            'service_name': log_data['module_info'],
            'hcmp_customer_id': log_data['customer_id'],
            'event_name': 'AUDIT_LOG',
            'hcmp_cust_id': log_data['customer_id'],
            'module_name': 'AIML',
            'source': 'HCMP',
            'namespace': namespace,
            'severity_level': log_data['severity_level'],
            'module_info': log_data['module_info'],
            'event_name': log_data['event_name'],
            'event_category': log_data['event_category'],
            'event_sub_category': log_data['event_sub_category'],
            'action_status': log_data['action_status'],
            'correlation_id': log_data['correlation_id'],
            'event_timestamp': str(datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%Y-%m-%dT%H:%M:%S.%fZ")),
            'responseTime': log_data.get('end_func'),
            'hcmp_source_info': {
                'hcmp_module_info': log_data['module_info'],
                'hcmp_service_info': log_data['module_info'],
                'line_number': log_data.get('line_number', ''),
                'source_file_name': str(log_data.get('file_name', '')),
                'source_file_version': 1.0
            },
            'request_info': {
                'request_id': log_data['correlation_id'],
                'request_url': str(log_data['request_url']),
                'request_type': str(log_data['request_type']),
                'client_ip': str(log_data['client_ip']),
                "requestPayload": json.dumps(log_data.get('request_payload', "")),
                'menuId': log_data.get('Menuid', ""),
                'featureName': str(log_data['Featurename']),
                'serviceUrl': {
                    "status": log_data.get('status', ""),
                    "menuServiceUrlId": log_data.get('menuServiceUrlId', ""),
                    "serviceURL": log_data.get('serviceURL', ""),
                    "serviceDesc": log_data.get('serviceDesc', ""),
                    "menuId": log_data.get('Menuid', ""),
                    "urlType": log_data.get('urlType', ""),
                    "menuDesc": log_data.get('menuDesc', ""),
                    "menuOwnerModule": log_data.get('menuOwnerModule', ""),
                    "menuName": log_data.get('menuName', "")
                }
            },
            'user_info': {
                'user_session': log_data.get('jwtToken', ""),
                'user_id': log_data['userId'],
                'user_name': log_data['userName'],
                'sessionId': log_data.get('sessionId', "")
            }
        }

        if log_data.get('error'):
            flattened_data['error'] = log_data['error']


        # event = requests.post(url=activity_logging_url, json=flattened_data, timeout=10)
        event = emitter.write_activity(flattened_data)
        print(f"Successfully Logged event for {log_data['userName']}: {event.text}")

    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        raise Error(status_code=500, details="logging failed")


async def authenticate_hcmp(token):
    try:
        if token:
            if token.startswith("Bearer"):
                _, _, token = token.partition(" ")
            header = jwt.get_unverified_headers(token)
        payload = jwt.decode(
            token,
            jwt_key,
            algorithms=[ALGORITHM],
            issuer=issuer_name,
            options={"verify_signature": True},
        )
        user = payload.get("sub")
        org = header.get("orgId")
        orgcode = header.get("orgCode")
        print("inside jwt token try", user, org)
        return {'orgid': org, 'user': user, 'orgcode': orgcode, "token": token}
    except Exception as e:
        traceback.print_exc()
        raise Error(status_code=401, details="Unauthenticated")

async def FetchDataFrRedis(token):
    try:
        rc = RedisCluster(startup_nodes=redis_startup_nodes, decode_responses=True, password=redis_password)
        data = rc.get(token)
        if data is not None:
            res = json.loads(data)
            return res

        else:
            return None

    except RedisClusterException as e:
        error_msg = str(e)
        traceback.print_exc()
        raise Error(status_code=500, details="RedisCluster Error", actualErrorMessage=error_msg)
    except json.JSONDecodeError as e:
        error_msg = str(e)
        traceback.print_exc()
        raise Error(status_code=500, details="JSONDecode Error", actualErrorMessage=error_msg)
    except Exception as e:
        error_msg = str(e)
        traceback.print_exc()
        raise Error(status_code=500, details="Server Error", actualErrorMessage=error_msg)

async def _flatten_urls(menu_svc_url):
    urls = []
    for _, v in menu_svc_url.items():
        for v1 in v:
            if v1.get("status") == "A":
                urls.append(v1.get("serviceURL"))
    return urls

def protected_route(func):
    @wraps(func)
    async def check_authentication(*args, **kwargs):
        token = None
        data = None
        log_data = {}
        service_path = socket.gethostname()
        split_service_path = service_path.split('-')
        module_info = "-".join(split_service_path[:-2])
        if 'request' not in kwargs:
            logger.error(f'Request does not satisfy HCMP authorization requirements kwargs')
            raise Error(status_code=401, details="No UserInfo Found/token not found",errorCode="NCDASH0002")

            # Checking if pre-requisites for Hcmp authorization are satisfied
        request = kwargs["request"]
        if public_token_name in request.cookies:
            token = request.cookies.get(public_token_name)
            print("inside "+public_token_name+" key in cookies")
            data = await authenticate_hcmp(token)
        elif 'token' in request.cookies:
            token = request.cookies.get('token')
            data = await authenticate_hcmp(token)
            print("inside token key in cookies")
        elif 'env' in request.headers and request.headers['env'] == 'local' and 'token' in request.headers:
            print("public token from headers")
            token = request.headers['token']
            data = await authenticate_hcmp(token)
            print("in token key env local and header")
        elif "Authorization" in request.headers:
            print("token from authorization")
            token = request.headers.get("Authorization")
            if token.startswith("Bearer"):
                _, _, token = token.partition(" ")
            data = await authenticate_hcmp(token)
            print("in authorization env local and header")
        else:
            logger.error(f'Request does not satisfy HCMP authorization requirements')
            raise Error(status_code=401, details="No UserInfo Found/token not found",errorCode="NCDASH0002")

        if request.headers.get('Menuid') and request.headers.get('Featurename'):
            log_data['Menuid'] = request.headers.get('Menuid')
            menuId = request.headers.get('Menuid')
            log_data['Featurename'] = request.headers.get('Featurename')
        else:
            log_data['Menuid'] = ""
            menuId = ""
            log_data['Featurename'] = ""
        print("menuid anf featurename",menuId,log_data['Featurename'])
        redisdata = await FetchDataFrRedis(token.lower())
        if redisdata == None:
            raise Error(status_code=401, details="session expired/Token not found in cluster",errorCode="NCDASH0002")

        allowed_urls = await _flatten_urls(redisdata.get("userMenuItems").get("menuServiceURL"))
        check_authentication.allowed_urls = allowed_urls
        parsed_url = urlparse(request.url.path)
        path_params_value=list(request.path_params.values())
        if not path_params_value:
            final_url = parsed_url.path
        else:
            split_params = '/' + '/'.join(path_params_value)
            final_url = parsed_url.path.split(split_params)[0]
        final_url = final_url.rstrip('/')
        final_url= final_url[1:]
        print(final_url)
        if final_url!="api/v1/custom-dashboard/alldashboardids" and final_url not in check_authentication.allowed_urls:
            raise Error(status_code=401, details="Access Forbidden. URL not allowed", errorCode="NCDASH0002")

        check_authentication.data = data
        check_authentication.redisdata = redisdata
        try:
            start_func = time.time()
            log_data['end_func'] = round((time.time()-start_func)*1000)
            retval = await func(*args, **kwargs)
            if not getattr(check_authentication, "LOG_ACTIVITY", False):
                return retval
            action_status = "SUCCESS"
            request_data = kwargs["request"]
            content_type = request_data.headers.get("Content-Type", "")
            if "multipart/form-data" in content_type:
                payload = 'file content'  # Set to "file content" for logging
            else:
                try:
                    payload = await request_data.json()
                except JSONDecodeError:
                    payload = None
            # try:
            #     payload = await request_data.json()
            # except JSONDecodeError:
            #     payload = None
            log_data['request_url'] = request_data.url
            log_data['request_type'] = request_data.method
            log_data['client_ip'] = request_data.client.host
            log_data['request_payload'] = payload
            log_data['action_status'] = action_status
            log_data['module_info'] = module_info
            log_data['file_name'] = check_authentication.__module__
            log_data['customer_id'] = check_authentication.redisdata.get('organizationId')
            log_data['userId'] = check_authentication.redisdata.get('userId')
            log_data['userName'] = check_authentication.redisdata.get('userName')
            log_data['event_name'] = getattr(check_authentication, 'ACT_EVENT_NAME', '')
            log_data['event_category'] = getattr(check_authentication, 'ACT_EVENT_CATEGORY', '')
            log_data['event_sub_category'] = getattr(check_authentication, 'ACT_EVENT_SUB_CATEGORY', '')
            log_data['correlation_id'] = getattr(check_authentication, 'ACT_CORRELATION_ID', '')
            log_data['line_number'] = getattr(check_authentication, 'ACT_LINE_NO', '')
            log_data['severity_level'] = 'INFO'
            log_data['jwtToken'] = check_authentication.redisdata.get('jwtToken')
            log_data['status_code_event'] = 200

            url_compare = final_url

            log_data['sessionId'] = check_authentication.redisdata.get('sessionId')
            print("###",url_compare,log_data['sessionId'])
            log_data['serviceURL'] = url_compare
            if check_authentication.redisdata.get('userMenuItems'):

                if check_authentication.redisdata['userMenuItems'].get('menuServiceURL'):
                    if check_authentication.redisdata['userMenuItems']['menuServiceURL'].get(menuId):
                        for i in check_authentication.redisdata['userMenuItems']['menuServiceURL'][menuId]:
                            if url_compare in i['serviceURL']:
                                log_data['serviceURL'] = i['serviceURL']
                                log_data['status'] = i.get('status', "")
                                log_data['urlType'] = i.get('urlType', "")
                                log_data['menuServiceUrlId'] = i.get('menuServiceUrlId', "")
                                log_data['serviceDesc'] = i.get('serviceDesc', "")
                                log_data['menuName'] = i.get('menuName', "")
                                log_data['menuDesc'] = i.get('menuDesc', "")
                                log_data['menuOwnerModule'] = i.get('menuOwnerModule', "")

            await log_activity_call(log_data)

        except Exception as e:
            print("here")
            if not getattr(check_authentication, "LOG_ACTIVITY", False):
                raise Error(status_code=getattr(e, "status_code", 500),
                            details=getattr(e, "details", "Something went wrong"),
                            actualErrorMessage=getattr(e, "actualErrorMessage", ""))
            # error = traceback.format_exception(etype=None, value=e, tb=e.__traceback__)
            error = traceback.format_exception(type(e), e, e.__traceback__)
            # Dont want to log VERY long error messages so truncate to a defined limit
            string_limit = 5000
            error_string = str(error)
            if len(error_string) > string_limit:
                log_data["error"] = error_string[0:string_limit]
            else:
                log_data["error"] = error_string
            action_status = "FAILED"
            request_data = kwargs["request"]
            log_data['status_code_event'] = 500
            log_data['request_url'] = request_data.url
            log_data['request_type'] = request_data.method
            log_data['client_ip'] = request_data.client.host
            log_data['action_status'] = action_status
            log_data['module_info'] = module_info
            log_data['file_name'] = check_authentication.__module__
            log_data['customer_id'] = check_authentication.redisdata.get('organizationId')
            log_data['userId'] = check_authentication.redisdata.get('userId')
            log_data['userName'] = check_authentication.redisdata.get('userName')
            log_data['event_name'] = getattr(check_authentication, 'ACT_EVENT_NAME', '')
            log_data['event_category'] = getattr(check_authentication, 'ACT_EVENT_CATEGORY', '')
            log_data['event_sub_category'] = getattr(check_authentication, 'ACT_EVENT_SUB_CATEGORY', '')
            log_data['correlation_id'] = getattr(check_authentication, 'ACT_CORRELATION_ID', '')
            log_data['line_number'] = getattr(check_authentication, 'ACT_LINE_NO', '')
            log_data['severity_level'] = 'ERROR'

            url_compare = final_url

            log_data['sessionId'] = check_authentication.redisdata.get('sessionId')
            log_data['serviceURL'] = url_compare
            if check_authentication.redisdata.get('userMenuItems'):
                log_data['sessionId'] = check_authentication.redisdata['userMenuItems'].get('sessionId')

                if check_authentication.redisdata['userMenuItems'].get('menuServiceURL'):
                    if check_authentication.redisdata['userMenuItems']['menuServiceURL'].get(menuId):
                        for i in check_authentication.redisdata['userMenuItems']['menuServiceURL'][menuId]:
                            if url_compare in i['serviceURL']:
                                log_data['serviceURL'] = i['serviceURL']
                                log_data['status'] = i.get('status', "")
                                log_data['urlType'] = i.get('urlType', "")
                                log_data['menuServiceUrlId'] = i.get('menuServiceUrlId', "")
                                log_data['serviceDesc'] = i.get('serviceDesc', "")
                                log_data['menuName'] = i.get('menuName', "")
                                log_data['menuDesc'] = i.get('menuDesc', "")
                                log_data['menuOwnerModule'] = i.get('menuOwnerModule', "")

            await log_activity_call(log_data)
            raise Error(status_code=getattr(e, "status_code", 500),
                        details=getattr(e, "details", "Something went wrong"),
                        actualErrorMessage=getattr(e, "actualErrorMessage", ""))

        return retval

    return check_authentication