import json
import argparse
import uuid
import boto3


parser = argparse.ArgumentParser("Index an HDF5 file")
parser.add_argument("-e", dest="hsds_endpoint", required=True, help="HSDS Endpoint URL")
parser.add_argument("-q", dest="query", default=None)

args = parser.parse_args()

sdb = boto3.client('sdb', region_name='us-west-2')
sqs = boto3.resource('sqs', region_name='us-west-2')
queue = sqs.get_queue_by_name(QueueName='climate_marble_work.fifo')

job_id = str(uuid.uuid1())
print("Submitting Job "+job_id)

select_expression = 'select * from BasicFusionFiles'
if args.query:
    select_expression = select_expression + " where "+args.query

query_results = sdb.select(
    SelectExpression=select_expression
)

if 'Items' in query_results:
    for item in query_results['Items']:
        file_values = {r['Name']: r['Value'] for r in item['Attributes']}
        record = {
            "job-id": job_id,
            "hsds-endpoint": args.hsds_endpoint,
            "terra-file": item['Name'],
            "year": file_values['Year'],
            "month": file_values['Month']
        }
        print(record)
        response = queue.send_message(
            MessageBody=json.dumps(record),
            MessageGroupId='hsds',
            MessageDeduplicationId=job_id + ":" + item['Name']
        )




