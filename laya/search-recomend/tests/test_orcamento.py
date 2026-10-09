import pytest
from app.orcamento import parse_budget, bucket_budget


@pytest.mark.parametrize("text,expected_min", [
    ("ate 150 reais", 150),
    ("no maximo R$ 80", 80),
    ("até 150", 150),
    ("entre R$ 100 e R$ 200", 200),
    ("2 mil", 2000),
    ("2,5 mil", 2500),
    ("uns cem conto", 110),
    ("cento e cinquenta", 150),
])
def test_parse_budget(text, expected_min):
    val, fonte = parse_budget(text)
    assert val is not None
    assert val >= expected_min
    assert fonte != "no_detectado"


def test_no_budget():
    val, fonte = parse_budget("quero um presente legal")
    assert val is None
    assert fonte == "no_detectado"


def test_bucket_budget():
    assert bucket_budget(None) == "sem_limite"
    assert bucket_budget(40) == "ate_50"
    assert bucket_budget(80) == "ate_100"
    assert bucket_budget(150) == "ate_150"
    assert bucket_budget(1200) == "premium"


def test_parse_budget_empty_string():
    val, fonte = parse_budget("")
    assert val is None
    assert fonte == "no_detectado"


def test_parse_budget_formatted_number():
    val, fonte = parse_budget("até 1200 reais")
    assert val == 1200.0
    assert fonte == "texto"


def test_parse_budget_brazilian_format():
    val, fonte = parse_budget("até R$ 1.200,00")
    assert val == 1200.0
    assert fonte == "texto"


def test_parse_budget_decimal_with_comma():
    val, fonte = parse_budget("até 99,99")
    assert val == 99.99
    assert fonte == "texto"


def test_parse_budget_cento_e_trinta():
    val, fonte = parse_budget("cento e trinta reais")
    assert val == 130.0
    assert fonte == "texto"
