import time
import logging
from app.workers.processor_service import ProcessorService
from app.workers.ranking_processor import RankingProcessor

logger = logging.getLogger(__name__)

class MainWorker:
    def __init__(self):
        self.video_processor = ProcessorService()
        self.ranking_processor = RankingProcessor()
        self.running = True
    
    def start(self):
        """Worker principal que monitorea continuamente"""
        logger.info("🚀 Iniciando ANB Worker Desacoplado...")
        
        cycle_count = 0
        
        while self.running:
            try:
                cycle_count += 1
                logger.info(f"🔄 Ciclo de procesamiento #{cycle_count}")
                
                # 1. Procesar videos pendientes
                video_result = self.video_processor.process_pending_videos()
                logger.info(f"📹 Videos procesados: {video_result}")
                
                # 2. Cada 10 ciclos, actualizar rankings (≈ cada 5 minutos)
                if cycle_count % 10 == 0:
                    ranking_result = self.ranking_processor.update_rankings()
                    logger.info(f"🏅 Rankings actualizados: {ranking_result}")
                    cycle_count = 0  # Resetear contador
                
                # 3. Esperar antes del siguiente ciclo
                time.sleep(30)  # Revisar cada 30 segundos
                
            except KeyboardInterrupt:
                logger.info("🛑 Deteniendo worker...")
                self.running = False
            except Exception as e:
                logger.error(f"❌ Error en ciclo principal: {str(e)}")
                time.sleep(60)  # Esperar más en caso de error

if __name__ == "__main__":
    worker = MainWorker()
    worker.start()