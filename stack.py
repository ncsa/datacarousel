from troposphere import Ref, Template, Parameter, Tags, Output
from troposphere.batch import ComputeEnvironment, ComputeResources, \
    JobQueue, ComputeEnvironmentOrder, JobDefinition, \
    ContainerProperties
from troposphere.ec2 import SecurityGroup
from troposphere.iam import Role, InstanceProfile

t = Template()

SubnetA = t.add_parameter(Parameter(
    'SubnetA',
    ConstraintDescription="Must be an existent subnet ID, in the chosen VPC.",
    Type="AWS::EC2::Subnet::Id"
))

VpcSecurityGroup = t.add_parameter(Parameter(
    'VpcSecurityGroup',
    Description="The VPCs default Security Group",
    ConstraintDescription='Must be a valid Security Group ID.',
    Type='AWS::EC2::SecurityGroup::Id'
))


Vpc = t.add_parameter(Parameter(
    'Vpc',
    ConstraintDescription='Must be a valid VPC ID.',
    Type='AWS::EC2::VPC::Id'
))

HSDSImage = t.add_parameter(Parameter(
    'HSDSImage',
    Type='String',
    Default='bengal1/h5pyd:develop',
))

BatchServiceRole = t.add_resource(Role(
    'BatchServiceRole',
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

BatchInstanceRole = t.add_resource(Role(
    'BatchInstanceRole',
    Path='/',
    Policies=[],
    ManagedPolicyArns=[
        'arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role',  # NOQA
        'arn:aws:iam::aws:policy/AmazonS3FullAccess'
    ],
    AssumeRolePolicyDocument={'Statement': [{
        'Action': ['sts:AssumeRole'],
        'Effect': 'Allow',
        'Principal': {'Service': ['ec2.amazonaws.com']}
    }]},
))

BatchJobRole = t.add_resource(Role(
    'BatchJobRole',
    Path='/',
    Policies=[],
    ManagedPolicyArns=[
        'arn:aws:iam::aws:policy/AmazonS3FullAccess'
    ],
    AssumeRolePolicyDocument={'Statement': [{
        'Action': ['sts:AssumeRole'],
        'Effect': 'Allow',
        'Principal': {'Service': ['ecs-tasks.amazonaws.com']}
    }]},
))

BatchInstanceProfile = t.add_resource(InstanceProfile(
    'BatchInstanceProfile',
    Path='/',
    Roles=[Ref(BatchInstanceRole)],
))

BatchSecurityGroup = t.add_resource(SecurityGroup(
    'BatchSecurityGroup',
    VpcId=Ref(Vpc),
    GroupDescription='Enable access to Batch instances',
    Tags=Tags(Name='batch-sg')
))

BatchComputeEnvironment = t.add_resource(ComputeEnvironment(
    'DataCarouselComputeEnvironment',
    Type='MANAGED',
    ServiceRole=Ref(BatchServiceRole),
    ComputeResources=ComputeResources(
        'DataCarouselComputeResources',
        Type='EC2',
        DesiredvCpus=1,
        MinvCpus=0,
        MaxvCpus=10,
        InstanceTypes=['optimal'],
        InstanceRole=Ref(BatchInstanceProfile),
        SecurityGroupIds=[Ref(VpcSecurityGroup)],
        Subnets=[
            Ref(SubnetA)
        ],
        Tags=dict(
            Name='batch-compute-environment',
            Project='NASA Data Carousel'
        )
    )
))

DataCarouselJobQueue = t.add_resource(JobQueue(
    'DataCarouselJobQueue',
    ComputeEnvironmentOrder=[
        ComputeEnvironmentOrder(
            ComputeEnvironment=Ref(BatchComputeEnvironment),
            Order=1
        ),
    ],
    Priority=1,
    State='ENABLED',
    JobQueueName='datacarousel-job-queue'
))

command = 'python work_flow.py 2002 12 s3://terrafusiondatasampler/P22/TERRA_BF_L1B_O85079_20151216160910_F000_V001.h5'
t.add_resource(JobDefinition(
    "ComputeRadience",
    Type='Container',
    ContainerProperties=ContainerProperties(
        Command=command.split(' '),
        Image='bengal1/climatemarble:latest',
        Memory=4096,
        Vcpus=1,
        JobRoleArn=Ref(BatchJobRole)
    )
))

hsload_command = "python /opt/nasa/index_file.py -e Ref::hsds_endpoint -p admin -u admin -s3 Ref::s3_input_file --domain Ref::domain"

t.add_resource(JobDefinition(
    "hsload",
    Type='Container',
    ContainerProperties=ContainerProperties(
        Command=hsload_command.split(' '),
        Image=Ref(HSDSImage),
        Memory=1024,
        Vcpus=1,
        JobRoleArn=Ref(BatchJobRole)
    )
))


t.add_output([
    Output('DataCarouselComputeEnvironment', Value=Ref(BatchComputeEnvironment)),
    Output('BatchSecurityGroup', Value=Ref(BatchSecurityGroup)),
    Output('DataCarouselJobQueue', Value=Ref(DataCarouselJobQueue))
])

print(t.to_json())
