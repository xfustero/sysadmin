# Exercise 1 
Consider the scenario where a user reports that a web application is unavailable. The application is hosted on a Nginx server which connects to a remote mysql server. You have been given shell access to the AWS EC2 instance hosting this application. Describe in general terms what steps you would take to investigate the cause of the outage and what commands you would use.
First, I would try to investigate if this is indeed a problem, and learn enough to mitigate the problem and get the application serving requests as soon as possible, to minimize disruption to our users.
Initially:
1. I would quickly try to check it myself if the application is running in the browser
2. I would quickly check any request metrics available, and try to gain any information
3. Check if the instance itself is healthy by connecting to it, and running `top` to check for load and memory usage, check for disk space available, for example
4. If instance is not healthy or can't connect to it, restart it
5. Check server logs for any clues

At this point, we should see if the issue is with the server, with the database, or is external
1. If the issue is with the server, try to restart it or perform some other appropriate action with clues from the log
2. If it is running, but log contains database failures, check the database server/logs and perform a similar analysis
3. If it is running and there are no visible database connectivity issues, the problem may be external, likely network connectivity

If there are network connectivity issues, we may need to use the Reachability Analyzer to check the connectivity from the internet to our server, and from our server to the database if necessary.
After the problem has been mitigated, it's time to do a root cause analysis, and take measures to ensure it doesn't happen again.

# Exercise 2 
Rewrite the Ansible role listed below to be idempotent. Suggest any other improvements.
```yaml
---
- name: Download terraform
  get_url: url=https://releases.hashicorp.com/terraform/0.11.7/terraform_0.11.7_linux_amd64.zip dest=/tmp/terraform_0.11.7.zip owner=root group=root mode=0644
- name: Extract terraform
  command: unzip -o /tmp/terraform_0.11.7.zip -d /usr/bin chdir=/tmp
  creates: "/usr/bin/terraform"
````
Explanation:
- The `get_url` task will not re-download if the dest file already exists, by default.
- The `command` task will not execute if the file name in the argument to ´creates´ exists.

Suggestions:
- Maybe not install terraform as root, perhaps install it as a regular user to another directory also in the path?
- Make the terraform version a variable for easier updates, and use the version as part of the file name argument to ´creates´
# Exercise 3
Write an S3 access policy for a bucket named example-bucket:
to allow read only access to objects in /my-ro-path/
to allow write only access to objects in /my-rw-path/
```
{
  "Id": "Policy1698247476082",
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Stmt1698246613200",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Effect": "Allow",
      "Resource": "arn:aws:s3:::example-bucket/my-ro-path/*",
      "Principal": {
        "AWS": [
          "example-bucket"
        ]
      }
    },
    {
      "Sid": "Stmt1698246707548",
      "Action": [
        "s3:PutObject"
      ],
      "Effect": "Allow",
      "Resource": "arn:aws:s3:::example-bucket/my-rw-path/*",
      "Principal": {
        "AWS": [
          "example-bucket"
        ]
      }
    }
  ]
}
```
## Bonus Question: 
Extending the above situation, describe what system changes would be necessary if the bucket was hosted by account A and the principal accessing the bucket was hosted by account B.

Configure object ACLs to include at least READ permission for Account B.
```
<AccessControlPolicy>
  <Owner>
    <ID> AccountACanonicalUserID </ID>
    <DisplayName> AccountADisplayName </DisplayName>
  </Owner>
  <AccessControlList>
...
    <Grant>
      <Grantee xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="CanonicalUser">
        <ID> AccountBCanonicalUserID </ID>
        <DisplayName> AccountBDisplayName </DisplayName>
      </Grantee>
      <Permission> READ </Permission>
    </Grant>
    ...
  </AccessControlList>
</AccessControlPolicy>
```
# Exercise 4
You have to deploy in kubernetes a basic webapp that consists in a Nginx server that needs to have a persistent volume. Please explain the main objects (namespace, pvc, etc) that will compose this application, how you would create the resources (helm, k8s manifests…) and how would you make the application accessible from your browser (service).

1. Namespace: I would create a new namespace called nginx-webapp, to provide some basic isolation and to avoid accidental resource overwrites due to name conflicts.
```
apiVersion: v1
kind: Namespace
metadata:
  name: nginx-webapp
```

2. StatefulSet with PersistentVolumeClaim template:
Since we require storage, and I assume individual storage for each pod, I would use a StatefulSet as a controller, to ensure that deployment and scaling are ordered and graceful, and allowing multiple replicas each with it´s own PV, and automatically dealing with attachment restrictions from cloud providers, etc...

```
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: nginx-webapp
  namespace: nginx-webapp
spec:
  serviceName: "nginx-service"
  replicas: 3
  selector:
    matchLabels:
      app: nginx-webapp
  template:
    metadata:
      labels:
        app: nginx-webapp
    spec:
      terminationGracePeriodSeconds: 10
      containers:
      - name: nginx
        image: nginx:latest
        ports:
        - containerPort: 80
        volumeMounts:
        - name: nginx-storage
          mountPath: /usr/share/nginx/html
  volumeClaimTemplates:
  - metadata:
      name: nginx-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 1Gi
```

3. Headless Service: Since we use a StatefulSet, I would use a Headlesss Service to manage the domain name for each pod.
Each pod will get a domain like nginx-webapp-0.nginx-service.nginx-webapp.cluster.local.svc and be directly accessible inside the cluster.

```
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
  namespace: nginx-webapp
  labels:
    app: nginx-webapp
spec:
  ports:
  - port: 80
    name: web
  clusterIP: None
  selector:
    app: nginx-webapp
```

4. External Service: For quick and easy access from outside the cluster, I would use a Service of type LoadBalancer, assuming our environment supports it.
This would already be accessible from the browser using the Service´s external IP at http://externa-ip/, though we should also maybe setup TLS and and CDN, maybe Cloudflare, in front of it.

```
apiVersion: v1
kind: Service
metadata:
  name: nginx-external-service
  namespace: nginx-webapp
spec:
  selector:
    app: nginx-webapp
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
  type: LoadBalancer
````

5. Deployment Strategy: For deployment strategy I would use raw manifests if this is a single use instance and static configuration, for simplicity.
If the app´s configuration would need to be dynamic and/or more complex, then I would use Helm, with configurable values.

# exercise 5
Explain, with as much detail as possible, what this Terraform code does:
```
terraform {
  required_version = "= 1.5.1"
  backend "s3" {
    region         = "us-west-2"
    key            = "myapp/terraform.tfstate"
    dynamodb_table = "infrastructure_statelock"
  }
  required_providers {
    aws = ">= 5.6.2"
  }
}

data "aws_ssm_parameter" "rds_passwd" {
    name = "/${var.application_name}/rds/passwd"
}

resource "aws_db_instance" "bitbucket_rds" {
    engine                 = postgres
    engine_version         = 12.14
    instance_class         = db.m6g.large
    storage_type           = gp2
    db_name                = myapp_db
    username               = test
    password               = data.aws_ssm_parameter.rds_passwd.value
    db_subnet_group_name   = aws_db_subnet_group.myapp_rds_subnet.name
    vpc_security_group_ids = [aws_security_group.myapp_rds_sg.id]
}
```
1.Configuration and Backend Configuration:
```
terraform {
  required_version = "= 1.5.1"
  backend "s3" {
    region         = "us-west-2"
    key            = "myapp/terraform.tfstate"
    dynamodb_table = "infrastructure_statelock"
  }
  required_providers {
    aws = ">= 5.6.2"
  }
}
```
- required_version: Indicates that Terraform version 1.5.1 is required for this code to run.
- backend "s3": Indicates that the state of the infrastructure managed by this Terraform configuration will be saved in an Amazon S3 bucket.
- region: The AWS region in which the S3 bucket is located.
- key: The S3 bucket path where the Terraform state file (terraform.tfstate) will be stored. Terraform's resources are tracked in this state file.
- dynamodb_table: The DynamoDB table that will be used for state locking. State locking ensures that only one Terraform operation is performed on your infrastructure at a time, preventing conflicts and inconsistencies.
- required_providers: Specifies which providers and versions are required to run this code. In this case, an AWS provider with a version of at least 5.6.2 is required.
It seems like we are missing the bucket name value, as can be seen in the documentation: https://developer.hashicorp.com/terraform/language/settings/backends/s3

2. AWS SSM Parameter Data Source:
```
data "aws_ssm_parameter" "rds_passwd" {
    name = "/${var.application_name}/rds/passwd"
}
```

This block retrieves a parameter from the Parameter Store of AWS Systems Manager (SSM).
The name of the parameter is derived from the value of the variable var.application_name, concatenated with /rds/passwd. It is retrieving the password for the RDS instance in this context.

3. AWS RDS Instance Resource:
```
resource "aws_db_instance" "bitbucket_rds" {
    engine                 = postgres
    engine_version         = 12.14
    instance_class         = db.m6g.large
    storage_type           = gp2
    db_name                = myapp_db
    username               = test
    password               = data.aws_ssm_parameter.rds_passwd.value
    db_subnet_group_name   = aws_db_subnet_group.myapp_rds_subnet.name
    vpc_security_group_ids = [aws_security_group.myapp_rds_sg.id]
}
```

- This block defines the bitbucket_rds AWS RDS instance resource.
- Configuration specifics:
  - PostgreSQL will be used as the database engine.
  - engine_version: The PostgreSQL engine version to be used is 12.14.
  - instance_class: db.m6g.large is the RDS instance type.
  - storage_type: gp2, which stands for General Purpose SSD, is the storage type.
  - db_name: The database name in the RDS instance will be myapp_db.
  - username: The database's master username is test.
  - password: The database password is obtained from the previously defined AWS SSM Parameter Store.
  - db_subnet_group_name: The RDS instance's subnet group is retrieved from another resource called aws_db_subnet_group.myapp_rds_subnet. This specifies where the RDS instance will be located within a VPC's subnets.
  - vpc_security_group_ids: An array of the RDS instance's security group IDs. It refers to a security group called aws_security_group.myapp_rds_sg in this case.
 In summary, this Terraform code configures AWS resources to create an RDS PostgreSQL instance with the specified configurations, stores its state in the AWS S3 backend, and retrieves the RDS password from the AWS SSM Parameter Store.
