# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import botocore
import boto3
import sys
import time
import os 
import toml
import util
import configparser

OPERATION =''


# Create Stack if it does not exist
def create_stack():
    global OPERATION
    try:
        client = boto3.client('cloudformation')
        response = client.describe_stacks(StackName=util.STACK_NAME)
        print("Stack already exists")
        return response
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ValidationError':
            print("Monitoring Stack does not exist, creating...")
            response = client.create_stack(
                StackName=util.STACK_NAME,
                TemplateURL=util.get_cfn_s3_url('monitor_stack'),
                Parameters=[
                    {
                        'ParameterKey': 'DeploymentType',
                        'ParameterValue': util.DEPLOYMENT_TYPE
                    },
                    {
                        'ParameterKey': 'ResourceRegions',
                        'ParameterValue': util.RESOURCE_REGIONS
                    },
                    {
                        'ParameterKey': 'ManagementAccountId',
                        'ParameterValue': util.MANAGEMENT_ACCOUNT_ID
                    },
                    {
                        'ParameterKey': 'ExcludedAccounts',
                        'ParameterValue': util.EXCLUDED_ACCOUNTS
                    },
                    {
                        'ParameterKey': 'TemplateVersion',
                        'ParameterValue': util.TEMPLATE_VERSION
                    },
                    {
                        'ParameterKey': 'SourceCodeBucketPrefix',
                        'ParameterValue': util.source_code_bucket_prefix
                    },
                    {
                        'ParameterKey': 'AthenaQueryRsltBucketPrefix',
                        'ParameterValue': util.athena_query_bucket_prefix
                    },
                    {
                        'ParameterKey': 'GlueDatabaseName',
                        'ParameterValue': util.GLUE_DB_NAME
                    },
                    {
                        'ParameterKey': 'QuicksightUserName',
                        'ParameterValue': util.QS_USER_NAME
                    },
                    {
                        'ParameterKey': 'QuicksightIdentityRegion',
                        'ParameterValue': util.QS_IDENTITY_REGION
                    }
                ],
                DisableRollback=False,
                Capabilities=['CAPABILITY_NAMED_IAM'],
                Tags=util.get_tags()
            )
# Update Stack if it exists
def update_stack():
    global OPERATION
    try:
        client = boto3.client('cloudformation')
        print(f"Updating Stack {util.STACK_NAME}")
        # print(f"TemplateBody {get_stack_set_template(template_type='main')}")
        response = client.update_stack(
            StackName=util.STACK_NAME,
            TemplateURL=util.get_cfn_s3_url('monitor_stack'),
            Parameters=[
                    {
                        'ParameterKey': 'DeploymentType',
                        'ParameterValue': util.DEPLOYMENT_TYPE
                    },
                    {
                        'ParameterKey': 'ResourceRegions',
                        'ParameterValue': util.RESOURCE_REGIONS
                    },
                    {
                        'ParameterKey': 'ManagementAccountId',
                        'ParameterValue': util.MANAGEMENT_ACCOUNT_ID
                    },
                    {
                        'ParameterKey': 'ExcludedAccounts',
                        'ParameterValue': util.EXCLUDED_ACCOUNTS
                    },
                    {
                        'ParameterKey': 'TemplateVersion',
                        'ParameterValue': util.TEMPLATE_VERSION
                    },
                    {
                        'ParameterKey': 'SourceCodeBucketPrefix',
                        'ParameterValue': util.source_code_bucket_prefix
                    },
                    {
                        'ParameterKey': 'AthenaQueryRsltBucketPrefix',
                        'ParameterValue': util.athena_query_bucket_prefix
                    },
                    {
                        'ParameterKey': 'GlueDatabaseName',
                        'ParameterValue': util.GLUE_DB_NAME
                    },
                    {
                        'ParameterKey': 'QuicksightUserName',
                        'ParameterValue': util.QS_USER_NAME
                    },
                    {
                        'ParameterKey': 'QuicksightIdentityRegion',
                        'ParameterValue': util.QS_IDENTITY_REGION
                    }
                ],
            Capabilities=['CAPABILITY_NAMED_IAM'],
            Tags=util.get_tags()
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ValidationError':
            print("Stack does not exist, nothing to update Validation Error %s" % e)
            return None
        else:
            print("Unexpected error: %s" % e)
            return None    
                    
            
# Delete Stack if it exists
def delete_stack():
    global OPERATION
    try:
        client = boto3.client('cloudformation')
        response = client.delete_stack(StackName=util.STACK_NAME)
        stac_status= client.describe_stacks(StackName=util.STACK_NAME).get('Stacks')[0].get('StackStatus')
        while stac_status != 'DELETE_COMPLETE' :
            print("Monitoring Stack deletion is in progress, waiting...")
            time.sleep(5)
            stac_status= client.describe_stacks(StackName=util.STACK_NAME).get('Stacks')[0].get('StackStatus')
        return response
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ValidationError':
            print("Monitoring Stack does not exist, nothing to delete")
            return None
        else:
            print("Unexpected error: %s" % e)
            return None

    
# Create Stack if it does not exist
def create():
    util.create_source_code_stack()
    create_stack()
    return None
def update():
    util.upload_source_code_to_S3()
    update_stack()
    return None
def delete():
    util.empty_S3("Empty Bucket - Source Code Objects", util.source_code_bucket_prefix)
    util.empty_S3("Empty Bucket - Raw Data",util.raw_data_bucket_prefix)
    util.empty_S3("Empty Bucket - Formatted Data",util.formatted_data_bucket_prefix)
    util.empty_S3("Empty Bucket - Archive Data",util.archive_data_bucket_prefix)
    util.empty_S3("Empty Bucket - Athena Qry Result Data",util.athena_query_bucket_prefix)
    util.delete_source_code_stack()
    delete_stack()
    return None    

def get_user_input():
    global OPERATION
    user_exit ='N'
    while user_exit == 'N':
        OPERATION = (input("Enter Operation - Create[C] or Delete[D] [Default: Create]:").replace(' ','')) or 'Create'
        
        #Validate Operation Input
        OPERATION=OPERATION.upper()
        if OPERATION not in ['CREATE','C','UPDATE','U','DELETE','D','RECREATE','R']:
            print("Invalid Operation")
            sys.exit(1)
        elif OPERATION in ['CREATE','C']:
            OPERATION = "Create"
        elif OPERATION in ['UPDATE','U']:
            OPERATION = "Update"
        elif OPERATION in ['DELETE','D']:
            OPERATION = "Delete"
        elif OPERATION in ['RECREATE','R']:
            OPERATION = "Recreate"

        util.get_monitor_stack_config()         

        print("\n\n")
        print("*"*80)
        print("-"*35+"User Input"+"-"*35)
        print("*"*80)
        print("Operation                    :",OPERATION)
        print("Stack Name                   :",util.STACK_NAME)
        print("Management Account ID        :",util.MANAGEMENT_ACCOUNT_ID)
        print("Deployment Type              :",util.DEPLOYMENT_TYPE)
        print("Template Version             :",util.TEMPLATE_VERSION)
        print("Glue Database Name           :",util.GLUE_DB_NAME)
        print("Quicksight User Name         :",util.QS_USER_NAME)
        print("Quicksight Identity Region   :",util.QS_IDENTITY_REGION)
        print("Principal Org ID             :",util.PRINCIPAL_ORG_ID)
        print("Regions                      :",util.RESOURCE_REGIONS)
        print("Excluded Accounts            :",util.EXCLUDED_ACCOUNTS)
        print("Source Code Stack Name       :",util.SOURCE_CODE_STACK)
        print("*"*80)
        
        user_exit = input("Do you want to proceed? (Y/N)  [Default: Y]:").upper().replace(' ','') or 'Y'

    return None

def update_config():
    try:
        import boto3
        
        config_file = os.path.join(util.CURRENT_DIRECTORY,'Config.toml')
        config = toml.load(config_file)
        stepfunction_role_arn=""
    

        cfclient = boto3.client('cloudformation')
        cfresponse = cfclient.describe_stacks(StackName=util.STACK_NAME)
        while cfresponse.get('Stacks')[0].get('StackStatus') not in ('CREATE_COMPLETE','UPDATE_COMPLETE'):
            print("Monitoring Stack creation/update is in progress, waiting...")
            time.sleep(5)
            cfresponse = cfclient.describe_stacks(StackName=util.STACK_NAME)

        stack_output = cfresponse.get('Stacks')[0].get('Outputs')
        for lst in stack_output:
            if lst.get('OutputKey') == 'StepFunctionsSnapshotInsightRole':
                stepfunction_role_arn = lst.get('OutputValue')

        config['management_stack']['stepfunction_role_arn'] = stepfunction_role_arn
        f = open(config_file,'w',encoding="utf-8")
        toml.dump(config, f)
        f.close()
        print('Config file updated!!!')
    except botocore.exceptions.ClientError as e:
        print("Unexpected error at update_config : %s" % e)
        return None

if __name__ == "__main__":

    get_user_input()
    
    if OPERATION == "Create": 
        create()
    elif OPERATION == "Update":
        update()    
    elif OPERATION == "Delete":
        delete()
    elif OPERATION == "Recreate":
        delete()
        create()
    else:
        print("Invalid Operation")
        sys.exit(1)