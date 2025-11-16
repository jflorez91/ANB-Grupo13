import boto3
import json
import logging
import time
from app.config.settings import settings

logger = logging.getLogger(__name__)

class SQSConsumer:
    def __init__(self):
        self.sqs = boto3.client(
            'sqs',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            aws_session_token=settings.AWS_SESSION_TOKEN,
            region_name=settings.AWS_REGION
        )
        
        # ✅ USA LA MISMA URL QUE EN ANB-API
        self.queue_url = "https://sqs.us-east-1.amazonaws.com/358815540510/anb-main-queue"
        self.running = True
    
    def poll_messages(self):
        """ANB-WORKERS escucha mensajes de SQS constantemente"""
        try:
            response = self.sqs.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=5,
                WaitTimeSeconds=10
            )
            
            messages = response.get('Messages', [])
            
            if messages:
                logger.info(f"📥 ANB-WORKERS → SQS: Recibidos {len(messages)} mensajes")
            
            for message in messages:
                try:
                    # Procesar el mensaje
                    body = json.loads(message['Body'])
                    action = body.get("action")
                    
                    if action == "process_video":
                        self.process_video_message(body)
                    
                    # Eliminar mensaje de la cola
                    self.sqs.delete_message(
                        QueueUrl=self.queue_url,
                        ReceiptHandle=message['ReceiptHandle']
                    )
                    
                    logger.info(f"✅ ANB-WORKERS: Mensaje procesado y eliminado de cola")
                    
                except Exception as e:
                    logger.error(f"❌ ANB-WORKERS Error procesando mensaje: {str(e)}")
            
            return len(messages)
            
        except Exception as e:
            logger.error(f"❌ ANB-WORKERS → SQS Error: {str(e)}")
            return 0
    
    def process_video_message(self, message_data):
        """Procesar mensaje de video usando el código existente"""
        try:
            from app.workers.processor_service import ProcessorService
            
            video_id = message_data["video_id"]
            logger.info(f"🎬 ANB-WORKERS: Procesando video {video_id} desde SQS")
            
            processor = ProcessorService()
            result = processor.process_single_video(video_id)
            
            if result.get("success"):
                logger.info(f"✅ ANB-WORKERS: Video {video_id} procesado exitosamente")
            else:
                logger.error(f"❌ ANB-WORKERS: Error procesando video {video_id}: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ ANB-WORKERS Error procesando video: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def start_consuming(self):
        """Iniciar consumo continuo de mensajes SQS"""
        logger.info("🚀 ANB-WORKERS: Iniciando consumidor SQS...")
        
        while self.running:
            try:
                messages_processed = self.poll_messages()
                
                if messages_processed == 0:
                    # Solo loggear cada 30 segundos cuando no hay mensajes
                    time.sleep(5)
                else:
                    time.sleep(2)  # Esperar menos si hay mensajes
                
            except KeyboardInterrupt:
                logger.info("🛑 ANB-WORKERS: Deteniendo consumidor SQS...")
                self.running = False
            except Exception as e:
                logger.error(f"❌ ANB-WORKERS Error en ciclo principal: {str(e)}")
                time.sleep(10)

# Instancia global
sqs_consumer = SQSConsumer()