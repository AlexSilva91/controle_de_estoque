from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from datetime import datetime

from app.models.fiscal_models import ConfiguracaoFiscal

def gerar_numero_nfe_mysql(db, cnpj, modelo=55):
    if modelo == 55:
        campo_numero = ConfiguracaoFiscal.ultimo_numero_nfe
        campo_serie = ConfiguracaoFiscal.serie_nfe
    elif modelo == 65:
        campo_numero = ConfiguracaoFiscal.ultimo_numero_nfce
        campo_serie = ConfiguracaoFiscal.serie_nfce
    else:
        raise ValueError("Modelo inválido")

    config = (
        db.query(ConfiguracaoFiscal)
        .filter(
            ConfiguracaoFiscal.cnpj == cnpj,
            ConfiguracaoFiscal.ativo.is_(True)
        )
        .with_for_update()
        .one()
    )

    proximo_numero = getattr(config, campo_numero.key) + 1
    setattr(config, campo_numero.key, proximo_numero)
    config.atualizado_em = datetime.now()

    return proximo_numero, getattr(config, campo_serie.key)
