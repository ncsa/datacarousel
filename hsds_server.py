from troposphere import Base64, FindInMap, GetAtt, Join
from troposphere import Parameter, Output, Ref, Template
import troposphere.ec2 as ec2
from troposphere.iam import Role

t = Template()

keyname_param = t.add_parameter(Parameter(
    "KeyName",
    Description="Name of an existing EC2 KeyPair to enable SSH "
                "access to the instance",
    Type="String",
))

ServiceRole = t.add_resource(Role(
    'ServiceRole',
    Path='/',
    Policies=[],
    ManagedPolicyArns=[
        'arn:aws:iam::aws:policy/service-role/AWSBatchServiceRole',
    ],
    AssumeRolePolicyDocument={'Statement': [{
        'Action': ['sts:AssumeRole'],
        'Effect': 'Allow',
        'Principal': {'Service': ['batch.amazonaws.com']}
    }]},
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
    ImageId="ami-0f7919c33c90f5b58",
    InstanceType="m4.large",
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
        "export BUCKET_NAME=terrafusiondatasampler",
        "export HSDS_ENDPOINT=http://localhost",
        Join("",["export AWS_IAM_ROLE=",Ref(ServiceRole)]),
        "cd hsds",
        "mv admin/config/passwd.default admin/config/passwd.txt"
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
