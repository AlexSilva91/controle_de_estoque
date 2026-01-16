def novoValor(valor_atual, desconto, qtd):
    if qtd == 0 or None:
        return 0
    if desconto == 0 or None:
        return 0
    if valor_atual == 0 or None:
        return 0

    desconto_por_unidade = desconto / qtd
    novo_valor = valor_atual - desconto_por_unidade

    return round(novo_valor, 2)
