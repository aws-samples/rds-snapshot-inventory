# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import botocore
import boto3
import sys
import time
import os 
import toml
import pathlib
import platform

STACK_NAME=''
SOURCE_CODE_STACK=''
MANAGEMENT_ACCOUNT_ID=''
RESOURCE_REGIONS=''
EXCLUDED_ACCOUNTS=''
DEPLOYMENT_TYPE =''
TEMPLATE_VERSION =''
GLUE_DB_NAME = ''
QS_USER_NAME=''
QS_IDENTITY_REGION=''

PRINCIPAL_ORG_ID =''
MONITORING_ACCOUNT_ID =''
STACK_SET_OU_IDS=''
PRIMARY_REGION=''
RAWDATAS3BUCKET_ARN =''
STEPFUNC_ARN =''

CURRENT_DIRECTORY=os.getcwd()

source_code_bucket_prefix = ''
raw_data_bucket_prefix = ''
formatted_data_bucket_prefix = ''
archive_data_bucket_prefix = ''
athena_query_bucket_prefix = ''
qs_supported_regions= []
#Read user input from Toml file for common config
def get_common_config():
    global source_code_bucket_prefix, raw_data_bucket_prefix, formatted_data_bucket_prefix, archive_data_bucket_prefix, athena_query_bucket_prefix, qs_supported_regions
    with open('Config.toml',encoding="utf-8") as f:
        config = toml.load(f)
        source_code_bucket_prefix = config['system_stack']['source_code_bucket_prefix']
        raw_data_bucket_prefix = config['system_stack']['raw_data_bucket_prefix']
        formatted_data_bucket_prefix = config['system_stack']['formatted_data_bucket_prefix']
        archive_data_bucket_prefix = config['system_stack']['archive_data_bucket_prefix']
        athena_query_bucket_prefix = config['system_stack']['athena_query_bucket_prefix']
        qs_supported_regions = config['system_stack']['qs_supported_regions']
    
    return None

#Read user input from Toml file for monitor stack
def get_monitor_stack_config():
    global  STACK_NAME, SOURCE_CODE_STACK, MANAGEMENT_ACCOUNT_ID, RESOURCE_REGIONS,EXCLUDED_ACCOUNTS, DEPLOYMENT_TYPE, TEMPLATE_VERSION, GLUE_DB_NAME, QS_USER_NAME, QS_IDENTITY_REGION, PRINCIPAL_ORG_ID, CURRENT_DIRECTORY
    get_common_config()
    with open('Config.toml',encoding="utf-8") as f:
        config = toml.load(f)
        STACK_NAME = config['monitoring_stack']['stack_name']
        MANAGEMENT_ACCOUNT_ID = config['monitoring_stack']['management_account_id']
        PRINCIPAL_ORG_ID = config['monitoring_stack']['principal_org_id']
        DEPLOYMENT_TYPE = config['monitoring_stack']['deployment_type']
        RESOURCE_REGIONS = config['monitoring_stack']['resource_regions']
        EXCLUDED_ACCOUNTS = config['monitoring_stack']['excluded_accounts']
        TEMPLATE_VERSION = config['system_stack']['template_version']
        GLUE_DB_NAME = config['monitoring_stack']['glue_database_name']
        QS_USER_NAME = config['monitoring_stack']['quicksight_user_name']
        SOURCE_CODE_STACK = STACK_NAME + "-SourceCode"

        if QS_USER_NAME is not None and len(QS_USER_NAME)>1:
            get_qs_iden_reg()
        #Validate Stack Name Input
        if STACK_NAME is None or len(STACK_NAME)==0:
            print("Invalid Stack Name")
            sys.exit(1)

        #Validate Management Account ID Input
        if MANAGEMENT_ACCOUNT_ID is None or len(MANAGEMENT_ACCOUNT_ID)==0:
            print("Invalid Management Account ID")
            sys.exit(1) 

        #Validate Principal Org Id
        if PRINCIPAL_ORG_ID is None or len(PRINCIPAL_ORG_ID)==0:
            print("Invalid Principal Org Id")
            sys.exit(1)     

        #Validate Deployment Type Input
        DEPLOYMENT_TYPE = DEPLOYMENT_TYPE.upper()
        if DEPLOYMENT_TYPE not in ['ORGANIZATION','O','CURRENT_ACCOUNT','C']  or len(DEPLOYMENT_TYPE)==0:
            print("Invalid Deployment Type")
            sys.exit(1)
        elif DEPLOYMENT_TYPE in ['ORGANIZATION','O']:
            DEPLOYMENT_TYPE = "ORGANIZATION"
        elif DEPLOYMENT_TYPE in ['CURRENT_ACCOUNT','C']:
            DEPLOYMENT_TYPE = "CURRENT_ACCOUNT"
        
        #Validate Resource Regions Input
        if RESOURCE_REGIONS is None or len(RESOURCE_REGIONS)==0:
            print("Invalid Resource Regions")
            sys.exit(1)       

        #Validate Template Version Input
        if TEMPLATE_VERSION is None or len(TEMPLATE_VERSION)==0:
            print("Invalid Template Version")
            sys.exit(1)

        #Validate Glue Database Name Input
        if GLUE_DB_NAME is None or len(GLUE_DB_NAME)==0:
            print("Invalid Glue Database Name")
            sys.exit(1)       
        #Dummy value assign to Exclude Account 
        if EXCLUDED_ACCOUNTS is None or len(EXCLUDED_ACCOUNTS)==0:
            EXCLUDED_ACCOUNTS = "111111111111,222222222222"   
            
    return None

#Read user input from Toml file for management stack
def get_mgmnt_stack_config():
    global  STACK_NAME, STACK_SET_OU_IDS, MANAGEMENT_ACCOUNT_ID, PRIMARY_REGION, MONITORING_ACCOUNT_ID, EXCLUDED_ACCOUNTS, PRINCIPAL_ORG_ID, DEPLOYMENT_TYPE, TEMPLATE_VERSION, RAWDATAS3BUCKET_ARN, STEPFUNC_ARN, SOURCE_CODE_STACK 
    get_common_config()
    with open('Config.toml',encoding="utf-8") as f:
        config = toml.load(f)
        STACK_NAME = config['monitoring_stack']['stack_name']
        STACK_SET_OU_IDS = config['management_stack']['stack_set_ou_id']
        MANAGEMENT_ACCOUNT_ID = config['monitoring_stack']['management_account_id']
        PRIMARY_REGION = config['management_stack']['primary_region']
        MONITORING_ACCOUNT_ID = config['management_stack']['monitoring_account_id']
        EXCLUDED_ACCOUNTS = config['monitoring_stack']['excluded_accounts']
        PRINCIPAL_ORG_ID      =  config['monitoring_stack']['principal_org_id']
        DEPLOYMENT_TYPE = config['monitoring_stack']['deployment_type']
        TEMPLATE_VERSION = config['system_stack']['template_version']
        RAWDATAS3BUCKET_ARN = config['management_stack']['raw_data_s3_bucket_arn']
        STEPFUNC_ARN = config['management_stack']['stepfunction_role_arn']
        SOURCE_CODE_STACK = STACK_NAME + "-SourceCode"


        #Validate Stack Name Input
        if STACK_NAME is None or len(STACK_NAME)==0:
            print("Invalid Stack Name")
            sys.exit(1)

        #Validate StackSet OU IDs Input
        if STACK_SET_OU_IDS is None or len(STACK_SET_OU_IDS)==0:
            print("Invalid StackSet OU IDs")
            sys.exit(1)

        #Validate Management Account ID Input
        if MANAGEMENT_ACCOUNT_ID is None or len(MANAGEMENT_ACCOUNT_ID)==0:
            print("Invalid Management Account ID")
            sys.exit(1)

        #Validate Primary Region Input
        if PRIMARY_REGION is None or len(PRIMARY_REGION)==0:
            print("Invalid Primary Region")
            sys.exit(1)

        #Validate Monitoring Account ID Input
        if MONITORING_ACCOUNT_ID is None or len(MONITORING_ACCOUNT_ID)==0:
            print("Invalid Monitoring Account ID")
            sys.exit(1)
        
        #Validate Principal Organization ID Input
        if PRINCIPAL_ORG_ID is None or len(PRINCIPAL_ORG_ID)==0:
            print("Invalid Principal Organization ID")
            sys.exit(1)

        #Validate Deployment Type Input
        DEPLOYMENT_TYPE = DEPLOYMENT_TYPE.upper()
        if DEPLOYMENT_TYPE not in ['ORGANIZATION','O','CURRENT_ACCOUNT','C']  or len(DEPLOYMENT_TYPE)==0:
            print("Invalid Deployment Type")
            sys.exit(1)
        elif DEPLOYMENT_TYPE in ['ORGANIZATION','O']:
            DEPLOYMENT_TYPE = "ORGANIZATION"
        elif DEPLOYMENT_TYPE in ['CURRENT_ACCOUNT','C']:
            DEPLOYMENT_TYPE = "CURRENT_ACCOUNT"
            
        #Validate Template Version Input
        if TEMPLATE_VERSION is None or len(TEMPLATE_VERSION)==0:
            print("Invalid Template Version")
            sys.exit(1)

        #Validate Raw Data Bucket ARN Input
        if RAWDATAS3BUCKET_ARN is None or len(RAWDATAS3BUCKET_ARN)==0:
            print("Invalid Raw Data Bucket ARN")
            sys.exit(1)

        #Validate Step Function ARN Input
        if STEPFUNC_ARN is None or len(STEPFUNC_ARN)==0:
            print("Invalid Step Function ARN")
            sys.exit(1)

        #Dummy value assign to Exclude Account 
        if EXCLUDED_ACCOUNTS is None or len(EXCLUDED_ACCOUNTS)==0:
            EXCLUDED_ACCOUNTS = "111111111111,222222222222"        

    return None

#Read Tags from Toml file
def get_tags():
    with open('Config.toml',encoding="utf-8") as f:
        config = toml.load(f)
        tags = config['Tags']
    return tags

# Get stack set template
def get_stack_set_template(template_type):
    try:
        global STACK_NAME, SOURCE_CODE_STACK, MANAGEMENT_ACCOUNT_ID, RESOURCE_REGIONS, DEPLOYMENT_TYPE, TEMPLATE_VERSION, GLUE_DB_NAME, PRINCIPAL_ORG_ID, CURRENT_DIRECTORY
        dir_prefix = os.path.join(CURRENT_DIRECTORY, "objects",TEMPLATE_VERSION,'cfn')
        if template_type == 'source_code':
            file=os.path.join(dir_prefix,'monitoring_account','sourcecode.yml')
            with open(file,encoding="utf-8") as f:
                return f.read()
        elif template_type == 'monitor_stack':
            file=os.path.join(dir_prefix,'monitoring_account','monitor_stack.yml')
            with open(file,encoding="utf-8") as f:
                return f.read()  
        elif template_type == 'management_stack':
            file=os.path.join(dir_prefix,'management_account','management_stack.yml')
            # print(f"file->{file}")
            with open(file,encoding="utf-8") as f:
                return f.read()      
    except Exception as e:
        print(f"Error in getting stack set template {e}")
        sys.exit(1)          
# Get Cfn S3 Url
def get_cfn_s3_url(name):
    try:
        import boto3
        global  STACK_NAME, SOURCE_CODE_STACK, MANAGEMENT_ACCOUNT_ID, RESOURCE_REGIONS, DEPLOYMENT_TYPE, TEMPLATE_VERSION, GLUE_DB_NAME, PRINCIPAL_ORG_ID, CURRENT_DIRECTORY, source_code_bucket_prefix
        account_id = boto3.client('sts').get_caller_identity().get('Account')
        region = boto3.session.Session().region_name
        bucket_name = f'{source_code_bucket_prefix}-{account_id}-{region}'
        if name == 'monitor_stack':
            s3_uri = f'https://{bucket_name}.s3.amazonaws.com/objects/{TEMPLATE_VERSION}/cfn/monitoring_account/monitor_stack.yml'
        elif name == 'management_stack':
            s3_uri = f'https://{bucket_name}.s3.amazonaws.com/objects/{TEMPLATE_VERSION}/cfn/management_account/management_stack.yml'    
        return s3_uri
    except Exception as e:
        print(f"Error in getting stack set template {e}")
        sys.exit(1)       
        
    
# Create Source Code Stack if it does not exist
def create_source_code_stack():
    global STACK_NAME, SOURCE_CODE_STACK, MANAGEMENT_ACCOUNT_ID, RESOURCE_REGIONS, DEPLOYMENT_TYPE, TEMPLATE_VERSION, GLUE_DB_NAME, PRINCIPAL_ORG_ID, CURRENT_DIRECTORY, source_code_bucket_prefix
    try:
        client = boto3.client('cloudformation')
        response = client.describe_stacks(StackName=SOURCE_CODE_STACK)
        print("Stack already exists")
        return response
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ValidationError':
            print("Source Code Stack does not exist, creating...")
            response = client.create_stack(
                StackName=SOURCE_CODE_STACK,
                TemplateBody=get_stack_set_template(template_type='source_code',),
                DisableRollback=False,
                Capabilities=['CAPABILITY_NAMED_IAM'],
                Parameters=[
                    {
                        'ParameterKey': 'PrincipalOrgID',
                        'ParameterValue': PRINCIPAL_ORG_ID
                    },
                    {
                        'ParameterKey': 'DeploymentType',
                        'ParameterValue': DEPLOYMENT_TYPE
                    },
                    {
                        'ParameterKey': 'SourceCodeBucketPrefix',
                        'ParameterValue': source_code_bucket_prefix
                    }

                ],
                Tags=get_tags()
            )
            upload_source_code_to_S3()

# Delete Source Code Stack if it exists
def delete_source_code_stack():
    global  STACK_NAME, SOURCE_CODE_STACK, MANAGEMENT_ACCOUNT_ID, RESOURCE_REGIONS, DEPLOYMENT_TYPE, TEMPLATE_VERSION, GLUE_DB_NAME, PRINCIPAL_ORG_ID, CURRENT_DIRECTORY
    try:
        client = boto3.client('cloudformation')
        response = client.delete_stack(StackName=SOURCE_CODE_STACK)
        stac_status= client.describe_stacks(StackName=SOURCE_CODE_STACK).get('Stacks')[0].get('StackStatus')
        while stac_status != 'DELETE_COMPLETE' :
            print("Source Code Stack deletion is in progress, waiting...")
            time.sleep(5)
            stac_status= client.describe_stacks(StackName=SOURCE_CODE_STACK).get('Stacks')[0].get('StackStatus')
        
        print("Source Code Stack deleted")
        return response
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ValidationError':
            print("Source Code Stack does not exist, nothing to delete")
            return None
        else:
            print("Unexpected error at Source Code Stack Deletion: %s" % e)
            return None

# Method to covert windows path to posix
def convert_windows_path_to_posix(path):
    result=None
    if platform.system() == 'Windows':
        result = pathlib.PureWindowsPath(path).as_posix()
    else:
        result = path
    return result    

# Upload Source Code to S3
def upload_source_code_to_S3():
    global STACK_NAME, SOURCE_CODE_STACK, MANAGEMENT_ACCOUNT_ID, RESOURCE_REGIONS, DEPLOYMENT_TYPE, TEMPLATE_VERSION, GLUE_DB_NAME, PRINCIPAL_ORG_ID, CURRENT_DIRECTORY, source_code_bucket_prefix
    try:
        import boto3
        cfclient = boto3.client('cloudformation')
        cfresponse = cfclient.describe_stacks(StackName=SOURCE_CODE_STACK)
        while cfresponse.get('Stacks')[0].get('StackStatus') != 'CREATE_COMPLETE':
            print("Source Code Stack creation is in progress, waiting...")
            time.sleep(5)
            cfresponse = cfclient.describe_stacks(StackName=SOURCE_CODE_STACK)
        client = boto3.client('s3')
        account_id = boto3.client('sts').get_caller_identity().get('Account')
        region = boto3.session.Session().region_name
        bucket_name = f'{source_code_bucket_prefix}-{account_id}-{region}'
        # dir_prefix = os.path.join(CURRENT_DIRECTORY, "objects",TEMPLATE_VERSION)
        dir_prefix = os.path.join(CURRENT_DIRECTORY)
        for root, dirs, files in os.walk(dir_prefix):
            for file in files:
                # Check file extension
                if (file.endswith('.py') or file.endswith('.zip') or file.endswith('.json') or file.endswith('.yml') or file.endswith('.toml')) and 'objects' in root:    
                    Filename=os.path.join(root, file)
                    Key=os.path.relpath(Filename,CURRENT_DIRECTORY)
                    #Code to covert windows path to posix
                    Key=convert_windows_path_to_posix(Key)    
                    client.upload_file( Filename, Bucket = bucket_name, Key= Key)
                    
        # upload(client,bucket_name)
        print('Source Code Uploaded!!!')
    except botocore.exceptions.ClientError as e:
        print("Unexpected error at upload_source_code_to_S3 : %s" % e)
        return None
    

# Delete S3 Source Code Objects    
def empty_S3(file_type,bucket):
    global  STACK_NAME, SOURCE_CODE_STACK, MANAGEMENT_ACCOUNT_ID, RESOURCE_REGIONS, DEPLOYMENT_TYPE, TEMPLATE_VERSION, GLUE_DB_NAME, PRINCIPAL_ORG_ID, CURRENT_DIRECTORY, source_code_bucket_prefix
    try:
        import boto3
        s3_client = boto3.client('s3')
        account_id = boto3.client('sts').get_caller_identity().get('Account')
        region = boto3.session.Session().region_name
        # bucket_name = f'{source_code_bucket_prefix}-{account_id}-{region}'
        bucket_name = f'{bucket}-{account_id}-{region}'
        # print(f' bucket name-{bucket_name}')
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name)

        cnt =0
        for page in pages:
            if 'Contents' in page:
                files_to_delete = []
                for item in page['Contents']:
                    files_to_delete.append({"Key": item["Key"]})
                    cnt=cnt+1
                    # print(f"Deleting {item['Key']}")
                if files_to_delete != None:
                    response = s3_client.delete_objects(
                            Bucket=bucket_name, Delete={"Objects": files_to_delete}
                        )
        boto3.resource('s3').Bucket(bucket_name).object_versions.all().delete()
        print(f"Object count {cnt}")            
        print(f'{file_type} Objects Deleted!!!')
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchBucket':
            print(f"{file_type} Bucket doesnot exists")
            return None
        else:
            print("Unexpected error: %s" % e)
            return None    

#Get Quicksight User Identity Region
def get_qs_iden_reg():
    global QS_IDENTITY_REGION, qs_supported_regions
    qs = boto3.client('quicksight')
    account_id = boto3.client('sts').get_caller_identity().get('Account')
    region = boto3.session.Session().region_name
    try:
        if region not in list(qs_supported_regions): 
            raise Exception(f"Quicksight is not supported in {region}")
        qs.describe_account_settings(AwsAccountId=account_id)
        QS_IDENTITY_REGION = region
        
        return QS_IDENTITY_REGION
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'AccessDeniedException':
            error = e.response['Error']['Message']
            # error = 'An error occurred (AccessDeniedException) when calling the DescribeAccountSettings operation: Operation is being called from endpoint ap-southeast-1, but your identity region is us-east-1. Please use the us-east-1 endpoint.'
            error_str_split = error.split(" ")
            error_str_splt_len = len(error_str_split)
            QS_IDENTITY_REGION  = error_str_split[error_str_splt_len-2]
            return QS_IDENTITY_REGION

def print_util():
    print("This is util.py")
    print("\n\n")
    print("*"*80)
    print("-"*35+"User Input"+"-"*35)
    print("*"*80)
    print("Stack Name                   :",STACK_NAME)
    print("Management Account ID        :",MANAGEMENT_ACCOUNT_ID)
    print("Principal Organization ID    :",PRINCIPAL_ORG_ID)
    print("Deployment Type              :",DEPLOYMENT_TYPE)
    print("Template Version             :",TEMPLATE_VERSION)
    print("Glue Database Name           :",GLUE_DB_NAME)
    print("Regions                      :",RESOURCE_REGIONS)
    print("Source Code Stack Name       :",SOURCE_CODE_STACK)
    print("*"*80)
    return None