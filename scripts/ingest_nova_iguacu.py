import asyncio
import sys
import logging
from datetime import date, timedelta
from pathlib import Path

# Adiciona o diretório raiz ao path para permitir importações do src
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.ingestors.diario_oficial import diario_ingestor
from src.core.database import db_manager

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ingest_nova_iguacu")

async def get_last_ingested_date():
    """
    Busca no banco de dados a data da última publicação de diário oficial processada.
    """
    try:
        if not db_manager._sqlite_connection:
            await db_manager.get_sqlite()
            
        async with db_manager._sqlite_connection.execute(
            "SELECT MAX(publication_date) FROM documents WHERE source = 'official_gazette'"
        ) as cursor:
            row = await cursor.fetchone()
            if row and row[0]:
                return date.fromisoformat(row[0])
    except Exception as e:
        logger.error(f"Erro ao buscar última data no banco: {e}")
    return None

async def main():
    logger.info("🛡️  Sentinela Cívico: Iniciando Ingestão de Nova Iguaçu")
    
    # 1. Determina a data de início
    last_date = await get_last_ingested_date()
    
    if last_date:
        # Se já temos dados, começamos do dia seguinte à última data encontrada
        # (Adicionamos um pequeno overlap de 1 dia por segurança se quiser, mas aqui vamos no dia seguinte)
        since_date = last_date + timedelta(days=1)
        logger.info(f"📅 Retomando ingestão a partir de: {since_date} (Último registro: {last_date})")
    else:
        # Se não há dados, inicia busca histórica de 1 ano (para testes iniciais conforme plano)
        since_date = date.today() - timedelta(days=365)
        logger.info(f"📅 Início histórico detectado. Buscando diários desde: {since_date}")
        
    until_date = date.today()
    
    if since_date > until_date:
        logger.info("✅ Tudo atualizado! Nenhuma nova data para pesquisar.")
        return

    # Palavras-chave estratégicas para a Tese de Nova Iguaçu
    keywords = ["Tinguá", "Meio Ambiente", "Licitação", "Contrato"]
    
    try:
        # 2. Busca os diários
        logger.info(f"🔍 Pesquisando diários entre {since_date} e {until_date}...")
        gazettes = await diario_ingestor.fetch_gazettes(
            since=since_date,
            until=until_date
        )
        
        if not gazettes:
            logger.warning("⚠️  Nenhum diário oficial encontrado no período.")
            return

        logger.info(f"✅ Encontrados {len(gazettes)} diários brutos. Iniciando processamento...")
        
        # 3. Processa e armazena (inclui deduplicação, download de PDF, OCR e indexação RAG)
        await diario_ingestor.process_and_store(gazettes, keywords=keywords)
        
        logger.info("🎉 Processo de integração concluído com sucesso!")
        
    except Exception as e:
        logger.error(f"❌ Erro fatal durante a ingestão: {e}")
    finally:
        await diario_ingestor.close()
        if hasattr(db_manager, "close"):
            await db_manager.close()

if __name__ == "__main__":
    asyncio.run(main())
