from flask import Flask
from app import create_app
from app.models import db
from app.models.entities import Caixa, FormaPagamento, MovimentacaoConta, SaldoFormaPagamento, TipoMovimentacao, Usuario
from passlib.context import CryptContext
from datetime import datetime
from sqlalchemy import and_
from app.services.crud import calcular_formas_pagamento, processar_movimentacoes_conta


def processar_movimentacoes_conta(caixa_id, usuario_logado_id, session):
    """
    Processa as movimentações do caixa na conta do usuário logado.
    Atualiza o campo atualizado_em da conta com a data de fechamento do caixa.
    """
    from sqlalchemy import func
    from datetime import datetime

    caixa = session.query(Caixa).filter_by(id=caixa_id).first()
    if not caixa:
        raise ValueError(f"Caixa ID {caixa_id} não encontrado")

    usuario = session.query(Usuario).filter_by(id=usuario_logado_id).first()
    if not usuario:
        raise ValueError(f"Usuário ID {usuario_logado_id} não encontrado")

    if not usuario.conta:
        raise ValueError(f"Usuário {usuario.nome} não possui conta cadastrada")

    conta = usuario.conta

    movimentacoes_existentes = session.query(MovimentacaoConta).filter_by(
        caixa_id=caixa_id,
        conta_id=conta.id
    ).count()

    if movimentacoes_existentes > 0:
        raise ValueError(f"Já existem movimentações processadas para o Caixa {caixa_id} na conta do usuário")

    valores_caixa = calcular_formas_pagamento(caixa_id, session)

    formas_creditar = [
        'dinheiro', 'pix_loja', 'pix_fabiano', 'pix_edfrance',
        'pix_maquineta', 'cartao_debito', 'cartao_credito'
    ]

    total_creditos = 0.0

    for forma_pagamento_str, valor in valores_caixa['vendas_por_forma_pagamento'].items():
        if forma_pagamento_str in formas_creditar and valor > 0:
            try:
                forma_pagamento = FormaPagamento(forma_pagamento_str)
            except ValueError:
                continue

            saldo_fp = next(
                (s for s in conta.saldos_forma_pagamento if s.forma_pagamento == forma_pagamento),
                None
            )

            if not saldo_fp:
                saldo_fp = SaldoFormaPagamento(
                    conta_id=conta.id,
                    forma_pagamento=forma_pagamento,
                    saldo=0.00
                )
                session.add(saldo_fp)
                session.flush()

            saldo_fp.saldo = float(saldo_fp.saldo) + valor
            saldo_fp.sincronizado = False

            movimentacao = MovimentacaoConta(
                conta_id=conta.id,
                tipo=TipoMovimentacao.entrada,
                forma_pagamento=forma_pagamento,
                valor=valor,
                descricao=f"Crédito líquido - Caixa {caixa_id}",
                data=caixa.data_fechamento,
                usuario_id=usuario_logado_id,
                caixa_id=caixa_id
            )
            session.add(movimentacao)
            total_creditos += valor

    conta.saldo_total = max(float(conta.saldo_total) + total_creditos, 0)
    conta.sincronizado = False

    # Atualiza data de atualização da conta com a data de fechamento do caixa
    conta.atualizado_em = caixa.data_fechamento

    session.commit()

    return {
        'usuario': usuario.nome,
        'conta_id': conta.id,
        'total_creditado': total_creditos,
        'novo_saldo_total': float(conta.saldo_total),
        'saldos_por_forma_pagamento': {
            saldo.forma_pagamento.value: float(saldo.saldo)
            for saldo in conta.saldos_forma_pagamento
        },
        'movimentacoes_processadas': len([
            mov for mov in conta.movimentacoes
            if mov.caixa_id == caixa_id
        ])
    }


# Inicializa o app e contexto de senha
app = create_app()

with app.app_context():
    data_inicial = datetime(2025, 10, 1)
    data_final = datetime(2025, 10, 9)
    
    # Cria todas as tabelas do banco de dados, se ainda não existirem
    db.create_all()
    session = db.session

    caixas = (
        session.query(Caixa)
        .filter(Caixa.data_abertura.between(data_inicial, data_final))
        .all()
    )

    for caixa in caixas:
        print(caixa.data_abertura.strftime('%d/%m/%Y'))
        print(f'Processando dados do caixa {caixa.id}')
        processar_movimentacoes_conta(caixa.id, 4, session)
        
        if caixa:
            print('Processamento concluido!')
        else:
            print(f'Erro ao processar dados do caixa {caixa.id}')
