import boto3
from botocore.exceptions import ClientError


class S3Service:
    def __init__(self, bucket_name: str):
        self.s3_client = boto3.client("s3")
        self.bucket_name = bucket_name

    def upload_file_content(self, file_content: bytes, destination_key: str, content_type: str = "text/csv") -> str:
        """
        Uploads raw bytes of a file to S3 bucket and returns the destination key.
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=destination_key,
                Body=file_content,
                ContentType=content_type
            )
            return destination_key
        except ClientError as e:
            print(f"Error uploading file to S3: {e.response['Error']['Message']}")
            raise e

