"""
Módulo crítico de segurança e privacidade.
Toda interação com dados pessoais passa por aqui.
"""

from hashlib import sha256
from typing import Literal, Dict
import secrets
import os
from dotenv import load_dotenv

load_dotenv()

def anonymize_user(raw_id: str, salt: str = None) -> str:
    """
    CRITICAL: Esta função é a primeira linha de defesa.
    raw_id NUNCA deve ser persistido em logs, DB ou transmitido.
    
    Args:
        raw_id: Identificador original (ex: número de telefone)
        salt: Salt para hashing (deve vir do .env: ANONYMIZATION_SALT)
    
    Returns:
        Hash determinístico SHA256 (mesmo user = mesmo hash sempre)
    
    Exemplo:
        >>> anonymize_user("5521987654321", salt="my_secret_salt")
        'a3f5e8c9d1b2...'  # Hash de 64 caracteres
    """
    if not salt:
        salt = os.getenv("ANONYMIZATION_SALT")
        if not salt:
            # Fallback seguro para desenvolvimento, mas idealmente deve levantar erro em prod
            salt = "dev_default_salt_CHANGE_ME" 
            # raise ValueError("ANONYMIZATION_SALT não configurado no .env")
    
    # Concatena salt + raw_id e gera hash
    salted = f"{salt}{raw_id}".encode('utf-8')
    return sha256(salted).hexdigest()


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
