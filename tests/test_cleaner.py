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
