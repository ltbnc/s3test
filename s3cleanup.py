#!/usr/bin/env python3

""" ./s3cleanup.py

Cleanup script for code deployments in a target S3 bucket.

https://github.com/ltbnc/s3test

"""

# Ownership
__author__ = "Logan Barfield"
__date__ = "2023/03/26"
__version = "0.0.1"

# Module Imports
import argparse
import os
import boto3

# Set up arguments
parser = argparse.ArgumentParser(description='Cleanup old deployments in S3.')
parser.add_argument('--aws-access-key-id', help='AWS access key id. Default: AWS_ACCESS_KEY_ID environment variable. [String]', default=os.environ.get('AWS_ACCESS_KEY_ID'))
parser.add_argument('--aws-secret-access-key', help='AWS secret access key. Default: AWS_ACCESS_KEY_ID environment variable. [String]', default=os.environ.get('AWS_SECRET_ACCESS_KEY'))
parser.add_argument('--aws-endpoint-url', help='AWS endpoint URL (e.g., http://localhost:4566 for localstack). Default: None [String]', default=None)
parser.add_argument('--bucket', help='S3 bucket name. [String]', required=True)
parser.add_argument('--aws-region', help='AWS region (e.g., us-east-1). Default: "us-east-1". [String]', default='us-east-1')
parser.add_argument('--object-name', help='Name of object to search for to match prefix. Default: "index.html". [String]', default='index.html')
parser.add_argument('--keep-count', help='Number of recent matches you to keep. Default: 5 [Int]', type=int, default=5)
parser.add_argument('--dry-run', help='Skip deletion of data, and just show which data is targeted for deletion. Default: False [Switch/Boolean]', action='store_true', default=False)

# Create a new boto3 session - Portable for variable AWS services
def createSession(accessKeyId, secretAccessKey, region):
    session = boto3.Session(
            aws_access_key_id=accessKeyId,
            aws_secret_access_key=secretAccessKey,
            region_name=region)

    return session

# Get the target S3 bucket resource (technically you could just use this instead of creating a session, but it would be less portable and lead to code duplication)
def getS3Bucket(session, bucketName, endpointUrl):
    s3Bucket = session.resource("s3", endpoint_url=endpointUrl).Bucket(bucketName)

    return s3Bucket

# Grab the last modified date from an object.  Used in a couple of places so just made it a method to keep things more readable.
def getLastModified(bucketObject):
    return bucketObject.last_modified

# Get the most recent <keepCount> deployments in target <bucket> containing the target <objectName>
def getDeployments(bucket, objectName, keepCount):
    # Sort deployments by last modified date (since creation date isn't a thing, we assume no modifications since creation)
    sortedDeployments = sorted(bucket.objects.all(), key=getLastModified, reverse=False)
    filteredDeployments = []
    targetDeployments = []
    # Filter our found objects to the ones containing <objectName> in the string.  Boto3 doesn't allow suffix filtering when we query for the initial list, so this will have to suffice.
    for i, obj in enumerate(sortedDeployments):
        if objectName in obj.key:
            filteredDeployments.append(obj)
    # Bail out if there are no matches.
    if not filteredDeployments:
        raise Exception("No objects found matching specified name: {}".format(objectName))
    # Filter the list down to only the last <keepCount> matches
    for i, obj in enumerate(filteredDeployments):
        if i >= keepCount:
            targetDeployments.append(obj)

    return targetDeployments

# Method to get the size of all objects under a specified prefix.  Not strictly necessary, but I feel like it's useful information.  Causes additional S3 queries, so it does incur a charge, and could be removed or put behind a toggle if unwanted.
def getPrefixSize(bucket, prefix):
    totalSize = 0
    for obj in bucket.objects.filter(Prefix=prefix):
        totalSize = totalSize + obj.size
    return totalSize
    

# Actually handle the data deletion
def deleteDeployments(bucket, deployments, dryRun):
    totalSize = 0
    # Get the total number of prefixes to be deleted
    prefixCount = len(deployments)
    print("Deleting {} old deployments from s3://{}:\n".format(prefixCount, bucket.name))
    # Loop over target deployments to be deleted
    for i, obj in enumerate(deployments):
        # Split the object string and grab the top level prefix so we can recursively delete
        tlObjectPrefix = str(obj.key).split('/')[0]
        # Grab the data usage of objects under the prefix
        prefixSize = getPrefixSize(bucket, tlObjectPrefix)
        totalSize = totalSize + prefixSize
        print(" Deleting s3://{}/{}".format(bucket.name, tlObjectPrefix))
        # If the dryRun flag is set then skip the actual delete, otherwise delete the data
        if dryRun:
            continue
        else:
            bucket.objects.filter(Prefix=tlObjectPrefix).delete()


    print("\nDeletion finished.\nTotal Deleted Deployments: {}\nTotal Deleted Data: {} KB".format(prefixCount, totalSize))
    if dryRun:
        print("!!! Dry run enabled, no data has been deleted. !!!")


# Run this when executed as a script
if __name__ == "__main__":
    # Grab that arguments from the argparse parameters
    args = parser.parse_args()

    # Bail out if Access Key ID and/or Secret Access Key aren't set, or if an invalid Keep Count is set
    if not args.aws_access_key_id:
        raise Exception("AWS Access Key ID is empty.  Please set access key ID and try again.")
    if not args.aws_secret_access_key:
        raise Exception("AWS Secret Access Key is empty.  Please set secret access key and try again.")
    if args.keep_count < -1:
        raise Exception("Argument 'keep-count' must be -1 or greater.  Please set a valid value and try again.")

    # Create the boto3 AWS session
    session = createSession(args.aws_access_key_id, args.aws_secret_access_key, args.aws_region)

    ## After instantiating the session, everything under here is bucket specific. You could put these behind an argument flag with an if statement, or drop them into a parent method to extend this script for other AWS related actions
    # Grab the bucket
    s3Bucket = getS3Bucket(session, args.bucket, args.aws_endpoint_url)

    # Grab the deployments to target for deletion
    deployments = getDeployments(s3Bucket, args.object_name, args.keep_count)

    # Delete the deployments
    deleteDeployments(s3Bucket, deployments, args.dry_run)

