import typer
import uvicorn
import pytest
import asyncio
from pathlib import Path
import os
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.config import settings

app = typer.Typer(
    name="Sentinela CLI",
    help="Ferramenta de linha de comando para gestão do Sentinela Cívico.",
    add_completion=False,
)

@app.command()
def start(
    host: str = "0.0.0.0", 
    port: int = 8000, 
    reload: bool = True
):
    """
    Inicia o servidor API (FastAPI).
    """
    print(f"🦅 Iniciando Sentinela API em http://{host}:{port}")
    uvicorn.run("src.interfaces.api.main:app", host=host, port=port, reload=reload)

@app.command()
def test(
    integration: bool = False,
    verbose: bool = False
):
    """
    Executa a suíte de testes (Pytest).
    """
    print("🧪 Executando testes...")
    args = []
    if not integration:
        # Default to unit tests only unless specified
        args.append("tests/unit")
    else:
        args.append("tests")
        
    if verbose:
        args.append("-v")
        
    retcode = pytest.main(args)
    if retcode == 0:
        print("✅ Todos os testes passaram!")
    else:
        print("❌ Falha nos testes.")
        raise typer.Exit(code=retcode)

@app.command()
def ingest(
    target: str = typer.Argument(..., help="Alvo da ingestão (ex: nova-iguacu, diario-oficial)"),
    days: int = typer.Option(7, help="Número de dias para buscar"),
    keywords: str = typer.Option("", help="Palavras-chave separadas por vírgula")
):
    """
    Executa rotinas de ingestão de dados.
    """
    print(f"📥 Iniciando ingestão para alvo: {target}")
    
    if target == "nova-iguacu":
        # Import script logic dynamically or call a function
        # For better architecture, we should extract the logic from scripts/ingest_nova_iguacu.py to a src module
        # But for now, let's wrap the script execution or import it
        from scripts.ingest_nova_iguacu import main as ingest_main
        
        # We need to adapt the script to accept args if it doesn't already
        # The script `ingest_nova_iguacu.py` doesn't take args currently, it hardcodes logic.
        # Ideally we refactor it, but simple run for now:
        asyncio.run(ingest_main())
        
    elif target == "local":
        print("📁 Escaneando pasta local data/ingest...")
        # Call local ingestor logic
        from src.ingestors.local_folder import local_ingestor
        async def run_local():
            files = await local_ingestor.list_pending_files()
            print(f"Arquivos pendentes: {len(files)}")
            # This is just a list, actual processing needs selection.
            # Automated processing all:
            if files and typer.confirm("Deseja processar TODOS os arquivos pendentes agora?"):
                # Simplification: assume 'document' type for all for CLI bulk
                items = [{"filename": f["filename"], "doc_type": "auto"} for f in files]
                res = await local_ingestor.process_selected_files(items)
                print(f"Processado: {res}")
        
        asyncio.run(run_local())
        
    else:
        print(f"⚠️ Alvo '{target}' desconhecido.")

@app.command()
def clean():
    """
    Limpa arquivos temporários e caches.
    """
    print("🧹 Limpando sistema...")
    paths_to_clean = [
        Path("data/uploads_temp"),
        Path("__pycache__"),
        Path(".pytest_cache")
    ]
    
    for p in paths_to_clean:
        if p.exists() and p.is_dir():
            # Implement careful recursive delete or just warn
            # For safety, let's just clear uploads_temp content
            if p.name == "uploads_temp":
                for f in p.glob("*"):
                    try:
                        f.unlink()
                        print(f"Deleted {f.name}")
                    except Exception as e:
                        print(f"Error deleting {f}: {e}")
            else:
                print(f"Skipping directory removal for {p} (manual cleanup recommended for safety)")
                
    # Also clear .DS_Store
    os.system("find . -name '.DS_Store' -delete")
    print("✅ Limpeza concluída.")

if __name__ == "__main__":
    app()
