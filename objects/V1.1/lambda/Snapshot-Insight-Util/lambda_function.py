# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import json
import boto3
import botocore
import os
import sys

from sys import exc_info
from traceback import format_exception

def get_bucket_policy(event,bucket_policy,exc_type):
    bucket_name = event['bucket_name'] 
    input = event['input']
    roleName=os.environ['RoleName']

    result = bucket_policy
    
    
    if exc_type == 'role':
        new_principal =  []
        for i in range(len(input)):
            account_id = input[i]['Id']
            new_principal_arn = f'arn:aws:iam::{account_id}:role/{roleName}'
            
            
            #Amend Linked Account Lambda Role
            new_principal.append(new_principal_arn)
            
        #Remove duplicate ARN
        new_principal = list(dict.fromkeys(new_principal))
            
        #Update the Principal
        result['Statement'][0]['Principal']['AWS']= new_principal
        result = json.dumps(result)
    elif exc_type == 'org':
        result['Statement'][0]['Principal']['AWS'] ='*'
        result = json.dumps(result)
    return result
    

def lambda_handler(event, context):
    
    try:
        bucket_name = event['bucket_name'] 
        input = event['input']
        roleName=os.environ['RoleName']
        
        print("***Event Details***")
        print(f'bucket_name - {bucket_name}')
        print(f'input - {input}')
        print(f'roleName - {roleName}')
        
        s3_client = boto3.client('s3')
        
        #Get Bucket Policy
        bucket_policy = s3_client.get_bucket_policy(Bucket=bucket_name)['Policy']
        bucket_policy = json.loads(bucket_policy)
        
        
        updated_bucket_policy=get_bucket_policy(event,bucket_policy,'role')
        s3_client.put_bucket_policy(Bucket=bucket_name, Policy=updated_bucket_policy)
        
        
        return input
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] != 'LimitExceedException':
            error_msg= "Bucket Policy Limit Exceed Exception"
            print(f"error_msg {error_msg}")
            try:
                updated_bucket_policy=get_bucket_policy(event,bucket_policy,'org')
                s3_client.put_bucket_policy(Bucket=bucket_name, Policy=updated_bucket_policy)
            except botocore.exceptions.ClientError as e:
                error_msg="Unexpected error at LimitExceedException:"+ str(sys.exc_info()[0])
            
                etype, value, tb = exc_info()
                info, error = format_exception(etype, value, tb)[-2:]
                error_msg= f'{error_msg} - Details :\n{info}\n{error}' 
                
                print(f"error_msg {error_msg}")
                status_code=400
                return {
                'statusCode': status_code,
                'body': error_msg
                }    
        else:    
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
