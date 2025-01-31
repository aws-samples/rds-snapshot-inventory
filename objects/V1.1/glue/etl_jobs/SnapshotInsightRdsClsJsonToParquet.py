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
    colName="`snapshot.rds_cls_detail`", newCol="cluster", outer=True
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
            "`snapshot.dbclustersnapshotidentifier`",
            "string",
            "`snapshot.dbclustersnapshotidentifier`",
            "string",
        ),
        (
            "`snapshot.dbclusteridentifier`",
            "string",
            "`snapshot.dbclusteridentifier`",
            "string",
        ),
        (
            "`snapshot.snapshotcreatetime`",
            "string",
            "`snapshot.snapshotcreatetime`",
            "string",
        ),
        ("`snapshot.engine`", "string", "`snapshot.engine`", "string"),
        ("`snapshot.enginemode`", "string", "`snapshot.enginemode`", "string"),
        ("`snapshot.allocatedstorage`", "int", "`snapshot.allocatedstorage`", "int"),
        ("`snapshot.status`", "string", "`snapshot.status`", "string"),
        ("`snapshot.port`", "int", "`snapshot.port`", "int"),
        ("`snapshot.vpcid`", "string", "`snapshot.vpcid`", "string"),
        (
            "`snapshot.clustercreatetime`",
            "string",
            "`snapshot.clustercreatetime`",
            "string",
        ),
        ("`snapshot.masterusername`", "string", "`snapshot.masterusername`", "string"),
        ("`snapshot.engineversion`", "string", "`snapshot.engineversion`", "string"),
        ("`snapshot.licensemodel`", "string", "`snapshot.licensemodel`", "string"),
        ("`snapshot.snapshottype`", "string", "`snapshot.snapshottype`", "string"),
        ("`snapshot.percentprogress`", "int", "`snapshot.percentprogress`", "int"),
        (
            "`snapshot.storageencrypted`",
            "boolean",
            "`snapshot.storageencrypted`",
            "boolean",
        ),
        ("`snapshot.kmskeyid`", "string", "`snapshot.kmskeyid`", "string"),
        (
            "`snapshot.dbclustersnapshotarn`",
            "string",
            "`snapshot.dbclustersnapshotarn`",
            "string",
        ),
        (
            "`snapshot.iamdatabaseauthenticationenabled`",
            "boolean",
            "`snapshot.iamdatabaseauthenticationenabled`",
            "boolean",
        ),
        ("`cluster.allocatedstorage`", "int", "`cluster.allocatedstorage`", "int"),
        (
            "`cluster.backupretentionperiod`",
            "int",
            "`cluster.backupretentionperiod`",
            "int",
        ),
        (
            "`cluster.dbclusteridentifier`",
            "string",
            "`cluster.dbclusteridentifier`",
            "string",
        ),
        (
            "`cluster.dbclusterparametergroup`",
            "string",
            "`cluster.dbclusterparametergroup`",
            "string",
        ),
        ("`cluster.dbsubnetgroup`", "string", "`cluster.dbsubnetgroup`", "string"),
        ("`cluster.status`", "string", "`cluster.status`", "string"),
        (
            "`cluster.earliestrestorabletime`",
            "string",
            "`cluster.earliestrestorabletime`",
            "string",
        ),
        ("`cluster.endpoint`", "string", "`cluster.endpoint`", "string"),
        ("`cluster.readerendpoint`", "string", "`cluster.readerendpoint`", "string"),
        ("`cluster.multiaz`", "boolean", "`cluster.multiaz`", "boolean"),
        ("`cluster.engine`", "string", "`cluster.engine`", "string"),
        ("`cluster.engineversion`", "string", "`cluster.engineversion`", "string"),
        (
            "`cluster.latestrestorabletime`",
            "string",
            "`cluster.latestrestorabletime`",
            "string",
        ),
        ("`cluster.port`", "int", "`cluster.port`", "int"),
        ("`cluster.masterusername`", "string", "`cluster.masterusername`", "string"),
        (
            "`cluster.preferredbackupwindow`",
            "string",
            "`cluster.preferredbackupwindow`",
            "string",
        ),
        (
            "`cluster.preferredmaintenancewindow`",
            "string",
            "`cluster.preferredmaintenancewindow`",
            "string",
        ),
        ("`cluster.hostedzoneid`", "string", "`cluster.hostedzoneid`", "string"),
        (
            "`cluster.storageencrypted`",
            "boolean",
            "`cluster.storageencrypted`",
            "boolean",
        ),
        ("`cluster.kmskeyid`", "string", "`cluster.kmskeyid`", "string"),
        (
            "`cluster.dbclusterresourceid`",
            "string",
            "`cluster.dbclusterresourceid`",
            "string",
        ),
        ("`cluster.dbclusterarn`", "string", "`cluster.dbclusterarn`", "string"),
        (
            "`cluster.iamdatabaseauthenticationenabled`",
            "boolean",
            "`cluster.iamdatabaseauthenticationenabled`",
            "boolean",
        ),
        (
            "`cluster.clustercreatetime`",
            "string",
            "`cluster.clustercreatetime`",
            "string",
        ),
        ("`cluster.enginemode`", "string", "`cluster.enginemode`", "string"),
        (
            "`cluster.deletionprotection`",
            "boolean",
            "`cluster.deletionprotection`",
            "boolean",
        ),
        (
            "`cluster.httpendpointenabled`",
            "boolean",
            "`cluster.httpendpointenabled`",
            "boolean",
        ),
        (
            "`cluster.activitystreamstatus`",
            "string",
            "`cluster.activitystreamstatus`",
            "string",
        ),
        (
            "`cluster.copytagstosnapshot`",
            "boolean",
            "`cluster.copytagstosnapshot`",
            "boolean",
        ),
        (
            "`cluster.crossaccountclone`",
            "boolean",
            "`cluster.crossaccountclone`",
            "boolean",
        ),
        (
            "`cluster.autominorversionupgrade`",
            "boolean",
            "`cluster.autominorversionupgrade`",
            "boolean",
        ),
        ("`cluster.networktype`", "string", "`cluster.networktype`", "string"),
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
