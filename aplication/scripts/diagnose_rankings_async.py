#!/usr/bin/env python3
import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
logging.basicConfig(level=logging.INFO)

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.config.settings import settings

async def diagnose_rankings_async():
    print("🔍 DIAGNÓSTICO ASÍNCRONO DE RANKINGS")
    print("=" * 50)
    
    # Usar conexión asíncrona
    async_engine = create_async_engine(settings.DATABASE_URL)
    
    async with async_engine.connect() as conn:
        # 1. Verificar votos
        result = await conn.execute(text("SELECT COUNT(*) as total FROM Voto"))
        total_votos = result.scalar()
        print(f"📊 Total de votos: {total_votos}")
        
        # 2. Verificar videos procesados y públicos
        result = await conn.execute(text("""
            SELECT COUNT(*) as total 
            FROM Video 
            WHERE estado = 'procesado' AND visibilidad = 'publico'
        """))
        total_videos = result.scalar()
        print(f"🎬 Videos procesados públicos: {total_videos}")
        
        # 3. Verificar jugadores con votos (CONSULTA COMPLETA)
        result = await conn.execute(text("""
            SELECT 
                j.id as jugador_id,
                u.nombre,
                u.apellido, 
                c.nombre as ciudad,
                COUNT(vt.id) as total_votos
            FROM Jugador j
            JOIN User u ON j.usuario_id = u.id
            JOIN Ciudad c ON j.ciudad_id = c.id
            JOIN Video v ON j.id = v.jugador_id
            JOIN Voto vt ON v.id = vt.video_id
            WHERE v.estado = 'procesado' AND v.visibilidad = 'publico'
            GROUP BY j.id, u.nombre, u.apellido, c.nombre
            ORDER BY total_votos DESC
            LIMIT 5
        """))
        
        jugadores_con_votos = result.all()
        print(f"👤 Jugadores con votos encontrados: {len(jugadores_con_votos)}")
        
        for jugador in jugadores_con_votos:
            print(f"   - {jugador.nombre} {jugador.apellido} ({jugador.ciudad}): {jugador.total_votos} votos")
        
        # 4. Verificar datos en tabla Ranking
        result = await conn.execute(text("SELECT COUNT(*) as total FROM Ranking"))
        total_rankings = result.scalar()
        print(f"🏆 Registros en tabla Ranking: {total_rankings}")
        
        # 5. Verificar temporada actual
        from datetime import datetime
        now = datetime.now()
        year = now.year
        quarter = (now.month - 1) // 3 + 1
        temporada = f"{year}-Q{quarter}"
        print(f"📅 Temporada actual: {temporada}")
        
    print("=" * 50)
    
    if total_votos == 0:
        print("❌ PROBLEMA: No hay votos en la base de datos")
    elif len(jugadores_con_votos) == 0:
        print("❌ PROBLEMA: No hay jugadores con videos procesados y votos")
    elif total_rankings == 0:
        print("❌ PROBLEMA: La tabla Ranking está vacía (revisar el servicio)")
    else:
        print("✅ Todo parece correcto")

if __name__ == "__main__":
    asyncio.run(diagnose_rankings_async())