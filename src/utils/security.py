"""
Módulo crítico de segurança e privacidade.
Toda interação com dados pessoais passa por aqui.
"""

from argon2 import PasswordHasher
from hashlib import sha256
from typing import Literal, Dict
import secrets
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Configure Argon2id (Memory-hard)
# time_cost=2, memory_cost=65536 (64MB), parallelism=2
ph = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=2)

def anonymize_user(raw_id: str, salt: str = None) -> str:
    """
    CRITICAL: Primeira linha de defesa de anonimato.
    Usa Argon2id (Memory-hard) para impedir força bruta com GPU.
    
    Args:
        raw_id: Identificador original
        salt: Salt (opcional, mas DEVE vir do .env em prod)
    
    Returns:
        Hash seguro do usuário.
    """
    if not salt:
        salt = os.getenv("ANONYMIZATION_SALT")
        if not salt or salt == "dev_secret_salt_CHANGE_IN_PROD":
            logger.warning("⚠️ SECURITY WARNING: Usando salt padrão/fraco! Configure ANONYMIZATION_SALT no .env.")
            salt = "dev_secret_salt_CHANGE_IN_PROD"
    
    # Argon2 já aplica salt internamente de forma segura, mas para determinação 
    # (mesmo raw_id = mesmo hash sempre para o mesmo sistema), precisamos de uma abordagem estática controlada
    # OU usamos o salt como parte da 'password' input se quisermos determinação simples
    # O Argon2 padrão gera salt aleatório (bom para senhas, ruim para lookup de usuário).
    # Para lookup determinístico (saber que User A é User A amanhã), precisamos de um mecanismo fixo.
    
    # Abordagem Híbrida Seguro-Determinística:
    # HMAC-SHA256(Key=GlobalSalt, Msg=RawID) -> Intermediate
    # Argon2(Msg=Intermediate) -> Mas Argon2 ainda é randomizado por design.
    
    # CORREÇÃO: Para fins de anonimização (lookup), precisamos de DETERMINISMO.
    # O Argon2 não é ideal para lookup determinístico direto 1:1 sem salt fixo.
    # Mas podemos fixar o salt se a lib permitir, ou usar HMAC-BLAKE2b.
    
    # Melhor abordagem para PROJETO ATUAL (sem mudar arquitetura de DB):
    # Manter Salt Global + PBKDF2 ou Argon2 com parâmetros fixos? 
    # A lib 'argon2-cffi' gera salts randomicos por padrão.
    # Vamos usar PBKDF2-HMAC-SHA512 que é NIST-approved e permite determinismo fácil.
    # O usuário pediu Argon2. Para Argon2 determinístico, precisamos passar o salt manualmente.
    # A lib argon2-cffi low-level permite isso.
    
    try:
        from argon2.low_level import hash_secret_raw, Type
        # Salt deve ter 16 bytes. Vamos derivar do nosso Salt String.
        # Enforce 16 bytes salt from global string
        salt_bytes = sha256(salt.encode()).digest()[:16]
        
        # Hash
        hashed_bytes = hash_secret_raw(
            secret=raw_id.encode(),
            salt=salt_bytes,
            time_cost=2,
            memory_cost=65536,
            parallelism=2,
            hash_len=32,
            type=Type.ID
        )
        return hashed_bytes.hex()
        
    except ImportError:
        # Fallback se Argon2 falhar (não deveria)
        return sha256(f"{salt}{raw_id}".encode()).hexdigest()


def generate_audit_token() -> str:
    """
    Gera ID único para rastrear uma interação específica.
    Usado para vincular logs sem expor identidade do usuário.
    
    Returns:
        Token aleatório de 32 caracteres hexadecimais
    
    Exemplo:
        >>> generate_audit_token()
        '7f3a9e2c1d8b5f4a6e9c0d1b2a3f4e5c'
    """
    return secrets.token_hex(16)


RoleType = Literal["cidadao", "moderador", "admin"]

# Matriz de permissões (RBAC simplificado)
PERMISSIONS: Dict[RoleType, Dict[str, bool]] = {
    "cidadao": {
        "chat": True,
        "upload": True,
        "view_own_data": True,
        "delete_own_data": True,
        "moderate_alerts": False,
        "edit_prompts": False,
        "view_analytics": False
    },
    "moderador": {
        "chat": True,
        "upload": True,
        "view_own_data": True,
        "delete_own_data": True,
        "moderate_alerts": True,  # Pode revisar alertas
        "edit_prompts": False,
        "view_analytics": True
    },
    "admin": {
        # Acesso total
        "chat": True,
        "upload": True,
        "view_own_data": True,
        "delete_own_data": True,
        "moderate_alerts": True,
        "edit_prompts": True,
        "view_analytics": True,
        "manage_users": True
    }
}

def check_permission(role: RoleType, action: str) -> bool:
    """
    Verifica se uma role tem permissão para executar uma ação.
    
    Args:
        role: Tipo de usuário
        action: Ação a ser verificada (ex: "edit_prompts")
    
    Returns:
        True se permitido, False caso contrário
    
    Exemplo:
        >>> check_permission("cidadao", "edit_prompts")
        False
        >>> check_permission("admin", "edit_prompts")
        True
    """
    return PERMISSIONS.get(role, {}).get(action, False)


def sanitize_filename(filename: str) -> str:
    """
    Remove caracteres perigosos de nomes de arquivo.
    Previne path traversal attacks.
    
    Args:
        filename: Nome do arquivo original
    
    Returns:
        Nome sanitizado
    """
    import re
    # Remove path separators e caracteres especiais
    safe_name = re.sub(r'[^\w\s\-\.]', '', filename)
    # Remove .. (path traversal)
    safe_name = safe_name.replace('..', '')
    return safe_name
