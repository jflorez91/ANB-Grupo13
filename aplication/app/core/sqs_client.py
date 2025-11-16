import boto3
import json
import logging
from app.config.settings import settings

logger = logging.getLogger(__name__)

class SQSClientAPI:
    def __init__(self):
        self.sqs = boto3.client(
            'sqs',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            aws_session_token=settings.AWS_SESSION_TOKEN,
            region_name=settings.AWS_REGION
        )
        
        # ✅ USA TU URL REAL AQUÍ
        self.queue_url = "https://sqs.us-east-1.amazonaws.com/358815540510/anb-main-queue"
    
    def send_video_for_processing(self, video_data: dict):
        """ANB-API envía video a SQS para que WORKERS lo procesen"""
        try:
            message_body = {
                "action": "process_video",
                "video_id": video_data["video_id"],
                "jugador_id": video_data["jugador_id"],
                "s3_key_original": video_data["s3_key_original"],
                "titulo": video_data["titulo"],
                "timestamp": video_data.get("timestamp")
            }
            
            response = self.sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(message_body)
            )
            
            logger.info(f"📨 ANB-API → SQS: Video {video_data['video_id']} enviado a cola")
            return {"success": True, "message_id": response['MessageId']}
            
        except Exception as e:
            logger.error(f"❌ ANB-API → SQS Error: {str(e)}")
            return {"success": False, "error": str(e)}

# Instancia global
sqs_client_api = SQSClientAPI()