# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import os
import datetime
import botocore
import boto3
import re
import sys
import json
import logging
import gzip
from sys import exc_info
from traceback import format_exception

logger = logging.getLogger()


from botocore.exceptions import ClientError
from botocore.config import Config

global_config = Config(
                 retries = {
                    'max_attempts': 10,
                    'mode': 'standard'
                 }
              )

    
from db.rds_ins.is_valid_rds_ins import is_ins_valid 
from db.rds_cluster.is_valid_rds_cluster import is_cluster_valid
from util.aws_utl import log,create_log_stream,is_key_exists,upload_to_s3
import util.aws_utl

#Create log group and log stream from AWS Console and replace the name below

# LOG_GROUP_NAME = "/aws/lambda/Snapshot-Insight"
LOG_GROUP_NAME = os.environ['LOG_GROUP']

LOG_STREAM_NAME = ""

cw_client  = boto3.client('logs', config=global_config)
# boto3 create cloudwatch log group
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/logs.html#CloudWatchLogs.Client.create_log_group
try:
    cw_client.create_log_group(logGroupName=LOG_GROUP_NAME)
except Exception as e:
  None

# SSM Parameter Store
ssm_client = boto3.client('ssm')

#Method to derive orphan snapshots related to RDS Instance
def rds_ins(rds_client,param_region,cw_strm_prefix):
  """
  List all the Orphan Snapshots for RDS - Instance.
  """
  # Create Log Stream
  global LOG_STREAM_NAME
  LOG_STREAM_NAME=create_log_stream(cw_client,LOG_GROUP_NAME,LOG_STREAM_NAME,cw_strm_prefix)  
  status_code=400
  
  try:
    
    rds_ins_paginator = rds_client.get_paginator('describe_db_snapshots')
    rds_ins_iterator  = rds_ins_paginator.paginate(
                                                  SnapshotType='manual',
                                                  IncludeShared=False,
                                                  IncludePublic=False)
    

    
    msg=""
    iter=1
    rds_ins_snap_dict=dict()
    rds_ins_dict=dict()
    json_array=[]
    # DB Instance Snapshots
    for db_res_inst in rds_ins_iterator:
      log(cw_client,LOG_GROUP_NAME, LOG_STREAM_NAME,f'db_res_inst : {db_res_inst}')
      for i in range(len(db_res_inst["DBSnapshots"])):
        if db_res_inst["DBSnapshots"][i]["DBInstanceIdentifier"] != "" and is_key_exists(db_res_inst['DBSnapshots'][i],'DbiResourceId'):
          if db_res_inst['DBSnapshots'][i] ['Status']== "available":
            rds_ins_dict=dict()
            
            ins_id= db_res_inst['DBSnapshots'][i]['DBInstanceIdentifier']
            dbi_rsrc_id = None
            snap_id = db_res_inst['DBSnapshots'][i]['DBSnapshotIdentifier']
            snap_crt_time = db_res_inst['DBSnapshots'][i]['SnapshotCreateTime']
            dbi_rsrc_id = db_res_inst['DBSnapshots'][i]['DbiResourceId']
            #Cross region copied snapshot edge case handle
            # Having if since DbiResourceId does not exists for cross region snapshot copy
            # if is_key_exists(db_res_inst['DBSnapshots'][i],'DbiResourceId'):
            #   dbi_rsrc_id = db_res_inst['DBSnapshots'][i]['DbiResourceId']
            rds_clnt=rds_client
            source_region = param_region
            src_db_snap_id = None
            # if is_key_exists(db_res_inst['DBSnapshots'][i],'SourceRegion') and is_key_exists(db_res_inst['DBSnapshots'][i],'SourceDBSnapshotIdentifier') :
            #   source_region = db_res_inst['DBSnapshots'][i]['SourceRegion']
            #   src_db_snap_id = db_res_inst['DBSnapshots'][i]['SourceDBSnapshotIdentifier'].split(':')[-1]
            # if source_region!=param_region:
            #    regional_config = Config(
            #             region_name=source_region,
            #             retries = {
            #                           'max_attempts': 10,
            #                           'mode': 'standard'
            #                       }
            #               )
                          
            #    rds_clnt = boto3.client('rds',region_name=source_region, config=regional_config,endpoint_url=f'https://rds.{source_region}.amazonaws.com')
              
            log(cw_client,LOG_GROUP_NAME, LOG_STREAM_NAME,f'>>>>> snap_id : {snap_id} instance_id : {ins_id} DBI-Rsrc-ID: {dbi_rsrc_id} snapshot_source_region: {source_region} src_db_snap_id: {src_db_snap_id}')
            valid_rds_ins,rds_ins_dict[ins_id]=is_ins_valid(rds_clnt,cw_client,LOG_GROUP_NAME, LOG_STREAM_NAME,ins_id,dbi_rsrc_id,source_region,snap_crt_time,src_db_snap_id)
            
            if not valid_rds_ins:
              msg=msg+"\n"+f"[{iter}] - Snapshot Name: {db_res_inst['DBSnapshots'][i]['DBSnapshotIdentifier']} || Type: {db_res_inst['DBSnapshots'][i]['SnapshotType']} || Status: {db_res_inst['DBSnapshots'][i]['Status']} || DBInstance: {db_res_inst['DBSnapshots'][i]['DBInstanceIdentifier']} || Snapshot ARN: {db_res_inst['DBSnapshots'][i]['DBSnapshotArn']}"
              iter=iter+1
              l=db_res_inst["DBSnapshots"][i]
              rds_ins_snap_dict[snap_id]=db_res_inst["DBSnapshots"][i]
              
              if is_key_exists(rds_ins_snap_dict,'SnapshotCreateTime'):         rds_ins_snap_dict[snap_id]["SnapshotCreateTime"]          = rds_ins_snap_dict[snap_id]["SnapshotCreateTime"].isoformat()
              if is_key_exists(rds_ins_snap_dict,'InstanceCreateTime'):         rds_ins_snap_dict[snap_id]["InstanceCreateTime"]          = rds_ins_snap_dict[snap_id]["InstanceCreateTime"].isoformat()
              if is_key_exists(rds_ins_snap_dict,'OriginalSnapshotCreateTime'): rds_ins_snap_dict[snap_id]["OriginalSnapshotCreateTime"]  = rds_ins_snap_dict[snap_id]["OriginalSnapshotCreateTime"].isoformat()
              if is_key_exists(rds_ins_snap_dict,'SnapshotDatabaseTime'):       rds_ins_snap_dict[snap_id]["SnapshotDatabaseTime"]        = rds_ins_snap_dict[snap_id]["SnapshotDatabaseTime"].isoformat()
  
              
              rds_ins_snap_dict[snap_id]["rds_ins_detail"]= []
              
              if (len(rds_ins_dict[ins_id])) > 0:
                if is_key_exists(rds_ins_dict,'AutomaticRestartTime'):          rds_ins_dict[ins_id][ins_id]["AutomaticRestartTime"]                                  = rds_ins_dict[ins_id][ins_id] ["AutomaticRestartTime"].isoformat() 
                if is_key_exists(rds_ins_dict,'InstanceCreateTime'):            rds_ins_dict[ins_id][ins_id]["InstanceCreateTime"]                                    = rds_ins_dict[ins_id][ins_id] ["InstanceCreateTime"].isoformat() 
                if is_key_exists(rds_ins_dict,'ResumeFullAutomationModeTime'):  rds_ins_dict[ins_id][ins_id]["PendingModifiedValues"]["ResumeFullAutomationModeTime"] = rds_ins_dict[ins_id][ins_id] ["PendingModifiedValues"]["ResumeFullAutomationModeTime"].isoformat() 
                if is_key_exists(rds_ins_dict,'ResumeFullAutomationModeTime'):  rds_ins_dict[ins_id][ins_id]["ResumeFullAutomationModeTime"]                          = rds_ins_dict[ins_id][ins_id] ["ResumeFullAutomationModeTime"].isoformat() 
                if is_key_exists(rds_ins_dict,'LatestRestorableTime'):          rds_ins_dict[ins_id][ins_id]["LatestRestorableTime"]                                  = rds_ins_dict[ins_id][ins_id] ["LatestRestorableTime"].isoformat() 
                if is_key_exists(rds_ins_dict,'ValidTill'):                     rds_ins_dict[ins_id][ins_id]["CertificateDetails"]["ValidTill"]                       = rds_ins_dict[ins_id][ins_id] ["CertificateDetails"]["ValidTill"].isoformat() 
                
                
                rds_ins_snap_dict[snap_id]["rds_ins_detail"].append(rds_ins_dict[ins_id][ins_id])
                
              json_array.append(rds_ins_snap_dict[snap_id])
            
          
    if msg !="":
      log_msg="\n"
      log_msg=log_msg+"\n"
      log_msg=log_msg+f"="*50
      log_msg=log_msg+"\n"+f"*"*5+ " Orphaned RDS Instance Snapshot Details "+ "*"*5
      log_msg=log_msg+"\n"+f"="*50
      log_msg=log_msg+"\n"+msg
      log(cw_client,LOG_GROUP_NAME, LOG_STREAM_NAME,log_msg)
      # log(cw_client,LOG_GROUP_NAME, LOG_STREAM_NAME,f"{rds_ins_snap_dict}")
      
      
      
      status_code=200
      return {
        'statusCode': status_code,
        'body': json_array
      }
      
  except botocore.exceptions.ClientError as e:
        
        error_msg="botocore Unexpected error at rds_ins:"+ str(e) 
        
        etype, value, tb = exc_info()
        info, error = format_exception(etype, value, tb)[-2:]
        error_msg= f'{error_msg} - Details :\n{info}\n{error}'
        
        log(cw_client,LOG_GROUP_NAME, LOG_STREAM_NAME,error_msg)  
        status_code=400
        return {
          'statusCode': status_code,
          'body': error_msg
        }
  except:
        error_msg="Unexpected error at rds_ins:"+ str(sys.exc_info()[0])
        
        etype, value, tb = exc_info()
        info, error = format_exception(etype, value, tb)[-2:]
        error_msg= f'{error_msg} - Details :\n{info}\n{error}'
        
        log(cw_client,LOG_GROUP_NAME, LOG_STREAM_NAME,error_msg) 
        status_code=400
        return {
          'statusCode': status_code,
          'body': error_msg
        }

#Method to derive orphan snapshots related to RDS Cluster
def rds_cls(rds_client,param_region,cw_strm_prefix):
  """
  List all the Orphan Snapshots for RDS - Cluster.
  """ 
  # Create Log Stream
  global LOG_STREAM_NAME
  LOG_STREAM_NAME=create_log_stream(cw_client,LOG_GROUP_NAME,LOG_STREAM_NAME,cw_strm_prefix)
  status_code=400
  
  try:
    # # DB Cluster Snapshots 
    
    rds_cls_paginator = rds_client.get_paginator('describe_db_cluster_snapshots')
    rds_cls_iterator  = rds_cls_paginator.paginate(
                                          SnapshotType='manual',
                                          IncludeShared=False,
                                          IncludePublic=False)
    
    msg=""
    iter=1
    rds_cls_snap_dict=dict()
    rds_cls_dict=dict()
    json_array=[]
    
    for db_res_cstr in rds_cls_iterator:
      log(cw_client,LOG_GROUP_NAME, LOG_STREAM_NAME,f'db_res_cstr : {db_res_cstr}')
      for i in range(len(db_res_cstr["DBClusterSnapshots"])):
        if db_res_cstr["DBClusterSnapshots"][i]["DBClusterIdentifier"] != "" and is_key_exists(db_res_cstr['DBClusterSnapshots'][i],'DbClusterResourceId'):
          if db_res_cstr['DBClusterSnapshots'][i] ['Status']== "available":
              rds_cls_dict=dict()
              
              cluster_id= db_res_cstr['DBClusterSnapshots'][i]['DBClusterIdentifier']
              dbi_cls_rsrc_id = None
              snap_id=db_res_cstr['DBClusterSnapshots'][i]['DBClusterSnapshotIdentifier']
              snap_crt_time = db_res_cstr['DBClusterSnapshots'][i]['SnapshotCreateTime']
              dbi_cls_rsrc_id = db_res_cstr['DBClusterSnapshots'][i]['DbClusterResourceId']
              #Cross region copied snapshot edge case handle
              # Having if since DbiResourceId does not exists for cross region snapshot copy
              # if is_key_exists(db_res_cstr['DBClusterSnapshots'][i],'DbClusterResourceId'):
              #   dbi_cls_rsrc_id = db_res_cstr['DBClusterSnapshots'][i]['DbClusterResourceId']
              
              source_region=param_region
              rds_clnt=rds_client
              src_db_cls_snap_id = None
              # if is_key_exists(db_res_cstr['DBClusterSnapshots'][i],'SourceDBClusterSnapshotArn'):
              #    source_region=db_res_cstr['DBClusterSnapshots'][i]['SourceDBClusterSnapshotArn'].split(":")[3]
              #    src_db_cls_snap_id=db_res_cstr['DBClusterSnapshots'][i]['SourceDBClusterSnapshotArn'].split(":")[-1]
              # if source_region!=param_region:
              #    regional_config = Config(
              #             region_name=source_region,
              #             retries = {
              #                           'max_attempts': 10,
              #                           'mode': 'standard'
              #                       }
              #               )
              #    rds_clnt = boto3.client('rds',region_name=source_region, config=regional_config,endpoint_url=f'https://rds.{source_region}.amazonaws.com')
              
              log(cw_client,LOG_GROUP_NAME, LOG_STREAM_NAME,f'>>>>> snap_id : {snap_id} cluster_id : {cluster_id} DBI-Cls-Rsrc-ID: {dbi_cls_rsrc_id}  snapshot_source_region: {source_region} src_db_cls_snap_id: {src_db_cls_snap_id} ')
              valid_rds_cluster,rds_cls_dict[cluster_id]=is_cluster_valid(rds_clnt,cw_client,LOG_GROUP_NAME, LOG_STREAM_NAME,cluster_id,dbi_cls_rsrc_id,source_region,snap_crt_time,src_db_cls_snap_id)
              log(cw_client,LOG_GROUP_NAME, LOG_STREAM_NAME,f'valid_rds_cluster : {valid_rds_cluster} for {cluster_id}')
              
              if not valid_rds_cluster:
                msg=msg+"\n"+f"[{iter}] - Snapshot Name: {db_res_cstr['DBClusterSnapshots'][i]['DBClusterSnapshotIdentifier']} || Type: {db_res_cstr['DBClusterSnapshots'][i]['SnapshotType']} || Status: {db_res_cstr['DBClusterSnapshots'][i]['Status']} || DBClusterSnapshotIdentifier: {db_res_cstr['DBClusterSnapshots'][i]['DBClusterIdentifier']} || Snapshot ARN: {db_res_cstr['DBClusterSnapshots'][i]['DBClusterSnapshotArn']}"
                iter=iter+1
                rds_cls_snap_dict[snap_id]=db_res_cstr["DBClusterSnapshots"][i]
                
                
                
                if is_key_exists(rds_cls_snap_dict,'SnapshotCreateTime'): rds_cls_snap_dict[snap_id]["SnapshotCreateTime"]  = rds_cls_snap_dict[snap_id]["SnapshotCreateTime"].isoformat()
                if is_key_exists(rds_cls_snap_dict,'ClusterCreateTime'):  rds_cls_snap_dict[snap_id]["ClusterCreateTime"]   = rds_cls_snap_dict[snap_id]["ClusterCreateTime"].isoformat()
                
                
                
                rds_cls_snap_dict[snap_id]["rds_cls_detail"]= []
                
                if (len(rds_cls_dict[cluster_id])) > 0:
                  if is_key_exists(rds_cls_dict,'AutomaticRestartTime'):                    rds_cls_dict[cluster_id][cluster_id]["AutomaticRestartTime"]                    = rds_cls_dict[cluster_id][cluster_id] ['AutomaticRestartTime'].isoformat()
                  if is_key_exists(rds_cls_dict,'EarliestRestorableTime'):                  rds_cls_dict[cluster_id][cluster_id]["EarliestRestorableTime"]                  = rds_cls_dict[cluster_id][cluster_id] ['EarliestRestorableTime'].isoformat()
                  if is_key_exists(rds_cls_dict,'LatestRestorableTime'):                    rds_cls_dict[cluster_id][cluster_id]["LatestRestorableTime"]                    = rds_cls_dict[cluster_id][cluster_id] ['LatestRestorableTime'].isoformat()
                  if is_key_exists(rds_cls_dict,'ClusterCreateTime'):                       rds_cls_dict[cluster_id][cluster_id]["ClusterCreateTime"]                       = rds_cls_dict[cluster_id][cluster_id] ['ClusterCreateTime'].isoformat()
                  if is_key_exists(rds_cls_dict,'EarliestBacktrackTime'):                   rds_cls_dict[cluster_id][cluster_id]["EarliestBacktrackTime"]                   = rds_cls_dict[cluster_id][cluster_id] ['EarliestBacktrackTime'].isoformat()
                  if is_key_exists(rds_cls_dict,'IOOptimizedNextAllowedModificationTime'):  rds_cls_dict[cluster_id][cluster_id]["IOOptimizedNextAllowedModificationTime"]  = rds_cls_dict[cluster_id][cluster_id] ['IOOptimizedNextAllowedModificationTime'].isoformat()
    
                  rds_cls_snap_dict[snap_id]["rds_cls_detail"].append(rds_cls_dict[cluster_id][cluster_id])
                
                json_array.append(rds_cls_snap_dict[snap_id])   

    if msg !="":
      log_msg="\n"
      log_msg=log_msg+"\n"
      log_msg=log_msg+f"="*50
      log_msg=log_msg+"\n"+f"*"*5+ " Orphaned RDS Cluster Snapshot Details "+ "*"*5
      log_msg=log_msg+"\n"+f"="*50
      log_msg=log_msg+"\n"+msg
      log(cw_client,LOG_GROUP_NAME, LOG_STREAM_NAME,log_msg)
      # log(cw_client,LOG_GROUP_NAME, LOG_STREAM_NAME,f"{rds_cls_snap_dict}")
      # print(log_msg)
      
      status_code=200
      return {
        'statusCode': status_code,
        'body': json_array
      }
      
  except botocore.exceptions.ClientError as e:
        error_msg="botocore Unexpected error at rds_cls:"+ str(e) 
        
        etype, value, tb = exc_info()
        info, error = format_exception(etype, value, tb)[-2:]
        error_msg= f'{error_msg} - Details :\n{info}\n{error}'
        
        log(cw_client,LOG_GROUP_NAME, LOG_STREAM_NAME,error_msg)
        status_code=400
        return {
          'statusCode': status_code,
          'body': error_msg
        }
  except:
        error_msg="Unexpected error at rds_cls:"+ str(sys.exc_info()[0])
        
        etype, value, tb = exc_info()
        info, error = format_exception(etype, value, tb)[-2:]
        error_msg= f'{error_msg} - Details :\n{info}\n{error}'
        
        log(cw_client,LOG_GROUP_NAME, LOG_STREAM_NAME,error_msg)
        status_code=400
        return {
          'statusCode': status_code,
          'body': error_msg
        }



##Lambda handler to control the invocation type        
def lambda_handler(event, context):
    
    
    try:
      print(f"event: {event} - Operation : {event['ops']} || Context: {context}")
      
      
      param_account_id = event['account_id']
      param_account_name = event['account_name']
      param_region = event['region']
      param_ops = event['ops']
      param_bucket_name = event['bucket_name']
      param_key = event['key']
      
      
      
      regional_config = Config(
                      region_name=param_region,
                      retries = {
                                    'max_attempts': 10,
                                    'mode': 'standard'
                                }
                        )
      
      
      
      
      
      file_content= {
        'aws_account' : param_account_id,
        'account_name' : param_account_name,
        'region': param_region,
        'ops': param_ops,
        'lambda_output':''
      }
      
      rds_client = boto3.client('rds',region_name=param_region, config=regional_config,endpoint_url=f'https://rds.{param_region}.amazonaws.com')
      
      excluded_acnt_list=ssm_client.get_parameter(Name=util.aws_utl.ssm_exc_acnt_arn,WithDecryption=True)['Parameter']['Value']
      excluded_acnt_list=list(excluded_acnt_list.split(','))
      print(f'excluded_acnt_list {excluded_acnt_list}') 
       
      ops=event['ops']
      
      ##Skip the operation if current account falls under excluded account id
      if param_account_id in excluded_acnt_list:
        ops = util.aws_utl.skip
      
      print(f'ops {ops}') 
      
      if (ops == util.aws_utl.rds_ins):
        # RDS Instance Snapshot Details
        file_content['lambda_output']= rds_ins(rds_client,param_region,f"RDS Instance|{param_account_id}|{param_region}")
      elif (ops == util.aws_utl.rds_cls):
        # RDS Cluster Snapshot Details
        file_content['lambda_output']= rds_cls(rds_client,param_region,f"RDS Cluster|{param_account_id}|{param_region}")
      elif (ops == util.aws_utl.skip):
        # Skip the execution
        file_content['lambda_output']={
                                      'statusCode': 300,
                                      'body': 'Skipping the execution as per user request'
                                    }
        print(f" {file_content['lambda_output']}")                            
      
      #Payload to return in stepfunction
      result= {
        'aws_account' : param_account_id,
        'account_name' : param_account_name,
        'region': param_region,
        'ops': param_ops,
        's3_upload_status': ''
      }
      
      
      
     
      #Upload to S3 - Raw data bucket in Monitoring Account
      if is_key_exists(file_content,'statusCode'):
        if file_content['lambda_output']['statusCode'] == 200  :
          result['s3_upload_status'] = upload_to_s3(param_bucket_name, param_key,file_content)
      
      return result
    except ClientError as e: 
        error_msg=e.response
        
        etype, value, tb = exc_info()
        info, error = format_exception(etype, value, tb)[-2:]
        error_msg= f'{error_msg} - Details :\n{info}\n{error}'
        
        print(f"error_msg {error_msg}")
        status_code=400
        return {
          'statusCode': status_code,
          'body': error_msg
        }
    except:
        error_msg="Unexpected error at Main-Handler:"+ str(sys.exc_info()[0])
        
        etype, value, tb = exc_info()
        info, error = format_exception(etype, value, tb)[-2:]
        error_msg= f'{error_msg} - Details :\n{info}\n{error}' 
        
        print(f"error_msg {error_msg}")
        status_code=400
        return {
          'statusCode': status_code,
          'body': error_msg
        }
        
    