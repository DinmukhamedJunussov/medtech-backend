# AWS Textract OCR handling

import boto3
from botocore.exceptions import ClientError


class OcrAws:
    def __init__(self):
        self.client = boto3.client('textract')

    def process_image(self, image_path):
        pass