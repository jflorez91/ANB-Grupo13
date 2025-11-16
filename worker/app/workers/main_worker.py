import time
import logging
from app.workers.sqs_consumer import sqs_consumer
from app.workers.ranking_processor import RankingProcessor

logger = logging.getLogger(__name__)

class MainWorker:
    def __init__(self):
        self.ranking_processor = RankingProcessor()
        self.running = True
        self.cycle_count = 0
    
    def start(self):
        """Worker principal que ahora usa SQS + rankings periódicos"""
        logger.info("🚀 Iniciando ANB Worker con SQS...")
        
        while self.running:
            try:
                self.cycle_count += 1
                
                # ✅ 1. PROCESAR MENSAJES SQS (VIDEOS)
                messages_processed = sqs_consumer.poll_messages()
                
                if messages_processed > 0:
                    logger.info(f"📥 Procesados {messages_processed} mensajes SQS")
                
                # ✅ 2. ACTUALIZAR RANKINGS CADA 10 CICLOS (≈ 5 minutos)
                if self.cycle_count % 10 == 0:
                    try:
                        logger.info("🔄 Ejecutando actualización periódica de rankings...")
                        ranking_result = self.ranking_processor.update_rankings()
                        logger.info(f"🏅 Rankings actualizados: {ranking_result}")
                        self.cycle_count = 0  # Resetear contador
                    except Exception as e:
                        logger.error(f"❌ Error actualizando rankings: {str(e)}")
                
                # ✅ 3. ESPERAR ANTES DEL SIGUIENTE CICLO
                # Si hay mensajes, esperar menos; si no, esperar más
                sleep_time = 2 if messages_processed > 0 else 10
                time.sleep(sleep_time)
                
            except KeyboardInterrupt:
                logger.info("🛑 Deteniendo worker...")
                self.running = False
            except Exception as e:
                logger.error(f"❌ Error en ciclo principal: {str(e)}")
                time.sleep(30)  # Esperar más en caso de error

    def start_sqs_only(self):
        """Alternativa: Solo SQS sin rankings periódicos"""
        logger.info("🚀 Iniciando ANB Worker (SQS solamente)...")
        
        # ✅ SOLO SQS - Los rankings se activarán por votos via SQS
        sqs_consumer.start_consuming()

if __name__ == "__main__":
    worker = MainWorker()
    worker.start()