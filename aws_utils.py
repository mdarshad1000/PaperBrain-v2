import boto3
import os
from dotenv import load_dotenv

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
        filename_test =[]
        for file in files:
            filename_test.append(file['Key'])
        podcast_urls = []
        for obj in response.get("Contents", []):
            podcast_urls.append({'url':                
                s3.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": bucket_name, "Key": obj["Key"]},
                    ExpiresIn=3600 
                ),'filename': obj['Key'].split('/')[-1]}
            )
        # print(podcast_urls)
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
    # Upload the local file to S3 with the specified key (paper_id)
    try:
        s3.upload_file(local_file_path, bucket_name, f"{paper_id}.mp3")
        print(f"Successfully uploaded {local_file_path} as {paper_id}.mp3 to bucket {bucket_name}")
    except Exception as e:
        print(f"Error uploading file: {e}")
    

def get_mp3_url(filename: str):
    try:
        # Generate a pre-signed URL for accessing the image from AWS S3
        response = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": filename},
            ExpiresIn=None,
            HttpMethod="GET",
        )
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