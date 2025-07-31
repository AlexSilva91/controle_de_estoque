from babel.dates import format_date
from babel.numbers import format_currency
from datetime import date
import locale

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

def formatar_data_br(data: date) -> str:
    return data.strftime('%d/%m/%Y') if data else None

def formatar_valor_br(valor: float) -> str:
    return format_currency(valor, 'BRL', locale='pt_BR')