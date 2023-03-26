#!/usr/bin/env python3

import argparse
import os
import boto3

parser = argparse.ArgumentParser(description='Cleanup old deployments in S3.')
parser.add_argument('--aws-access-key-id', help='AWS access key id. Default: AWS_ACCESS_KEY_ID environment variable. [String]', default=os.environ.get('AWS_ACCESS_KEY_ID'))
parser.add_argument('--aws-secret-access-key', help='AWS secret access key. Default: AWS_ACCESS_KEY_ID environment variable. [String]', default=os.environ.get('AWS_SECRET_ACCESS_KEY'))
parser.add_argument('--aws-endpoint-url', help='AWS endpoint URL (e.g., http://localhost:4566 for localstack). Default: None [String]', default=None)
parser.add_argument('--bucket', help='S3 bucket name. [String]', required=True)
parser.add_argument('--aws-region', help='AWS region (e.g., us-east-1). Default: "us-east-1". [String]', default='us-east-1')
parser.add_argument('--object-name', help='Name of object to search for to match prefix. Default: "index.html". [String]', default='index.html')
parser.add_argument('--keep-count', help='Number of recent matches you to keep. Default: 5 [Int]', type=int, default=5)
parser.add_argument('--dry-run', help='Skip deletion of data, and just show which data is targeted for deletion. Default: False [Switch/Boolean]', action='store_true', default=False)

def createSession(accessKeyId, secretAccessKey, region):
    session = boto3.Session(
            aws_access_key_id=accessKeyId,
            aws_secret_access_key=secretAccessKey,
            region_name=region)

    return session

def getS3Bucket(session, bucketName, endpointUrl):
    s3Bucket = session.resource("s3", endpoint_url=endpointUrl).Bucket(bucketName)

    return s3Bucket

def getLastModified(bucketObject):
    return bucketObject.last_modified

def getDeployments(bucket, objectName, keepCount):
    sortedDeployments = sorted(bucket.objects.all(), key=getLastModified, reverse=False)
    filteredDeployments = []
    targetDeployments = []
    for i, obj in enumerate(sortedDeployments):
        if objectName in obj.key:
            filteredDeployments.append(obj)
    if not filteredDeployments:
        raise Exception("No objects found matching specified name: {}".format(objectName))
    for i, obj in enumerate(filteredDeployments):
        if i >= keepCount:
            targetDeployments.append(obj)

    return targetDeployments

def getPrefixSize(bucket, prefix):
    totalSize = 0
    for obj in bucket.objects.filter(Prefix=prefix):
        totalSize = totalSize + obj.size
    return totalSize
    

def deleteDeployments(bucket, deployments, dryRun):
    totalSize = 0
    prefixCount = len(deployments)
    print("Deleting {} old deployments from s3://{}:\n".format(prefixCount, bucket.name))
    for i, obj in enumerate(deployments):
        tlObjectPrefix = str(obj.key).split('/')[0]
        prefixSize = getPrefixSize(bucket, tlObjectPrefix)
        totalSize = totalSize + prefixSize
        print(" Deleting s3://{}/{}".format(bucket.name, tlObjectPrefix))
        if dryRun:
            continue
        else:
            bucket.objects.filter(Prefix=tlObjectPrefix).delete()


    print("\nDeletion finished.\nTotal Deleted Deployments: {}\nTotal Deleted Data: {} KB".format(prefixCount, totalSize))
    if dryRun:
        print("!!! Dry run enabled, no data has been deleted. !!!")


if __name__ == "__main__":
    args = parser.parse_args()

    if not args.aws_access_key_id:
        raise Exception("AWS Access Key ID is empty.  Please set access key ID and try again.")
    if not args.aws_secret_access_key:
        raise Exception("AWS Secret Access Key is empty.  Please set secret access key and try again.")
    if args.keep_count < -1:
        raise Exception("Argument 'keep-count' must be -1 or greater.  Please set a valid value and try again.")

    session = createSession(args.aws_access_key_id, args.aws_secret_access_key, args.aws_region)
    s3Bucket = getS3Bucket(session, args.bucket, args.aws_endpoint_url)
    deployments = getDeployments(s3Bucket, args.object_name, args.keep_count)
    deleteDeployments(s3Bucket, deployments, args.dry_run)

