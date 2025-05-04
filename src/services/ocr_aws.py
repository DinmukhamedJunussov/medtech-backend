import boto3

textract_client = boto3.client('textract', region_name='us-east-1')

async def analyze_document(file_bytes):
    response = textract_client.analyze_document(
        Document={'Bytes': file_bytes},
        FeatureTypes=['TABLES']
    )
    return response