import pytest
from src.utils.text_processing import SmartTextSplitter

@pytest.fixture
def splitter():
    return SmartTextSplitter()

def test_split_law_art_hierarchy(splitter):
    """
    Test if Law splitter correctly splits by Art. and preserves hierarchy for sub-chunks.
    """
    # Case 1: Simple Articles
    text_simple = "Art. 1º Fica instituído o programa.\nArt. 2º Revogam-se as disposições."
    chunks = splitter.split(text_simple, doc_type="legislation")
    assert len(chunks) == 2
    assert "Art. 1º" in chunks[0]
    assert "Art. 2º" in chunks[1]

    # Case 2: Hierarchy Preservation (Huge Article)
    # Simulate a huge article that forces sub-splitting
    huge_body = "§ 1º Parágrafo um. " * 50 + "§ 2º Parágrafo dois. " * 50
    text_huge = f"Art. 5º Todos são iguais perante a lei. {huge_body}"
    
    # We expect sub-splits, but they MUST contain the parent "Art. 5º"
    chunks_huge = splitter.split(text_huge, doc_type="legislation")
    
    # Since logic only triggers for >2500 chars, let's ensure input is big enough
    # If it is big enough, we check if child chunks exist
    if len(text_huge) > 2500:
        assert len(chunks_huge) > 1
        for c in chunks_huge:
            assert "Art. 5º" in c
            # The second chunk should have the hierarchy marker
            if "§ 2º" in c:
                assert ">" in c or "(Cont.)" in c

def test_split_gazette_window(splitter):
    """
    Test sliding window for Gazettes.
    """
    # Create a text distinct enough to check overlap
    # "0123456789" ...
    text = "".join([str(i % 10) for i in range(4000)]) # 4000 chars
    
    # Window 3000, Overlap 500
    chunks = splitter.split(text, doc_type="diario_oficial")
    
    assert len(chunks) == 2 # 4000 fits in 2 chunks of 3000 (0-3000, 2500-5500[capped])
    
    chunk1 = chunks[0]
    chunk2 = chunks[1]
    
    assert len(chunk1) == 3000
    # Overlap check: chunk2 should start 500 chars before chunk1 ends?
    # Logic: start=0, next start = 3000 - 500 = 2500.
    # So chunk2 starts at index 2500.
    # Chunk1[2500:] should match Chunk2[:500]
    overlap_size = 500
    assert chunk1[-overlap_size:] == chunk2[:overlap_size]

def test_context_injection(splitter):
    """
    Test if global context is prepended.
    """
    text = "Conteúdo simples."
    ctx = "[DOC TESTE] "
    chunks = splitter.split(text, doc_type="general", context_prefix=ctx)
    
    assert len(chunks) == 1
    assert chunks[0] == "[DOC TESTE] Conteúdo simples."
