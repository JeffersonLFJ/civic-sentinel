from enum import Enum

class DocType(str, Enum):
    """
    Classificação hierárquica de documentos (Pirâmide de Kelsen).
    Usado para metadados e lógica de decisão do LLM.
    """
    # TOPO (Norma Fundamental)
    CONSTITUICAO = "constituicao"
    
    # MEIO (Legislativo)
    LEI_COMPLEMENTAR = "lei_complementar"
    LEI_ORDINARIA = "lei_ordinaria"
    
    # BASE (Administrativo / Executivo)
    MEDIDA_PROVISORIA = "medida_provisoria"
    DECRETO = "decreto"
    PORTARIA = "portaria"
    RESOLUCAO = "resolucao"
    
    # PUBLICIDADE & OUTROS
    DIARIO_OFICIAL = "diario_oficial" # Meio de publicidade (contém atos da base)
    DOCUMENTO_GERAL = "documento_geral"
    DENUNCIA = "denuncia"
    TABLE = "tabela"

class Sphere(str, Enum):
    """
    Esfera de competência federativa (Eixo Horizontal).
    """
    FEDERAL = "federal"
    ESTADUAL = "estadual"
    MUNICIPAL = "municipal"
    GERAL = "geral" # Quando a norma se aplica a todos (ex: CF/88 em certos pontos)
    DESCONHECIDA = "unknown"
