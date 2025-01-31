# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import botocore
import boto3
import sys
import time
import os
import util

OPERATION =''


# Create Stack Set if it does not exist
def create_stack_set():
    try:
        client = boto3.client('cloudformation')
        response = client.describe_stack_set(StackSetName=util.STACK_NAME)
        print("StackSet already exists")
        return response
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'StackSetNotFoundException':
            print("StackSet does not exist, creating...")
            # print("StackSet url: " + util.get_cfn_s3_url('management_stack'))
            response = client.create_stack_set(
                StackSetName=util.STACK_NAME,
                Description='StackSet to find Orphan Snapshots',
                TemplateURL=util.get_cfn_s3_url('management_stack'),
                PermissionModel='SERVICE_MANAGED',
                AutoDeployment={
                    'Enabled': True,
                    'RetainStacksOnAccountRemoval': False
                },
                Capabilities=[
                    'CAPABILITY_NAMED_IAM',
                ],
                Parameters=[
                    {
                        'ParameterKey': 'ManagementAccountId',
                        'ParameterValue': util.MANAGEMENT_ACCOUNT_ID
                    },
                    {
                        'ParameterKey': 'PrimaryRegion',
                        'ParameterValue': util.PRIMARY_REGION
                    },
                    {
                        'ParameterKey': 'PrincipalOrgID',
                        'ParameterValue': util.PRINCIPAL_ORG_ID
                    },
                    {
                        'ParameterKey': 'MonitoringAccountId',
                        'ParameterValue': util.MONITORING_ACCOUNT_ID
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
                        'ParameterKey': 'RawDataS3BucketArn',
                        'ParameterValue': util.RAWDATAS3BUCKET_ARN
                    },
                    {
                        'ParameterKey': 'StepFunctionRoleArn',
                        'ParameterValue': util.STEPFUNC_ARN
                    },
                    {
                        'ParameterKey': 'SourceCodeBucketPrefix',
                        'ParameterValue': util.source_code_bucket_prefix
                    }
                ],
                Tags= util.get_tags()

            )
            return response
        else:
            print("Unexpected error: %s" % e)

# Create Stack Instances if it does not exist
def create_stack_insts():
    try:
        client = boto3.client('cloudformation')
        response = client.list_stack_instances(StackSetName=util.STACK_NAME)
        
        if len(response.get('Summaries')) > 0:
            print("StackSet Instance already exists")
        else:
            print("StackSet Instance does not exist, creating...")
            response = client.create_stack_instances(
                StackSetName=util.STACK_NAME,
                DeploymentTargets= {
                    'OrganizationalUnitIds': util.STACK_SET_OU_IDS.split(",")
                },
                Regions=util.PRIMARY_REGION.split(","),
                OperationPreferences={
                    'RegionConcurrencyType': 'PARALLEL',
                    'FailureTolerancePercentage': 5,
                    'MaxConcurrentPercentage': 100,
                    'ConcurrencyMode': 'SOFT_FAILURE_TOLERANCE'
                }

            )    
        return response
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'StackSetNotFoundException':
            print("StackSet Instance does not exist, creating...")
        else:
            print("Unexpected error: %s" % e)

# Delete stack set if it exists
def delete_stack_set():
    try:
        client = boto3.client('cloudformation')
        while len(client.list_stack_instances(StackSetName=util.STACK_NAME).get('Summaries')) >0 :
                print("StackSet Instance deletion is in progress, waiting...")
                time.sleep(5)
        response = client.delete_stack_set(StackSetName=util.STACK_NAME)
        return response
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'StackSetNotFoundException':
            print("StackSet does not exist, nothing to delete")
            return None
        else:
            print("Unexpected error: %s" % e)
            return None

# Delete Stack Instances if it exists
def delete_stack_insts():
    try:
        client = boto3.client('cloudformation')
        response = client.delete_stack_instances(
            StackSetName=util.STACK_NAME,
            DeploymentTargets= {
                    'OrganizationalUnitIds': util.STACK_SET_OU_IDS.split(",")
                },
            Regions=util.PRIMARY_REGION.split(","),
            RetainStacks=False,
            OperationPreferences={
                'RegionConcurrencyType': 'PARALLEL',
                'FailureTolerancePercentage': 5,
                'MaxConcurrentPercentage': 100,
                'ConcurrencyMode': 'SOFT_FAILURE_TOLERANCE'
            }
        )
        return response
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'StackSetNotFoundException':
            print("StackSet Instance does not exist, nothing to delete")
            return None
        else:
            print("Unexpected error: %s" % e)
            return None

# Create Stack if it does not exist
def create_stack():
    try:
        client = boto3.client('cloudformation')
        response = client.describe_stacks(StackName=util.STACK_NAME)
        print("Management Account Stack already exists")
        return response
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ValidationError':
            print("Management Account Stack does not exist, creating...")
            response = client.create_stack(
                StackName=util.STACK_NAME,
                TemplateURL=util.get_cfn_s3_url('management_stack'),
                Parameters=[
                    {
                        'ParameterKey': 'ManagementAccountId',
                        'ParameterValue': util.MANAGEMENT_ACCOUNT_ID
                    },
                    {
                        'ParameterKey': 'PrimaryRegion',
                        'ParameterValue': util.PRIMARY_REGION
                    },
                    {
                        'ParameterKey': 'PrincipalOrgID',
                        'ParameterValue': util.PRINCIPAL_ORG_ID
                    },
                    {
                        'ParameterKey': 'MonitoringAccountId',
                        'ParameterValue': util.MONITORING_ACCOUNT_ID
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
                        'ParameterKey': 'RawDataS3BucketArn',
                        'ParameterValue': util.RAWDATAS3BUCKET_ARN
                    },
                    {
                        'ParameterKey': 'StepFunctionRoleArn',
                        'ParameterValue': util.STEPFUNC_ARN
                    },
                    {
                        'ParameterKey': 'SourceCodeBucketPrefix',
                        'ParameterValue': util.source_code_bucket_prefix
                    }
                ],
                DisableRollback=False,
                Capabilities=['CAPABILITY_NAMED_IAM'],
                Tags=util.get_tags()
            )
# Delete Stack if it exists
def delete_stack():
    try:
        client = boto3.client('cloudformation')
        response = client.delete_stack(StackName=util.STACK_NAME)
        stac_status= client.describe_stacks(StackName=util.STACK_NAME).get('Stacks')[0].get('StackStatus')
        while stac_status != 'DELETE_COMPLETE' :
            print("Management Account Stack deletion is in progress, waiting...")
            time.sleep(5)
            stac_status= client.describe_stacks(StackName=util.STACK_NAME).get('Stacks')[0].get('StackStatus')
        return response
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ValidationError':
            print("Management Account Stack does not exist, nothing to delete")
            return None
        else:
            print("Unexpected error: %s" % e)
            return None
        
def create():
    util.create_source_code_stack()
    create_stack_set()
    create_stack_insts()
    create_stack()
    return None

def delete():
    util.empty_S3("Source Code",util.source_code_bucket_prefix)
    util.delete_source_code_stack()
    delete_stack_insts()
    delete_stack_set()
    delete_stack()
    return None    


#Get User Input
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

        util.get_mgmnt_stack_config()

        print("\n\n")
        print("*"*80)
        print("-"*35+"User Input"+"-"*35)
        print("*"*80)
        print("Operation                            :",OPERATION)
        print("StackSet Name                        :",util.STACK_NAME)
        print("Management Account ID                :",util.MANAGEMENT_ACCOUNT_ID)
        print("StackSet OU IDs                      :",util.STACK_SET_OU_IDS)
        print("Primary Region                       :",util.PRIMARY_REGION)
        print("Monitoring Account ID                :",util.MONITORING_ACCOUNT_ID)
        print("Excluded Accounts                    :",util.EXCLUDED_ACCOUNTS)
        print("Principal Organization ID            :",util.PRINCIPAL_ORG_ID)
        print("Deployment Type                      :",util.DEPLOYMENT_TYPE)
        print("Template Version                     :",util.TEMPLATE_VERSION)
        print("Raw Data S3 Bucket ARN               :",util.RAWDATAS3BUCKET_ARN)
        print("Step Function ARN                    :",util.STEPFUNC_ARN)
        print("Source Code Stack Name               :",util.SOURCE_CODE_STACK)
        print("*"*80)
        

        user_exit = input("Do you want to proceed? (Y/N):").upper()

    
    return None


if __name__ == "__main__":
    
    get_user_input()
    if OPERATION == "Create":
        create()
    elif OPERATION == "Delete":
        delete()
    elif OPERATION == "Recreate":
        delete()
        create()
    else:
        print("Invalid Operation")
        sys.exit(1)