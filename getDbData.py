import time
start_time = time.time()
print(f"[{time.strftime('%X')}] Starting getDbData load...")
import json
import traceback
from utils.database.models import *
from sqlalchemy import update
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from utils.exceptions import Error
from utils.logger import logger
from schema import RunJobRequest
import base64
import requests
from kubernetes import client
from kubernetes.client.rest import ApiException
from dotenv import load_dotenv
import os
from requests.auth import HTTPBasicAuth
# from Encryption import decryptKey
from starlette.responses import JSONResponse

load_dotenv()
print(f"[{time.strftime('%X')}] getDbData loaded in {time.time() - start_time:.2f}s")


def get_job_config_by_job_instance_id(connection, request: RunJobRequest):
    cust_setup_info = connection.query(MonCustomerSetupInfo.customer_setup_info_id,
                                       MonCustomerSetupInfo.config,
                                       MonCustomerSetupInfo.setup_info_id,
                                       MonCustomerSetupInfo.component_name,
                                       MonCustomerSetupInfo.is_scheduled,
                                       MonCustomerSetupInfo.run_config,
                                       PlsJobInsMst.CLIENT_ID.label("customer_id"),
                                       PlsJobInsMst.IS_STREAMING
                                       ).join(
        PlsJobInsMst,
        PlsJobInsMst.JOB_INSTANCE_ID == MonCustomerSetupInfo.job_instance_id
    ).filter(
        MonCustomerSetupInfo.job_instance_id == request.job_instance_id,
        MonCustomerSetupInfo.status == 'A',
        PlsJobInsMst.status == 'A'
    ).all()
    if len(cust_setup_info) == 0:
        raise Error(status_code=400, details="No job cust_setup_info_id mapped to this job_instance_id")
    if len(cust_setup_info) > 1:
        raise Error(status_code=400, details="Multiple customer setup infoIds found mapped with job instance Id")
    return cust_setup_info[0]
    # cust_setup_info_id = cust_setup_info[0].customer_setup_info_id
    # run_config = cust_setup_info[0].config
    # setup_info_id = cust_setup_info[0].setup_info_id
    # customer_id = cust_setup_info[0].customer_id
    # component_name = cust_setup_info[0].component_name
    # is_scheduled = cust_setup_info[0].is_scheduled
    # logger.info(f'''Customer Setup Info ID found for the given Job
    #             Instance Id {request.job_instance_id} is {cust_setup_info_id}''')
    # return cust_setup_info_id, run_config, setup_info_id, customer_id, component_name, is_scheduled


def get_job_config_by_job_instance_id_stop(connection, job_instance_id: int):
    cust_setup_info = connection.query(MonCustomerSetupInfo.customer_setup_info_id,
                                       MonCustomerSetupInfo.config,
                                       MonCustomerSetupInfo.setup_info_id,
                                       MonCustomerSetupInfo.component_name,
                                       MonCustomerSetupInfo.is_scheduled,
                                       MonCustomerSetupInfo.run_config,
                                       PlsJobInsMst.CLIENT_ID.label("customer_id"),
                                       PlsJobInsMst.IS_STREAMING
                                       ).join(
        PlsJobInsMst,
        PlsJobInsMst.JOB_INSTANCE_ID == MonCustomerSetupInfo.job_instance_id
    ).filter(
        MonCustomerSetupInfo.job_instance_id == job_instance_id,
        MonCustomerSetupInfo.status == 'A',
        PlsJobInsMst.status == 'A'
    ).all()
    if len(cust_setup_info) == 0:
        raise Error(status_code=400, details="No job cust_setup_info_id mapped to this job_instance_id")
    if len(cust_setup_info) > 1:
        raise Error(status_code=400, details="Multiple customer setup infoIds found mapped with job instance Id")
    return cust_setup_info[0]
    # cust_setup_info_id = cust_setup_info[0].customer_setup_info_id
    # run_config = cust_setup_info[0].config
    # setup_info_id = cust_setup_info[0].setup_info_id
    # customer_id = cust_setup_info[0].customer_id
    # component_name = cust_setup_info[0].component_name
    # is_scheduled = cust_setup_info[0].is_scheduled
    # logger.info(f'''Customer Setup Info ID found for the given Job
    #             Instance Id {request.job_instance_id} is {cust_setup_info_id}''')
    # return cust_setup_info_id, run_config, setup_info_id, customer_id, component_name, is_scheduled



def get_cluster_info_for_customer(customer_id: int, cluster_type, connection: Session):
    cluster_infos = connection.query(
        MonClusterMaster
    ).join(
        MonCustomerClusterMap,
        MonCustomerClusterMap.cluster_id == MonClusterMaster.cluster_id
    ).filter(
        MonCustomerClusterMap.customer_id == customer_id,
        MonCustomerClusterMap.status == 'A',
        MonClusterMaster.status == 'A',
        MonCustomerClusterMap.type == cluster_type
    ).all()

    if len(cluster_infos) > 1:
        raise Error(status_code=500, details=f"Multiple clusters mapped against customerId" +
                                             f" {customer_id} and cluster type {cluster_type}")
    if len(cluster_infos) == 0:
        raise Error(status_code=500, details=f"No clusters mapped against " +
                                             f"customerId {customer_id} and cluster type {cluster_type}")

    return cluster_infos[0]


def get_job_data_by_jobinstace_id(jobinstance_id, connection: Session):
    return connection.query(PlsJobInsMst).filter(
        PlsJobInsMst.JOB_INSTANCE_ID == jobinstance_id, PlsJobInsMst.status == "A").first()


def update_setup_run_config(connection: Session, run_config: dict, customer_setup_info_id, final_config):
    config_str = json.dumps(run_config)
    stmt = (
        update(MonCustomerSetupInfo)
        .where(MonCustomerSetupInfo.customer_setup_info_id == customer_setup_info_id)
        .values(run_config=config_str,
                config=(json.dumps(final_config))
                )
    )
    connection.execute(stmt)


def GetAppIDStandalone(MasterUrl, SparkAppName, SparkUIUsername, SparkUIPassword):
    MasterUrlSplit = MasterUrl.split(":")
    SparkUrl = f'''https://{MasterUrlSplit[0]}:8081/json'''
    credentials = f"{SparkUIUsername}:{SparkUIPassword}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    headers = {'Authorization': f'Basic {encoded_credentials}'}
    logger.info(f"Making request to URL:{SparkUrl}, with headers:{json.dumps(headers, indent=4)}")
    response = requests.request("GET", SparkUrl, headers=headers, verify=False)
    logger.info(f"Response received:{response.text}")
    RunningJobsList = json.loads(response.text)
    for RunningJobsRow in RunningJobsList.get('activeapps'):
        if RunningJobsRow.get('name') == SparkAppName:
            return RunningJobsRow.get('id')

    return False


def KillStandaloneJob(MasterUrl, AppID, SparkUIUsername, SparkUIPassword):
    MasterUrlSplit = MasterUrl.split(":")
    url = f'''https://{MasterUrlSplit[0]}:8081/app/kill/'''
    payload = f'''id={AppID}&terminate=true'''

    credentials = f"{SparkUIUsername}:{SparkUIPassword}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': f'Basic {encoded_credentials}'}
    logger.info(f"Making request to URL:{url}, with headers:{json.dumps(headers, indent=4)}")
    response = requests.request("POST", url, headers=headers, data=payload, verify=False)
    logger.info(f"Response received:{response.text}")
    return response


def UpdateStandaloneUIUrl(MasterUrl, SparkAppName, JobInstanceId, SparkUIUsername, SparkUIPassword, connection):
    try:
        MasterUrlSplit = MasterUrl.split(":")
        SparkUrl = f'''https://{MasterUrlSplit[0]}:8081'''
        credentials = f"{SparkUIUsername}:{SparkUIPassword}"
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        headers = {'Authorization': f'Basic {encoded_credentials}'}
        SparkUIUrl = None
        LoopCounter = 0
        while SparkUIUrl is None and LoopCounter < 3:
            logger.info(f"Making request to URL: {SparkUrl} with headers: {json.dumps(headers)}")
            response = requests.request("GET", SparkUrl, headers=headers, verify=False)
            logger.info(f"HTML Received {response.text}")
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                for a_tag in soup.find_all('a'):
                    if a_tag.get_text() == SparkAppName:
                        SparkUIUrl = a_tag['href']
                        break

            LoopCounter += 1
        if SparkUIUrl:
            UpdatePlsJobInsMstSparkUI(JobInstanceId, SparkUIUrl, connection)
            logger.info(f"Standalone Spark UI: {SparkUIUrl}")
    except Exception as e:
        print(e)

def UpdatePlsJobInsMstSparkUI(JobInstanceId, SPARKUI, connection):
    update_query = (
        update(PlsJobInsMst.__table__)
        .where(PlsJobInsMst.JOB_INSTANCE_ID == JobInstanceId)
        .values(SPARKUI=SPARKUI)
    )
    connection.execute(update_query)
    connection.commit()


######kubernetes SOK##########


def get_namespace_from_job_instance_id(connection, job_instance_id):
    # MODULE_ID FROM SETUPINFOID-> BASE INSTANCEID ->PLS_JOB_INS_MST.JOB_INSTANCE_ID -> MODULEID
    module_ids = connection.query(
        PlsJobInsMst.MODULE_ID
    ).filter(PlsJobInsMst.JOB_INSTANCE_ID == job_instance_id)
    logger.info(f"Query for moduleId generated: {module_ids} "
                f"job_instance_id: {job_instance_id}")
    module_ids = module_ids.all()

    if len(module_ids) > 1:
        raise Error(status_code=400, details=f"Module Id data incorrect. Please check the data "
                                             f"from job_instance_id :{job_instance_id}")
    if len(module_ids) == 0:
        raise Error(status_code=400, details=f"Error in job configuration of this setup_info_id"
                                             f":{job_instance_id}. Please check the base job mapping ")

    module_id = module_ids[0].MODULE_ID
    namespaces = connection.query(PlsJobNamespace.namespace).filter(
        PlsJobNamespace.status == 'A',
        PlsJobNamespace.module_id == module_id
    ).all()

    if len(namespaces) > 1:
        raise Error(status_code=500, details=f"Multiple namespaces mapped against module ID {module_id}")
    if len(namespaces) == 0:
        raise Error(status_code=500, details=f"No namespace mapped against moduleId {module_id}")
    namespace = namespaces[0].namespace
    return namespace


def get_token_uuid_for_namespace(connection, namespace: str, customer_id: int):
    token_uuids = connection.query(PlsMaClusterNamespaceUuid.uuid).join(
        MonCustomerClusterMap,
        MonCustomerClusterMap.cluster_id == PlsMaClusterNamespaceUuid.clusterid
    ).join(
        MonClusterMaster,
        MonClusterMaster.cluster_id == MonCustomerClusterMap.cluster_id
    ).filter(
        PlsMaClusterNamespaceUuid.namespace == namespace,
        PlsMaClusterNamespaceUuid.status == 'A',
        MonCustomerClusterMap.customer_id == customer_id,
        MonCustomerClusterMap.status == 'A',
        MonClusterMaster.status == 'A'
    )

    logger.info(f"Query for moduleId generated: {token_uuids} "
                f"namespace: {namespace}")
    token_uuids = token_uuids.all()

    if len(token_uuids) > 1:
        raise Error(status_code=500, details=f"Multiple token_uuids mapped against namespace {namespace}")
    if len(token_uuids) == 0:
        raise Error(status_code=500, details=f"No token_uuids mapped against namespace {namespace}")
    token_uuid = token_uuids[0].uuid
    return token_uuid


def DeleteK8Job(endpoint, job_name_with_id, namespace, token):
    url = f"https://{endpoint}/apis/batch/v1/namespaces/{namespace}/jobs/{job_name_with_id}"
    payload = {}
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    logger.info(
        f"Making Request for delete job {job_name_with_id} with URL:{url}, PAYLOAD: {payload},headers: {headers}")
    response = requests.request("DELETE", url, headers=headers, data=payload, verify=False)
    logger.info(f"Response for delete job {response.text}")
    return response


def DeleteK8Deployment(endpoint, job_name_with_id, namespace, token):
    url = f'''https://{endpoint}/apis/apps/v1/namespaces/{namespace}/deployments/{job_name_with_id}'''
    payload = {}
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    logger.info(
        f"Making Request for delete deployments {job_name_with_id} with URL:{url}, PAYLOAD: {payload},headers: {headers}")
    response = requests.request("DELETE", url, headers=headers, data=payload, verify=False)
    logger.info(f"Response for delete deployments {response.text}")
    return response


# def DeleteK8Pods(endpoint, podname, namespace, token):
#     k8s_url = f"https://{endpoint}"
#     configuration = kubernetes.client.Configuration()
#
#     configuration.host = k8s_url
#     configuration.verify_ssl = False
#     configuration.api_key_prefix['authorization'] = 'Bearer'
#     configuration.api_key['authorization'] = token
#
#     with kubernetes.client.ApiClient(configuration) as api_client:
#         api_instance = kubernetes.client.CoreV1Api(api_client)
#         pod_list = api_instance.list_namespaced_pod(namespace=namespace)
#
#         pod_names = []
#         my_list = []
#         for i in pod_list.items:
#             pod_names.append((i.status.pod_ip, i.metadata.namespace, i.metadata.name))
#             my_list.append(i.metadata.name)
#
#         print("************* pod_names******", pod_names)
#         print("**********True********")
#
#         prefix_to_find = podname
#         suffix_to_find = "driver"
#         result = [s for s in my_list if s.endswith(suffix_to_find) and s.startswith(prefix_to_find)]
#
#
#
#         for pod in result:
#             pod_name = pod
#             api_instance.delete_namespaced_pod(name=pod, namespace=namespace, grace_period_seconds=0)
#             print(f"Pod {pod_name} deleted successfully.")
#     return True
#
def DeleteK8Pods(endpoint: str, podname: str, namespace: str, token: str) -> bool:

    k8s_url = f"https://{endpoint}"

    configuration = client.Configuration()
    configuration.host = k8s_url
    configuration.verify_ssl = False  
    configuration.api_key_prefix['authorization'] = 'Bearer'
    configuration.api_key['authorization'] = token

    try:
        with client.ApiClient(configuration) as api_client:
            v1 = client.CoreV1Api(api_client)

            pods = v1.list_namespaced_pod(namespace=namespace)
            matching_pods = [
                pod.metadata.name for pod in pods.items
                if pod.metadata.name.startswith(podname) and pod.metadata.name.endswith("driver")
            ]

            if not matching_pods:
                logger.warning(f"No matching pods found for prefix '{podname}' and suffix 'driver'.")
                return False

            for pod_name in matching_pods:
                try:
                    v1.delete_namespaced_pod(
                        name=pod_name,
                        namespace=namespace,
                        grace_period_seconds=0
                    )
                    logger.info(f" Pod '{pod_name}' deleted successfully.")
                except ApiException as e:
                    if e.status == 404:
                        logger.warning(f"Pod '{pod_name}' not found. Might already be deleted.")
                    else:
                        logger.error(f"Error deleting pod '{pod_name}': {e.reason}")
                        raise

        return True

    except Exception as e:
        logger.exception(" Failed to delete pods.")
        raise

def CheckJobDeploymenExits(endpoint, job_name_with_id, namespace, token, K8Type):
    url = f"https://{endpoint}/apis/batch/v1/namespaces/{namespace}/{K8Type}/{job_name_with_id}"
    payload = {}
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    logger.info(
        f"Making Request for delete job {job_name_with_id} with URL:{url}, PAYLOAD: {payload},headers: {headers}")

    response = requests.get(url, headers=headers, data=payload, verify=False)
    if response.status_code == 200:
        return True
    elif response.status_code == 404:
        print(f"{K8Type} {job_name_with_id} does not exist in namespace {namespace}.")
        return False
    else:
        print(f"Failed to check job existence. Status code: {response.status_code}")
        return False


def UpdateK8UIUrl(MasterURL, JobInstanceId, ComponentName, Namespace, token, connection, action):
    try:
        MasterIp = MasterURL.split(':')[0]
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        url = f'https://{MasterURL}/api/v1/namespaces/{Namespace}/services/{ComponentName}'

        # Check if the service already exists
        response = requests.get(url, headers=headers, verify=False)

        if response.status_code == 200 and action != 'Create':
            # Service exists, get the nodePort
            ResultDict = response.json()
            NodePort = ResultDict.get('spec').get('ports')[0].get('nodePort')
            K8NodePort = f'http://{MasterIp}:{NodePort}'
            logger.info(f"Service already exists. K8NodePort: {K8NodePort}")
            if action == 'Delete':
                url = f'https://{MasterURL}/api/v1/namespaces/{Namespace}/services/{ComponentName}'
                delete_response = requests.delete(url, headers=headers, verify=False)
                if delete_response.status_code == 200:
                    UpdatePlsJobInsMstSparkUI(JobInstanceId, None, connection)
                else:
                    logger.info(f"Delete service failed. Service name: {ComponentName}, URL:{url}, "
                                f"response: {delete_response.text}")

        elif action == 'Create':
            # Service does not exist, create it
            url = f'https://{MasterURL}/api/v1/namespaces/{Namespace}/services'
            PayLoad = {
                'apiVersion': 'v1',
                'kind': 'Service',
                'metadata': {
                    'name': ComponentName,
                    'namespace': Namespace
                },
                'spec': {
                    'ports': [{
                        'name': ComponentName,
                        'port': 4040,
                        'protocol': 'TCP',
                        'targetPort': 4040
                    }],
                    'selector': {
                        'app_name_ui': ComponentName,
                        'spark-role': 'driver'
                    },
                    'type': 'NodePort'
                }
            }

            logger.info(f"Making request to URL: {url}, PAYLOAD: {PayLoad}, headers: {headers}")
            Result = requests.post(url, headers=headers, data=json.dumps(PayLoad), verify=False)

            if Result.status_code == 201:
                # Successfully created service, get the nodePort
                ResultDict = Result.json()
                NodePort = ResultDict.get('spec').get('ports')[0].get('nodePort')
                K8NodePort = f'http://{MasterIp}:{NodePort}'
                logger.info(f"Service created. K8NodePort: {K8NodePort}")
                UpdatePlsJobInsMstSparkUI(JobInstanceId, K8NodePort, connection)
            else:
                logger.error(f"Failed to create service. Response: {Result.text}")
                return None


    except Exception as e:
        traceback.print_exc()
        print(e)

'''      

def get_cred(uuid, cred_url, debug=False, proxy=None):
    headers = {
        'Content-Type': 'application/json',
        f'Authorization': 'Basic Y21zX3VzZXI6ejJmOSNROT1WZjwoM2k='
    }

    data = {'uuid': uuid}

    try:
        if proxy:
            proxies = {
                'http': proxy,
                'https': proxy
            }
            response = requests.post(cred_url, headers=headers, json=data, verify=False, proxies=proxies)
        else:
            response = requests.post(cred_url, headers=headers, json=data, verify=False)

        if response.status_code == 200:
            print_debug("CMS API Call Successful with status code 200!", debug)
            json_dict = response.json()
            encrypted_cred = json_dict.get("responseData", {}).get("value")

'''

def get_value_from_cms(uuid):
    cms_url = os.environ.get('CMS_URL_GET_CRED')
    cms_user = os.environ.get('CMS_USER')
    cms_pass = os.environ.get('CMS_PASSWORD')

    if not all([cms_url, cms_user, cms_pass]):
        print("Missing CMS credentials or URL.")
        return None

    payload = {"uuid": uuid}
    headers = {
        'Content-Type': 'application/json',
    }

    try:
        print(f"cms_url: {cms_url}, uuid: {uuid}, cms_user: {cms_user}")
        auth = HTTPBasicAuth(cms_user, cms_pass)
        response = requests.post(cms_url, auth=auth, headers=headers, json=payload, verify=False)

        if response.status_code != 200:
            print(f"CMS returned {response.status_code}: {response.text}")
            return None

        try:
            data = response.json()
        except ValueError as e:
            print(f"Failed to decode JSON from CMS response: {e}, content: {response.text}")
            return None

        encoded_content = data.get("responseData", {}).get("value")
        if not encoded_content:
            print(f"Missing 'value' in responseData: {data}")
            return None

        decoded_data = base64.b64decode(encoded_content).decode("utf-8")
        return decoded_data

    except Exception as e:
        print(f"Error fetching data from CMS API: {e}, URL: {cms_url}, UUID: {uuid}")
        print(traceback.format_exc())
        return None

def getDataFromVault(uuid):
    #cms="http://dev.hcmp.jio.com/openapi"
    # payload = {"uuid": uuid, "version": version}
    #cms_url = cms + "/credential-management/cms/v1/getCredential"
    cms_url = "http://dev.hcmp.jio.com/openapi/credential-management/cms/v1/getcredential"
    cms_url = "https://sit.hcmp.jio.com/openapi/credential-management/v1/cms/getcredential"
    # cms_url = f"{app_config.cms_url}/openapi/credential-management/cms/v1/getcredential"
    headers = {
        'Content-Type': 'application/json',
        f'Authorization': 'Basic Y21zX3VzZXI6ejJmOSNROT1WZjwoM2k='
    }
    payload = {'uuid': uuid}
    logger.info(f"Making Request with {cms_url}, PAYLOAD: {payload}")

    response = requests.post(
        cms_url,
        json=payload,
        headers=headers,
        verify=False
    )
    logger.info(f"Vault API response recieved {response.text}")
    data = json.loads(response.text)

    if response.status_code == 200:
        return json.loads(response.text)
    else:
        raise Error(status_code=response.status_code, details=response.text)



def run_standalone_job(cluster_manager, master_url, payload):
    url = f"http://{master_url}/v1/submissions/create"
    headers = {
        "Content-Type": "application/json"
    }
    logger.info(
        f"Making Request for {cluster_manager} with URL:{url}, PAYLOAD: {json.dumps(payload)},headers: {headers}")
    response = requests.request("POST", url, headers=headers, json=payload, verify=False)
    if response.status_code not in [200, 201]:
        logger.error(f"Error calling api: respose got: {response.text}")
        raise Error(status_code=400, details=json.loads(response.text))
    # response.raise_for_status()
    logger.info(f"Response of the trigger job call: {response.text}")
    response = json.loads(response.text)
    return response


def start_kubernetes_stream_job(master_url, namespace, payload, token):
    url = f"https://{master_url}/apis/apps/v1/namespaces/{namespace}/deployments"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    logger.info(
        f"Making Request for K8s with URL:{url}, NAMESPACE: {namespace}, PAYLOAD: {payload},headers: {headers}")
    response = requests.request("POST", url, headers=headers, data=payload, verify=False)
    if response.status_code == 409:
        raise Error(status_code=409, details=f"Deployment with name already exists. {response}")
    if response.status_code not in [200, 201]:
        logger.error(f"Error calling api: respose got: {response.text}")
        raise Error(status_code=400, details=json.loads(response.text))
    # response.raise_for_status()
    logger.info(f"Response of the trigger job call: {response.text}")
    response = json.loads(response.text)
    return response


def run_kubernets_batch_job(master_url, namespace, payload, token):
    url = f"https://{master_url}/apis/batch/v1/namespaces/{namespace}/jobs"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    logger.info(
        f"Making Request for K8s with URL:{url}, NAMESPACE: {namespace}, PAYLOAD: {json.dumps(payload)},headers: {headers}")
    response = requests.request("POST", url, headers=headers, data=payload, verify=False)
    if response.status_code not in [200, 201]:
        logger.error(f"Error calling api: respose got: {response.text}")
        raise Error(status_code=400, details=json.loads(response.text))
    # response.raise_for_status()
    logger.info(f"Response of the trigger job call: {response.text}")
    response = json.loads(response.text)
    return response


def get_new_run_config_spark(job_name_with_id, setup_config,updated_config, job_data, cluster_data, request: RunJobRequest,
                             connection: Session,job_instance_id) -> dict:

    cluster_config = json.loads(cluster_data.config)
    cluster_manager = cluster_config["cluster_manager"]
    logger.info(f"Cluster manager:{cluster_manager}")

    namespace = None
    if cluster_manager == 'k8s':
        # namespace = get_namespace_from_job_instance_id(connection, job_instance_id=request.job_instance_id)
        namespace = get_namespace_from_job_instance_id(connection, job_instance_id=job_instance_id)
    logger.info(f"Namespace:{namespace}")

    master_url = cluster_config["master_url"]
    logger.info(f"cluster config: {cluster_config}")

    job_id = job_data.JOB_ID
    is_streaming = job_data.IS_STREAMING
    logger.info(f"job config: {job_id}, {is_streaming}")

    gnrc_conf_details = get_job_gnrc_conf_by_streaming_status_and_cluster_manager(connection=connection,
                                                                                     cluster_manager=cluster_manager,
                                                                                     is_streaming=True if job_data.IS_STREAMING == 'Y'
                                                                                     else False)
    gnrc_config = gnrc_conf_details.config
    replacement_configs = get_replacement_configs(connection=connection,
                                                     cluster_manager=cluster_manager,
                                                     JOB_ID=job_id,
                                                     streaming=True if is_streaming == 'Y' else False,
                                                     clusterid=cluster_data.cluster_id
                                                     )

    replacement_data = {}
    for i in replacement_configs:
        if i.replacement_key in replacement_data:

            # TODO: Needs change in the if statements logic when its partially mentioned
            if i.cluster_manager is not None and i.is_streaming is not None and i.job_id is not None and i.clusterid is not None:
                replacement_data[i.replacement_key] = i.replacement_value
        else:
            replacement_data[i.replacement_key] = i.replacement_value

    replacement_data.update(setup_config)
    replacement_data["component_name"] = job_name_with_id
    # replacement_data["job_instance_id"] = request.job_instance_id
    replacement_data["job_instance_id"] = job_instance_id
    replacement_data["master_url"] = master_url
    replacement_data['job_name_with_id'] = job_name_with_id
    replacement_data['namespace'] = namespace
    final_config = None

    logger.info(f"Replacement data final {json.dumps(replacement_data)}")
    if replacement_data:
        final_config = gnrc_config.format(**replacement_data)
    final_config = json.loads(final_config)

    args = final_config['spec']['template']['spec']['containers'][0]['args']
    if updated_config:
        updated_args = update_spark_conf_args(args, updated_config)
        final_config['spec']['template']['spec']['containers'][0]['args'] = updated_args

    # Ensure request.data is a dictionary
    request_data = request.data if isinstance(request.data, dict) else {}

    # Append "--offset" and its value if provided
    offset_value = request_data.get("offset")
    if offset_value:
        args.append(f"--offset={offset_value}")

    # Append "--debug" and its value if provided
    debug_value = request_data.get("debug")
    if debug_value:
        args.append(f"--debug={debug_value}")

    return final_config

def update_spark_conf_args(args: list, update_data: dict) -> list:
    updated_args = []
    skip_next = False
    existing_keys = set()

    for i in range(len(args)):
        if skip_next:
            skip_next = False
            continue

        if args[i] == '--conf' and i + 1 < len(args):
            key_val = args[i + 1]
            key, sep, val = key_val.partition('=')
            if key in update_data:
                updated_args.append('--conf')
                updated_args.append(f"{key}={update_data[key]}")
                existing_keys.add(key)
                skip_next = True
            else:
                updated_args.append('--conf')
                updated_args.append(key_val)
                existing_keys.add(key)
                skip_next = True
        else:
            updated_args.append(args[i])

    # Append new keys that didn't exist
    for key, val in update_data.items():
        if key not in existing_keys:
            updated_args.extend(['--conf', f"{key}={val}"])

    return updated_args

#
# def get_new_run_config_spark(job_name_with_id, setup_config, job_data, cluster_data, request: RunJobRequest, connection: Session) -> dict:
#     cluster_config = json.loads(cluster_data.config)
#     cluster_manager = cluster_config["cluster_manager"]
#     logger.info(f"Cluster manager: {cluster_manager}")
#
#     namespace = None
#     if cluster_manager == 'k8s':
#         namespace = get_namespace_from_job_instance_id(connection, job_instance_id=request.job_instance_id)
#     logger.info(f"Namespace: {namespace}")
#
#     master_url = cluster_config["master_url"]
#     job_id = job_data.JOB_ID
#     is_streaming = job_data.IS_STREAMING
#     logger.info(f"job config: {job_id}, {is_streaming}")
#
#     gnrc_conf_details = get_job_gnrc_conf_by_streaming_status_and_cluster_manager(
#         connection=connection,
#         cluster_manager=cluster_manager,
#         is_streaming=True if job_data.IS_STREAMING == 'Y' else False
#     )
#     gnrc_config = gnrc_conf_details.config
#
#     # Replacement config is used for formatting placeholders in gnrc_config
#     replacement_configs = get_replacement_configs(
#         connection=connection,
#         cluster_manager=cluster_manager,
#         JOB_ID=job_id,
#         streaming=True if is_streaming == 'Y' else False,
#         clusterid=cluster_data.cluster_id
#     )
#
#     replacement_data =4 {}
#     for i in replacement_configs:
#         if i.replacement_key in replacement_data:
#             if i.cluster_manager and i.is_streaming and i.job_id and i.clusterid:
#                 replacement_data[i.replacement_key] = i.replacement_value
#         else:
#             replacement_data[i.replacement_key] = i.replacement_value
#
#     replacement_data.update({
#         "component_name": job_name_with_id,
#         "job_instance_id": request.job_instance_id,
#         "master_url": master_url,
#         "job_name_with_id": job_name_with_id,
#         "namespace": namespace
#     })
#
#     logger.info(f"Replacement data final: {json.dumps(replacement_data)}")
#
#     # Format and parse config
#     final_config = gnrc_config.format(**replacement_data)
#     final_config = json.loads(final_config)
#
#     # Update Spark submit args
#     args = final_config['spec']['template']['spec']['containers'][0]['args']
#     updated_args = update_spark_conf_args(args, setup_config)
#     final_config['spec']['template']['spec']['containers'][0]['args'] = updated_args
#
#     # Optional args
#     offset_value = request.data.get("offset")
#     if offset_value:
#         updated_args.append(f"--offset={offset_value}")
#
#     debug_value = request.data.get("debug")
#     if debug_value:
#         updated_args.append(f"--debug={debug_value}")
#
#     return final_config


def get_job_gnrc_conf_by_streaming_status_and_cluster_manager(cluster_manager: str, is_streaming: bool,
                                                              connection: Session):
    is_streaming_int = 1 if is_streaming else 0

    gnrc_conf = (
        connection.query(HcmpMaJobGrncConf)
        .filter(
            HcmpMaJobGrncConf.cluster_manager == cluster_manager,
            HcmpMaJobGrncConf.is_streaming == is_streaming_int,  # Use the converted integer value
            HcmpMaJobGrncConf.status == "A"
        )
        .first()
    )

    logger.info(f"gnrc_conf query: {gnrc_conf}")

    return gnrc_conf


def get_replacement_configs(connection: Session, cluster_manager, streaming: bool, JOB_ID, clusterid):
    replacement_configs = connection.query(HcmpMaJobConfReplacements).filter(
        (HcmpMaJobConfReplacements.cluster_manager == cluster_manager) |
        (HcmpMaJobConfReplacements.cluster_manager.is_(None)),
        (HcmpMaJobConfReplacements.is_streaming == (1 if streaming else 0)) |
        (HcmpMaJobConfReplacements.is_streaming.is_(None)),
        (HcmpMaJobConfReplacements.job_id == JOB_ID) |
        (HcmpMaJobConfReplacements.job_id.is_(None)),
        (HcmpMaJobConfReplacements.clusterid == clusterid) |
        (HcmpMaJobConfReplacements.clusterid.is_(None)),
        HcmpMaJobConfReplacements.status == "A").all()
    return replacement_configs

