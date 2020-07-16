# Data Carousel
This implements an AWS service that allows researchers to analyze HDF5 data 
stored in AWS Glacier archive. It does this by creating a regular process for
restoring the data to S3 and running researcher-supplied batch jobs in Amazon's
Elastic Container Serivce against that data.

This repo holds an environment for executing docker-based scripts to ingest
and manage fused Terra HDF5 files.

* `loader.py` - this script lists object in the Terra Fusion data carousel
bucket and pushes records to the file index work queue.

* `index_file.py` - This script reads from the work queue and calls the the 
HSDS load script to index the file and save metadata records in the HSDS server.

* `record_metadata.py` - This script will list files available in the HSDS. It
extracts some useful metadata and creates records in the `BasicFusionFiles`. 
These records are used when we submit jobs.

## AWS Dependent Environment
The application is provided as a CloudFormation template. This template is 
produced using the 
[troposphere cloud library](https://github.com/cloudtools/troposphere).

The chart assumes the existence of a Virtual Private Cloud, a public subnet, 
and a default VPC security group.

These can be created with the AWS Console. There is a VPC wizard that can be 
launched from the VPC Dashboard. The simple setup is the 
_VPC with a single public subnet_ option. Give your VPC a name and accept the
rest of the defaults. 

Edit the generated public subnet and set _Auto-assign public IPv4 address_ to
True.

Note the ID of this generated public subnet along with the VPC's default 
security group.

## Build CloudFormation Template
We use the Troposhere python DSL to reduce the complexity of creating 
CloudFormation templates. You can generate new templates with
```shell script
pip install -r requirements.txt
python stack.py > stack.json
```

## Create the Data Carousel with CloudFormation
1. Go to the CloudFormation page in the AWS Console and click on _Create Stack_
2. Select _Template is Ready_
3. Select _Upload a Template file_
4. Choose the generated `stack.json` file and click _Next_
5. Enter a name for your data carousel stack
6. Paste the ID of the generated public Subnet as _Subnet A_
7. Select your new VPC and that VPC's default Security Group in the other fields
8. Click Next and then Next and
 _acknowledge that AWS CloudFormation might create IAM resources._
 9. Click _Create Stack_ and wait.....
 
 ## Run a Radience Batch Job
 We have a single sample batch job based on an
 [example from Yizhe Zhan](https://github.com/uiucYizhe/ClimateMarble). To
 run it, vist the AWS Batch page in the console and on the Dashboard, select
 _Create Job_.
 
 Name your batch job, select the `ComputeRadience` job definition, the 
 `datacarousel-job-queue` and accept the rest of the default values. Click on
 _Submit Job_.
 
 You can visit the EC2 page in the console to see the server start up to run
 the container. You can monitor the job's progress from the Batch dashboard.
 
 When the job completes, it will store a compressed numpy file in a bucket in 
 your S3 account.
 


