from sqlalchemy import Column, Integer, String, DateTime, BLOB, CLOB
from sqlalchemy.ext.declarative import declarative_base
import datetime
from sqlalchemy.sql import func
from sqlalchemy.schema import PrimaryKeyConstraint

Base = declarative_base()

class DeeptraceIndexPattern(Base):
    __tablename__ = 'deeptrace_index_pattern'
    
    seq = Column(Integer(), primary_key=True)
    field_type = Column(String(500))
    field_name = Column(String(500))
    root = Column(String(500))
    status = Column(String(500))
    created_by = Column(String(500))
    created_on = Column(DateTime())
    updated_by = Column(String(500))
    updated_on = Column(DateTime())


class ObsSparkJobDetails(Base):
    __tablename__ = 'obs_spark_job_details'
    
    job_name = Column(String(100), primary_key=True)
    job_owner = Column(String(100), nullable=True)
    job_description = Column(String(500), nullable=True)
    job_type = Column(String(100), nullable=True)

    
class MonClusterMaster(Base):
    __tablename__ = 'mon_cluster_master'

    cluster_id = Column(Integer(), primary_key=True)
    name = Column(String(64), nullable=True)
    category = Column(String(64), nullable=True)
    type = Column(String(64), nullable=True)
    config= Column(CLOB(), nullable=True)
    status = Column(String(64), nullable=True)  
    created_by = Column(String(64), nullable=True)
    created_on = Column(DateTime(), nullable=True, server_default=func.now())
    updated_by = Column(String(64), nullable=True)
    updated_on = Column(DateTime(), nullable=True, onupdate=func.now())


class MonCustomerClusterMap(Base):
    __tablename__ = 'mon_customer_cluster_map'

    cluster_map_id = Column(Integer(), primary_key=True)
    customer_id = Column(Integer(), nullable=True)
    cluster_id =  Column(Integer(), nullable=True)               
    type = Column(String(64), nullable=True)
    config= Column(CLOB(), nullable=True)
    status = Column(String(64), nullable=True)                
    created_by = Column(String(64), nullable=True)
    created_on = Column(DateTime(), nullable=True, server_default=func.now())
    updated_by = Column(String(64), nullable=True)
    updated_on = Column(DateTime(), nullable=True, onupdate=func.now())            
                    
class MonSetupInfo(Base):
    __tablename__ = 'mon_setup_info'

    setup_info_id = Column(Integer(), primary_key=True)
    component_type_id = Column(String(64), nullable=True)
    component_name = Column(String(1000), nullable=True)
    status = Column(String(64), nullable=True)
    config = Column(CLOB(), nullable=True)
    monitoring_component_usage = Column(String(64), nullable=True)
    depends_on = Column(String(64), nullable=True)
    sequence = Column(Integer(), nullable=True)            
    created_by = Column(String(64), nullable=True)
    created_on = Column(DateTime(), nullable=True, server_default=func.now())
    updated_by = Column(String(64), nullable=True)
    updated_on = Column(DateTime(), nullable=True, onupdate=func.now())
    source = Column(String(64), nullable=True)
#     source_ref_id = Column(Integer(), nullable=True) 
    is_scheduled = Column(String(1), nullable=True)
    group_id= Column(Integer(), nullable=True) 
    multiple_instances_allowed= Column(Integer(), nullable=True) 
    scheduled_frequency = Column(String(64), nullable=True)
    base_instance_id = Column(Integer(), nullable=True)
    pipeline_id = Column(Integer(), nullable=True)
#     job_type = Column(String(255), nullable=True)
                    
class MonMetricComponentMap(Base):
    __tablename__ = 'mon_metric_component_map'

    id = Column(Integer(), primary_key=True)  
    source = Column(String(64), nullable=True)
    metric_type = Column(String(64), nullable=True)
    metric_identifier = Column(String(64), nullable=True)
    setup_info_id = Column(Integer(), nullable=True)
    component_type_id = Column(Integer(), nullable=True)
    status = Column(String(64), nullable=True)                                 
    created_by = Column(String(64), nullable=True)
    created_on = Column(DateTime(), nullable=True, server_default=func.now())
    updated_by = Column(String(64), nullable=True)
    updated_on = Column(DateTime(), nullable=True, onupdate=func.now())
                    
class MonConfigPlans(Base):
    __tablename__ = 'mon_config_plans'
                                    
    plan_id = Column(Integer(), primary_key=True)     
    plan_name = Column(String(64), nullable=True)
    plan_description = Column(String(64), nullable=True)
    kafka_policy = Column(String(64), nullable=True)
    elastic_policy = Column(String(64), nullable=True)
    is_default = Column(String(64), nullable=True)
    status = Column(String(64), nullable=True)                
#     spark_stream_policy = Column(CLOB,nullable=True)
#     spark_batch_policy = Column(CLOB,nullable=True)
    spark_policy = Column(CLOB,nullable=True)
    logstash_policy = Column(CLOB,nullable=True)              
    created_by = Column(String(64), nullable=True)
    created_on = Column(DateTime(), nullable=True, server_default=func.now())
    updated_by = Column(String(64), nullable=True)
    updated_on = Column(DateTime(), nullable=True, onupdate=func.now())

class MonCustomerSetupInfo(Base):
    __tablename__ = 'mon_customer_setup_info'

    customer_setup_info_id = Column(Integer(), primary_key=True)
    customer_id = Column(Integer(), nullable=True)
    setup_info_id = Column(Integer(), nullable=True)
    component_type_id = Column(Integer(), nullable=True)
    component_name = Column(String(64), nullable=True)
    status = Column(String(64), nullable=True)
    monitoring_component_usage = Column(String(64), nullable=True)
    config = Column(CLOB,nullable=True)
    sequence = Column(Integer(), nullable=True)
    depends_on = Column(String(64), nullable=True)
    cluster_map_id = Column(Integer(), nullable=True)
    task_status = Column(String(64), nullable=True)
    response_status = Column(CLOB,nullable=True)                               
    created_by = Column(String(64), nullable=True)
    created_on = Column(DateTime(), nullable=True, server_default=func.now())
    updated_by = Column(String(64), nullable=True)
    updated_on = Column(DateTime(), nullable=True, onupdate=func.now())
    source = Column(String(64), nullable=True)
    job_instance_id = Column(String(64), nullable=True)
    driver_id = Column(String(64), nullable=True)
#     source_ref_id = Column(Integer(), nullable=True) 
    is_scheduled = Column(String(1), nullable=True)
    scheduled_id = Column(Integer(), nullable=True) 
    group_id= Column(Integer(), nullable=True) 
    log_type = Column(String(64), nullable=True)
    scheduled_frequency = Column(String(64), nullable=True)
    pre_cust_setup_info_id = Column(Integer(), nullable=True)
    pipeline_id = Column(Integer(), nullable=True)
    run_config = Column(CLOB,nullable= True)
               
class MonCustomerPlan(Base):
    __tablename__ = "mon_customer_plan"

    cust_plan_id = Column(Integer(), primary_key=True)
    customer_id = Column(Integer(), nullable=True)
    plan_id = Column(Integer(), nullable=True)
    status = Column(String(64),nullable=True)                 
    created_by = Column(String(64), nullable=True)
    created_on = Column(DateTime(), nullable=True, server_default=func.now())
    updated_by = Column(String(64), nullable=True)
    updated_on = Column(DateTime(), nullable=True, onupdate=func.now())
    
class MonSetupComponentMaster(Base):
    __tablename__ = "mon_setup_component_master"

    component_type_id = Column(Integer(), primary_key=True)
    component_type = Column(String(64), nullable=True)
    cluster_type = Column(String(64), nullable=True)
    status = Column(String(64),nullable=True)                 
    created_by = Column(String(64), nullable=True)
    created_on = Column(DateTime(), nullable=True, server_default=func.now())
    updated_by = Column(String(64), nullable=True)
    updated_on = Column(DateTime(), nullable=True, onupdate=func.now()) 
    
class PlsToolAttMst(Base):
    __tablename__ = "pls_tool_att_mst"

    tool_att_id = Column(Integer(), primary_key=True)
    att_name = Column(String(64), nullable=True)             
    created_by_id = Column(String(64), nullable=True)
    created_on = Column(DateTime(), nullable=True, server_default=func.now())
    updated_by_id = Column(String(64), nullable=True)
    updated_on = Column(DateTime(), nullable=True, onupdate=func.now()) 
    status = Column(String(64),nullable=True)    
    
class MonSetupProperties(Base):
    __tablename__ = "mon_setup_properties"

    property_id = Column(Integer(), primary_key=True)
    entity = Column(String(50), nullable=True)
    entity_id = Column(Integer(), nullable=True)
    property_name = Column(String(100), nullable=True)
    type = Column(String(20),nullable=True) 
    sql_query = Column(String(4000), nullable=True)
    value = Column(String(1000), nullable=True)
    default_value = Column(String(1000), nullable=True)
    status = Column(String(1),nullable=True) 
    created_by = Column(String(64), nullable=True)
    created_on = Column(DateTime(), nullable=True, server_default=func.now())
    updated_by = Column(String(64), nullable=True)
    updated_on = Column(DateTime(), nullable=True, onupdate=func.now())   

class MonComponentGroupMaster(Base):
    __tablename__ = "mon_component_group_master"

    group_id = Column(Integer(), primary_key=True)
    group_name = Column(String(200), nullable=True)
    config = Column(String(4000), nullable=True)
    status = Column(String(1),nullable=True) 
    enabled = Column(Integer(), nullable=True)
    created_by = Column(String(100), nullable=True)
    created_on = Column(DateTime(), nullable=True, server_default=func.now())
    updated_by = Column(String(100), nullable=True)
    updated_on = Column(DateTime(), nullable=True, onupdate=func.now())   

class PlsClntResAttMap(Base):
    __tablename__ = "pls_clnt_res_att_map"

    clnt_res_att_map_id = Column(Integer(), primary_key=True)
    customer_setup_info_id = Column(Integer(), nullable=True)
    att_id = Column(Integer(), nullable=True)
    att_value = Column(String(500), nullable=True)
    status = Column(String(10),nullable=True)  
    
class MonSetupPropertiesAtt(Base):
    __tablename__ = "mon_setup_properties_att"

    id = Column(Integer(), primary_key=True)
    setup_info_id = Column(Integer(), nullable=True)
#     att = Column(String(500), nullable=True)
    tool_att_id = Column(Integer(), nullable=True) 
    client_maintenance = Column(Integer(), nullable=True)
    status = Column(String(10),nullable=True)  
    created_by = Column(String(100), nullable=True)
    create_on = Column(DateTime(), nullable=True, server_default=func.now())
    updated_by = Column(String(100), nullable=True)
    updated_on = Column(DateTime(), nullable=True, onupdate=func.now()) 
    mandatory_field_ref_id = Column(Integer(), nullable=True) 
    
class PlsSourceMst(Base):
    __tablename__ = "pls_source_mst"

    source_id = Column(Integer(), primary_key=True)
    source_name = Column(String(500), nullable=True)
    client_id = Column(Integer(), nullable=True)
    status = Column(String(10),nullable=True)
    default_source_id = Column(Integer(), nullable=True)
    
class DefaultConfig(Base):
    __tablename__ = "default_config"

    id = Column(Integer(), primary_key=True)
    component_type_id = Column(Integer(), nullable=True)
    config_type = Column(String(500), nullable=True)
    config = Column(CLOB,nullable=True)
    status = Column(String(10),nullable=True)
    
class PlsClntMst(Base):
    __tablename__ = "pls_clnt_mst"

    clnt_mst_id = Column(Integer(), primary_key=True)
    clnt_name = Column(String(500), nullable=True)
    created_by_id = Column(String(64), nullable=True)
    created_on = Column(DateTime(), nullable=True, server_default=func.now())
    updated_by_id = Column(String(64), nullable=True)
    updated_on = Column(DateTime(), nullable=True, onupdate=func.now()) 
    status = Column(String(64),nullable=True) 
    
class HcmpMobProjMst(Base):
    __tablename__ = "hcmp_mob_proj_mst"

    project_id = Column(Integer(), primary_key=True)
    project_desc = Column(String(500), nullable=True)
    status = Column(String(64),nullable=True)
    created_by = Column(String(64), nullable=True)
    created_on = Column(DateTime(), nullable=True, server_default=func.now())
    updated_by = Column(String(64), nullable=True)
    updated_on = Column(DateTime(), nullable=True, onupdate=func.now()) 
    
    
class HcmpServiceProviders(Base):
    __tablename__ = "hcmp_service_providers"

    id = Column(Integer(), primary_key=True)
    name = Column(String(200), nullable=True)
    description = Column(String(1000),nullable=True)
    type = Column(String(50), nullable=True)
    category = Column(String(50),nullable=True)
    code = Column(String(50), nullable=True)
    has_resource_groups = Column(String(64),nullable=True)
    supports_discovery = Column(String(50),nullable=True)
    status = Column(String(50), nullable=True)
    created_by = Column(String(64), nullable=True)
    created_on = Column(DateTime(), nullable=True, server_default=func.now())
    updated_by = Column(String(64), nullable=True)
    updated_on = Column(DateTime(), nullable=True, onupdate=func.now()) 
    icon_path = Column(String(64), nullable=True)
    customer_id = Column(Integer(), nullable=True)
    enabled = Column(String(50), nullable=True)
    provider_prefix_code = Column(String(200),nullable=True)
    is_live = Column(String(50),nullable=True)
    
class MonSourceEntry(Base):
    __tablename__ = "mon_source_entry"

    id = Column(Integer(), primary_key=True)
    module = Column(String(255), nullable=True)
    source = Column(String(255), nullable=True)
    source_ref_id = Column(Integer(), nullable=True) 
    pipeline_desc = Column(String(500), nullable=True)
    status = Column(String(1), nullable=True)
    created_by = Column(String(255), nullable=True)
    created_on = Column(DateTime(), nullable=True, server_default=func.now())
    updated_by = Column(String(255), nullable=True)
    updated_on = Column(DateTime(), nullable=True, onupdate=func.now()) 
    
class HcmpMaPipelineMst(Base):
    __tablename__ = "hcmp_ma_pipeline_mst"

    pipeline_id = Column(Integer(), primary_key=True)
    source = Column(String(255), nullable=True)
#     source_ref_id = Column(Integer(), nullable=True) 
    pipeline_desc = Column(String(500), nullable=True)
    status = Column(String(1), nullable=True)
    created_by = Column(String(255), nullable=True)
    created_on = Column(DateTime(), nullable=True, server_default=func.now())
    updated_by = Column(String(255), nullable=True)
    updated_on = Column(DateTime(), nullable=True, onupdate=func.now()) 
    module_id = Column(Integer(), nullable=True)
    csp_id = Column(Integer(), nullable=True)
    
class PlsJobInsMst(Base):
    __tablename__ = "pls_job_ins_mst"

    JOB_INSTANCE_ID = Column(Integer(), primary_key=True)
    JOB_ID = Column(Integer())
    JOB_INSTANCE_DESCRIPTION = Column(String(100), nullable=True)
    IS_STREAMING = Column(String(1))
    CLIENT_ID = Column(Integer(), nullable=True) 
    status = Column(String(1), nullable=True)
    CREATED_BY_ID = Column(String(100), nullable=True)
    created_on = Column(DateTime(), nullable=True, server_default=func.now())
    UPDATED_BY_ID = Column(String(100), nullable=True)
    updated_on = Column(DateTime(), nullable=True, onupdate=func.now()) 
    IS_LOCKED = Column(String(1), nullable=True)
    RUNNINGINTERVAL = Column(Integer(), nullable=True) 
    CONCURRENCY = Column(Integer(), nullable=True) 
    THRESOLD = Column(Integer(), nullable=True)
    LAG_THRESOLD = Column(Integer(), nullable=True) 
    MODULE_ID = Column(Integer(), nullable=True) 
    ONPREM = Column(Integer(), nullable=True)
    IS_BASE_JOB = Column(String(1), nullable=True)
    SPARKUI = Column(String(1), nullable=True)

class DeeptraceAssetIdMapping(Base):
    __tablename__ = 'deeptrace_asset_id_mapping'

    virtual_id = Column(String(255), primary_key=True)
    asset_id = Column(String(255), nullable=True)
    application_name = Column(String(255), nullable=True)
    application_id = Column(Integer(), nullable=True)
    customer_name = Column(String(255), nullable=True)
    customer_id = Column(Integer(), nullable=True)
    created_by = Column(String(255), nullable=True)
    created_on = Column(DateTime(), nullable=True)
    updated_by = Column(String(255), nullable=True)
    updated_on = Column(DateTime(), nullable=True)
    status = Column(String(255), nullable=True) 
    
class HcmpMaCustPipeline(Base):
    __tablename__ = "hcmp_ma_cust_pipeline"

    cust_pipe_ld = Column(Integer(), primary_key=True)
    customer_id = Column(Integer(), nullable=True)
    pipeline_id = Column(Integer(), nullable=True)
    status = Column(String(1), nullable=True)
    created_by = Column(String(255), nullable=True)
    created_on = Column(DateTime(), nullable=True, server_default=func.now())
    updated_by = Column(String(255), nullable=True)
    updated_on = Column(DateTime(), nullable=True, onupdate=func.now()) 
    
    
class HcmpMaPipelineCompHist(Base):
    __tablename__ = "hcmp_ma_pipeline_comp_hist"

    id = Column(Integer(), primary_key=True)
    customer_id = Column(Integer(), nullable=True)
    pipeline_id = Column(Integer(), nullable=True)
    setup_info_id = Column(Integer(), nullable=True)
    config_prop = Column(CLOB,nullable=True)
    created_by = Column(String(255), nullable=True)
    created_on = Column(DateTime(), nullable=True, server_default=func.now())
    updated_by = Column(String(255), nullable=True)
    updated_on = Column(DateTime(), nullable=True, onupdate=func.now()) 
    success_status = Column(String(255), nullable=True)
    error_desc = Column(String(4000), nullable=True)
    purpose = Column(String(255), nullable=True)
    cust_setup_info_id = Column(Integer(), nullable=True)
    
class HcmpMaCompMandatoryAtt(Base):
    __tablename__ = "hcmp_ma_comp_mandatory_att"

    id = Column(Integer(), primary_key=True)
    component_type_id = Column(Integer(), nullable=True)
    att_id = Column(Integer(), nullable=True)
    status = Column(String(1), nullable=True)
    created_by = Column(String(255), nullable=True)
    created_on = Column(DateTime(), nullable=True, server_default=func.now())
    updated_by = Column(String(255), nullable=True)
    updated_on = Column(DateTime(), nullable=True, onupdate=func.now()) 
    
class MonSetupSubComponentMaster(Base):
    __tablename__ = "mon_setup_sub_component_master"

    config_type_id = Column(Integer(), primary_key=True)
    config_type = Column(String(255), nullable=True)
    component_type_id = Column(Integer(), nullable=True)
    status = Column(String(255), nullable=True)
    created_by = Column(String(255), nullable=True)
    created_on = Column(DateTime(), nullable=True, server_default=func.now())
    updated_by = Column(String(255), nullable=True)
    updated_on = Column(DateTime(), nullable=True, onupdate=func.now()) 
    
class MonComponentConfigMaster(Base):
    __tablename__ = "mon_component_config_master"

    id = Column(Integer(), primary_key=True)
    config_type_id = Column(Integer(), nullable=True)
    plan_id = Column(Integer(), nullable=True)
    config = Column(CLOB,nullable=True)
    status = Column(String(255), nullable=True)
    created_by = Column(String(255), nullable=True)
    created_on = Column(DateTime(), nullable=True, server_default=func.now())
    updated_by = Column(String(255), nullable=True)
    updated_on = Column(DateTime(), nullable=True, onupdate=func.now()) 
    
class ApplicationPods(Base):
    __tablename__ = "application_pods"
    
    pod_name = Column(String(100), primary_key=True)
    application = Column(String(100), nullable=True)
    
class DeeptraceKafkaTopic(Base):
    __tablename__ = "deeptrace_kafka_topic"
    id = Column(Integer(), primary_key=True)
    kafka_topics = Column(String(255), nullable=True)
    description = Column(String(255), nullable=True)
    latest_timestamp = Column(String(255), nullable=True)

class DeeptraceTypeList(Base):
    __tablename__ = "DEEPTRACE_TYPE_LIST"
    
    items = Column(String(100), nullable=False)
    type = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)

    __table_args__ = (
        PrimaryKeyConstraint('items', 'type'),
    )

class PlsMaComponentDep(Base):
    __tablename__ = "pls_ma_component_dep"

    id = Column(Integer(), primary_key=True)
    setup_info_id = Column(Integer())
    dependency_id = Column(Integer())
    status = Column(String(255), nullable=True)
    created_by = Column(String(255), nullable=True)
    created_on = Column(DateTime(), nullable=True, server_default=func.now())
    updated_by = Column(String(255), nullable=True)
    updated_on = Column(DateTime(), nullable=True, onupdate=func.now())
    
class HcmpMaJobGrncConf(Base):
    __tablename__ = "HCMP_MA_JOB_GRNC_CONF"

    gnrc_conf_id = Column(Integer(), primary_key=True)
    cluster_manager = Column(String(255), nullable=True)
    is_streaming = Column(Integer(), nullable=True)
    config = Column(CLOB,nullable=True)
    status = Column(String(255), nullable=True)
    created_by = Column(String(255), nullable=True)
    created_on = Column(DateTime(), nullable=True, server_default=func.now())
    updated_by = Column(String(255), nullable=True)
    updated_on = Column(DateTime(), nullable=True, onupdate=func.now()) 
    
class HcmpMaJobConfReplacements(Base):
    __tablename__ = "hcmp_ma_job_conf_replacements"

    replacement_id = Column(Integer(), primary_key=True)
    job_id = Column(Integer(), nullable=True)
    cluster_manager = Column(String(255),nullable=True)
    is_streaming = Column(Integer(),nullable=True)
    clusterid = Column(Integer(),nullable=True)
    replacement_key = Column(String(4000), nullable=True)
    replacement_value = Column(String(4000), nullable=True)
    status = Column(String(255), nullable=True)
    created_by = Column(String(255), nullable=True)
    created_on = Column(DateTime(), nullable=True, server_default=func.now())
    updated_by = Column(String(255), nullable=True)
    updated_on = Column(DateTime(), nullable=True, onupdate=func.now()) 
    
class PlsJobNamespace(Base):
    __tablename__ = "pls_job_namespace"

    job_ns_id = Column(Integer(), primary_key=True)
    module_id = Column(Integer())
    namespace = Column(String(255))
    token_uuid = Column(String(4000), nullable=True)
    status = Column(String(255), nullable=True)
    created_by = Column(String(255), nullable=True)
    created_on = Column(DateTime(), nullable=True, server_default=func.now())
    updated_by = Column(String(255), nullable=True)
    updated_on = Column(DateTime(), nullable=True, onupdate=func.now()) 
    
class PlsMaClusterNamespaceUuid(Base):
    __tablename__ = "pls_ma_cluster_namespace_uuid"

    id = Column(Integer(), primary_key=True)
    clusterid = Column(Integer(),nullable=True)
    namespace = Column(String(255))
    uuid = Column(String(255), nullable=True)
    status = Column(String(255), nullable=True)
    created_by = Column(String(255), nullable=True)
    created_on = Column(DateTime(), nullable=True, server_default=func.now())
    updated_by = Column(String(255), nullable=True)
    updated_on = Column(DateTime(), nullable=True, onupdate=func.now()) 


class PLS_CLNT_CON_STR_ATTR(Base):
    __tablename__ = "PLS_CLNT_CON_STR_ATTR"
    ATTRIBUTE_ID = Column(Integer(), primary_key=True)
    CONNECTION_ATT_MASTER_ID = Column(Integer(),nullable=True)
    CONNECTION_STRING_ID = Column(Integer(),nullable=True)
    VALUE = Column(String(255), nullable=True)


class PLS_CON_ATTR_MST(Base):
    __tablename__ = "PLS_CON_ATTR_MST"
    CONNECTION_ATT_MASTER_ID = Column(Integer(), primary_key=True)
    KEY = Column(String(255), nullable=True)
    LOGSTASH_KEY = Column(String(255), nullable=True)
    IS_CMS = Column(String)
    IS_FILE = Column(String)
    IS_ENCRYPTED = Column(String)


class PLS_CLNT_CON_STR_MST(Base):
    __tablename__ = "PLS_CLNT_CON_STR_MST"
    CONNECTION_STRING_ID = Column(Integer(), primary_key=True)
    DESCRIPTION = Column(String(255), nullable=True)
    CLIENT_ID = Column(Integer(), primary_key=True)