# s3test
S3 test script for deleting old deployment data.

## Usage

```
$ ./s3cleanup.py -h

usage: s3cleanup.py [-h] [--aws-access-key-id AWS_ACCESS_KEY_ID] [--aws-secret-access-key AWS_SECRET_ACCESS_KEY] [--aws-endpoint-url AWS_ENDPOINT_URL] --bucket BUCKET [--aws-region AWS_REGION] [--object-name OBJECT_NAME]
                   [--keep-count KEEP_COUNT] [--dry-run]

Cleanup old deployments in S3.

optional arguments:
  -h, --help            show this help message and exit
  --aws-access-key-id AWS_ACCESS_KEY_ID
                        AWS access key id. Default: AWS_ACCESS_KEY_ID environment variable. [String]
  --aws-secret-access-key AWS_SECRET_ACCESS_KEY
                        AWS secret access key. Default: AWS_ACCESS_KEY_ID environment variable. [String]
  --aws-endpoint-url AWS_ENDPOINT_URL
                        AWS endpoint URL (e.g., http://localhost:4566 for localstack). Default: None [String]
  --bucket BUCKET       S3 bucket name. [String]
  --aws-region AWS_REGION
                        AWS region (e.g., us-east-1). Default: "us-east-1". [String]
  --object-name OBJECT_NAME
                        Name of object to search for to match prefix. Default: "index.html". [String]
  --keep-count KEEP_COUNT
                        Number of recent matches you to keep. Default: 5 [Int]
  --dry-run             Skip deletion of data, and just show which data is targeted for deletion. Default: False [Switch/Boolean]
```

* Example:

```
$ ./s3cleanup.py --bucket testbucket --aws-endpoint-url http://localhost:4566 --aws-access-key-id test --aws-secret-access-key test --dry-run --keep-count 350 --dry-run 
```

* You can use environment variables for AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:

```
export AWS_ACCESS_KEY_ID=<access_key_id>
export AWS_SECRET_ACCESS_KEY=<secret_access_key>
```

* Run with --dry-run flag to see what data would be deleted.

## Prerequisuites

* Python3
* Boto3

```
$ sudo apt update
$ sudo apt install python3 python3-pip
$ pip3 install boto3
```

* Developed and tested on Ubuntu 20.04 with localstack


## Assumptions

* All deployments are in a single bucket.
* No versioning enabled on the target bucket.
* Less than 1000 total objects in the bucket.
* Prefixes are not objects themselves.
* All deployments have consistent file names.

## FAQ

* This script can be on any client machine the user deems secure with access to AWS or localstack. The only dependencies should be Python3 with boto3.
* If you're worried about accidentally deleting data, run with the --dry-run flag first.  I would also suggest testing this script against localstack or a non-production bucket first.

## Potential Improvements

* Use pagination to allow for buckets with more than 1000 objects.
* Reduce the total number of calls to AWS to reduce costs when deleting large amounts of data (potentially delete in chunks with boto3 delete_objects).

