import asyncio
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestors.local_folder import local_ingestor

async def test_scan():
    print("🚀 Iniciando Scan Local de Teste...")
    results = await local_ingestor.scan_and_process()
    print(f"📊 Resultado: {results}")

if __name__ == '__main__':
    asyncio.run(test_scan())
