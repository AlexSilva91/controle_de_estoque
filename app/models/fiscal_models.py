"""
app/models/fiscal_models.py

Modelos adicionais para controle fiscal - COMPATÍVEL com sistema existente
NÃO modifica os modelos principais - apenas adiciona novas tabelas
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, 
    Text, DECIMAL, Boolean, UniqueConstraint
)
from sqlalchemy.orm import relationship
from .base import Base
from .entities import NotaFiscal  # Importe apenas para relações


# --------------------
# 1. CONFIGURAÇÕES FISCAIS DA EMPRESA
# --------------------
class ConfiguracaoFiscal(Base):
    __tablename__ = "configuracoes_fiscais"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Dados da Empresa (Emitente)
    razao_social = Column(String(150), nullable=False)
    nome_fantasia = Column(String(150), nullable=True)
    cnpj = Column(String(14), nullable=False)
    inscricao_estadual = Column(String(14), nullable=True)
    inscricao_municipal = Column(String(15), nullable=True)
    cnae_principal = Column(String(7), nullable=True)
    regime_tributario = Column(String(2), nullable=True)  # 1=Simples, 2=Normal, 3=MEI
    
    # Endereço
    logradouro = Column(String(200), nullable=False)
    numero = Column(String(20), nullable=False)
    complemento = Column(String(100), nullable=True)
    bairro = Column(String(100), nullable=False)
    codigo_municipio = Column(String(7), nullable=False)
    municipio = Column(String(100), nullable=False)
    uf = Column(String(2), nullable=False)
    cep = Column(String(8), nullable=False)
    telefone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    
    # Sequenciais
    serie_nfe = Column(String(3), default="1", nullable=False)
    serie_nfce = Column(String(3), default="2", nullable=False)
    ambiente = Column(String(1), default="2", nullable=False)  # 1=Produção, 2=Homologação
    ultimo_numero_nfe = Column(Integer, default=0, nullable=False)
    ultimo_numero_nfce = Column(Integer, default=0, nullable=False)
    
    # Controle
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=datetime.now, nullable=False)
    atualizado_em = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    sincronizado = Column(Boolean, default=False, nullable=False)
    
    def __repr__(self):
        return f"<ConfiguracaoFiscal(id={self.id}, cnpj={self.cnpj}, razao_social={self.razao_social})>"


# --------------------
# 1. CONFIGURAÇÕES FISCAIS DO CLIENTE
# --------------------
class ClienteFiscal(Base):
    __tablename__ = "clientes_fiscal"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Identificação
    cpf_cnpj = Column(String(14), nullable=False, unique=True, index=True)
    nome_cliente = Column(String(150), nullable=False)
    nome_fantasia = Column(String(150), nullable=True)
    
    # Dados Fiscais
    indicador_ie = Column(Integer, nullable=False, default=9)  # 1=Contribuinte, 2=Isento, 9=Não Contribuinte
    inscricao_estadual = Column(String(14), nullable=True)
    inscricao_municipal = Column(String(15), nullable=False)
    inscricao_suframa = Column(String(9), nullable=False)
    
    # Endereço
    cep = Column(String(8), nullable=False)
    logradouro = Column(String(200), nullable=False)
    numero = Column(String(20), nullable=False)
    complemento = Column(String(100), nullable=True)
    bairro = Column(String(100), nullable=False)
    codigo_municipio = Column(String(7), nullable=False)
    municipio = Column(String(100), nullable=False)
    uf = Column(String(2), nullable=False)
    codigo_pais = Column(Integer, nullable=False, default=1058)
    pais = Column(String(60), nullable=False, default="BRASIL")
    
    # Contato
    telefone = Column(String(20), nullable=False)
    celular = Column(String(20), nullable=False)
    email = Column(String(100), nullable=False)
    fax = Column(String(20), nullable=False)
    
    # Informações Adicionais
    observacoes = Column(Text, nullable=False)
    tipo_cliente = Column(String(20), nullable=False)  # fisica, juridica
    regime_tributario = Column(String(2), nullable=False)  # 1=Simples, 2=Normal, 3=MEI
    
    # Controle
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=datetime.now, nullable=False)
    atualizado_em = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    sincronizado = Column(Boolean, default=False, nullable=False)

    
    def to_dict(self):
        """Converte o cliente para dicionário"""
        return {
            # Identificação
            "id": self.id,
            "cpf_cnpj": self.cpf_cnpj,
            "nome_cliente": self.nome_cliente,
            "nome_fantasia": self.nome_fantasia,
            
            # Dados Fiscais
            "indicador_ie": self.indicador_ie,
            "inscricao_estadual": self.inscricao_estadual,
            "inscricao_municipal": self.inscricao_municipal,
            "inscricao_suframa": self.inscricao_suframa,
            
            # Endereço
            "endereco": {
                "cep": self.cep,
                "logradouro": self.logradouro,
                "numero": self.numero,
                "complemento": self.complemento,
                "bairro": self.bairro,
                "codigo_municipio": self.codigo_municipio,
                "municipio": self.municipio,
                "uf": self.uf,
                "codigo_pais": self.codigo_pais,
                "pais": self.pais
            },
            
            # Contato
            "contato": {
                "telefone": self.telefone,
                "celular": self.celular,
                "email": self.email,
                "fax": self.fax
            },
            
            # Informações Adicionais
            "observacoes": self.observacoes,
            "tipo_cliente": self.tipo_cliente,
            "regime_tributario": self.regime_tributario,
            
            # Controle
            "ativo": self.ativo,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
            "atualizado_em": self.atualizado_em.isoformat() if self.atualizado_em else None,
            "sincronizado": self.sincronizado
        }
    
    def to_nfe_dict(self):
        """Converte para formato esperado pela NFe (compatível com seu exemplo)"""
        return {
            "CpfCnpj": self.cpf_cnpj,
            "NmCliente": self.nome_cliente,
            "IndicadorIe": self.indicador_ie,
            "Ie": self.inscricao_estadual or "",
            "IsUf": self.uf,
            "Endereco": {
                "Cep": self.cep,
                "Logradouro": self.logradouro,
                "Complemento": self.complemento or "",
                "Numero": self.numero,
                "Bairro": self.bairro,
                "CodMunicipio": self.codigo_municipio,
                "Municipio": self.municipio,
                "Uf": self.uf,
                "CodPais": self.codigo_pais,
                "Pais": self.pais
            },
            "Contato": {
                "Telefone": self.telefone or "",
                "Email": self.email or "",
                "Fax": self.fax or ""
            }
        }
    
    @staticmethod
    def from_dict(dados):
        """Cria um cliente a partir de um dicionário"""
        endereco = dados.get("Endereco", {}) if "Endereco" in dados else dados.get("endereco", {})
        contato = dados.get("Contato", {}) if "Contato" in dados else dados.get("contato", {})
        
        return ClienteFiscal(
            cpf_cnpj=dados.get("CpfCnpj") or dados.get("cpf_cnpj", ""),
            nome_cliente=dados.get("NmCliente") or dados.get("nome_cliente", ""),
            nome_fantasia=dados.get("nome_fantasia"),
            indicador_ie=dados.get("IndicadorIe") or dados.get("indicador_ie", 9),
            inscricao_estadual=dados.get("Ie") or dados.get("inscricao_estadual"),
            inscricao_municipal=dados.get("inscricao_municipal"),
            inscricao_suframa=dados.get("inscricao_suframa"),
            cep=endereco.get("Cep") or endereco.get("cep", ""),
            logradouro=endereco.get("Logradouro") or endereco.get("logradouro", ""),
            numero=endereco.get("Numero") or endereco.get("numero", ""),
            complemento=endereco.get("Complemento") or endereco.get("complemento"),
            bairro=endereco.get("Bairro") or endereco.get("bairro", ""),
            codigo_municipio=endereco.get("CodMunicipio") or endereco.get("codigo_municipio", ""),
            municipio=endereco.get("Municipio") or endereco.get("municipio", ""),
            uf=endereco.get("Uf") or endereco.get("uf", ""),
            codigo_pais=endereco.get("CodPais") or endereco.get("codigo_pais", 1058),
            pais=endereco.get("Pais") or endereco.get("pais", "BRASIL"),
            telefone=contato.get("Telefone") or contato.get("telefone"),
            celular=contato.get("celular"),
            email=contato.get("Email") or contato.get("email"),
            fax=contato.get("Fax") or contato.get("fax"),
            observacoes=dados.get("observacoes"),
            tipo_cliente=dados.get("tipo_cliente"),
            regime_tributario=dados.get("regime_tributario")
        )
    
    def __repr__(self):
        return f"<Cliente(id={self.id}, cpf_cnpj={self.cpf_cnpj}, nome={self.nome_cliente[:30]}...)>"

# --------------------
# 2. DADOS FISCAIS DO PRODUTO (Mapeamento)
# --------------------
class ProdutoFiscal(Base):
    __tablename__ = "produtos_fiscais"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False, unique=True)
    
    # Dados Fiscais
    codigo_ncm = Column(String(8), nullable=True)
    codigo_cest = Column(String(7), nullable=True)
    codigo_ean = Column(String(14), nullable=True)
    codigo_gtin_trib = Column(String(14), nullable=True)
    unidade_tributaria = Column(String(6), nullable=True)
    valor_unitario_trib = Column(DECIMAL(16, 4), nullable=True)
    
    # Classificação
    origem = Column(String(1), nullable=True, default="0")  # 0=Nacional, 1=Estrangeira
    tipo_item = Column(String(2), nullable=True)  # 00=Mercadoria, 01=Matéria-prima
    
    # Tributação
    cst_icms = Column(String(3), nullable=True)
    cfop = Column(String(4), nullable=True)
    aliquota_icms = Column(DECIMAL(5, 2), nullable=True)
    cst_pis = Column(String(2), nullable=True)
    aliquota_pis = Column(DECIMAL(5, 2), nullable=True)
    cst_cofins = Column(String(2), nullable=True)
    aliquota_cofins = Column(DECIMAL(5, 2), nullable=True)
    
    # Informações
    informacoes_fisco = Column(Text, nullable=True)
    informacoes_complementares = Column(Text, nullable=True)
    
    # Status
    homologado = Column(Boolean, default=False, nullable=False)
    data_homologacao = Column(DateTime, nullable=True)
    justificativa_homologacao = Column(Text, nullable=True)
    
    # Controle
    criado_em = Column(DateTime, default=datetime.now, nullable=False)
    atualizado_em = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    sincronizado = Column(Boolean, default=False, nullable=False)
    
    # Relacionamento (opcional, se quiser acessar o produto)
    produto = relationship("Produto", backref="dados_fiscais")
    
    def to_dict(self):
        """Converte todos os campos do ProdutoFiscal para um dicionário"""
        return {
            # IDs
            "id": self.id,
            "produto_id": self.produto_id,
            
            # Dados do produto relacionado (se carregado)
            "produto_nome": self.produto.nome if self.produto else None,
            "produto_codigo": self.produto.codigo if self.produto else None,
            "produto_unidade": self.produto.unidade.value if self.produto and hasattr(self.produto.unidade, 'value') else str(self.produto.unidade) if self.produto and self.produto.unidade else None,
            "produto_valor_unitario": float(self.produto.valor_unitario) if self.produto and self.produto.valor_unitario else None,
            
            # Dados Fiscais
            "codigo_ncm": self.codigo_ncm,
            "codigo_cest": self.codigo_cest,
            "codigo_ean": self.codigo_ean,
            "codigo_gtin_trib": self.codigo_gtin_trib,
            "unidade_tributaria": self.unidade_tributaria,
            "valor_unitario_trib": float(self.valor_unitario_trib) if self.valor_unitario_trib else None,
            
            # Classificação
            "origem": self.origem,
            "tipo_item": self.tipo_item,
            
            # Tributação ICMS
            "cst_icms": self.cst_icms,
            "cfop": self.cfop,
            "aliquota_icms": float(self.aliquota_icms) if self.aliquota_icms else None,
            
            # Tributação PIS
            "cst_pis": self.cst_pis,
            "aliquota_pis": float(self.aliquota_pis) if self.aliquota_pis else None,
            
            # Tributação COFINS
            "cst_cofins": self.cst_cofins,
            "aliquota_cofins": float(self.aliquota_cofins) if self.aliquota_cofins else None,
            
            # Informações
            "informacoes_fisco": self.informacoes_fisco,
            "informacoes_complementares": self.informacoes_complementares,
            
            # Status
            "homologado": self.homologado,
            "data_homologacao": self.data_homologacao.isoformat() if self.data_homologacao else None,
            "justificativa_homologacao": self.justificativa_homologacao,
            
            # Controle
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
            "atualizado_em": self.atualizado_em.isoformat() if self.atualizado_em else None,
            "sincronizado": self.sincronizado
        }
    
    def __repr__(self):
        return f"<ProdutoFiscal(id={self.id}, produto_id={self.produto_id}, ncm={self.codigo_ncm})>"

# --------------------
# 3. TRANSPORTADORAS
# --------------------
class Transportadora(Base):
    __tablename__ = "transportadoras"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Dados
    razao_social = Column(String(150), nullable=False)
    nome_fantasia = Column(String(150), nullable=True)
    cnpj = Column(String(14), nullable=True)
    cpf = Column(String(11), nullable=True)
    inscricao_estadual = Column(String(14), nullable=True)
    
    # Endereço
    logradouro = Column(String(200), nullable=True)
    numero = Column(String(20), nullable=True)
    complemento = Column(String(100), nullable=True)
    bairro = Column(String(100), nullable=True)
    municipio = Column(String(100), nullable=True)
    uf = Column(String(2), nullable=True)
    cep = Column(String(8), nullable=True)
    telefone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    
    # Fiscais
    modalidade_frete = Column(String(1), nullable=True, default="0")
    placa_veiculo = Column(String(7), nullable=True)
    uf_veiculo = Column(String(2), nullable=True)
    rntc = Column(String(20), nullable=True)
    
    # Controle
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=datetime.now, nullable=False)
    atualizado_em = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    sincronizado = Column(Boolean, default=False, nullable=False)
    
    def __repr__(self):
        nome = self.nome_fantasia or self.razao_social
        return f"<Transportadora(id={self.id}, nome={nome[:20]}...)>"


# --------------------
# 4. VEÍCULOS DE TRANSPORTE
# --------------------
class VeiculoTransporte(Base):
    __tablename__ = "veiculos_transporte"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    transportadora_id = Column(Integer, ForeignKey("transportadoras.id"), nullable=True)
    
    # Dados
    placa = Column(String(7), nullable=False)
    uf = Column(String(2), nullable=False)
    rntc = Column(String(20), nullable=True)
    tipo_veiculo = Column(String(50), nullable=True) 
    capacidade_carga = Column(DECIMAL(10, 3), nullable=True)
    proprietario = Column(String(150), nullable=True)
    
    # Controle
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=datetime.now, nullable=False)
    atualizado_em = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    sincronizado = Column(Boolean, default=False, nullable=False)
    
    # Relacionamento
    transportadora = relationship("Transportadora", backref="veiculos")
    
    def __repr__(self):
        return f"<VeiculoTransporte(id={self.id}, placa={self.placa}, uf={self.uf})>"


# --------------------
# 5. HISTÓRICO DE ALTERAÇÕES DA NOTA
# --------------------
class NotaFiscalHistorico(Base):
    __tablename__ = "notas_fiscais_historico"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nota_fiscal_id = Column(Integer, ForeignKey("notas_fiscais.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    
    # Alteração
    tipo_alteracao = Column(String(50), nullable=False)
    dados_anteriores = Column(Text, nullable=True)
    dados_novos = Column(Text, nullable=True)
    descricao = Column(Text, nullable=True)
    
    # Resposta SEFAZ
    codigo_status = Column(String(3), nullable=True)
    motivo_status = Column(String(255), nullable=True)
    protocolo = Column(String(15), nullable=True)
    xml_resposta = Column(Text, nullable=True)
    
    # Controle
    sucesso = Column(Boolean, default=True, nullable=False)
    mensagem_erro = Column(Text, nullable=True)
    data_alteracao = Column(DateTime, default=datetime.now, nullable=False)
    sincronizado = Column(Boolean, default=False, nullable=False)
    
    # Relacionamentos (opcional)
    nota_fiscal = relationship("NotaFiscal", backref="historicos")
    usuario = relationship("Usuario")
    
    def __repr__(self):
        return f"<NotaFiscalHistorico(id={self.id}, nota_id={self.nota_fiscal_id}, tipo={self.tipo_alteracao})>"


# --------------------
# 6. EVENTOS DA NOTA FISCAL
# --------------------
class NotaFiscalEvento(Base):
    __tablename__ = "notas_fiscais_eventos"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nota_fiscal_id = Column(Integer, ForeignKey("notas_fiscais.id"), nullable=False)
    
    # Evento
    tipo_evento = Column(String(6), nullable=False)  # 110110=CC-e, 110111=CANC, etc.
    sequencia_evento = Column(Integer, nullable=False, default=1)
    descricao_evento = Column(String(100), nullable=False)
    justificativa = Column(Text, nullable=True)
    
    # Resposta
    numero_protocolo = Column(String(15), nullable=True)
    data_recebimento = Column(DateTime, nullable=True)
    codigo_status = Column(String(3), nullable=True)
    motivo_status = Column(Text, nullable=True)
    xml_evento = Column(Text, nullable=True)
    xml_retorno = Column(Text, nullable=True)
    
    # Controle
    processado = Column(Boolean, default=False, nullable=False)
    sucesso = Column(Boolean, default=True, nullable=False)
    data_registro = Column(DateTime, default=datetime.now, nullable=False)
    data_processamento = Column(DateTime, nullable=True)
    sincronizado = Column(Boolean, default=False, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('nota_fiscal_id', 'tipo_evento', 'sequencia_evento', 
                        name='uq_nota_evento_sequencia'),
    )
    
    def __repr__(self):
        return f"<NotaFiscalEvento(id={self.id}, nota_id={self.nota_fiscal_id}, evento={self.tipo_evento})>"


# --------------------
# 7. VOLUMES/REMESSAS
# --------------------
class NotaFiscalVolume(Base):
    __tablename__ = "notas_fiscais_volumes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nota_fiscal_id = Column(Integer, ForeignKey("notas_fiscais.id"), nullable=False)
    quantidade = Column(Integer, nullable=False, default=1)
    especie = Column(String(60), nullable=True)
    marca = Column(String(60), nullable=True)
    numeracao = Column(String(60), nullable=True)
    
    # Peso
    peso_liquido = Column(DECIMAL(16, 3), nullable=True)
    peso_bruto = Column(DECIMAL(16, 3), nullable=True)
    
    # Lacres
    lacres = Column(Text, nullable=True)
    
    # Controle
    criado_em = Column(DateTime, default=datetime.now, nullable=False)
    sincronizado = Column(Boolean, default=False, nullable=False)
    
    def __repr__(self):
        return f"<NotaFiscalVolume(id={self.id}, nota_id={self.nota_fiscal_id}, qtd={self.quantidade})>"

