# s3 service
import boto3
import os
import logging
from dotenv import load_dotenv
from boto3.s3.transfer import TransferConfig


class S3Manager:
    def __init__(self):
        load_dotenv()
        logging.basicConfig(level=logging.INFO)
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION_NAME")
        )
        self.bucket_name = os.getenv("S3_BUCKET_NAME")


    def get_url(self, filename: str):
        """Construct a URL for accessing an MP3 file from AWS S3."""
        return {
            "url": f"https://{self.bucket_name}.s3.{os.getenv('AWS_REGION_NAME')}.amazonaws.com/{filename}"
        }


    def upload_mp3_to_s3(self, paper_id: str):
        """Upload an MP3 file to S3."""
        local_file_path = f'static/podcast/{paper_id}/{paper_id}.mp3'
        if not os.path.exists(local_file_path):
            logging.error(f"File {local_file_path} does not exist.")
            return

        config = TransferConfig(multipart_threshold=1024**2*10)  # 10MB
        try:
            self.s3.upload_file(local_file_path, self.bucket_name,
                                f"{paper_id}.mp3", Config=config)
            logging.info(
                f"Successfully uploaded {local_file_path} as {paper_id}.mp3 to bucket {self.bucket_name}")
        except Exception as e:
            logging.error(f"Error uploading file: {e}")

    def upload_thumbnail_to_s3(self, paper_id: str, image_bytes: bytes):
        """Upload a thumbnail image to S3."""
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=f"{paper_id}.png",
            Body=image_bytes,
            ContentType='image/png'
        )

    def get_podcast_list(self):
        """Retrieve list of podcasts from S3 bucket."""
        try:
            response = self.s3.list_objects_v2(Bucket=self.bucket_name)
            files = response.get("Contents", [])
            return [
                {
                    'url': f"https://{self.bucket_name}.s3.{os.getenv('AWS_REGION_NAME')}.amazonaws.com/{obj['Key']}",
                    'filename': obj['Key'].split('/')[-1]
                }
                for obj in files
            ]
        except Exception as e:
            logging.error(f"Failed to get podcast list: {e}")
            return []

    def check_podcast_exists(self, paper_id: str):
        """Check if a podcast exists in S3 bucket."""
        podcast_list = self.get_podcast_list()
        for podcast in podcast_list:
            if podcast['filename'] == f'{paper_id}.mp3':
                return True, podcast['url']
        return False, None
