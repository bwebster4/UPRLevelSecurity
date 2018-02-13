import boto3
from application import S3_BUCKET_NAME

s3 = boto3.client('s3')
s3.create_bucket(Bucket=S3_BUCKET_NAME)

