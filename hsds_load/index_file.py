import os
import sys

import argparse
import h5pyd as h5py
import urllib.parse

parser = argparse.ArgumentParser("Index an HDF5 file")
parser.add_argument("-e", dest="hsds_endpoint", required=True, help="HSDS Endpoint URL")
parser.add_argument("-s3", dest="s3_file", required=True)
parser.add_argument("--domain", required=True)
parser.add_argument("-u", dest='user', default='admin')
parser.add_argument("-p", dest='password', default='admin')

args = parser.parse_args()

file_bits = urllib.parse.urlparse(args.s3_file)


# dir = h5py.Folder(args.domain+file_bits.path+"/", mode='r', endpoint=args.hsds_endpoint, username=args.user,
#                   password=args.password)

domain = args.domain+file_bits.path

try:
    f = h5py.File(domain=domain,
                  endpoint=args.hsds_endpoint, username=args.user,
                  password=args.password)
    print(f)
    print("file exists. Deleteing it before moving ahead")
    os.system("hsrm -e {} -u {} -p {} {}".format(args.hsds_endpoint, args.user, args.password, domain+"/"))
except IOError:
    print("File is not there.. All clear")

dest_domain = args.domain + "/".join(file_bits.path.split("/")[:-1])+"/"

status = os.system("hsload -e {} --link --loglevel info -p {} -u {} {} {}".format(
    args.hsds_endpoint,
    args.password,
    args.user,
    args.s3_file,
    dest_domain
))

if status:
    print("There was an error in the hsload")
    sys.exit(status)
