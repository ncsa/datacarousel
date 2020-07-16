import json
import boto3


def lambda_handler(event, context):
    sdb = boto3.client('sdb', region_name='us-west-2')
    sqs = sqs = boto3.resource('sqs', region_name='us-west-2')

    print(sdb.list_domains()['DomainNames'])
    for record in event['Records']:
        eventName = record['eventName']
        if eventName == 'ObjectRestore:Post':
            bucket = record['s3']['bucket']['name']
            object = record['s3']['object']['key']
            size = record['s3']['object']['size'] / 1e9
            print(f'Restored {object} from {bucket} with a size of {size}Gb')

            condition = f" where FilePath = '{object}'"

            query_results = sdb.select(
                SelectExpression="select * from DatacaorouselJobFiles " + condition)
            if 'Items' in query_results:
                for item in query_results['Items']:
                    # Convert name/value pairs into a dict
                    file_values = {r['Name']: r['Value'] for r in item['Attributes']}
                    print(file_values)
                    queue_name = file_values['JobID'] + ".fifo"

                    file_record = sdb.select(
                        SelectExpression=f'select * from BasicFusionFiles where itemName() = "{object}"')
                    metadata = {r['Name']: r['Value'] for r in
                                file_record['Items'][0]['Attributes']}

                    try:
                        existing_queue = sqs.get_queue_by_name(QueueName=queue_name)
                    except Exception as eek:
                        print("Can't find existing queueue", eek)
                        existing_queue = sqs.create_queue(
                            QueueName=queue_name,
                            Attributes={'FifoQueue': "true"}
                        )

                    print(f'Existing queue {existing_queue}')

                    record = {
                        'terra-file': object,
                        'year': metadata['Year'],
                        'month': metadata['Month']
                    }
                    response = existing_queue.send_message(
                        MessageBody=json.dumps(record),
                        MessageGroupId='hsds',
                        MessageDeduplicationId=object
                    )
                    print(response)
        else:
            print(f'Ooops, Ignoring {eventName}')

    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
