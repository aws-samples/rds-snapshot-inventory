# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import boto3
import json
import sys
import util
import datetime

from sys import exc_info
from traceback import format_exception
from botocore.config import Config

from util.aws_utl import get_arn_prefix,log,is_key_exists,getDbiResourceId
import util.aws_utl



#Method to validate source RDS Instance. Return False if RDS Instace not found
def is_ins_valid(rds_clnt,cw_rds_client,LOG_GROUP_NAME, LOG_STREAM_NAME,instance_id,dbi_rsrcId,src_region,snap_crt_time,src_db_snap_id):
    rds_ins_dict=dict()
    db_instance_crt_time=datetime
    result=bool
    functionName = sys._getframe().f_code.co_name
    # log(cw_rds_client,LOG_GROUP_NAME, LOG_STREAM_NAME,f'Calling Function: {functionName} ********** ')
    # log(cw_rds_client,LOG_GROUP_NAME, LOG_STREAM_NAME,f'DB Instance ID: {instance_id}') 
    # log(cw_rds_client,LOG_GROUP_NAME, LOG_STREAM_NAME,f'DB Snapshot Create Time: {snap_crt_time} Type {type(snap_crt_time)}') 
    source_region = src_region
    dbi_rsrc_id   = dbi_rsrcId
    rds_client    = rds_clnt
    src_snp_id    = src_db_snap_id
    
    log(cw_rds_client,LOG_GROUP_NAME, LOG_STREAM_NAME,f'Initial DB Instance ID: {instance_id} source_region {source_region} DB Rsrc ID: {dbi_rsrc_id} Src DB Snap Id : {src_db_snap_id} ')     
    
    try:
        
        # find DbiResourceId from snapshot lineage, -Cross region copied snapshot edge case handle
        # if dbi_rsrc_id == None:
        #   rds_client,src_snp_id,source_region,dbi_rsrc_id = getDbiResourceId(util.aws_utl.rds_ins,rds_client,src_snp_id,source_region,dbi_rsrc_id,cw_rds_client,LOG_GROUP_NAME, LOG_STREAM_NAME)
        
        if not instance_id.startswith('arn'):
            instance_arn=get_arn_prefix('rds',source_region)+':db:'+instance_id 
        else:
            instance_arn=instance_id
        
        log(cw_rds_client,LOG_GROUP_NAME, LOG_STREAM_NAME,f'Derived DB Instance ARN: {instance_arn} source_region {source_region} DB-Rsrc-ID: {dbi_rsrc_id} Src-DB-Snap-Id : {src_snp_id} ')     
        
        
        response = rds_client.describe_db_instances(Filters=[{'Name': 'dbi-resource-id','Values': [str(dbi_rsrc_id)]},])
        # response = rds_client.describe_db_instances(DBInstanceIdentifier=instance_arn)
        
        # log(cw_rds_client,LOG_GROUP_NAME, LOG_STREAM_NAME,f'response describe_db_instances Length: {len(response["DBInstances"])} ') 
        # Return False if No DB exists
        if len(response["DBInstances"]) == 0:
          result=False
          return (result,rds_ins_dict)
        
        # log(cw_rds_client,LOG_GROUP_NAME, LOG_STREAM_NAME,f'response describe_db_instances: {response} ') 
        for i in range(len(response["DBInstances"])):
          if response["DBInstances"][i]["DBInstanceIdentifier"] != "" :
            db_instance= response['DBInstances'][i]['DBInstanceIdentifier']
            res_dbi_rsrc_id = response['DBInstances'][i]['DbiResourceId']
            db_instance_crt_time= response['DBInstances'][i]['InstanceCreateTime']
            rds_ins_dict[instance_id]=response["DBInstances"][i]
            log(cw_rds_client,LOG_GROUP_NAME, LOG_STREAM_NAME,f"Derived DB Instance: {db_instance } DB-Rescrc-Id: {res_dbi_rsrc_id}")
            
            
            # if instance_id == db_instance :
            if res_dbi_rsrc_id == dbi_rsrc_id:  
              # log(cw_rds_client,LOG_GROUP_NAME, LOG_STREAM_NAME,f'DB Instance Create Time: {db_instance_crt_time} Type {type(db_instance_crt_time)}' ) 
              #Handle edge case where New Instance with same name as Old instance
              if snap_crt_time < db_instance_crt_time:
                log(cw_rds_client,LOG_GROUP_NAME, LOG_STREAM_NAME,'New Instance with same name as Old instance')
                result=False
                return (result,rds_ins_dict)
              else:
                result=True
                return (result,rds_ins_dict)
            else:
              result=False
              return (result,rds_ins_dict)
          else : 
            result=False
            return (result,rds_ins_dict)
    except :
        error_msg=f"Unexpected error at: {functionName} "+ str(sys.exc_info()[0])
        
        etype, value, tb = exc_info()
        info, error = format_exception(etype, value, tb)[-2:]
        error_msg= f'{error_msg} - Details :\n{info}\n{error}'
        
        log(cw_rds_client,LOG_GROUP_NAME, LOG_STREAM_NAME,error_msg)
        result=False
        return (result,rds_ins_dict)   

# if __name__=='__main__':
#     print(is_ins_valid('database-1'))