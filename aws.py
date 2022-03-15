import boto3
from botocore.exceptions import NoCredentialsError
import os
import io


def upload_to_aws(local_file_name, bucket, s3_file_name):
    s3 = s3_connection()
    try:
        s3.upload_file(local_file_name, bucket, s3_file_name)
        print("Upload Successful")
        return True
    except FileNotFoundError:
        print("The file was not found")
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False


def s3_connection():
    try:
        s3 = boto3.client('s3', aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
                        aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'])
        return s3
    except:
        s3 = boto3.client('s3', aws_access_key_id='AKIASL3TWUMYHMDW3SM2', aws_secret_access_key='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')
        return s3
    else:
        raise("Unable to connect to s3 using given credientials")


bi = io.BytesIO()
bucket="qa-projects-gn"
import pdb;pdb.set_trace()
bi.write(b"R0lGODdhAQABAPAAAP8AAAAAACwAAAAAAQABAAACAkQBADs=")
print(bi.getvalue())
bi.seek(0)
s3_connection().upload_fileobj(bi, "qa-projects-gn/test/BytesIO/image.jpg")

s3_connection().put_object(Body=bi, Bucket="qa-projects-gn", Key="image.jpg")

# upload_to_aws('py3.png', bucket="qa-projects-gn", s3_file_name="py3.png") # Normal upload working