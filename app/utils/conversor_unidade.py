from decimal import Decimal


def converter_quantidade(qtde: Decimal, unidade_origem: str, unidade_destino: str, info_produto: dict) -> Decimal:
    if unidade_origem == unidade_destino:
        return qtde

    peso_kg_por_saco = info_produto.get('peso_kg_por_saco', Decimal('50'))
    pacotes_por_saco = info_produto.get('pacotes_por_saco', Decimal('10'))
    pacotes_por_fardo = info_produto.get('pacotes_por_fardo', Decimal('5'))
    peso_kg_por_pacote = peso_kg_por_saco / pacotes_por_saco

    # Saco para outras unidades
    if unidade_origem == 'saco' and unidade_destino == 'kg':
        return qtde * peso_kg_por_saco
    if unidade_origem == 'saco' and unidade_destino == 'pacote':
        return qtde * pacotes_por_saco
    if unidade_origem == 'saco' and unidade_destino == 'fardo':
        return qtde * (pacotes_por_saco / pacotes_por_fardo)

    # Kg para outras unidades
    if unidade_origem == 'kg' and unidade_destino == 'saco':
        return qtde / peso_kg_por_saco
    if unidade_origem == 'kg' and unidade_destino == 'pacote':
        return qtde / peso_kg_por_pacote
    if unidade_origem == 'kg' and unidade_destino == 'fardo':
        return (qtde / peso_kg_por_pacote) / pacotes_por_fardo

    # Pacote para outras unidades
    if unidade_origem == 'pacote' and unidade_destino == 'kg':
        return qtde * peso_kg_por_pacote
    if unidade_origem == 'pacote' and unidade_destino == 'saco':
        return qtde / pacotes_por_saco
    if unidade_origem == 'pacote' and unidade_destino == 'fardo':
        return qtde / pacotes_por_fardo

    # Fardo para outras unidades
    if unidade_origem == 'fardo' and unidade_destino == 'pacote':
        return qtde * pacotes_por_fardo
    if unidade_origem == 'fardo' and unidade_destino == 'kg':
        return qtde * pacotes_por_fardo * peso_kg_por_pacote
    if unidade_origem == 'fardo' and unidade_destino == 'saco':
        return (qtde * pacotes_por_fardo) / pacotes_por_saco

    raise ValueError(f"Conversão de {unidade_origem} para {unidade_destino} não suportada")