import os

import boto3
import sys

import argparse
import h5pyd as h5py

parser = argparse.ArgumentParser("Index an HDF5 file")
parser.add_argument("-e", dest="hsds_endpoint", required=True, help="HSDS Endpoint URL")
parser.add_argument("--ls", dest='list', action='store_const', const=True)

parser.add_argument("--domain", required=False)
parser.add_argument("-u", dest='user', default='admin')
parser.add_argument("-p", dest='password', default='admin')
parser.add_argument("--purge", dest='purge', action='store_const', const=True)

args = parser.parse_args()

sdb = boto3.client('sdb', region_name='us-west-2')

if args.purge:
    print("Purge!!!")
    sdb.delete_domain(
        DomainName="BasicFusionFiles"
    )

if 'BasicFusionFiles' not in sdb.list_domains()['DomainNames']:
    sdb.create_domain(
        DomainName="BasicFusionFiles"
    )


if args.list:
    q = sdb.select(
        SelectExpression='select * from BasicFusionFiles where MISR_Path="P125"'
    )

    if 'Items' in q:
        for item in q['Items']:
            print(item)
    sys.exit(0)

misr_paths = h5py.Folder(domain_name=args.domain,
                         endpoint=args.hsds_endpoint, username=args.user,
                         password=args.password
                         )
for path in misr_paths:
    h5_files = h5py.Folder(
        domain_name=args.domain+path+"/",
        endpoint=args.hsds_endpoint, username=args.user,
        password=args.password
    )
    for h5_file in h5_files:
        root_name = h5_file.split('.')[0]

        satellite, dataset, level, orbit, timestamp, _, _ = root_name.split("_")
        year = timestamp[:4]
        month = timestamp[4:6]
        day = timestamp[6:8]
        print(year, month, day)
        print(root_name, orbit, timestamp)
        sdb.put_attributes(
            DomainName="BasicFusionFiles",
            ItemName=args.domain+path+"/"+h5_file,
            Attributes = [
                {
                    'Name': 'MISR_Path',
                    'Value': path,
                    'Replace': True
                },
                {
                    'Name': 'Orbit',
                    'Value': orbit,
                    'Replace': True
                },
                {
                    'Name': 'Year',
                    'Value': year,
                    'Replace': True
                },
                {
                    'Name': 'Month',
                    'Value': month,
                    'Replace': True
                },
                {
                    'Name': 'Day',
                    'Value': day,
                    'Replace': True
                }
            ]

        )
