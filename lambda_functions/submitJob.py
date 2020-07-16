import json
import uuid
import boto3
from datetime import datetime
from datetime import timedelta


def _make_sdb_property(name, value):
    return {
        'Name': name,
        'Value': value,
        'Replace': True
    }


def lambda_handler(event, context):
    assert 'username' in event
    assert 'job_description' in event

    job_id = str(uuid.uuid1())

    sdb = boto3.client('sdb', region_name='us-west-2')

    if 'DataCaorouselJobs' not in sdb.list_domains()['DomainNames']:
        sdb.create_domain(
            DomainName="DataCaorouselJobs"
        )

    if 'DataCaorouselJobFiles' not in sdb.list_domains()['DomainNames']:
        sdb.create_domain(
            DomainName="DataCaorouselJobFiles"
        )

    select_expression = 'select * from BasicFusionFiles'
    if 'query' in event:
        select_expression = select_expression + " where " + event['query']

    try:
        file_count = 0
        query_results = sdb.select(SelectExpression=select_expression)

        if 'Items' in query_results:
            for item in query_results['Items']:
                file_values = {r['Name']: r['Value'] for r in item['Attributes']}
                file_path = item['Name']
                sdb.put_attributes(
                    DomainName="DataCaorouselJobFiles",
                    ItemName=job_id + file_path,
                    Attributes=[
                        _make_sdb_property('JobID', job_id),
                        _make_sdb_property('File', str(file_count))
                    ]
                )
                file_count += 1

        sdb.put_attributes(
            DomainName="DataCaorouselJobs",
            ItemName=job_id,
            Attributes=[
                _make_sdb_property('UserName', event['username']),
                _make_sdb_property('JobDescription', event['job_description']),
                _make_sdb_property('Query', select_expression),
                _make_sdb_property('FileCount', str(file_count))
            ]
        )

        # make up a expected run time
        expected_run_start = datetime.now() + timedelta(days=15)
        return {
            'statusCode': 200,
            'body': {
                "job-id": job_id,
                'file-count': file_count,
                'expected-run-start-time': str(expected_run_start)
            }
        }

    except Exception as eek:
        return {
            'statusCode': 500,
            'body': f'Bad Query: {select_expression}, {eek}'
        }

