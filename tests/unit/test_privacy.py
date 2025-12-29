import pytest
from src.utils.privacy import pii_scrubber

def test_cpf_scrubbing():
    text = "Meu CPF é 123.456.789-00."
    assert "123.456.789-00" not in pii_scrubber.scrub(text)
    assert "[CPF_REMOVIDO]" in pii_scrubber.scrub(text)

def test_email_scrubbing():
    text = "Fale comigo em joao.silva@teste.com ou admin@sentinela.org"
    scrubbed = pii_scrubber.scrub(text)
    assert "joao.silva@teste.com" not in scrubbed
    assert "admin@sentinela.org" not in scrubbed
    assert "[EMAIL_REMOVIDO]" in scrubbed

def test_phone_scrubbing():
    text = "Ligue (21) 99999-8888 ou 21 1234-5678"
    scrubbed = pii_scrubber.scrub(text)
    assert "(21) 99999-8888" not in scrubbed
    assert "21 1234-5678" not in scrubbed
    assert "[TELEFONE_REMOVIDO]" in scrubbed

def test_social_media_scrubbing():
    text = "Me siga em instagram.com/jefferson ou @jefferson.dev"
    scrubbed = pii_scrubber.scrub(text)
    assert "instagram.com/jefferson" not in scrubbed
    assert "@jefferson.dev" not in scrubbed
    assert "[LINK_REDE_SOCIAL_REMOVIDO]" in scrubbed
    assert "[REDESOCIAL_REMOVIDO]" in scrubbed

def test_mixed_content():
    text = "Sou @joao, meu email é joao@ig.com e meu zap é (11) 91234-5678."
    scrubbed = pii_scrubber.scrub(text)
    assert "[REDESOCIAL_REMOVIDO]" in scrubbed
    assert "[EMAIL_REMOVIDO]" in scrubbed
    assert "[TELEFONE_REMOVIDO]" in scrubbed
