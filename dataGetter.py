import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from starlette.responses import JSONResponse

start_time = time.time()
print(f"[{time.strftime('%X')}] 🔄 Starting dataGetter load...")
from sqlalchemy.orm import Session
from utils.exceptions import Error
from utils.logger import logger
from schema import RunJobRequest,StopJobRequestSchema
import base64
import json
import getDbData as db
import constants
print(f"[{time.strftime('%X')}] ✅ dataGetter loaded in {time.time() - start_time:.2f}s")


def run_job(request: RunJobRequest, connection: Session):
    logger.info(f"run_job request: {request.model_dump_json(indent=4)}")
    responses = []
    for job_id in request.job_instance_ids:
        # Step 1: Get job setup info and Spark cluster config
        # cust_setup_info_data = db.get_job_config_by_job_instance_id(connection, request)
        cust_setup_info_data = db.get_job_config_by_job_instance_id_stop(connection, job_id)

        logger.info(f"cust_setup_info_id {cust_setup_info_data.customer_setup_info_id},"
                    f"customer_id {cust_setup_info_data.customer_id},"
                    f"component_name {cust_setup_info_data.component_name},"
                    f"config {cust_setup_info_data.config},"
                    f"is_scheduled {cust_setup_info_data.is_scheduled},"
                    f"IS_STREAMING {cust_setup_info_data.IS_STREAMING},"
                    )

        cluster_data = db.get_cluster_info_for_customer(
            customer_id=cust_setup_info_data.customer_id,
            cluster_type=constants.SPARK,
            connection=connection)

        cluster_info_config = cluster_data.config
        cluster_info_config = json.loads(cluster_info_config)
        logger.info(f"Cluster config data received for spark: {cluster_info_config}")

        url = cluster_info_config['master_url']
        # job_instance_id = request.job_instance_id
        job_instance_id = job_id
        job_name_with_id = cust_setup_info_data.component_name

        # if not request.data:
        #     request.data = json.loads(cust_setup_info_data.run_config)
        setup_config = json.loads(cust_setup_info_data.run_config)
        # job_data = db.get_job_data_by_jobinstace_id(jobinstance_id=request.job_instance_id, connection=connection)
        job_data = db.get_job_data_by_jobinstace_id(jobinstance_id=job_id, connection=connection)
        run_config = db.get_new_run_config_spark(
            job_name_with_id=job_name_with_id,
            setup_config=setup_config,
            updated_config=request.data,
            job_data=job_data,
            cluster_data=cluster_data,
            request=request,
            connection=connection,
            job_instance_id=job_id
        )

        # db.update_setup_run_config(
        #     connection=connection,
        #     run_config=request.data,
        #     final_config=run_config,
        #     customer_setup_info_id=cust_setup_info_data.customer_setup_info_id)

        if 'master_url' not in cluster_info_config or 'cluster_manager' not in cluster_info_config:
            raise Error(status_code=500, details='Incorrect Cluster config. Please contact administrator')

        if cluster_info_config['cluster_manager'] == 'standlone':

            SparkAppName = job_name_with_id
            SparkUIUsername = cluster_info_config.get('spark_ui_user')
            SparkUIPassword = cluster_info_config.get('spark_ui_password')
            DriverAppID = db.GetAppIDStandalone(url, SparkAppName, SparkUIUsername, SparkUIPassword)
            # if CommService.CheckJobAlreadyRunning(url, SparkAppName, SparkUIUsername, SparkUIPassword):
            if DriverAppID != False:
                StandAloneKillResponse = db.KillStandaloneJob(url, DriverAppID, SparkUIUsername, SparkUIPassword)
                logger.info(f"StandAloneKillResponse: {StandAloneKillResponse}")

            DriverAppID = db.GetAppIDStandalone(url, SparkAppName, SparkUIUsername, SparkUIPassword)
            if DriverAppID != False:
                time.sleep(3)

            response = run_job_final_call(
                endpoint=url,
                payload=run_config,
                cluster_manager=cluster_info_config['cluster_manager'])

            db.UpdateStandaloneUIUrl(url, SparkAppName, job_instance_id, SparkUIUsername, SparkUIPassword, connection)
            return response

        else:
            namespace = db.get_namespace_from_job_instance_id(connection, job_id)
            token_uuid = db.get_token_uuid_for_namespace(connection, namespace, customer_id=cust_setup_info_data.customer_id)

            try:
                #token_encoded = db.getDataFromVault(token_uuid)['responseData']['value']
                # token_encoded = 'ZXlKaGJHY2lPaUpTVXpJMU5pSXNJbXRwWkNJNklqZDJMV3BPVW5SdU5FOTZTQzFYY1V0dGIxZzRVRUpQT0VKR1owVTBlSGhXVEVwTlNYWXphVTEyUmtraWZRLmV5SnBjM01pT2lKcmRXSmxjbTVsZEdWekwzTmxjblpwWTJWaFkyTnZkVzUwSWl3aWEzVmlaWEp1WlhSbGN5NXBieTl6WlhKMmFXTmxZV05qYjNWdWRDOXVZVzFsYzNCaFkyVWlPaUpxYVc4dGFHTnRjQzFrWlNJc0ltdDFZbVZ5Ym1WMFpYTXVhVzh2YzJWeWRtbGpaV0ZqWTI5MWJuUXZjMlZqY21WMExtNWhiV1VpT2lKemNHRnlheTFoWkcwdGRHOXJaVzR0T1hKbk9Hc2lMQ0pyZFdKbGNtNWxkR1Z6TG1sdkwzTmxjblpwWTJWaFkyTnZkVzUwTDNObGNuWnBZMlV0WVdOamIzVnVkQzV1WVcxbElqb2ljM0JoY21zdFlXUnRJaXdpYTNWaVpYSnVaWFJsY3k1cGJ5OXpaWEoyYVdObFlXTmpiM1Z1ZEM5elpYSjJhV05sTFdGalkyOTFiblF1ZFdsa0lqb2lOV1pqTkRGak1qSXRaV00yTXkwME56aGxMV0UxWW1VdE9USTFPVFJoTmpCbE1UZ3hJaXdpYzNWaUlqb2ljM2x6ZEdWdE9uTmxjblpwWTJWaFkyTnZkVzUwT21wcGJ5MW9ZMjF3TFdSbE9uTndZWEpyTFdGa2JTSjkuMFhJWFFOYjl5aFp5V1NkaTJTUXRsX3lZVkdaMnpZd0MxVG9OdjAzVkRBSERKWWhIUlJGZzRPVjRWbWlTb2k2S0hvZ2tPMXVsdjdvbkxOMmlpR3E1STZ6X09CZEh3dVFLNWV5MXItcGZNS2dkNTM0cllWdFpCQjJUdmpaNXctSlZpaDFRTTFnRWNnWFliTTcxSEIzVl9FVTJKd0pXOHFDX1ZEZ3JoeXhTTDRBOXdEQmFDNVVfSmFhVXg0ZGtKcFIyTWVpT3JFbHl1NjB3aWw3VFpxbElzZFVXMXFhNWVMTXlPVDdKWkFValNDekpXcTVaVWZ6NGZKczZFeklXZEtMeUVQMTZkaXR5UmhFdUlCb3pFNF8tS0dJVEtmR204bFNGN0FrSVZLeUlqc05JazJqVGd1OEJOSTVZaklJaDRVYXpRTk80ZFc2LXdaOS1lb1gwY1U3SmVB'
                token_encoded = 'ZXlKaGJHY2lPaUpTVXpJMU5pSXNJbXRwWkNJNklsVklaRmRvYTFvM1UwdDVUVXhWU2xWeWJXeG5WbVZZUVZKbU9UWjRNVW80VFVWSWNGZzVWVGxEU1dNaWZRLmV5SnBjM01pT2lKcmRXSmxjbTVsZEdWekwzTmxjblpwWTJWaFkyTnZkVzUwSWl3aWEzVmlaWEp1WlhSbGN5NXBieTl6WlhKMmFXTmxZV05qYjNWdWRDOXVZVzFsYzNCaFkyVWlPaUpxYVc4dGFHTnRjQzFrWlMxdlluTmxjblpoWW1sc2FYUjVJaXdpYTNWaVpYSnVaWFJsY3k1cGJ5OXpaWEoyYVdObFlXTmpiM1Z1ZEM5elpXTnlaWFF1Ym1GdFpTSTZJbk53WVhKckxXRmtiUzEwYjJ0bGJpMDVjbWM0YXlJc0ltdDFZbVZ5Ym1WMFpYTXVhVzh2YzJWeWRtbGpaV0ZqWTI5MWJuUXZjMlZ5ZG1salpTMWhZMk52ZFc1MExtNWhiV1VpT2lKemNHRnlheTFoWkcwaUxDSnJkV0psY201bGRHVnpMbWx2TDNObGNuWnBZMlZoWTJOdmRXNTBMM05sY25acFkyVXRZV05qYjNWdWRDNTFhV1FpT2lKaU1HVm1OV0kwT1MxbU1qZGlMVFJoT0RBdFlXWmpZeTB3TUdVd05ERTNOVFF4TTJZaUxDSnpkV0lpT2lKemVYTjBaVzA2YzJWeWRtbGpaV0ZqWTI5MWJuUTZhbWx2TFdoamJYQXRaR1V0YjJKelpYSjJZV0pwYkdsMGVUcHpjR0Z5YXkxaFpHMGlmUS5mUkxybjl0al90ZjRsaUp4TEpEcTNnODJEUlR5eFl5eGVKVlRmMzJrLVRpTUdEbWhweElxbkgyU2ZwRVMzQUlEeWNNNW9FMzV4SjBIbkxMRldfVjhvS3E2cUc3N2FfeXFHR3Jxb0xoSUpkNmlyeHpOdXpNYnJjZkZZT0kxZENvZ2lVUHJ2Qk0wUjU1X0lRTmdGNUloWE9odmZ2d3ZQVnJIMlpvcWJ3RDI5OVF6UmNiaXlkcjdNQTZ0UlVJUnY2cUNBLVI4Rmozc2UzRjdlR1NVczcyd3BNVmFtLVhnVjV6NGxmc3JKc3EyWVotSWRTczFNdkVWQWZpRGJlOFBIOHhWNlY2d1U4RG1vblZDTTc2X3A5YjAxYl9OYWlRc3gxSzA5RkIyaW1tNnpBREZ5dHBWTGw3MFFxMlhyUWxwdVZwa055cVpFQ3FGYXVfUHdoWUZHWFNISUE=' #sit token
                token = base64.b64decode(token_encoded).decode("utf-8")
                #token=db.get_value_from_cms(token_uuid)
            except Exception as e:
                raise Error(status_code=500, details=f"Failed to fetch or decode token: {str(e)}")

            #####Check Pod Exits####
            if request.restart:
                if cust_setup_info_data.IS_STREAMING == 'N':
                    DeleteK8JobResponse = db.DeleteK8Job(url, job_name_with_id, namespace, token)
                    if DeleteK8JobResponse.status_code not in [200, 201, 404]:
                        raise Error(status_code=400, details=json.loads(DeleteK8JobResponse.text))
                    StatusCode = DeleteK8JobResponse.status_code
                    logger.info(f"Delete Job Status Code: {DeleteK8JobResponse.status_code}")
                    logger.info(f"Delete Job Response: {DeleteK8JobResponse.text}")
                    K8Type = 'jobs'
                else:
                    DeleteK8DeploymentResponse = db.DeleteK8Deployment(url, job_name_with_id, namespace, token)
                    if DeleteK8DeploymentResponse.status_code not in [200, 201, 404]:
                        raise Error(status_code=400, details=json.loads(DeleteK8DeploymentResponse.text))
                    StatusCode = DeleteK8DeploymentResponse.status_code
                    logger.info(f"Delete Deployment Status Code: {DeleteK8DeploymentResponse.status_code}")
                    logger.info(f"Delete Deployment Response: {DeleteK8DeploymentResponse.text}")
                    K8Type = 'deployments'

                    # Check if resources still exist
                    ExitsStatus = db.CheckJobDeploymenExits(url, job_name_with_id, namespace, token, K8Type)
                    if ExitsStatus:
                        logger.info("🔄 Job/Deployment still exists, waiting...")
                        time.sleep(3)

                db.DeleteK8Pods(url, job_name_with_id, namespace, token)


            response = run_job_final_call(
                endpoint=url,
                namespace=namespace,
                payload=run_config,
                token=token,
                cluster_manager=cluster_info_config['cluster_manager'],
                IS_STREAMING=cust_setup_info_data.IS_STREAMING)

            db.UpdateK8UIUrl(url, job_instance_id, job_name_with_id, namespace, token, connection, action='Create')
            responses.append({"job_instance_id": job_id, "status": "success", "response": response})
    return responses


def run_job_final_call(endpoint, payload, cluster_manager, IS_STREAMING=None, namespace=None, token=None):
    response = None
    payload = json.dumps(payload) if isinstance(payload, dict) else payload
    if cluster_manager == 'k8s' and IS_STREAMING == 'N':
        response = db.run_kubernets_batch_job(endpoint, namespace, payload, token)
    elif cluster_manager == 'k8s' and IS_STREAMING == 'Y':
        response = db.start_kubernetes_stream_job(endpoint, namespace, payload, token)
    else:
        response = db.run_standalone_job(cluster_manager, endpoint, payload)
    return response


########################################################################################################################################


def stop_job(request: StopJobRequestSchema, connection: Session):
    # Step 1: Get component and customer info from job_instance_id
    for job_id in request.job_instance_ids:
        cust_setup_info = db.get_job_config_by_job_instance_id_stop(connection, job_id)
        #cust_setup_info = db.get_job_config_by_job_instance_id(connection, request)

        # Step 2: Get cluster configuration for Spark
        cluster_data = db.get_cluster_info_for_customer(
            customer_id=cust_setup_info.customer_id,
            cluster_type=constants.SPARK,
            connection=connection
        )
        cluster_config = json.loads(cluster_data.config or '{}')

        # Validate essential cluster config keys
        if 'master_url' not in cluster_config or 'cluster_manager' not in cluster_config:
            raise Error(status_code=500, details='Incorrect Cluster config. Please contact administrator')

        url = cluster_config['master_url']
        cluster_manager = cluster_config['cluster_manager']
        job_name = cust_setup_info.component_name
        # job_instance_id = request.job_instance_id
        job_instance_id = job_id

        # Step 3: Stop job depending on cluster manager type
        if cluster_manager == 'standalone':  # Fixed typo from 'standlone'
            spark_user = cluster_config.get('spark_ui_user')
            spark_pass = cluster_config.get('spark_ui_password')

            app_id = db.GetAppIDStandalone(url, job_name, spark_user, spark_pass)
            if not app_id:
                raise Error(status_code=400, details={'message': 'Job not found'})

            response = db.KillStandaloneJob(url, app_id, spark_user, spark_pass)
            if response.status_code not in [200, 201]:
                raise Error(status_code=400, details=json.loads(response.text))

            return {'status': 'Job deleted successfully'}

        else:  # Kubernetes-based cluster
            namespace = db.get_namespace_from_job_instance_id(connection, job_instance_id)
            token_uuid = db.get_token_uuid_for_namespace(
                connection,
                namespace=namespace,
                customer_id=cust_setup_info.customer_id
            )

            try:
                # token_encoded = db.getDataFromVault(token_uuid)['responseData']['value']
                # token_encoded = 'ZXlKaGJHY2lPaUpTVXpJMU5pSXNJbXRwWkNJNklqZDJMV3BPVW5SdU5FOTZTQzFYY1V0dGIxZzRVRUpQT0VKR1owVTBlSGhXVEVwTlNYWXphVTEyUmtraWZRLmV5SnBjM01pT2lKcmRXSmxjbTVsZEdWekwzTmxjblpwWTJWaFkyTnZkVzUwSWl3aWEzVmlaWEp1WlhSbGN5NXBieTl6WlhKMmFXTmxZV05qYjNWdWRDOXVZVzFsYzNCaFkyVWlPaUpxYVc4dGFHTnRjQzFrWlNJc0ltdDFZbVZ5Ym1WMFpYTXVhVzh2YzJWeWRtbGpaV0ZqWTI5MWJuUXZjMlZqY21WMExtNWhiV1VpT2lKemNHRnlheTFoWkcwdGRHOXJaVzR0T1hKbk9Hc2lMQ0pyZFdKbGNtNWxkR1Z6TG1sdkwzTmxjblpwWTJWaFkyTnZkVzUwTDNObGNuWnBZMlV0WVdOamIzVnVkQzV1WVcxbElqb2ljM0JoY21zdFlXUnRJaXdpYTNWaVpYSnVaWFJsY3k1cGJ5OXpaWEoyYVdObFlXTmpiM1Z1ZEM5elpYSjJhV05sTFdGalkyOTFiblF1ZFdsa0lqb2lOV1pqTkRGak1qSXRaV00yTXkwME56aGxMV0UxWW1VdE9USTFPVFJoTmpCbE1UZ3hJaXdpYzNWaUlqb2ljM2x6ZEdWdE9uTmxjblpwWTJWaFkyTnZkVzUwT21wcGJ5MW9ZMjF3TFdSbE9uTndZWEpyTFdGa2JTSjkuMFhJWFFOYjl5aFp5V1NkaTJTUXRsX3lZVkdaMnpZd0MxVG9OdjAzVkRBSERKWWhIUlJGZzRPVjRWbWlTb2k2S0hvZ2tPMXVsdjdvbkxOMmlpR3E1STZ6X09CZEh3dVFLNWV5MXItcGZNS2dkNTM0cllWdFpCQjJUdmpaNXctSlZpaDFRTTFnRWNnWFliTTcxSEIzVl9FVTJKd0pXOHFDX1ZEZ3JoeXhTTDRBOXdEQmFDNVVfSmFhVXg0ZGtKcFIyTWVpT3JFbHl1NjB3aWw3VFpxbElzZFVXMXFhNWVMTXlPVDdKWkFValNDekpXcTVaVWZ6NGZKczZFeklXZEtMeUVQMTZkaXR5UmhFdUlCb3pFNF8tS0dJVEtmR204bFNGN0FrSVZLeUlqc05JazJqVGd1OEJOSTVZaklJaDRVYXpRTk80ZFc2LXdaOS1lb1gwY1U3SmVB'
                 token_encoded = 'ZXlKaGJHY2lPaUpTVXpJMU5pSXNJbXRwWkNJNklsVklaRmRvYTFvM1UwdDVUVXhWU2xWeWJXeG5WbVZZUVZKbU9UWjRNVW80VFVWSWNGZzVWVGxEU1dNaWZRLmV5SnBjM01pT2lKcmRXSmxjbTVsZEdWekwzTmxjblpwWTJWaFkyTnZkVzUwSWl3aWEzVmlaWEp1WlhSbGN5NXBieTl6WlhKMmFXTmxZV05qYjNWdWRDOXVZVzFsYzNCaFkyVWlPaUpxYVc4dGFHTnRjQzFrWlMxdlluTmxjblpoWW1sc2FYUjVJaXdpYTNWaVpYSnVaWFJsY3k1cGJ5OXpaWEoyYVdObFlXTmpiM1Z1ZEM5elpXTnlaWFF1Ym1GdFpTSTZJbk53WVhKckxXRmtiUzEwYjJ0bGJpMDVjbWM0YXlJc0ltdDFZbVZ5Ym1WMFpYTXVhVzh2YzJWeWRtbGpaV0ZqWTI5MWJuUXZjMlZ5ZG1salpTMWhZMk52ZFc1MExtNWhiV1VpT2lKemNHRnlheTFoWkcwaUxDSnJkV0psY201bGRHVnpMbWx2TDNObGNuWnBZMlZoWTJOdmRXNTBMM05sY25acFkyVXRZV05qYjNWdWRDNTFhV1FpT2lKaU1HVm1OV0kwT1MxbU1qZGlMVFJoT0RBdFlXWmpZeTB3TUdVd05ERTNOVFF4TTJZaUxDSnpkV0lpT2lKemVYTjBaVzA2YzJWeWRtbGpaV0ZqWTI5MWJuUTZhbWx2TFdoamJYQXRaR1V0YjJKelpYSjJZV0pwYkdsMGVUcHpjR0Z5YXkxaFpHMGlmUS5mUkxybjl0al90ZjRsaUp4TEpEcTNnODJEUlR5eFl5eGVKVlRmMzJrLVRpTUdEbWhweElxbkgyU2ZwRVMzQUlEeWNNNW9FMzV4SjBIbkxMRldfVjhvS3E2cUc3N2FfeXFHR3Jxb0xoSUpkNmlyeHpOdXpNYnJjZkZZT0kxZENvZ2lVUHJ2Qk0wUjU1X0lRTmdGNUloWE9odmZ2d3ZQVnJIMlpvcWJ3RDI5OVF6UmNiaXlkcjdNQTZ0UlVJUnY2cUNBLVI4Rmozc2UzRjdlR1NVczcyd3BNVmFtLVhnVjV6NGxmc3JKc3EyWVotSWRTczFNdkVWQWZpRGJlOFBIOHhWNlY2d1U4RG1vblZDTTc2X3A5YjAxYl9OYWlRc3gxSzA5RkIyaW1tNnpBREZ5dHBWTGw3MFFxMlhyUWxwdVZwa055cVpFQ3FGYXVfUHdoWUZHWFNISUE=' #sit token
                 token = base64.b64decode(token_encoded).decode("utf-8")
                #token = db.get_value_from_cms(token_uuid)
            except Exception as e:
                raise Error(status_code=500, details=f"Failed to fetch token from Vault: {str(e)}")

            # Stop scheduled job (K8 Job) or long-running service (K8 Deployment)
            try:
                if cust_setup_info.IS_STREAMING == 'N':
                    response = db.DeleteK8Job(url, job_name, namespace, token)
                else:
                    response = db.DeleteK8Deployment(url, job_name, namespace, token)
            except RuntimeError as e:
                return JSONResponse(status_code=404, content={"message": str(e)})
            except Exception as e:
                return JSONResponse(status_code=500, content={"message": str(e)})

                # Handle response by status code
            if response.status_code in [200, 201]:
                logger.info(
                    f"Successfully deleted {'Job' if cust_setup_info.is_scheduled == 'Y' else 'Deployment'}: {job_name}")
            elif response.status_code == 404:
                logger.warning(
                    f"{'Job' if cust_setup_info.is_scheduled == 'Y' else 'Deployment'} '{job_name}' not found in namespace '{namespace}'. Assuming already deleted.")
            else:
                # Try to extract error details, fallback to raw text
                try:
                    error_details = json.loads(response.text)
                except json.JSONDecodeError:
                    error_details = {"message": "Unknown error", "raw_response": response.text}

                logger.error(
                    f"Failed to delete {'Job' if cust_setup_info.is_scheduled == 'Y' else 'Deployment'} '{job_name}': {error_details}")
                raise Error(status_code=400, details=error_details)

            # Clean-up pods and update UI URL references
            try:
                result=db.DeleteK8Pods(url, job_name, namespace, token)
                if result is False:
                    return JSONResponse(status_code=404,content={"message": "No matching pods found to delete"})
            except RuntimeError as e:
                return JSONResponse(status_code=404, content={"message": str(e)})
            except Exception as e:
                return JSONResponse(status_code=500, content={"message": str(e)})

            db.UpdateK8UIUrl(
                MasterURL=url,
                action="Delete",
                Namespace=namespace,
                JobInstanceId=job_instance_id,
                ComponentName=job_name,
                token=token,
                connection=connection
            )

            #return {"status": "Job deleted successfully"}
            print(f"Stopping job {job_id}")
    return {"status": "success", "stopped_jobs": request.job_instance_ids}
