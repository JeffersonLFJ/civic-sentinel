import asyncio
import sys
from pathlib import Path
from datetime import date, timedelta
import logging

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestors.diario_oficial import diario_ingestor

logging.basicConfig(level=logging.DEBUG)

async def test_connection():
    try:
        print("🔍 Testando conexão com a API do Querido Diário...")
        # busca os últimos 3 dias
        since = date.today() - timedelta(days=3)
        gazettes = await diario_ingestor.fetch_gazettes(since=since)
        print(f"✅ Conexão bem-sucedida! Encontrados {len(gazettes)} diários nos últimos 3 dias.")
        if gazettes:
            print(f"Exemplo: {gazettes[0].get('date')} - {gazettes[0].get('territory_name')}")
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
    finally:
        await diario_ingestor.close()

if __name__ == '__main__':
    asyncio.run(test_connection())
