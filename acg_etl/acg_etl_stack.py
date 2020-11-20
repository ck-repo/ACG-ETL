from aws_cdk import (
    core,
    aws_lambda as _lambda,
    aws_dynamodb,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_events,
    aws_events_targets,
)

class AcgEtlStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Creates VPC
        vpc = ec2.Vpc(self, id)

        # Creates RDS Database
        instance = rds.DatabaseInstance(
            self, "RDS",
            database_name="covid",
            engine=rds.DatabaseInstanceEngine.mysql(
                version=rds.MysqlEngineVersion.VER_8_0_21
            ),
            vpc=vpc,
            port=3306,
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE2,
                ec2.InstanceSize.MICRO,
            ),
            removal_policy=core.RemovalPolicy.DESTROY,
            deletion_protection=False,
            vpc_placement=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
        )

        # Add inbound rule to RDS SG
        instance.connections.allow_from_any_ipv4(ec2.Port.tcp(3306), "Open to the world")

        # Defines Lambda layers
        python_etl_layer = _lambda.LayerVersion(
            self, "python-etl",
            code=_lambda.AssetCode('C:\Code\ACG Challenge – AWS ETL\python.zip'))
        
        # Defines an AWS Lambda resource
        my_lambda = _lambda.Function(
            self, 'etlhandler',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='etl.extract_csv1',
            layers=[python_etl_layer],
            timeout=core.Duration.seconds(30),
            memory_size=(256)
        )

        # Add Lambda Environment Variables
        my_lambda.add_environment("RDS_INSTANCE", instance.instance_endpoint.hostname)
        my_lambda.add_environment("SECRET_NAME", instance.secret.secret_full_arn)
        
        # Grant permission to lambda to access RDS Secret
        instance.secret.grant_read(my_lambda)

        # Create a Cloudwatch Event rule
        four_hour_rule = aws_events.Rule(
            self, "four_hour_rule",
            schedule=aws_events.Schedule.rate(core.Duration.minutes(240)),
        )

        # Add target to Cloudwatch Event
        four_hour_rule.add_target(aws_events_targets.LambdaFunction(my_lambda))