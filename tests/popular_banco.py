from flask import Flask
from app.models import db
from app.models.entities import Produto, Cliente, UnidadeMedida
from app import create_app
from decimal import Decimal
from datetime import datetime

app = create_app()

with app.app_context():
    db.create_all()

    # Produtos com todos os campos preenchidos
    produtos = [
        Produto(
            codigo="RAC-001",
            nome="Ração Cavalo 25kg",
            tipo="ração",
            marca="Haras Gold",
            unidade=UnidadeMedida.saco,
            valor_unitario=Decimal("98.50"),
            estoque_quantidade=Decimal("120.000"),
            ativo=True
        ),
        Produto(
            codigo="MIL-060",
            nome="Milho em grão 60kg",
            tipo="grão",
            marca="AgroFort",
            unidade=UnidadeMedida.saco,
            valor_unitario=Decimal("75.00"),
            estoque_quantidade=Decimal("300.000"),
            ativo=True
        ),
        Produto(
            codigo="FAR-050",
            nome="Farelo de soja 50kg",
            tipo="farelo",
            marca="NutriSoja",
            unidade=UnidadeMedida.saco,
            valor_unitario=Decimal("112.00"),
            estoque_quantidade=Decimal("150.000"),
            ativo=True
        ),
        Produto(
            codigo="SAL-030",
            nome="Sal mineral 30kg",
            tipo="sal",
            marca="MinerFort",
            unidade=UnidadeMedida.saco,
            valor_unitario=Decimal("47.90"),
            estoque_quantidade=Decimal("200.000"),
            ativo=True
        ),
        Produto(
            codigo="CAS-020",
            nome="Casquinha de soja 20kg",
            tipo="farelo",
            marca="SojaMix",
            unidade=UnidadeMedida.saco,
            valor_unitario=Decimal("39.50"),
            estoque_quantidade=Decimal("180.000"),
            ativo=True
        ),
        Produto(
            codigo="RAC-015",
            nome="Ração Canina 15kg",
            tipo="ração",
            marca="DogPremium",
            unidade=UnidadeMedida.saco,
            valor_unitario=Decimal("124.90"),
            estoque_quantidade=Decimal("90.000"),
            ativo=True
        ),
        Produto(
            codigo="RAC-010",
            nome="Ração Felina 10kg",
            tipo="ração",
            marca="CatMix",
            unidade=UnidadeMedida.saco,
            valor_unitario=Decimal("102.90"),
            estoque_quantidade=Decimal("75.000"),
            ativo=True
        ),
        Produto(
            codigo="SUP-001",
            nome="Suplemento vitamínico",
            tipo="suplemento",
            marca="VitaPlus",
            unidade=UnidadeMedida.unidade,
            valor_unitario=Decimal("55.00"),
            estoque_quantidade=Decimal("350.000"),
            ativo=True
        ),
        Produto(
            codigo="RAC-005",
            nome="Ração Pintinho 5kg",
            tipo="ração",
            marca="AvioStart",
            unidade=UnidadeMedida.saco,
            valor_unitario=Decimal("29.90"),
            estoque_quantidade=Decimal("200.000"),
            ativo=True
        ),
        Produto(
            codigo="MIL-030T",
            nome="Milho triturado 30kg",
            tipo="grão",
            marca="MilhoBom",
            unidade=UnidadeMedida.saco,
            valor_unitario=Decimal("60.00"),
            estoque_quantidade=Decimal("400.000"),
            ativo=True
        ),
    ]

    for produto in produtos:
        existe = Produto.query.filter_by(nome=produto.nome).first()
        if not existe:
            db.session.add(produto)

    db.session.commit()
    print("✅ Produtos cadastrados com todos os campos preenchidos.")
