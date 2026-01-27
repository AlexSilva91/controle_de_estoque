"""
app/services/fiscal_crud.py

CRUD completo para os modelos fiscais - COMPATÍVEL com sistema existente
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_
from app.models.fiscal_models import (
    ConfiguracaoFiscal,
    ProdutoFiscal,
    Transportadora,
    VeiculoTransporte,
    NotaFiscalHistorico,
    NotaFiscalEvento,
    NotaFiscalVolume
)
from app.models.entities import NotaFiscal, Usuario
from app.utils.fiscal.helpers import NFeHelpers


# ============================================
# 1. CRUD CONFIGURAÇÃO FISCAL
# ============================================
class ConfiguracaoFiscalCRUD:
    """CRUD para Configurações Fiscais da Empresa"""
    
    # Modelo associado a esta classe CRUD
    model = ConfiguracaoFiscal
    
    @staticmethod
    def criar(db: Session, dados: Dict[str, Any]) -> ConfiguracaoFiscal:
        """
        Cria uma nova configuração fiscal
        """
        try:
            # Trata os dados antes de criar
            dados_tratados = NFeHelpers.tratar_dados_configuracao(dados)
            
            config = ConfiguracaoFiscal(
                razao_social=dados_tratados['razao_social'],
                nome_fantasia=dados_tratados.get('nome_fantasia'),
                cnpj=dados_tratados['cnpj'],
                inscricao_estadual=dados_tratados.get('inscricao_estadual'),
                inscricao_municipal=dados_tratados.get('inscricao_municipal'),
                cnae_principal=dados_tratados.get('cnae_principal'),
                regime_tributario=dados_tratados.get('regime_tributario'),
                logradouro=dados_tratados['logradouro'],
                numero=dados_tratados['numero'],
                complemento=dados_tratados.get('complemento'),
                bairro=dados_tratados['bairro'],
                codigo_municipio=dados_tratados.get('codigo_municipio'),
                municipio=dados_tratados.get('municipio'),
                uf=dados_tratados.get('uf'),
                cep=dados_tratados['cep'],
                telefone=dados_tratados.get('telefone'),
                email=dados_tratados.get('email'),
                serie_nfe=dados_tratados.get('serie_nfe', '1'),
                serie_nfce=dados_tratados.get('serie_nfce', '2'),
                ambiente=dados_tratados.get('ambiente', '2'),
                ultimo_numero_nfe=dados_tratados.get('ultimo_numero_nfe', 0),
                ultimo_numero_nfce=dados_tratados.get('ultimo_numero_nfce', 0),
                ativo=dados_tratados.get('ativo', True)
            )
            
            db.add(config)
            db.commit()
            db.refresh(config)
            return config
            
        except ValueError as e:
            db.rollback()
            raise ValueError(f"Erro ao criar configuração fiscal: {str(e)}")
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro inesperado: {str(e)}")
    
    @staticmethod
    def obter_por_id(db: Session, id: int) -> Optional[ConfiguracaoFiscal]:
        """
        Obtém configuração fiscal por ID
        """
        return db.query(ConfiguracaoFiscal).filter(ConfiguracaoFiscal.id == id).first()
    
    @staticmethod
    def obter_por_cnpj(db: Session, cnpj: str) -> Optional[ConfiguracaoFiscal]:
        """
        Obtém configuração fiscal por CNPJ
        """
        return db.query(ConfiguracaoFiscal).filter(ConfiguracaoFiscal.cnpj == cnpj).first()
    
    @staticmethod
    def obter_ativa(db) -> Optional[ConfiguracaoFiscal]:
        """
        Obtém a configuração fiscal ativa
        """
        return db.query(ConfiguracaoFiscal).filter(
            ConfiguracaoFiscal.ativo == True
        ).first()
    
    @staticmethod
    def listar_todas(db: Session, skip: int = 0, limit: int = 100) -> List[ConfiguracaoFiscal]:
        """
        Lista todas as configurações fiscais
        """
        return db.query(ConfiguracaoFiscal).offset(skip).limit(limit).all()
    
    @staticmethod
    def atualizar(db: Session, id: int, dados: Dict[str, Any]) -> Optional[ConfiguracaoFiscal]:
        """
        Atualiza configuração fiscal
        """
        dados_tratados = NFeHelpers.tratar_dados_configuracao(dados)
        config = ConfiguracaoFiscalCRUD.obter_por_id(db, id)
        if not config:
            return None
        
        try:
            for key, value in dados_tratados.items():
                if hasattr(config, key) and value is not None:
                    setattr(config, key, value)
            
            config.atualizado_em = datetime.now()
            db.commit()
            db.refresh(config)
            return config
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao atualizar configuração: {str(e)}")
    
    @staticmethod
    def excluir(db: Session, id: int) -> bool:
        """
        Desativa uma configuração fiscal (soft delete)
        """
        config = ConfiguracaoFiscalCRUD.obter_por_id(db, id)
        if not config:
            return False
        
        try:
            config.ativo = False
            config.atualizado_em = datetime.now()
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao desativar configuração: {str(e)}")
    
    @staticmethod
    def reativar(db: Session, id: int) -> Optional[ConfiguracaoFiscal]:
        """
        Reativa uma configuração fiscal (inverso do soft delete)
        """
        config = ConfiguracaoFiscalCRUD.obter_por_id(db, id)
        if not config:
            return None
        
        try:
            config.ativo = True
            config.atualizado_em = datetime.now()
            db.commit()
            db.refresh(config)
            return config
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao reativar configuração: {str(e)}")
        
    @staticmethod
    def incrementar_numero_nfe(db: Session, id: int) -> int:
        """
        Incrementa e retorna o próximo número da NFe
        """
        config = ConfiguracaoFiscalCRUD.obter_por_id(db, id)
        if not config:
            raise ValueError("Configuração fiscal não encontrada")
        
        config.ultimo_numero_nfe += 1
        db.commit()
        return config.ultimo_numero_nfe
    
    @staticmethod
    def incrementar_numero_nfce(db: Session, id: int) -> int:
        """
        Incrementa e retorna o próximo número da NFCe
        """
        config = ConfiguracaoFiscalCRUD.obter_por_id(db, id)
        if not config:
            raise ValueError("Configuração fiscal não encontrada")
        
        config.ultimo_numero_nfce += 1
        db.commit()
        return config.ultimo_numero_nfce


# ============================================
# 2. CRUD PRODUTO FISCAL
# ============================================
class ProdutoFiscalCRUD:
    """CRUD para Dados Fiscais de Produtos"""
    
    model = ProdutoFiscal
    
    @staticmethod
    def criar(db: Session, dados: Dict[str, Any]) -> ProdutoFiscal:
        """
        Cria dados fiscais para um produto
        """
        try:
            # Verifica se já existe
            existente = db.query(ProdutoFiscal).filter(
                ProdutoFiscal.produto_id == dados['produto_id']
            ).first()
            
            if existente:
                raise ValueError(f"Já existem dados fiscais para o produto ID {dados['produto_id']}")
            
            produto_fiscal = ProdutoFiscal(
                produto_id=dados['produto_id'],
                codigo_ncm=dados.get('codigo_ncm'),
                codigo_cest=dados.get('codigo_cest'),
                codigo_ean=dados.get('codigo_ean'),
                codigo_gtin_trib=dados.get('codigo_gtin_trib'),
                unidade_tributaria=dados.get('unidade_tributaria'),
                valor_unitario_trib=dados.get('valor_unitario_trib'),
                origem=dados.get('origem', '0'),
                tipo_item=dados.get('tipo_item'),
                cst_icms=dados.get('cst_icms'),
                cfop=dados.get('cfop'),
                aliquota_icms=dados.get('aliquota_icms'),
                cst_pis=dados.get('cst_pis'),
                aliquota_pis=dados.get('aliquota_pis'),
                cst_cofins=dados.get('cst_cofins'),
                aliquota_cofins=dados.get('aliquota_cofins'),
                informacoes_fisco=dados.get('informacoes_fisco'),
                informacoes_complementares=dados.get('informacoes_complementares'),
                homologado=dados.get('homologado', False)
            )
            
            db.add(produto_fiscal)
            db.commit()
            db.refresh(produto_fiscal)
            return produto_fiscal
            
        except IntegrityError as e:
            db.rollback()
            raise ValueError(f"Erro ao criar dados fiscais do produto: {str(e)}")
    
    @staticmethod
    def obter_por_id(db: Session, id: int) -> Optional[ProdutoFiscal]:
        """
        Obtém dados fiscais por ID
        """
        return db.query(ProdutoFiscal).filter(ProdutoFiscal.id == id).first()
    
    @staticmethod
    def obter_por_produto_id(db: Session, produto_id: int) -> Optional[ProdutoFiscal]:
        """
        Obtém dados fiscais por ID do produto
        """
        return db.query(ProdutoFiscal).filter(
            ProdutoFiscal.produto_id == produto_id
        ).first()
    
    @staticmethod
    def obter_por_ncm(db: Session, ncm: str) -> List[ProdutoFiscal]:
        """
        Obtém produtos fiscais por NCM
        """
        return db.query(ProdutoFiscal).filter(
            ProdutoFiscal.codigo_ncm == ncm
        ).all()
    
    @staticmethod
    def listar_homologados(db: Session, skip: int = 0, limit: int = 100) -> List[ProdutoFiscal]:
        """
        Lista produtos fiscais homologados
        """
        return db.query(ProdutoFiscal).filter(
            ProdutoFiscal.homologado == True
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def listar_todos(db: Session, skip: int = 0, limit: int = 100) -> List[ProdutoFiscal]:
        """
        Lista todos os produtos fiscais
        """
        return db.query(ProdutoFiscal).offset(skip).limit(limit).all()
    
    @staticmethod
    def listar_nao_homologados(db: Session, skip: int = 0, limit: int = 100) -> List[ProdutoFiscal]:
        """
        Lista produtos fiscais não homologados
        """
        return db.query(ProdutoFiscal).filter(
            ProdutoFiscal.homologado == False
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def listar_por_ids(db: Session, produto_ids: List[int]) -> List[ProdutoFiscal]:
        """
        Lista dados fiscais para uma lista de IDs de produtos
        """
        return db.query(ProdutoFiscal).filter(
            ProdutoFiscal.produto_id.in_(produto_ids)
        ).all()
    
    @staticmethod
    def atualizar(db: Session, id: int, dados: Dict[str, Any]) -> Optional[ProdutoFiscal]:
        """
        Atualiza dados fiscais do produto
        """
        produto_fiscal = ProdutoFiscalCRUD.obter_por_id(db, id)
        if not produto_fiscal:
            return None
        
        try:
            campos_atualizaveis = [
                'codigo_ncm', 'codigo_cest', 'codigo_ean', 'codigo_gtin_trib',
                'unidade_tributaria', 'valor_unitario_trib', 'origem', 'tipo_item',
                'cst_icms', 'cfop', 'aliquota_icms', 'cst_pis', 'aliquota_pis',
                'cst_cofins', 'aliquota_cofins', 'informacoes_fisco',
                'informacoes_complementares', 'homologado'
            ]
            
            for key, value in dados.items():
                if key in campos_atualizaveis and value is not None:
                    setattr(produto_fiscal, key, value)
            
            if dados.get('homologado') == True and not produto_fiscal.data_homologacao:
                produto_fiscal.data_homologacao = datetime.now()
                produto_fiscal.justificativa_homologacao = dados.get('justificativa_homologacao')
            
            produto_fiscal.atualizado_em = datetime.now()
            db.commit()
            db.refresh(produto_fiscal)
            return produto_fiscal
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao atualizar dados fiscais: {str(e)}")
    
    @staticmethod
    def excluir(db: Session, id: int) -> bool:
        """
        Exclui dados fiscais do produto
        """
        produto_fiscal = ProdutoFiscalCRUD.obter_por_id(db, id)
        if not produto_fiscal:
            return False
        
        try:
            db.delete(produto_fiscal)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao excluir dados fiscais: {str(e)}")
    
    @staticmethod
    def homologar(db: Session, id: int, justificativa: str = None) -> Optional[ProdutoFiscal]:
        """
        Homologa os dados fiscais do produto
        """
        produto_fiscal = ProdutoFiscalCRUD.obter_por_id(db, id)
        if not produto_fiscal:
            return None
        
        try:
            produto_fiscal.homologado = True
            produto_fiscal.data_homologacao = datetime.now()
            produto_fiscal.justificativa_homologacao = justificativa
            produto_fiscal.atualizado_em = datetime.now()
            
            db.commit()
            db.refresh(produto_fiscal)
            return produto_fiscal
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao homologar produto: {str(e)}")


# ============================================
# 3. CRUD TRANSPORTADORA
# ============================================
class TransportadoraCRUD:
    """CRUD para Transportadoras"""
    
    model = Transportadora
    
    @staticmethod
    def criar(db: Session, dados: Dict[str, Any]) -> Transportadora:
        """
        Cria uma nova transportadora
        """
        try:
            # Validação: CNPJ ou CPF obrigatório
            if not dados.get('cnpj') and not dados.get('cpf'):
                raise ValueError("CNPJ ou CPF é obrigatório")
            
            transportadora = Transportadora(
                razao_social=dados['razao_social'],
                nome_fantasia=dados.get('nome_fantasia'),
                cnpj=dados.get('cnpj'),
                cpf=dados.get('cpf'),
                inscricao_estadual=dados.get('inscricao_estadual'),
                logradouro=dados.get('logradouro'),
                numero=dados.get('numero'),
                complemento=dados.get('complemento'),
                bairro=dados.get('bairro'),
                municipio=dados.get('municipio'),
                uf=dados.get('uf'),
                cep=dados.get('cep'),
                telefone=dados.get('telefone'),
                email=dados.get('email'),
                modalidade_frete=dados.get('modalidade_frete', '0'),
                placa_veiculo=dados.get('placa_veiculo'),
                uf_veiculo=dados.get('uf_veiculo'),
                rntc=dados.get('rntc'),
                ativo=dados.get('ativo', True)
            )
            
            db.add(transportadora)
            db.commit()
            db.refresh(transportadora)
            return transportadora
            
        except IntegrityError as e:
            db.rollback()
            raise ValueError(f"Erro ao criar transportadora: {str(e)}")
    
    @staticmethod
    def obter_por_id(db: Session, id: int) -> Optional[Transportadora]:
        """
        Obtém transportadora por ID
        """
        return db.query(Transportadora).filter(Transportadora.id == id).first()
    
    @staticmethod
    def obter_por_cnpj(db: Session, cnpj: str) -> Optional[Transportadora]:
        """
        Obtém transportadora por CNPJ
        """
        return db.query(Transportadora).filter(
            Transportadora.cnpj == cnpj,
            Transportadora.ativo == True
        ).first()
    
    @staticmethod
    def obter_por_cpf(db: Session, cpf: str) -> Optional[Transportadora]:
        """
        Obtém transportadora por CPF
        """
        return db.query(Transportadora).filter(
            Transportadora.cpf == cpf,
            Transportadora.ativo == True
        ).first()
    
    @staticmethod
    def buscar_por_nome(db: Session, nome: str, skip: int = 0, limit: int = 50) -> List[Transportadora]:
        """
        Busca transportadoras por nome/razão social
        """
        return db.query(Transportadora).filter(
            and_(
                Transportadora.ativo == True,
                or_(
                    Transportadora.razao_social.ilike(f"%{nome}%"),
                    Transportadora.nome_fantasia.ilike(f"%{nome}%")
                )
            )
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def listar_ativas(db: Session, skip: int = 0, limit: int = 100) -> List[Transportadora]:
        """
        Lista transportadoras ativas
        """
        return db.query(Transportadora).filter(
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def atualizar(db: Session, id: int, dados: Dict[str, Any]) -> Optional[Transportadora]:
        """
        Atualiza transportadora
        """
        transportadora = TransportadoraCRUD.obter_por_id(db, id)
        if not transportadora:
            return None
        
        try:
            for key, value in dados.items():
                if hasattr(transportadora, key) and value is not None:
                    setattr(transportadora, key, value)
            
            transportadora.atualizado_em = datetime.now()
            db.commit()
            db.refresh(transportadora)
            return transportadora
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao atualizar transportadora: {str(e)}")
    
    @staticmethod
    def excluir(db: Session, id: int) -> bool:
        """
        Exclui transportadora (soft delete - desativa)
        """
        transportadora = TransportadoraCRUD.obter_por_id(db, id)
        if not transportadora:
            return False
        
        try:
            transportadora.ativo = False
            transportadora.atualizado_em = datetime.now()
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao excluir transportadora: {str(e)}")


# ============================================
# 4. CRUD VEÍCULO DE TRANSPORTE
# ============================================
class VeiculoTransporteCRUD:
    """CRUD para Veículos de Transporte"""
    
    model = VeiculoTransporte
    
    @staticmethod
    def criar(db: Session, dados: Dict[str, Any]) -> VeiculoTransporte:
        """
        Cria um novo veículo de transporte
        """
        try:
            # Trata os dados antes de criar
            dados_tratados = NFeHelpers.tratar_dados_veiculo(dados)
            
            # Converte campos específicos
            capacidade_carga = dados_tratados.get('capacidade_carga')
            if capacidade_carga is not None:
                try:
                    capacidade_carga = Decimal(str(capacidade_carga))
                except:
                    capacidade_carga = None
            
            transportadora_id = dados_tratados.get('transportadora_id')
            if transportadora_id is not None:
                try:
                    transportadora_id = int(transportadora_id)
                except:
                    transportadora_id = None
            
            ativo = dados_tratados.get('ativo', True)
            if isinstance(ativo, str):
                ativo = ativo.lower() in ('true', '1', 'yes', 'sim')
            
            veiculo = VeiculoTransporte(
                transportadora_id=transportadora_id,
                placa=dados_tratados['placa'],
                uf=dados_tratados['uf'],
                rntc=dados_tratados.get('rntc'),
                tipo_veiculo=dados_tratados.get('tipo_veiculo'),
                capacidade_carga=capacidade_carga,
                proprietario=dados_tratados.get('proprietario'),
                ativo=ativo
            )
            
            db.add(veiculo)
            db.commit()
            db.refresh(veiculo)
            return veiculo
            
        except IntegrityError as e:
            db.rollback()
            raise ValueError(f"Erro ao criar veículo: {str(e)}")
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro inesperado ao criar veículo: {str(e)}")
    
    @staticmethod
    def obter_por_id(db: Session, id: int) -> Optional[VeiculoTransporte]:
        """
        Obtém veículo por ID
        """
        return db.query(VeiculoTransporte).filter(VeiculoTransporte.id == id).first()
    
    @staticmethod
    def obter_por_placa(db: Session, placa: str) -> Optional[VeiculoTransporte]:
        """
        Obtém veículo por placa
        """
        placa_formatada = placa.upper().replace('-', '').replace(' ', '')
        return db.query(VeiculoTransporte).filter(
            VeiculoTransporte.placa == placa_formatada,
            VeiculoTransporte.ativo == True
        ).first()
    
    @staticmethod
    def listar_por_transportadora(db: Session, transportadora_id: int) -> List[VeiculoTransporte]:
        """
        Lista veículos de uma transportadora
        """
        return db.query(VeiculoTransporte).filter(
            VeiculoTransporte.transportadora_id == transportadora_id,
            VeiculoTransporte.ativo == True
        ).all()
    
    @staticmethod
    def listar_ativos(db: Session, skip: int = 0, limit: int = 100) -> List[VeiculoTransporte]:
        """
        Lista veículos ativos
        """
        return db.query(VeiculoTransporte).offset(skip).limit(limit).all()
    
    @staticmethod
    def atualizar(db: Session, id: int, dados: Dict[str, Any]) -> Optional[VeiculoTransporte]:
        """
        Atualiza veículo de transporte
        """
        veiculo = VeiculoTransporteCRUD.obter_por_id(db, id)
        if not veiculo:
            return None
        
        try:
            for key, value in dados.items():
                if hasattr(veiculo, key) and value is not None:
                    # Formata placa se for o campo
                    if key == 'placa':
                        value = value.upper().replace('-', '').replace(' ', '')
                    setattr(veiculo, key, value)
            
            veiculo.atualizado_em = datetime.now()
            db.commit()
            db.refresh(veiculo)
            return veiculo
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao atualizar veículo: {str(e)}")
    
    @staticmethod
    def excluir(db: Session, id: int) -> bool:
        """
        Exclui veículo (soft delete - desativa)
        """
        veiculo = VeiculoTransporteCRUD.obter_por_id(db, id)
        if not veiculo:
            return False
        
        try:
            veiculo.ativo = False
            veiculo.atualizado_em = datetime.now()
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao excluir veículo: {str(e)}")

    @staticmethod
    def reativar(db: Session, id: int) -> Optional[VeiculoTransporte]:
        """
        Reativa um veículo de transporte
        """
        veiculo = VeiculoTransporteCRUD.obter_por_id(db, id)
        if not veiculo:
            return None
        
        try:
            veiculo.ativo = True
            veiculo.atualizado_em = datetime.now()
            db.commit()
            db.refresh(veiculo)
            return veiculo
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao reativar veículo: {str(e)}")
        
# ============================================
# 5. CRUD HISTÓRICO DA NOTA FISCAL
# ============================================
class NotaFiscalHistoricoCRUD:
    """CRUD para Histórico de Alterações da Nota Fiscal"""
    
    model = NotaFiscalHistorico
    
    @staticmethod
    def criar(db: Session, dados: Dict[str, Any]) -> NotaFiscalHistorico:
        """
        Cria um novo registro no histórico da nota fiscal
        """
        try:
            historico = NotaFiscalHistorico(
                nota_fiscal_id=dados['nota_fiscal_id'],
                usuario_id=dados['usuario_id'],
                tipo_alteracao=dados['tipo_alteracao'],
                dados_anteriores=dados.get('dados_anteriores'),
                dados_novos=dados.get('dados_novos'),
                descricao=dados.get('descricao'),
                codigo_status=dados.get('codigo_status'),
                motivo_status=dados.get('motivo_status'),
                protocolo=dados.get('protocolo'),
                xml_resposta=dados.get('xml_resposta'),
                sucesso=dados.get('sucesso', True),
                mensagem_erro=dados.get('mensagem_erro')
            )
            
            db.add(historico)
            db.commit()
            db.refresh(historico)
            return historico
            
        except IntegrityError as e:
            db.rollback()
            raise ValueError(f"Erro ao criar histórico: {str(e)}")
    
    @staticmethod
    def obter_por_id(db: Session, id: int) -> Optional[NotaFiscalHistorico]:
        """
        Obtém histórico por ID
        """
        return db.query(NotaFiscalHistorico).filter(NotaFiscalHistorico.id == id).first()
    
    @staticmethod
    def listar_por_nota(db: Session, nota_fiscal_id: int, skip: int = 0, limit: int = 100) -> List[NotaFiscalHistorico]:
        """
        Lista histórico de uma nota fiscal
        """
        return db.query(NotaFiscalHistorico).filter(
            NotaFiscalHistorico.nota_fiscal_id == nota_fiscal_id
        ).order_by(NotaFiscalHistorico.data_alteracao.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def listar_por_usuario(db: Session, usuario_id: int, skip: int = 0, limit: int = 100) -> List[NotaFiscalHistorico]:
        """
        Lista histórico por usuário
        """
        return db.query(NotaFiscalHistorico).filter(
            NotaFiscalHistorico.usuario_id == usuario_id
        ).order_by(NotaFiscalHistorico.data_alteracao.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def listar_por_tipo(db: Session, tipo_alteracao: str, skip: int = 0, limit: int = 100) -> List[NotaFiscalHistorico]:
        """
        Lista histórico por tipo de alteração
        """
        return db.query(NotaFiscalHistorico).filter(
            NotaFiscalHistorico.tipo_alteracao == tipo_alteracao
        ).order_by(NotaFiscalHistorico.data_alteracao.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def registrar_alteracao(
        db: Session,
        nota_fiscal_id: int,
        usuario_id: int,
        tipo_alteracao: str,
        descricao: str,
        dados_anteriores: str = None,
        dados_novos: str = None,
        sucesso: bool = True,
        mensagem_erro: str = None
    ) -> NotaFiscalHistorico:
        """
        Método helper para registrar uma alteração
        """
        dados = {
            'nota_fiscal_id': nota_fiscal_id,
            'usuario_id': usuario_id,
            'tipo_alteracao': tipo_alteracao,
            'descricao': descricao,
            'dados_anteriores': dados_anteriores,
            'dados_novos': dados_novos,
            'sucesso': sucesso,
            'mensagem_erro': mensagem_erro
        }
        
        return NotaFiscalHistoricoCRUD.criar(db, dados)


# ============================================
# 6. CRUD EVENTO DA NOTA FISCAL
# ============================================
class NotaFiscalEventoCRUD:
    """CRUD para Eventos da Nota Fiscal"""
    
    model = NotaFiscalEvento
    
    @staticmethod
    def criar(db: Session, dados: Dict[str, Any]) -> NotaFiscalEvento:
        """
        Cria um novo evento da nota fiscal
        """
        try:
            # Determina a sequência do evento
            sequencia = dados.get('sequencia_evento', 1)
            if sequencia == 1:
                ultimo_evento = db.query(NotaFiscalEvento).filter(
                    NotaFiscalEvento.nota_fiscal_id == dados['nota_fiscal_id'],
                    NotaFiscalEvento.tipo_evento == dados['tipo_evento']
                ).order_by(NotaFiscalEvento.sequencia_evento.desc()).first()
                
                if ultimo_evento:
                    sequencia = ultimo_evento.sequencia_evento + 1
            
            evento = NotaFiscalEvento(
                nota_fiscal_id=dados['nota_fiscal_id'],
                tipo_evento=dados['tipo_evento'],
                sequencia_evento=sequencia,
                descricao_evento=dados['descricao_evento'],
                justificativa=dados.get('justificativa'),
                numero_protocolo=dados.get('numero_protocolo'),
                data_recebimento=dados.get('data_recebimento'),
                codigo_status=dados.get('codigo_status'),
                motivo_status=dados.get('motivo_status'),
                xml_evento=dados.get('xml_evento'),
                xml_retorno=dados.get('xml_retorno'),
                processado=dados.get('processado', False),
                sucesso=dados.get('sucesso', True)
            )
            
            db.add(evento)
            db.commit()
            db.refresh(evento)
            return evento
            
        except IntegrityError as e:
            db.rollback()
            raise ValueError(f"Erro ao criar evento: {str(e)}")
    
    @staticmethod
    def obter_por_id(db: Session, id: int) -> Optional[NotaFiscalEvento]:
        """
        Obtém evento por ID
        """
        return db.query(NotaFiscalEvento).filter(NotaFiscalEvento.id == id).first()
    
    @staticmethod
    def listar_por_nota(db: Session, nota_fiscal_id: int) -> List[NotaFiscalEvento]:
        """
        Lista eventos de uma nota fiscal
        """
        return db.query(NotaFiscalEvento).filter(
            NotaFiscalEvento.nota_fiscal_id == nota_fiscal_id
        ).order_by(NotaFiscalEvento.data_registro).all()
    
    @staticmethod
    def listar_todos(db: Session, skip: int = 0, limit: int = 100, 
                    tipo_evento: str = None, processado: bool = None) -> List[NotaFiscalEvento]:
        """
        Lista todos os eventos com filtros opcionais
        """
        query = db.query(NotaFiscalEvento)
        
        if tipo_evento:
            query = query.filter(NotaFiscalEvento.tipo_evento == tipo_evento)
        
        if processado is not None:
            query = query.filter(NotaFiscalEvento.processado == processado)
        
        return query.order_by(NotaFiscalEvento.data_registro.desc())\
                   .offset(skip).limit(limit).all()
    
    @staticmethod
    def obter_ultimo_evento(db: Session, nota_fiscal_id: int, tipo_evento: str = None) -> Optional[NotaFiscalEvento]:
        """
        Obtém o último evento da nota fiscal
        """
        query = db.query(NotaFiscalEvento).filter(
            NotaFiscalEvento.nota_fiscal_id == nota_fiscal_id
        )
        
        if tipo_evento:
            query = query.filter(NotaFiscalEvento.tipo_evento == tipo_evento)
        
        return query.order_by(NotaFiscalEvento.sequencia_evento.desc()).first()
    
    @staticmethod
    def marcar_processado(db: Session, id: int, sucesso: bool = True, xml_retorno: str = None) -> Optional[NotaFiscalEvento]:
        """
        Marca evento como processado
        """
        evento = NotaFiscalEventoCRUD.obter_por_id(db, id)
        if not evento:
            return None
        
        try:
            evento.processado = True
            evento.sucesso = sucesso
            evento.data_processamento = datetime.now()
            
            if xml_retorno:
                evento.xml_retorno = xml_retorno
            
            db.commit()
            db.refresh(evento)
            return evento
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao marcar evento como processado: {str(e)}")
    
    @staticmethod
    def registrar_cancelamento(
        db: Session,
        nota_fiscal_id: int,
        justificativa: str,
        protocolo: str = None,
        xml_evento: str = None
    ) -> NotaFiscalEvento:
        """
        Método helper para registrar cancelamento
        """
        dados = {
            'nota_fiscal_id': nota_fiscal_id,
            'tipo_evento': '110111',  # Código para cancelamento
            'descricao_evento': 'Cancelamento de NF-e',
            'justificativa': justificativa,
            'numero_protocolo': protocolo,
            'xml_evento': xml_evento
        }
        
        return NotaFiscalEventoCRUD.criar(db, dados)
    
    @staticmethod
    def registrar_carta_correcao(
        db: Session,
        nota_fiscal_id: int,
        correcoes: str,
        sequencia: int = 1,
        protocolo: str = None,
        xml_evento: str = None
    ) -> NotaFiscalEvento:
        """
        Método helper para registrar carta de correção
        """
        dados = {
            'nota_fiscal_id': nota_fiscal_id,
            'tipo_evento': '110110',  # Código para CC-e
            'sequencia_evento': sequencia,
            'descricao_evento': f'Carta de Correção {sequencia}',
            'justificativa': correcoes,
            'numero_protocolo': protocolo,
            'xml_evento': xml_evento
        }
        
        return NotaFiscalEventoCRUD.criar(db, dados)


# ============================================
# 7. CRUD VOLUMES DA NOTA FISCAL
# ============================================
class NotaFiscalVolumeCRUD:
    """CRUD para Volumes/Remessas da Nota Fiscal"""
    
    model = NotaFiscalVolume
    
    @staticmethod
    def criar(db: Session, dados: Dict[str, Any]) -> NotaFiscalVolume:
        """
        Cria um novo volume para nota fiscal
        """
        try:
            volume = NotaFiscalVolume(
                nota_fiscal_id=dados['nota_fiscal_id'],
                quantidade=dados.get('quantidade', 1),
                especie=dados.get('especie'),
                marca=dados.get('marca'),
                numeracao=dados.get('numeracao'),
                peso_liquido=dados.get('peso_liquido'),
                peso_bruto=dados.get('peso_bruto'),
                lacres=dados.get('lacres')
            )
            
            db.add(volume)
            db.commit()
            db.refresh(volume)
            return volume
            
        except IntegrityError as e:
            db.rollback()
            raise ValueError(f"Erro ao criar volume: {str(e)}")
    
    @staticmethod
    def criar_multiplos(db: Session, nota_fiscal_id: int, volumes: List[Dict[str, Any]]) -> List[NotaFiscalVolume]:
        """
        Cria múltiplos volumes para uma nota fiscal
        """
        try:
            volumes_criados = []
            for volume_data in volumes:
                volume_data['nota_fiscal_id'] = nota_fiscal_id
                volume = NotaFiscalVolumeCRUD.criar(db, volume_data)
                volumes_criados.append(volume)
            
            db.commit()
            return volumes_criados
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao criar múltiplos volumes: {str(e)}")
    
    @staticmethod
    def obter_por_id(db: Session, id: int) -> Optional[NotaFiscalVolume]:
        """
        Obtém volume por ID
        """
        return db.query(NotaFiscalVolume).filter(NotaFiscalVolume.id == id).first()
    
    @staticmethod
    def listar_por_nota(db: Session, nota_fiscal_id: int) -> List[NotaFiscalVolume]:
        """
        Lista volumes de uma nota fiscal
        """
        return db.query(NotaFiscalVolume).filter(
            NotaFiscalVolume.nota_fiscal_id == nota_fiscal_id
        ).all()
    
    @staticmethod
    def atualizar(db: Session, id: int, dados: Dict[str, Any]) -> Optional[NotaFiscalVolume]:
        """
        Atualiza volume da nota fiscal
        """
        volume = NotaFiscalVolumeCRUD.obter_por_id(db, id)
        if not volume:
            return None
        
        try:
            campos_atualizaveis = [
                'quantidade', 'especie', 'marca', 'numeracao',
                'peso_liquido', 'peso_bruto', 'lacres'
            ]
            
            for key, value in dados.items():
                if key in campos_atualizaveis and value is not None:
                    setattr(volume, key, value)
            
            db.commit()
            db.refresh(volume)
            return volume
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao atualizar volume: {str(e)}")
    
    @staticmethod
    def excluir(db: Session, id: int) -> bool:
        """
        Exclui volume da nota fiscal
        """
        volume = NotaFiscalVolumeCRUD.obter_por_id(db, id)
        if not volume:
            return False
        
        try:
            db.delete(volume)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao excluir volume: {str(e)}")
    
    @staticmethod
    def excluir_todos_por_nota(db: Session, nota_fiscal_id: int) -> bool:
        """
        Exclui todos os volumes de uma nota fiscal
        """
        try:
            db.query(NotaFiscalVolume).filter(
                NotaFiscalVolume.nota_fiscal_id == nota_fiscal_id
            ).delete()
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao excluir volumes da nota: {str(e)}")


# ============================================
# FACADE PARA ACESSO SIMPLIFICADO
# ============================================
class FiscalManager:
    """
    Facade para gerenciamento fiscal unificado
    """
    
    def __init__(self, db):
        self.db = db
    
    # Métodos de conveniência
    def obter_configuracao_ativa(self) -> Optional[ConfiguracaoFiscal]:
        """Obtém a configuração fiscal ativa"""
        return ConfiguracaoFiscalCRUD.obter_ativa(self.db)
    
    def obter_produto_fiscal(self, produto_id: int) -> Optional[ProdutoFiscal]:
        """Obtém dados fiscais de um produto"""
        return ProdutoFiscalCRUD.obter_por_produto_id(self.db.session, produto_id)
    
    def buscar_transportadora_por_documento(self, documento: str) -> Optional[Transportadora]:
        """Busca transportadora por CNPJ ou CPF"""
        if len(documento) == 11:
            return TransportadoraCRUD.obter_por_cpf(self.db.session, documento)
        else:
            return TransportadoraCRUD.obter_por_cnpj(self.db.session, documento)
    
    def registrar_evento_nota(self, nota_id: int, tipo: str, descricao: str, **kwargs) -> NotaFiscalEvento:
        """Registra um evento para uma nota fiscal"""
        dados = {
            'nota_fiscal_id': nota_id,
            'tipo_evento': tipo,
            'descricao_evento': descricao,
            **kwargs
        }
        return NotaFiscalEventoCRUD.criar(self.db.session, dados)