# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import os
import json
import sys
import botocore
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
config = Config(
                 retries = {
                    'max_attempts': 10,
                    'mode': 'standard'
                 }
              )



def lambda_handler(event, context):
    try:
        
        status_code=200
        s3_client = boto3.client('s3', config=config)
        
        
        SourceBucket = event['SourceBucket']
        SourceBucketKey = event['SourceBucketKey']
        TargetBucket = event['TargetBucket']
        TargetBucketPrefix = event['TargetBucketPrefix']
        CurrentDate = event['CurrentDate']
        ExecutionId = event['ExecutionId'] 
        
        SourceFileKey=SourceBucketKey
        
        ExecutionId=ExecutionId.split(':')[-1]
        #Setting Prefix for Raw files
        if os.environ['FILE_RAW'] in SourceBucket:
            SourceFileKey=SourceFileKey.replace('.json',f'-{ExecutionId}.json') #amend the file name
            if os.environ['RDS_INS_OPS'] in SourceBucketKey :
                TargetBucketPrefix = f'{TargetBucketPrefix}{os.environ['RDS_INS_OPS']}_{os.environ['FILE_RAW']}_{os.environ['FILE_ARCHIVE']}'     
            elif os.environ['RDS_CLS_OPS'] in SourceBucketKey :
                TargetBucketPrefix = f'{TargetBucketPrefix}{os.environ['RDS_CLS_OPS']}_{os.environ['FILE_RAW']}_{os.environ['FILE_ARCHIVE']}'
            TargetBucketPrefix=f'{TargetBucketPrefix}/{CurrentDate}'    
            SourceFileKey = SourceFileKey.replace(SourceFileKey.split('/')[0],TargetBucketPrefix) #amend the prefix with _archive    
                
        
        #Setting Prefix for Formatted files
        if os.environ['FILE_FORMATTED'] in SourceBucket:
            SourceFileKey=SourceFileKey.replace('.parquet',f'-{ExecutionId}.parquet') #amend the file name
            if os.environ['RDS_INS_OPS'] in SourceBucketKey :
                TargetBucketPrefix = f'{TargetBucketPrefix}{os.environ['RDS_INS_OPS']}_{os.environ['FILE_FORMATTED']}_{os.environ['FILE_ARCHIVE']}'     
            elif os.environ['RDS_CLS_OPS'] in SourceBucketKey :
                TargetBucketPrefix = f'{TargetBucketPrefix}{os.environ['RDS_CLS_OPS']}_{os.environ['FILE_FORMATTED']}_{os.environ['FILE_ARCHIVE']}'
            TargetBucketPrefix=f'{TargetBucketPrefix}/{CurrentDate}' 
            SourceFileKey = SourceFileKey.replace(SourceFileKey.split('/')[0],TargetBucketPrefix)   #amend the prefix with _archive
        
        
        print(f'SourceFileKey -> {SourceFileKey}')
        TargetBucketPrefix =SourceFileKey 
        
        
        print(f'TargetBucketPrefix -> {TargetBucketPrefix}')
        
        s3_client.copy_object(
            CopySource  = {'Bucket': SourceBucket, 'Key': SourceBucketKey},
            Bucket      = TargetBucket, # Destination bucket
            Key         = TargetBucketPrefix # Destination path/filename
        )
        
        
        s3_client.delete_object(
            Bucket=SourceBucket,
            Key=SourceBucketKey
        )
    except ClientError as e: 
        error_msg=e.response
        print(f"error_msg {error_msg}")
        status_code=400
        return {
          'statusCode': status_code,
          'body': error_msg
        }
    except:
        error_msg="Unexpected error at Main-Handler:"+ str(sys.exc_info()[0])
        print(f"error_msg {error_msg}")
        status_code=400
        return {
          'statusCode': status_code,
          'body': error_msg
        }
    
