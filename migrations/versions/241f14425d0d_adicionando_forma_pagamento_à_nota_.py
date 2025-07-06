"""Adicionando forma_pagamento à nota fiscal

Revision ID: 241f14425d0d
Revises: bac86124cca5
Create Date: 2025-07-06 01:00:23.640070

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '241f14425d0d'
down_revision = 'bac86124cca5'
branch_labels = None
depends_on = None

# Define o Enum forma_pagamento
forma_pagamento_enum = sa.Enum(
    'pix_fabiano',
    'pix_maquineta',
    'dinheiro',
    'cartao_credito',
    'cartao_debito',
    'a_prazo',
    name='formapagamento'
)

def upgrade():
    # Cria o ENUM no banco (se ainda não existir)
    forma_pagamento_enum.create(op.get_bind(), checkfirst=True)

    # Adiciona a nova coluna
    op.add_column('notas_fiscais', sa.Column('forma_pagamento', forma_pagamento_enum, nullable=True))


def downgrade():
    # Remove a coluna
    op.drop_column('notas_fiscais', 'forma_pagamento')

    # Remove o ENUM
    forma_pagamento_enum.drop(op.get_bind(), checkfirst=True)
