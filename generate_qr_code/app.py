import json
import qrcode
from io import BytesIO
import os
import uuid
import logging
import boto3
from botocore.exceptions import ClientError

S3_BUCKET = os.getenv('S3_BUCKET', 'generate-qr-code-api')
REGION = os.getenv('REGION', 'eu-west-2')
URL_EXPIRE = os.getenv('URL_EXPIRE', 86400)
LOGGER_LEVEL = os.getenv('LOGGER_LEVEL', 'INFO').upper()

logger = logging.getLogger()
logger.setLevel(getattr(logging, LOGGER_LEVEL))

s3_client = boto3.client('s3')

def generate_qr_code_image(data: str) -> bytes:
    """
    Create a PNG QR‑code for the supplied text. Returns raw PNG bytes.
    """
    try:
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        return buffer.getvalue()
    except Exception as e:
        logger.error(f"Failed to generate QR code: {e}")
        raise RuntimeError(f"Failed to generate QR code: {e}") from e

def write_to_s3(bucket: str, key: str, data: bytes) -> str:
    """
    Uploads the given data to S3 and returns the public URL.
    """
    try:
        s3_client.put_object(Bucket=bucket, Key=key, Body=data, ContentType='image/png')
        return f"https://{bucket}.s3.amazonaws.com/{key}"
    except ClientError as e:
        logger.error(f"Failed to upload to S3: {e}")
        raise RuntimeError(f"Failed to upload data to S3: {e}") from e

def generate_presigned_url(bucket: str, key: str, expires_in: int = URL_EXPIRE) -> str:
    try:
        return s3_client.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=expires_in,
            HttpMethod='GET'
        )
    except ClientError as e:
        logger.error(f"Failed to generate presigned URL: {e}")
        raise RuntimeError(f"Failed to generate presigned URL: {e}") from e

def lambda_handler(event, context):
    try:
        query_params = event.get('queryStringParameters') or {}
        text = query_params.get('text', '')
        if not text:
            raise ValueError("Missing 'text' query string parameter")

        qr_code_image = generate_qr_code_image(text)

        key = f"qr-codes/{uuid.uuid4()}.png"

        write_to_s3(S3_BUCKET, key, qr_code_image)

        presigned_url = generate_presigned_url(S3_BUCKET, key)

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "message": "Image uploaded successfully",
                "bucket": S3_BUCKET,
                "key": key,
                "url": presigned_url 
            }),
        }
    
    except Exception as e:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)}),
        }