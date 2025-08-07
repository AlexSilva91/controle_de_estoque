from babel.dates import format_date
from babel.numbers import format_currency
from datetime import date
import locale

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

def formatar_data_br(data: date) -> str:
    return data.strftime('%d/%m/%Y') if data else None

def formatar_valor_br(valor: float) -> str:
    return format_currency(valor, 'BRL', locale='pt_BR')

def format_currency(value):
    """Formata valores monetários no padrão brasileiro (R$ XX.XXX,XX)"""
    if value is None:
        value = 0
    return "{:,.2f}".format(float(value)).replace(",", "X").replace(".", ",").replace("X", ".")

def format_number(value, is_weight=False):
    """
    Formata números no padrão brasileiro
    Se is_weight=True, formata com 3 casas decimais (para pesos)
    Caso contrário, formata como inteiro ou com 2 casas decimais
    """
    if value is None:
        value = 0
    value = float(value)
    
    if is_weight:
        # Para pesos (kg, sacos), mostra até 3 casas decimais
        return "{:,.2f}".format(value).replace(",", "X").replace(".", ",").replace("X", ".")
    elif value.is_integer():
        # Para inteiros (contagens)
        return "{:,.0f}".format(value).replace(",", ".")
    else:
        # Para outros números decimais
        return "{:,.2f}".format(value).replace(",", "X").replace(".", ",").replace("X", ".")