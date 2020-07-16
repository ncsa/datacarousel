import json
import os

import boto3
import sys

import argparse
import h5pyd as h5py
import urllib.parse

# Get the service resource
sqs = boto3.resource('sqs', region_name='us-west-2')

parser = argparse.ArgumentParser("Index an HDF5 file")
parser.add_argument("-q", dest="sqs_queue", required=True, help="SQS Work Queue")
parser.add_argument("-u", dest='user', default='admin')
parser.add_argument("-p", dest='password', default='admin')

args = parser.parse_args()


# Get the queue
print("Ready to index files from "+args.sqs_queue)
queue = sqs.get_queue_by_name(QueueName=args.sqs_queue)

done = False
while not done:
    messages = queue.receive_messages(WaitTimeSeconds=1)
    if not messages:
        break

    for message in messages:
        print(message.body)
        params = json.loads(message.body)
        message.delete()

        file_bits = urllib.parse.urlparse(params['s3_input_file'])

        domain = file_bits.path

        try:
            f = h5py.File(domain=domain,
                          endpoint=params['hsds_endpoint'], username=args.user,
                          password=args.password)
            print(f)
            print("file exists. Deleteing it before moving ahead")
            os.system("hsrm -e {} -u {} -p {} {}".format(params['hsds_endpoint'], args.user, args.password, domain+"/"))
        except IOError:
            print("File is not there.. All clear")

        dest_domain = "/".join(file_bits.path.split("/")[:-1])+"/"

        status = os.system("hsload -e {} --link --loglevel error -p {} -u {} {} {}".format(
            params['hsds_endpoint'],
            args.password,
            args.user,
            params['s3_input_file'],
            dest_domain
        ))

        if status:
            print("There was an error in the hsload")
            sys.exit(status)
