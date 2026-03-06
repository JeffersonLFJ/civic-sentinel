
from fastapi.testclient import TestClient
from src.interfaces.api.main import app
from src.core.settings_manager import settings_manager
from src.config import settings

client = TestClient(app)
ADMIN_HEADERS = {"X-Admin-Key": settings.ADMIN_API_KEY, "X-Role": "admin"}

def test_admin_settings_lifecycle():
    print("\n🚀 Iniciando Teste de Integração (Admin API)...")

    # 1. Get Initial Settings
    response = client.get("/api/admin/settings", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    data = response.json()
    print(f"✅ GET Inicial OK. Temp atual: {data['llm_temperature']}")
    
    # 2. Update Settings
    new_payload = {
        "llm_temperature": 0.7,
        "llm_top_k": 80,
        "llm_num_ctx": 16384,
        "rag_top_k": 8,
        "system_prompt": "Prompt de Teste"
    }
    response = client.post("/api/admin/settings", json=new_payload, headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    print("✅ POST Update OK.")
    
    # 3. Verify Update via API
    response = client.get("/api/admin/settings", headers=ADMIN_HEADERS)
    data = response.json()
    assert data['llm_temperature'] == 0.7
    assert data['llm_top_k'] == 80
    assert data['system_prompt'] == "Prompt de Teste"
    print("✅ Verificação de Persistência OK.")
    
    # 4. Verify Backend Logic (SettingsManager Singleton)
    # The API update should reflect in the manager immediately
    assert settings_manager.temperature == 0.7
    print("✅ SettingsManager Singleton atualizado.")
    
    # 5. Reset Prompt
    response = client.post("/api/admin/settings/reset_prompt", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    
    response = client.get("/api/admin/settings", headers=ADMIN_HEADERS)
    assert response.json()['system_prompt'] == ""
    print("✅ Reset Prompt OK.")

    print("\n🎉 Todos os testes de integração passaram!")

if __name__ == "__main__":
    test_admin_settings_lifecycle()
