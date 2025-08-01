from datetime import datetime
from app.database import SessionLocal
from app.models.entities import Produto, Desconto, produto_desconto_association


def processar_venda(session, dados):
    resultado = []

    for item in dados['itens']:
        produto_id = item['produto_id']
        quantidade = item['quantidade']

        print(f"\n🔍 Processando produto_id={produto_id} | quantidade={quantidade}")

        produto = session.query(Produto).get(produto_id)
        if not produto:
            print("❌ Produto não encontrado!")
            resultado.append({
                'produto_id': produto_id,
                'erro': 'Produto não encontrado'
            })
            continue

        valor_unitario = float(produto.valor_unitario)
        valor_total_original = valor_unitario * quantidade
        print(f"💰 Valor unitário original: {valor_unitario:.2f} | Valor total original: {valor_total_original:.2f}")

        descontos = (
            session.query(Desconto)
            .join(produto_desconto_association)
            .filter(
                produto_desconto_association.c.produto_id == produto_id,
                Desconto.ativo == True
            ).all()
        )
        print(f"🎯 Descontos encontrados: {len(descontos)}")

        melhor_desconto = None
        valor_final = valor_total_original
        valor_desconto_total = 0.0

        for d in descontos:
            print(f"  ➤ Avaliando desconto: {d.identificador} | tipo={d.tipo} | valor={d.valor}")

            # Verifica validade
            if d.valido_ate:
                print(f"     ⏳ Validade: {d.valido_ate}")
                if datetime.utcnow() > d.valido_ate:
                    print("     ❌ Desconto expirado.")
                    continue

            # Verifica quantidade
            min_qtd = float(d.quantidade_minima or 0)
            max_qtd = float(d.quantidade_maxima or float('inf'))
            print(f"     📦 Faixa válida: {min_qtd} a {max_qtd}")

            if not (min_qtd <= quantidade <= max_qtd):
                print("     ❌ Quantidade fora da faixa.")
                continue

            # Calcula desconto
            if d.tipo == 'fixo':
                valor_unitario_descontado = float(d.valor)
                total_com_desconto = valor_unitario_descontado * quantidade
                desconto_aplicado = valor_total_original - total_com_desconto
                print(f"     ✅ Novo valor unitário: {valor_unitario_descontado:.2f} | Total com desconto: {total_com_desconto:.2f}")
                print(f"     💸 Desconto aplicado: {desconto_aplicado:.2f}")
            elif d.tipo == 'percentual':
                desconto_aplicado = valor_total_original * (float(d.valor) / 100)
                total_com_desconto = valor_total_original - desconto_aplicado
                print(f"     ✅ Desconto percentual: {d.valor}% | Valor do desconto: {desconto_aplicado:.2f}")
                print(f"     💸 Total com desconto: {total_com_desconto:.2f}")
            else:
                print("     ⚠️ Tipo de desconto desconhecido. Ignorando.")
                continue

            if melhor_desconto is None or desconto_aplicado > valor_desconto_total:
                melhor_desconto = d
                valor_final = total_com_desconto
                valor_desconto_total = desconto_aplicado
                print("     ⭐ Melhor desconto atualizado.")

        resultado.append({
            'produto_id': produto_id,
            'quantidade': quantidade,
            'valor_unitario': round(valor_unitario, 2),
            'valor_total_original': round(valor_total_original, 2),
            'valor_desconto': round(valor_desconto_total, 2),
            'valor_final': round(valor_final, 2),
            'desconto_aplicado': melhor_desconto.identificador if melhor_desconto else None
        })

    return resultado