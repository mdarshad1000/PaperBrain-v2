import boto3
import os
from dotenv import load_dotenv
from boto3.s3.transfer import TransferConfig

load_dotenv()

s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION_NAME")
)

bucket_name = os.getenv("S3_BUCKET_NAME")


def get_podcast_list():
    try:
        # List all objects (podcasts) in the S3 bucket
        response = s3.list_objects_v2(Bucket=bucket_name)
        files = response.get("Contents")
        podcast_urls = []
        for obj in files:
            # Construct a URL for accessing the object from AWS S3
            url = f"https://{bucket_name}.s3.{os.getenv('AWS_REGION_NAME')}.amazonaws.com/{obj['Key']}"
            podcast_urls.append({'url': url, 'filename': obj['Key'].split('/')[-1]})
    except Exception as e:
        print(e)
    return podcast_urls


def check_podcast_exists(paper_id: str):
    podcast_list = get_podcast_list()
    for podcast in podcast_list:
        if podcast['filename'] == f'{paper_id}.mp3':
            return True, podcast['url']
    return False, None


def upload_mp3_to_s3(paper_id: str):
    # Create an S3 client
    s3 = boto3.client('s3')
    local_file_path = f'podcast/{paper_id}/{paper_id}.mp3'
    # Create a transfer configuration that uses multipart upload for files over 10MB
    config = TransferConfig(multipart_threshold=1024**2*10)  # 10MB
    # Upload the local file to S3 with the specified key (paper_id)
    try:
        s3.upload_file(local_file_path, bucket_name, f"{paper_id}.mp3", Config=config)
        print(f"Successfully uploaded {local_file_path} as {paper_id}.mp3 to bucket {bucket_name}")
    except Exception as e:
        print(f"Error uploading file: {e}")


def get_mp3_url(filename: str):
    try:
        # Construct a URL for accessing the object from AWS S3
        response = f"https://{bucket_name}.s3.{os.getenv('AWS_REGION_NAME')}.amazonaws.com/{filename}"
        return {"url": response}
    except Exception as e:
        raise e
    

def get_podcast_json_file():
    k = get_podcast_list()
    x = {}

    ptr = 1
    for item in k:
        x.update({ptr:item['url']})
        ptr += 1
        
    import json
    with open('pm3_files.json', 'w') as f:
        json.dump(x, f)
        
# get_podcast_json_file()
# print(get_mp3_url('1905.10543v1.mp3'))