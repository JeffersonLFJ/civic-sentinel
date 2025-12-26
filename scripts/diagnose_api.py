import httpx
import asyncio

async def diagnose_api():
    # Testando com barra final, que pode ser crucial para certas APIs no Netlify
    url_trailing = "https://queridodiario.ok.org.br/api/gazettes/"
    url_direct = "https://queridodiario.ok.org.br/api/gazettes"
    
    params = {
        "territory_ids": "3303500",
        "published_since": "2024-05-20",
        "size": "1"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://queridodiario.ok.org.br/",
    }

    test_cases = [
        ("URL sem barra final", url_direct),
        ("URL com barra final", url_trailing),
    ]

    for label, url in test_cases:
        print(f"\n--- {label}: {url} ---")
        try:
            r = httpx.get(url, params=params, headers=headers, timeout=10, follow_redirects=True)
            print(f"Status: {r.status_code}")
            print(f"URL Final: {r.url}")
            print(f"Tipo: {r.headers.get('content-type')}")
            if "json" in r.headers.get('content-type', ''):
                print("✅ SUCESSO!")
                print(str(r.json())[:100] + "...")
            else:
                print("❌ HTML recebido")
                title = r.text.split('<title>')[1].split('</title>')[0] if '<title>' in r.text else "Sem título"
                print(f"Título: {title}")
        except Exception as e:
            print(f"Erro: {e}")

if __name__ == "__main__":
    asyncio.run(diagnose_api())
