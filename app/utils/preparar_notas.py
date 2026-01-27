from decimal import Decimal
from datetime import datetime
from zoneinfo import ZoneInfo
from app.models.entities import Produto
from app.services.crud import buscar_descontos_por_produto_id 

def preparar_dados_nota(dados_venda: dict, session) -> dict:
    """
    Processa os dados da venda, aplica descontos e formata para a geração da NFC-e.
    
    Args:
        dados_venda: Dicionário com os dados da venda (payload)
        session: Sessão do banco de dados
        
    Returns:
        Dicionário formatado para a geração da NFC-e com informações de desconto
    """
    # Cria cópia dos dados para não modificar o original
    dados_nota = dados_venda.copy()
    
    # Processa cada item para calcular descontos
    valor_total = Decimal('0.00')
    valor_desconto_total = Decimal('0.00')
    
    for item in dados_nota['itens']:
        produto_id = item['produto_id']
        quantidade = Decimal(str(item['quantidade']))
        valor_unitario_original = Decimal(str(item['valor_unitario']))
        valor_total_item_original = valor_unitario_original * quantidade
        
        # Busca o produto no banco de dados
        produto = session.query(Produto).get(produto_id)
        if not produto:
            raise ValueError(f"Produto com ID {produto_id} não encontrado")
        
        # Verifica se o valor unitário informado já está com desconto
        valor_unitario_informado = Decimal(str(item.get('valor_unitario', valor_unitario_original)))
        valor_total_informado = Decimal(str(item.get('valor_total', valor_unitario_informado * quantidade)))
        
        # Calcula o desconto aplicado
        desconto_item = valor_total_item_original - valor_total_informado
        
        # Adiciona informações de desconto ao item
        item['valor_unitario_original'] = float(valor_unitario_original)
        item['valor_total_original'] = float(valor_total_item_original)
        item['desconto_aplicado'] = float(desconto_item) if desconto_item > 0 else 0.0
        item['valor_unitario'] = float(valor_unitario_informado)
        item['valor_total'] = float(valor_total_informado)
        item['descricao'] = produto.nome  # Adiciona descrição do produto
        
        # Atualiza totais
        valor_total += valor_total_informado
        valor_desconto_total += desconto_item
    
    # Adiciona informações de desconto total à nota
    dados_nota['valor_total'] = float(valor_total)
    dados_nota['valor_desconto_total'] = float(valor_desconto_total) if valor_desconto_total > 0 else 0.0
    
    # Formata a data de emissão
    dados_nota['data_emissao'] = datetime.now(ZoneInfo("America/Sao_Paulo"))
    
    return dados_nota
