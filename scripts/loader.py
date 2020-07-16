import json
from datetime import datetime

import sys

import boto3

client = boto3.client("s3")
sqs = boto3.resource('sqs', region_name='us-west-2')
queue = sqs.get_queue_by_name(QueueName='hsload_work.fifo')

print(queue.url)
print(queue.attributes.get('DelaySeconds'))

files = client.list_objects(
    Bucket="datacarousel.restore",
    Prefix="terrafusion/P108"
)

timestamp = str(datetime.today().timestamp())

running = 0
for file in files['Contents']:
    print(file['Key'])
    restore_folder, modis_orbit, filename = file['Key'].split("/")
    job_name = filename.split(".")[0]

    print(modis_orbit, job_name)
    parameters = {
        'domain': '/terrafusion',
        'hsds_endpoint': 'http://ec2-34-221-10-72.us-west-2.compute.amazonaws.com',
        's3_input_file': 's3://datacarousel.restore/' + file['Key']
    }

    print(parameters)

    response = queue.send_message(
        MessageBody=json.dumps(parameters),
        MessageGroupId='hsds',
        MessageDeduplicationId=file['Key'] + timestamp
    )

    # The response is NOT a resource, but gives you a message ID and MD5
    print(response.get('MessageId'))
    print(response.get('MD5OfMessageBody'))

    running+=1
    if running > 20:
        break



