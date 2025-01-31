# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import boto3
import json
import sys
import pprint
import util
import datetime

from sys import exc_info
from traceback import format_exception

# sys.path.append("../../..")
from util.aws_utl import get_arn_prefix,log,is_key_exists,getDbiResourceId
import util.aws_utl


#Method to validate source RDS Cluster. Return False if RDS Cluster not found
def is_cluster_valid(rds_clnt,cw_client,LOG_GROUP_NAME, LOG_STREAM_NAME,cluster_id,dbi_cls_rsrcId,src_region,snap_crt_time,src_db_cls_snap_id):
    rds_cls_dict=dict()
    db_cluster_crt_time=datetime
    result=bool

    
    functionName = sys._getframe().f_code.co_name
    # log(cw_client,LOG_GROUP_NAME, LOG_STREAM_NAME,f'Calling Function: {functionName} ********** ')
    # log(cw_client,LOG_GROUP_NAME, LOG_STREAM_NAME,f'DB Custer ID: {cluster_id}') 
    # log(cw_client,LOG_GROUP_NAME, LOG_STREAM_NAME,f'DB Snapshot Create Time: {snap_crt_time} Type {type(snap_crt_time)}')
    source_region     = src_region
    dbi_cls_rsrc_id   = dbi_cls_rsrcId
    rds_client        = rds_clnt
    src_snp_id        = src_db_cls_snap_id
    
    log(cw_client,LOG_GROUP_NAME, LOG_STREAM_NAME,f'Initial DB Cluster ID: {cluster_id} snapshotsource_region {source_region} DB-Cls-Rsrc-ID: {dbi_cls_rsrc_id} Src-DB-Cls-Snap-Id : {src_db_cls_snap_id} ')     
    
    try:
        # find DbiResourceId from snapshot lineage, -Cross region copied snapshot edge case handle
        # if dbi_cls_rsrcId == None:
        #   rds_client,src_snp_id,source_region,dbi_cls_rsrc_id = getDbiResourceId(util.aws_utl.rds_cls,rds_client,src_snp_id,source_region,dbi_cls_rsrc_id,cw_client,LOG_GROUP_NAME, LOG_STREAM_NAME)
        
        if not cluster_id.startswith('arn'):
            cluster_arn=get_arn_prefix('rds',source_region)+':cluster:'+cluster_id
        else:
            cluster_arn=cluster_id
    
        log(cw_client,LOG_GROUP_NAME, LOG_STREAM_NAME,f'Derived DB Cluster ARN: {cluster_arn} source_region {source_region} DB-Cls-Rsrc-ID: {dbi_cls_rsrc_id} Src-DB-Cls-Snap-Id : {src_snp_id} ') 
        
        # response = rds_client.describe_db_clusters(DBClusterIdentifier=cluster_arn)
        response = rds_client.describe_db_clusters(Filters=[{'Name': 'db-cluster-resource-id','Values': [str(dbi_cls_rsrc_id)]},])
        
        # Return False if No DB exists
        if len(response["DBClusters"]) == 0:
          result=False
          return (result,rds_cls_dict)
        
        # log(cw_client,LOG_GROUP_NAME, LOG_STREAM_NAME,f' Response: {response}')
        for i in range(len(response["DBClusters"])):
          # log(cw_client,LOG_GROUP_NAME, LOG_STREAM_NAME,f'Response<=: {response["DBClusters"][i]["DBClusterIdentifier"]}')
          if response["DBClusters"][i]["DBClusterIdentifier"] != "":
            db_cluster= response['DBClusters'][i]['DBClusterIdentifier']
            res_dbi_rsrc_id = response['DBClusters'][i]['DbClusterResourceId']
            db_cluster_crt_time = response['DBClusters'][i]['ClusterCreateTime']
            rds_cls_dict[cluster_id]=response["DBClusters"][i]
            log(cw_client,LOG_GROUP_NAME, LOG_STREAM_NAME,f"Derived DB Name: {response['DBClusters'][i]['DBClusterIdentifier'] }")
            

            # if cluster_id == db_cluster :
            if res_dbi_rsrc_id == dbi_cls_rsrc_id: 
              # log(cw_client,LOG_GROUP_NAME, LOG_STREAM_NAME,f'DB Cluster Create Time: {db_cluster_crt_time} Type {type(db_cluster_crt_time)}' ) 
              #Handle edge case where New Cluster with same name as Old Cluster
              if snap_crt_time < db_cluster_crt_time:
                log(cw_client,LOG_GROUP_NAME, LOG_STREAM_NAME,'New Cluster with same name as Old Cluster')
                result=False
                return (result,rds_cls_dict)
              else:
                result=True
                return (result,rds_cls_dict)
            else:
              result=False
              return (result,rds_cls_dict)
          else:
              result=False
              return (result,rds_cls_dict)    
    except :
        error_msg=f"Unexpected error at: {functionName} "+ str(sys.exc_info()[0])
        
        etype, value, tb = exc_info()
        info, error = format_exception(etype, value, tb)[-2:]
        error_msg= f'{error_msg} - Details :\n{info}\n{error}'
        
        # log(cw_client,LOG_GROUP_NAME, LOG_STREAM_NAME,error_msg)  
        result=False
        return (result,rds_cls_dict)  

# if __name__=='__main__':
#     print(is_cluster_valid('database-5'))