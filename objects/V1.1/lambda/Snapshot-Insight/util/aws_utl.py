# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import os
import boto3
import botocore
import time
from datetime import datetime
import re
import json
from botocore.config import Config
import sys
from sys import exc_info
from traceback import format_exception
from botocore.exceptions import ClientError



account_id=boto3.client("sts").get_caller_identity().get("Account")
region=os.environ['AWS_REGION']


#Permitted Operation
# ebs='ebs'
# rds_ins = 'rds_ins'
# rds_cls = 'rds_cls'
# skip = 'skip'

rds_ins=os.environ['RDS_INS_OPS']
rds_cls=os.environ['RDS_CLS_OPS']
skip=os.environ['SKIP_OPS']
ssm_exc_acnt_arn=os.environ['EXCLUDED_ACCOUNTS']



def get_account_id():
    return account_id
    
        
def get_region():
    return region
    
def get_arn_prefix(service_name,source_region):
    """
    Returns the ARN prefix for the given service name.
    """
    return f"arn:aws:{service_name}:{source_region}:{account_id}"

def log(cw_client,log_group_name, log_stream_name, log_message):
    try:
        # TODO: write code..
        #Getting last sequence token
        response = cw_client.describe_log_streams(logGroupName=log_group_name,logStreamNamePrefix=log_stream_name)
        
        log_event = {
            'logGroupName': log_group_name,
            'logStreamName': log_stream_name,
            'logEvents': [
                {
                    'timestamp': int(round(time.time() * 1000)),
                    'message': log_message
                },
            ],
        }
        
        #Adding last sequence token to log event before sending logs if it exists
        if 'uploadSequenceToken' in response['logStreams'][0]:
            log_event.update(
                {'sequenceToken': response['logStreams'][0]['uploadSequenceToken']})
    
        # print("logs to send : ", log_event)
        response = cw_client.put_log_events(**log_event)
    except :
        return None
    

def create_log_stream(cw_client,LOG_GROUP_NAME,LOG_STREAM_NAME,prefix):
  dt = datetime.utcnow()
  LOG_STREAM_NAME="Orphaned-Resources-{:0>4d}{:0>2d}{:0>2d}-{:0>2d}{:0>2d}{:0>2d}.{:0>6d}"
  LOG_STREAM_NAME=prefix+"|"+LOG_STREAM_NAME.format(dt.year, dt.month, dt.day,dt.hour,dt.minute,dt.second,dt.microsecond)
#   print(LOG_STREAM_NAME)
  cw_client.create_log_stream(logGroupName=LOG_GROUP_NAME, logStreamName=LOG_STREAM_NAME) 
  return LOG_STREAM_NAME   


# Get Key Value from Dict
def is_key_exists(d, key):
    if key in d:
        return d[key]
    for k, v in d.items():
        if isinstance(v, dict):
            result = is_key_exists(v, key)
            if result is not None:
                return result
    return None

# Get root DbiResourceId - Cross region copied snapshot edge case handle
def getDbiResourceId(ops,rds_clnt,src_snpid,src_region,dbi_rsrcid,cw_rds_client,LOG_GROUP_NAME, LOG_STREAM_NAME):
    global rds_ins,rds_cls
    rds_client      =  rds_clnt
    src_snp_id      =  src_snpid
    source_region   =  src_region
    dbi_rsrc_id     =  dbi_rsrcid
    
    log(cw_rds_client,LOG_GROUP_NAME, LOG_STREAM_NAME,f'Inside getDbiResourceId : src_snp_id: {src_snp_id} source_region: {source_region} dbi_rsrc_id: {dbi_rsrc_id}')
    
    while dbi_rsrc_id == None :
        regional_config = Config(
                        region_name=source_region,
                        retries = {
                                      'max_attempts': 10,
                                      'mode': 'standard'
                                  }
                          )    
        rds_client = boto3.client('rds',region_name=source_region, config=regional_config,endpoint_url=f'https://rds.{source_region}.amazonaws.com')
              
        if ops == rds_ins:
              src_snp_dtl = rds_client.describe_db_snapshots(DBSnapshotIdentifier=src_snp_id,SnapshotType='manual',IncludeShared=False,IncludePublic=False)['DBSnapshots']
              
              if len(src_snp_dtl) > 0:
                if is_key_exists(src_snp_dtl[0],'DbiResourceId'):
                  dbi_rsrc_id = src_snp_dtl[0]['DbiResourceId']
                else:
                  log(cw_rds_client,LOG_GROUP_NAME, LOG_STREAM_NAME,f'Inside While Loop : response {src_snp_dtl} ')
                  dbi_rsrc_id = None
                  source_region = src_snp_dtl[0]['SourceRegion']
                  src_snp_id = src_snp_dtl[0]['SourceDBSnapshotIdentifier'].split(':')[-1]
              else:
                dbi_rsrc_id ="Snapshot Lineage Broken. Consider it orphan" 
                
        if ops == rds_cls:
              src_snp_dtl = rds_client.describe_db_cluster_snapshots(DBClusterSnapshotIdentifier=src_snp_id,SnapshotType='manual',IncludeShared=False,IncludePublic=False)['DBClusterSnapshots']
              
              if len(src_snp_dtl) > 0:
                if is_key_exists(src_snp_dtl[0],'DbClusterResourceId'):
                  dbi_rsrc_id = src_snp_dtl[0]['DbClusterResourceId']
                else:
                  log(cw_rds_client,LOG_GROUP_NAME, LOG_STREAM_NAME,f'Inside While Loop : response {src_snp_dtl} ')
                  dbi_rsrc_id = None
                  source_region = src_snp_dtl[0]['SourceDBClusterSnapshotArn'].split(":")[3]
                  src_snp_id = src_snp_dtl[0]['SourceDBClusterSnapshotArn'].split(':')[-1]
              else:
                dbi_rsrc_id ="Snapshot Lineage Broken. Consider it orphan"         
    
    return (rds_client,src_snp_id,source_region,dbi_rsrc_id)
    


# python method to upload raw json to monitoring S3 raw bucket
def upload_to_s3(bucket_name, key, content):
    result_str=""
    try:
        region=None
        region_output=boto3.client('s3').get_bucket_location(Bucket=bucket_name)
        if is_key_exists(region_output,'LocationConstraint'):
            if region_output.get('LocationConstraint') is not None :
                region=region_output.get('LocationConstraint')
        
        
        if region is None:
            region='us-east-1'
            
        regional_config = Config(
                                  region_name=region,
                                  retries = {
                                                'max_attempts': 10,
                                                'mode': 'standard'
                                             }
                                    )
                                    
        endpoint_url=f'https://s3.{region}.amazonaws.com'
        # endpoint_url=f'http://{bucket_name}.s3-website.{region}.amazonaws.com'
        # s3 = boto3.client('s3',region_name=region, config=regional_config,endpoint_url=endpoint_url)
        s3 = boto3.client('s3',region_name=region, config=regional_config)
        s3.put_object(
              Body=json.dumps(content, indent=2).encode('utf-8'),
              Bucket=bucket_name,
              Key=key
          )
        result_str="Orphan Resources File Uploaded Successfully"
        return result_str
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchBucket':
            error_msg=f"{bucket_name} Bucket doesnot exists"
        
            etype, value, tb = exc_info()
            info, error = format_exception(etype, value, tb)[-2:]
            error_msg= f'{error_msg} - Details :\n{info}\n{error}'
            print(error_msg)
            
            return None
        else:
            error_msg="Unexpected error at upload_to_s3:"+ str(sys.exc_info()[0])
        
            etype, value, tb = exc_info()
            info, error = format_exception(etype, value, tb)[-2:]
            error_msg= f'{error_msg} - Details :\n{info}\n{error}'
            print(error_msg)
            
            return None 



    

# if __name__=='__main__':
#     print(get_ins_img_id('Created by CreateImage(i-05c0260237c720454) for ami-0be1b9cd8c398fa84'))