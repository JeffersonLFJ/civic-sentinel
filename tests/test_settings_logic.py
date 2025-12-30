
import asyncio
import httpx
from src.core.settings_manager import settings_manager

BASE_URL = "http://127.0.0.1:8000/api/admin"

async def test_settings_flow():
    print("🚀 Iniciando Teste de Settings API...")
    
    # 1. Check Initial State (Backend direct)
    initial_temp = settings_manager.temperature
    print(f"🌡️ Temperatura Inicial (Manager): {initial_temp}")
    
    # Needs running server?
    # I can test via direct calls to router if I mocking requests, but integration test needs server.
    # Since I cannot easily start the server and wait in this script without blocking,
    # I will assume the server is NOT running and I should import app or run checking imports.
    # Actually, the user usually runs the server.
    
    # BUT, I can test the SettingsManager logic directly first.
    
    print("--- Teste Unitário: SettingsManager ---")
    settings_manager.update({"llm_temperature": 0.9})
    assert settings_manager.temperature == 0.9
    print("✅ Update persistido em memória.")
    
    # Load separate instance to check file persistence
    from src.core.settings_manager import SettingsManager
    idx2 = SettingsManager()
    assert idx2.temperature == 0.9
    print("✅ Persistência JSON verificada.")
    
    # Reset
    settings_manager.update({"llm_temperature": 0.1})
    print("✅ Reset feito.")

    print("✅ Teste Settings Concluído.")

if __name__ == "__main__":
    asyncio.run(test_settings_flow())
