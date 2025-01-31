# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import os
CURRENT_DIRECTORY=os.getcwd()
import sys
import shutil
import toml

def build():
    '''
    Method to build artifact for lambda function
    '''
    try:
        TEMPLATE_VERSION=None
        with open('Config.toml',encoding="utf-8") as f:
            config = toml.load(f)
            TEMPLATE_VERSION = config['system_stack']['template_version']
        dir_prefix = os.path.join(CURRENT_DIRECTORY, "objects",TEMPLATE_VERSION,'lambda')
        lambda_name = ["Snapshot-Insight","Snapshot-Insight-S3Object-Archive","Snapshot-Insight-Util"]
        for name in lambda_name:
            src_lambda_dir = os.path.join(dir_prefix, name)
            output_dir=os.path.join(dir_prefix, 'zip',name)
            shutil.make_archive(output_dir, "zip", src_lambda_dir)

        print(f"Artifacts built successfully !!!")    
    except Exception as e:
        print(f"Error in building artifact {e}")
        sys.exit(1)            

if __name__ == "__main__":
    build()