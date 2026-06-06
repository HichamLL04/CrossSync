import pytest
from src.cleaner import clean_text

def test_clean_html_tags():
    raw = '<font face="Humana Sans" size="46" color="#f0e5e3"><b>Hola Mundo</b></font>'
    assert clean_text(raw) == "Hola Mundo"

def test_clean_ass_tags():
    raw = '{\\an8}Esto es un texto en la parte superior'
    assert clean_text(raw) == "Esto es un texto en la parte superior"

def test_clean_mixed_tags():
    raw = '{\\an8}<b>Texto</b>'
    assert clean_text(raw) == "Texto"

def test_preserve_formatting():
    from src.sync_pipeline import preserve_formatting
    
    # Position tag & HTML font wrapper
    raw = '<font face="Humana" size="46"><b>{\\an8}A pesar de ello</b></font>'
    assert preserve_formatting("A pesar de ello", raw) == '{\\an8}<font face="Humana" size="46"><b>A pesar de ello</b></font>'
    
    # HTML styling tag wrapper
    assert preserve_formatting("Texto normal", "<b>Texto normal</b>") == "<b>Texto normal</b>"
    
    # Plain text without styling
    assert preserve_formatting("Sin tags", "Sin tags") == "Sin tags"
    
    # Only position tag
    assert preserve_formatting("Parte 1", "{\\an8}Parte completa") == "{\\an8}Parte 1"
    
    # Empty part text
    assert preserve_formatting("", "{\\an8}Parte completa") == ""
