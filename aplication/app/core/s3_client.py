import boto3
import logging
from botocore.exceptions import ClientError
from app.config.settings import settings

logger = logging.getLogger(__name__)

class S3Client:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            aws_session_token=settings.AWS_SESSION_TOKEN,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.S3_BUCKET_NAME
    
    async def upload_file(self, file_content: bytes, s3_key: str, content_type: str = "video/mp4"):
        """Subir archivo a S3"""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type
            )
            
            # Generar URL del archivo
            file_url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
            logger.info(f"✅ Archivo subido a S3: {s3_key}")
            return file_url
            
        except ClientError as e:
            logger.error(f"❌ Error subiendo archivo a S3: {str(e)}")
            raise
    
    async def download_file(self, s3_key: str):
        """Descargar archivo de S3"""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return response['Body'].read()
        except ClientError as e:
            logger.error(f"❌ Error descargando archivo de S3: {str(e)}")
            raise
    
    async def delete_file(self, s3_key: str):
        """Eliminar archivo de S3"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"🗑️ Archivo eliminado de S3: {s3_key}")
        except ClientError as e:
            logger.error(f"❌ Error eliminando archivo de S3: {str(e)}")
            raise
    
    def generate_presigned_url(self, s3_key: str, expiration: int = 3600):
        """Generar URL firmada para acceso temporal"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"❌ Error generando URL firmada: {str(e)}")
            raise

# Instancia global
s3_client = S3Client()