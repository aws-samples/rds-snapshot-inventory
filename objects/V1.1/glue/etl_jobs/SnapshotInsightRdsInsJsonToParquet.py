# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
import gs_flatten
import gs_explode

args = getResolvedOptions(sys.argv, ["JOB_NAME", "glue_database", "source_table_name","target_s3_path"])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

# Script generated for node Raw - AWS Glue Data Catalog
RawAWSGlueDataCatalog_node1701154441609 = glueContext.create_dynamic_frame.from_catalog(
    database=args["glue_database"],
    table_name=args["source_table_name"],
    transformation_ctx="RawAWSGlueDataCatalog_node1701154441609",
)

# Script generated for node Output Flatten
OutputFlatten_node1701154734647 = RawAWSGlueDataCatalog_node1701154441609.gs_flatten()

# Script generated for node Output Explode Array
OutputExplodeArray_node1701154816996 = OutputFlatten_node1701154734647.gs_explode(
    colName="`lambda_output.body`", newCol="snapshot", outer=True
)

# Script generated for node Snap Flatten
SnapFlatten_node1701154936420 = OutputExplodeArray_node1701154816996.gs_flatten()

# Script generated for node Instance Explode Array
InstanceExplodeArray_node1701155173754 = SnapFlatten_node1701154936420.gs_explode(
    colName="`snapshot.rds_ins_detail`", newCol="Instance", outer=True
)

# Script generated for node Instance Flatten
InstanceFlatten_node1701155373115 = InstanceExplodeArray_node1701155173754.gs_flatten()

# Script generated for node Drop Array Change Schema
DropArrayChangeSchema_node1701155592951 = ApplyMapping.apply(
    frame=InstanceFlatten_node1701155373115,
    mappings=[
        ("aws_account", "string", "aws_account", "string"),
        ("account_name", "string", "account_name", "string"),
        ("region", "string", "region", "string"),
        ("ops", "string", "ops", "string"),
        ("`lambda_output.statuscode`", "int", "`lambda_output.statuscode`", "int"),
        ("par_year", "string", "par_year", "string"),
        ("par_month", "string", "par_month", "string"),
        ("par_day", "string", "par_day", "string"),
        ("par_sf_exc_id", "string", "par_sf_exc_id", "string"),
        ("par_account_id", "string", "par_account_id", "string"),
        ("par_region", "string", "par_region", "string"),
        (
            "`snapshot.dbsnapshotidentifier`",
            "string",
            "`snapshot.dbsnapshotidentifier`",
            "string",
        ),
        (
            "`snapshot.dbinstanceidentifier`",
            "string",
            "`snapshot.dbinstanceidentifier`",
            "string",
        ),
        (
            "`snapshot.snapshotcreatetime`",
            "string",
            "`snapshot.snapshotcreatetime`",
            "string",
        ),
        ("`snapshot.engine`", "string", "`snapshot.engine`", "string"),
        ("`snapshot.allocatedstorage`", "int", "`snapshot.allocatedstorage`", "int"),
        ("`snapshot.status`", "string", "`snapshot.status`", "string"),
        ("`snapshot.port`", "int", "`snapshot.port`", "int"),
        (
            "`snapshot.availabilityzone`",
            "string",
            "`snapshot.availabilityzone`",
            "string",
        ),
        ("`snapshot.vpcid`", "string", "`snapshot.vpcid`", "string"),
        (
            "`snapshot.instancecreatetime`",
            "string",
            "`snapshot.instancecreatetime`",
            "string",
        ),
        ("`snapshot.masterusername`", "string", "`snapshot.masterusername`", "string"),
        ("`snapshot.engineversion`", "string", "`snapshot.engineversion`", "string"),
        ("`snapshot.licensemodel`", "string", "`snapshot.licensemodel`", "string"),
        ("`snapshot.snapshottype`", "string", "`snapshot.snapshottype`", "string"),
        ("`snapshot.iops`", "int", "`snapshot.iops`", "int"),
        (
            "`snapshot.optiongroupname`",
            "string",
            "`snapshot.optiongroupname`",
            "string",
        ),
        ("`snapshot.percentprogress`", "int", "`snapshot.percentprogress`", "int"),
        ("`snapshot.storagetype`", "string", "`snapshot.storagetype`", "string"),
        ("`snapshot.encrypted`", "boolean", "`snapshot.encrypted`", "boolean"),
        ("`snapshot.kmskeyid`", "string", "`snapshot.kmskeyid`", "string"),
        ("`snapshot.dbsnapshotarn`", "string", "`snapshot.dbsnapshotarn`", "string"),
        (
            "`snapshot.iamdatabaseauthenticationenabled`",
            "boolean",
            "`snapshot.iamdatabaseauthenticationenabled`",
            "boolean",
        ),
        ("`snapshot.dbiresourceid`", "string", "`snapshot.dbiresourceid`", "string"),
        (
            "`snapshot.originalsnapshotcreatetime`",
            "string",
            "`snapshot.originalsnapshotcreatetime`",
            "string",
        ),
        ("`snapshot.snapshottarget`", "string", "`snapshot.snapshottarget`", "string"),
        ("`snapshot.storagethroughput`", "int", "`snapshot.storagethroughput`", "int"),
        ("`snapshot.sourceregion`", "string", "`snapshot.sourceregion`", "string"),
        (
            "`snapshot.sourcedbsnapshotidentifier`",
            "string",
            "`snapshot.sourcedbsnapshotidentifier`",
            "string",
        ),
        (
            "`instance.dbinstanceidentifier`",
            "string",
            "`instance.dbinstanceidentifier`",
            "string",
        ),
        (
            "`instance.dbinstanceclass`",
            "string",
            "`instance.dbinstanceclass`",
            "string",
        ),
        ("`instance.engine`", "string", "`instance.engine`", "string"),
        (
            "`instance.dbinstancestatus`",
            "string",
            "`instance.dbinstancestatus`",
            "string",
        ),
        ("`instance.masterusername`", "string", "`instance.masterusername`", "string"),
        (
            "`instance.endpoint.address`",
            "string",
            "`instance.endpoint.address`",
            "string",
        ),
        ("`instance.endpoint.port`", "int", "`instance.endpoint.port`", "int"),
        (
            "`instance.endpoint.hostedzoneid`",
            "string",
            "`instance.endpoint.hostedzoneid`",
            "string",
        ),
        ("`instance.allocatedstorage`", "int", "`instance.allocatedstorage`", "int"),
        (
            "`instance.instancecreatetime`",
            "string",
            "`instance.instancecreatetime`",
            "string",
        ),
        (
            "`instance.preferredbackupwindow`",
            "string",
            "`instance.preferredbackupwindow`",
            "string",
        ),
        (
            "`instance.backupretentionperiod`",
            "int",
            "`instance.backupretentionperiod`",
            "int",
        ),
        (
            "`instance.availabilityzone`",
            "string",
            "`instance.availabilityzone`",
            "string",
        ),
        (
            "`instance.dbsubnetgroup.dbsubnetgroupname`",
            "string",
            "`instance.dbsubnetgroup.dbsubnetgroupname`",
            "string",
        ),
        (
            "`instance.dbsubnetgroup.dbsubnetgroupdescription`",
            "string",
            "`instance.dbsubnetgroup.dbsubnetgroupdescription`",
            "string",
        ),
        (
            "`instance.dbsubnetgroup.vpcid`",
            "string",
            "`instance.dbsubnetgroup.vpcid`",
            "string",
        ),
        (
            "`instance.dbsubnetgroup.subnetgroupstatus`",
            "string",
            "`instance.dbsubnetgroup.subnetgroupstatus`",
            "string",
        ),
        (
            "`instance.preferredmaintenancewindow`",
            "string",
            "`instance.preferredmaintenancewindow`",
            "string",
        ),
        (
            "`instance.latestrestorabletime`",
            "string",
            "`instance.latestrestorabletime`",
            "string",
        ),
        ("`instance.multiaz`", "boolean", "`instance.multiaz`", "boolean"),
        ("`instance.engineversion`", "string", "`instance.engineversion`", "string"),
        (
            "`instance.autominorversionupgrade`",
            "boolean",
            "`instance.autominorversionupgrade`",
            "boolean",
        ),
        ("`instance.licensemodel`", "string", "`instance.licensemodel`", "string"),
        ("`instance.iops`", "int", "`instance.iops`", "int"),
        (
            "`instance.publiclyaccessible`",
            "boolean",
            "`instance.publiclyaccessible`",
            "boolean",
        ),
        ("`instance.storagetype`", "string", "`instance.storagetype`", "string"),
        ("`instance.dbinstanceport`", "int", "`instance.dbinstanceport`", "int"),
        (
            "`instance.storageencrypted`",
            "boolean",
            "`instance.storageencrypted`",
            "boolean",
        ),
        ("`instance.kmskeyid`", "string", "`instance.kmskeyid`", "string"),
        ("`instance.dbiresourceid`", "string", "`instance.dbiresourceid`", "string"),
        (
            "`instance.cacertificateidentifier`",
            "string",
            "`instance.cacertificateidentifier`",
            "string",
        ),
        (
            "`instance.copytagstosnapshot`",
            "boolean",
            "`instance.copytagstosnapshot`",
            "boolean",
        ),
        (
            "`instance.monitoringinterval`",
            "int",
            "`instance.monitoringinterval`",
            "int",
        ),
        (
            "`instance.enhancedmonitoringresourcearn`",
            "string",
            "`instance.enhancedmonitoringresourcearn`",
            "string",
        ),
        (
            "`instance.monitoringrolearn`",
            "string",
            "`instance.monitoringrolearn`",
            "string",
        ),
        ("`instance.dbinstancearn`", "string", "`instance.dbinstancearn`", "string"),
        (
            "`instance.iamdatabaseauthenticationenabled`",
            "boolean",
            "`instance.iamdatabaseauthenticationenabled`",
            "boolean",
        ),
        (
            "`instance.performanceinsightsenabled`",
            "boolean",
            "`instance.performanceinsightsenabled`",
            "boolean",
        ),
        (
            "`instance.performanceinsightskmskeyid`",
            "string",
            "`instance.performanceinsightskmskeyid`",
            "string",
        ),
        (
            "`instance.performanceinsightsretentionperiod`",
            "int",
            "`instance.performanceinsightsretentionperiod`",
            "int",
        ),
        (
            "`instance.deletionprotection`",
            "boolean",
            "`instance.deletionprotection`",
            "boolean",
        ),
        (
            "`instance.maxallocatedstorage`",
            "int",
            "`instance.maxallocatedstorage`",
            "int",
        ),
        (
            "`instance.customerownedipenabled`",
            "boolean",
            "`instance.customerownedipenabled`",
            "boolean",
        ),
        (
            "`instance.activitystreamstatus`",
            "string",
            "`instance.activitystreamstatus`",
            "string",
        ),
        ("`instance.backuptarget`", "string", "`instance.backuptarget`", "string"),
        ("`instance.networktype`", "string", "`instance.networktype`", "string"),
        ("`instance.storagethroughput`", "int", "`instance.storagethroughput`", "int"),
        (
            "`instance.masterusersecret.secretarn`",
            "string",
            "`instance.masterusersecret.secretarn`",
            "string",
        ),
        (
            "`instance.masterusersecret.secretstatus`",
            "string",
            "`instance.masterusersecret.secretstatus`",
            "string",
        ),
        (
            "`instance.masterusersecret.kmskeyid`",
            "string",
            "`instance.masterusersecret.kmskeyid`",
            "string",
        ),
        (
            "`instance.certificatedetails.caidentifier`",
            "string",
            "`instance.certificatedetails.caidentifier`",
            "string",
        ),
        (
            "`instance.certificatedetails.validtill`",
            "string",
            "`instance.certificatedetails.validtill`",
            "string",
        ),
    ],
    transformation_ctx="DropArrayChangeSchema_node1701155592951",
)

# Script generated for node Amazon S3
AmazonS3_node1701155695695 = glueContext.write_dynamic_frame.from_options(
    frame=DropArrayChangeSchema_node1701155592951,
    connection_type="s3",
    format="glueparquet",
    connection_options={
        "path": args["target_s3_path"],
        "partitionKeys": ["par_account_id", "par_region"],
    },
    format_options={"compression": "uncompressed"},
    transformation_ctx="AmazonS3_node1701155695695",
)

job.commit()
