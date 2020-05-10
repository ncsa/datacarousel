from troposphere import Base64, FindInMap, GetAtt, Join, Name
from troposphere import Parameter, Output, Ref, Template
import troposphere.ec2 as ec2
from troposphere.iam import Role, InstanceProfile

t = Template()

keyname_param = t.add_parameter(Parameter(
    "KeyName",
    Description="Name of an existing EC2 KeyPair to enable SSH "
                "access to the instance",
    Type="AWS::EC2::KeyPair::KeyName",
))

az_param = t.add_parameter(Parameter(
    "AZ",
    Description="Availability Zone to place instance",
    Type="AWS::EC2::AvailabilityZone::Name",
))

ami_param = t.add_parameter(Parameter(
    "AMIImage",
    Description="AWS Linux AMI Image to use",
    Type="AWS::EC2::Image::Id",
))

bucket_param = t.add_parameter(Parameter(
    "HSDSBucket",
    Description="Bucket for storing hsds metadata",
    Type="String",
))

ServiceRole = t.add_resource(Role(
    'ServiceRole',
    Path='/',
    Policies=[],
    ManagedPolicyArns=[
        'arn:aws:iam::aws:policy/AmazonS3FullAccess',
    ],
    AssumeRolePolicyDocument={'Statement': [{
        'Action': ['sts:AssumeRole'],
        'Effect': 'Allow',
        'Principal': {'Service': ['ec2.amazonaws.com']}
    }]},
))


ServiceInstanceProfile = t.add_resource(InstanceProfile(
    "ServiceProfile",
    Path='/',
    Roles=[Ref(ServiceRole)]
))

security_group = t.add_resource(ec2.SecurityGroup(
    'HDSFSecurityGroup',
    GroupDescription='Allows SSH access from anywhere',
    SecurityGroupIngress=[
        ec2.SecurityGroupRule(
            IpProtocol='tcp',
            FromPort=22,
            ToPort=22,
            CidrIp='0.0.0.0/0'
        ),
        # Allow ingress to the HDF Service Node
        ec2.SecurityGroupRule(
            IpProtocol='tcp',
            FromPort=80,
            ToPort=80,
            CidrIp='0.0.0.0/0'
        )

    ]
))

ec2_instance = t.add_resource(ec2.Instance(
    "HdsfServer",
    AvailabilityZone=Ref(az_param),
    ImageId=Ref(ami_param),
    InstanceType="m4.large",
    # This doesn't work, but it seems like we need to fix a problem in
    # https://github.com/cloudtools/troposphere/blob/2dc788dbc89c15ce5984f9c40b143494336a2348/troposphere/ec2.py#L311
    # It only works if the profile exists outside of the template
    # Til this is investigated you have to manually edit the generated json file and
    # remove the \" s
    IamInstanceProfile='{"Ref": "ServiceProfile"}',
    KeyName=Ref(keyname_param),
    SecurityGroups=[Ref(security_group)],
    UserData=Base64(Join("\n", [
        "#!/bin/bash",
        "yum update -y",
        "amazon-linux-extras install docker",
        "service docker start",
        "usermod -a -G docker ec2-user",
        'curl -L "https://github.com/docker/compose/releases/download/1.25.4/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose',
        "chmod +x /usr/local/bin/docker-compose",
        "yum install -y git",
        "cat <<-EOL > /opt/start_server.sh",
        "git clone https://github.com/HDFGroup/hsds.git",
        "export AWS_S3_GATEWAY=http://s3.amazonaws.com",
        Join("", ["export BUCKET_NAME=",Ref(bucket_param)]),
        'export HSDS_ENDPOINT=http://$(curl http://169.254.169.254/latest/meta-data/public-hostname)',
        Join("",["export AWS_IAM_ROLE=",Ref(ServiceRole)]),
        "cd hsds",
        "mv admin/config/passwd.default admin/config/passwd.txt",
        "./runall.sh",
        "EOL",
        "chmod o+rx /opt/start_server.sh"]))))



t.add_output([
    Output(
        "InstanceId",
        Description="InstanceId of the newly created EC2 instance",
        Value=Ref(ec2_instance),
    ),
    Output(
        "AZ",
        Description="Availability Zone of the newly created EC2 instance",
        Value=GetAtt(ec2_instance, "AvailabilityZone"),
    ),
    Output(
        "PublicIP",
        Description="Public IP address of the newly created EC2 instance",
        Value=GetAtt(ec2_instance, "PublicIp"),
    ),
    Output(
        "PrivateIP",
        Description="Private IP address of the newly created EC2 instance",
        Value=GetAtt(ec2_instance, "PrivateIp"),
    ),
    Output(
        "PublicDNS",
        Description="Public DNSName of the newly created EC2 instance",
        Value=GetAtt(ec2_instance, "PublicDnsName"),
    ),
    Output(
        "PrivateDNS",
        Description="Private DNSName of the newly created EC2 instance",
        Value=GetAtt(ec2_instance, "PrivateDnsName"),
    ),
])

print(t.to_json())
