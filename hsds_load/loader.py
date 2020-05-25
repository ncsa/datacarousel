import sys

import boto3

client = boto3.client("s3")
batch = boto3.client("batch")

queue_name = "spotqueue"
job_result = batch.list_jobs(jobQueue=queue_name)
running_jobs = [job['jobName'] for job in job_result['jobSummaryList']]


print(running_jobs)

files = client.list_objects(
    Bucket="terrafusiondatasampler",
    Prefix="P125"
)

running = 0
for file in files['Contents']:
    modis_orbit, filename = file['Key'].split("/")
    job_name = filename.split(".")[0]

    if job_name in running_jobs:
        print("Job "+job_name + " already running. Skipping")
    else:
        print(modis_orbit, job_name)
        parameters = {
            'domain': '/terra',
            'hsds_endpoint': 'http://ec2-54-218-100-163.us-west-2.compute.amazonaws.com',
            's3_input_file': 's3://terrafusiondatasampler/' + file['Key']
        }

        print(parameters)
        response = batch.submit_job(
            jobName=job_name,
            jobQueue=queue_name,
            jobDefinition='hsload-a5c32c7e61da41a:1',
            parameters={
                'domain': '/terra',
                'hsds_endpoint': 'http://ec2-52-32-176-236.us-west-2.compute.amazonaws.com',
                's3_input_file': 's3://terrafusiondatasampler/'+file['Key']
            }
        )

        print(response)
        running+=1
        if running > 5:
            break



