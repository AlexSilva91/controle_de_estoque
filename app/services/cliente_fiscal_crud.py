"""
app/services/cliente_fiscal_crud.py

CRUD completo para Clientes Fiscais
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, or_
from app.models.fiscal_models import ClienteFiscal
from app.utils.fiscal.helpers import NFeHelpers


# ============================================
# CRUD CLIENTE FISCAL
# ============================================
class ClienteFiscalCRUD:
    """CRUD para Clientes Fiscais"""
    
    # Modelo associado a esta classe CRUD
    model = ClienteFiscal
    
    @staticmethod
    def criar(db: Session, dados: Dict[str, Any]) -> ClienteFiscal:
        """
        Cria um novo cliente fiscal
        
        Args:
            db: Sessão do banco de dados
            dados: Dicionário com os dados do cliente
        
        Returns:
            ClienteFiscal: Cliente criado
        
        Raises:
            ValueError: Se houver erro de validação
            Exception: Se houver erro inesperado
        """
        try:
            # Valida e trata os dados antes de criar
            dados_tratados = ClienteFiscalCRUD._tratar_dados_criacao(dados)
            
            # Verifica se cliente já existe pelo CPF/CNPJ
            existente = db.query(ClienteFiscal).filter(
                ClienteFiscal.cpf_cnpj == dados_tratados['cpf_cnpj']
            ).first()
            
            if existente:
                raise ValueError(f"Cliente com CPF/CNPJ {dados_tratados['cpf_cnpj']} já cadastrado")
            
            # Cria o cliente
            cliente = ClienteFiscal(
                # Identificação
                cpf_cnpj=dados_tratados['cpf_cnpj'],
                nome_cliente=dados_tratados['nome_cliente'],
                nome_fantasia=dados_tratados.get('nome_fantasia'),
                
                # Dados Fiscais
                indicador_ie=dados_tratados.get('indicador_ie', 9),
                inscricao_estadual=dados_tratados.get('inscricao_estadual'),
                inscricao_municipal=dados_tratados.get('inscricao_municipal', ''),
                inscricao_suframa=dados_tratados.get('inscricao_suframa', ''),
                
                # Endereço
                cep=dados_tratados['cep'],
                logradouro=dados_tratados['logradouro'],
                numero=dados_tratados['numero'],
                complemento=dados_tratados.get('complemento'),
                bairro=dados_tratados['bairro'],
                codigo_municipio=dados_tratados['codigo_municipio'],
                municipio=dados_tratados['municipio'],
                uf=dados_tratados['uf'],
                codigo_pais=dados_tratados.get('codigo_pais', 1058),
                pais=dados_tratados.get('pais', 'BRASIL'),
                
                # Contato
                telefone=dados_tratados.get('telefone', ''),
                celular=dados_tratados.get('celular', ''),
                email=dados_tratados.get('email', ''),
                fax=dados_tratados.get('fax', ''),
                
                # Informações Adicionais
                observacoes=dados_tratados.get('observacoes', ''),
                tipo_cliente=dados_tratados.get('tipo_cliente', 'fisica'),
                regime_tributario=dados_tratados.get('regime_tributario', '1'),
                
                # Controle
                ativo=dados_tratados.get('ativo', True),
                sincronizado=dados_tratados.get('sincronizado', False)
            )
            
            db.add(cliente)
            db.commit()
            db.refresh(cliente)
            return cliente
            
        except ValueError as e:
            db.rollback()
            raise ValueError(f"Erro ao criar cliente fiscal: {str(e)}")
        except IntegrityError as e:
            db.rollback()
            raise ValueError(f"Erro de integridade ao criar cliente: {str(e)}")
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro inesperado ao criar cliente: {str(e)}")
    
    @staticmethod
    def obter_por_id(db: Session, id: int, ativo: bool = True) -> Optional[ClienteFiscal]:
        """
        Obtém cliente fiscal por ID
        
        Args:
            db: Sessão do banco de dados
            id: ID do cliente
            ativo: Se True, filtra apenas clientes ativos
        
        Returns:
            Optional[ClienteFiscal]: Cliente encontrado ou None
        """
        query = db.query(ClienteFiscal).filter(ClienteFiscal.id == id)
            
        return query.first()
    
    @staticmethod
    def obter_por_cpf_cnpj(db: Session, cpf_cnpj: str, ativo: bool = True) -> Optional[ClienteFiscal]:
        """
        Obtém cliente fiscal por CPF/CNPJ
        
        Args:
            db: Sessão do banco de dados
            cpf_cnpj: CPF ou CNPJ do cliente
            ativo: Se True, filtra apenas clientes ativos
        
        Returns:
            Optional[ClienteFiscal]: Cliente encontrado ou None
        """
        # Remove caracteres não numéricos
        cpf_cnpj_limpo = ''.join(filter(str.isdigit, cpf_cnpj))
        
        query = db.query(ClienteFiscal).filter(ClienteFiscal.cpf_cnpj == cpf_cnpj_limpo)
            
        return query.first()
    
    @staticmethod
    def buscar_por_nome(db: Session, nome: str, ativo: bool = True, 
                       skip: int = 0, limit: int = 50) -> List[ClienteFiscal]:
        """
        Busca clientes por nome
        
        Args:
            db: Sessão do banco de dados
            nome: Nome ou parte do nome para busca
            ativo: Se True, filtra apenas clientes ativos
            skip: Número de registros a pular
            limit: Número máximo de registros
        
        Returns:
            List[ClienteFiscal]: Lista de clientes encontrados
        """
        query = db.query(ClienteFiscal).filter(
            or_(
                ClienteFiscal.nome_cliente.ilike(f"%{nome}%"),
                ClienteFiscal.nome_fantasia.ilike(f"%{nome}%")
            )
        )
        
        return query.order_by(ClienteFiscal.nome_cliente)\
                   .offset(skip)\
                   .limit(limit)\
                   .all()
    
    @staticmethod
    def listar_todos(db: Session, ativo: bool = None, skip: int = 0, 
                    limit: int = 100) -> List[ClienteFiscal]:
        """
        Lista todos os clientes fiscais
        
        Args:
            db: Sessão do banco de dados
            ativo: Filtro por status ativo/inativo (None para todos)
            skip: Número de registros a pular
            limit: Número máximo de registros
        
        Returns:
            List[ClienteFiscal]: Lista de clientes
        """
        query = db.query(ClienteFiscal)
        
        if ativo is not None:
            query = query.filter(ClienteFiscal.ativo == ativo)
        
        return query.order_by(ClienteFiscal.nome_cliente)\
                   .offset(skip)\
                   .limit(limit)\
                   .all()
    
    @staticmethod
    def listar_por_tipo(db: Session, tipo_cliente: str, ativo: bool = True,
                       skip: int = 0, limit: int = 100) -> List[ClienteFiscal]:
        """
        Lista clientes por tipo (fisica/juridica)
        
        Args:
            db: Sessão do banco de dados
            tipo_cliente: 'fisica' ou 'juridica'
            ativo: Se True, filtra apenas clientes ativos
            skip: Número de registros a pular
            limit: Número máximo de registros
        
        Returns:
            List[ClienteFiscal]: Lista de clientes
        """
        query = db.query(ClienteFiscal).filter(
            ClienteFiscal.tipo_cliente == tipo_cliente
        )
        
        if ativo:
            query = query.filter(ClienteFiscal.ativo == True)
        
        return query.order_by(ClienteFiscal.nome_cliente)\
                   .offset(skip)\
                   .limit(limit)\
                   .all()
    
    @staticmethod
    def listar_por_uf(db: Session, uf: str, ativo: bool = True,
                     skip: int = 0, limit: int = 100) -> List[ClienteFiscal]:
        """
        Lista clientes por UF
        
        Args:
            db: Sessão do banco de dados
            uf: Sigla da UF (ex: 'SP', 'RJ')
            ativo: Se True, filtra apenas clientes ativos
            skip: Número de registros a pular
            limit: Número máximo de registros
        
        Returns:
            List[ClienteFiscal]: Lista de clientes
        """
        query = db.query(ClienteFiscal).filter(
            ClienteFiscal.uf == uf.upper()
        )
        
        if ativo:
            query = query.filter(ClienteFiscal.ativo == True)
        
        return query.order_by(ClienteFiscal.nome_cliente)\
                   .offset(skip)\
                   .limit(limit)\
                   .all()
    
    @staticmethod
    def listar_por_regime_tributario(db: Session, regime: str, ativo: bool = True,
                                    skip: int = 0, limit: int = 100) -> List[ClienteFiscal]:
        """
        Lista clientes por regime tributário
        
        Args:
            db: Sessão do banco de dados
            regime: Regime tributário ('1', '2', '3')
            ativo: Se True, filtra apenas clientes ativos
            skip: Número de registros a pular
            limit: Número máximo de registros
        
        Returns:
            List[ClienteFiscal]: Lista de clientes
        """
        query = db.query(ClienteFiscal).filter(
            ClienteFiscal.regime_tributario == regime
        )
        
        if ativo:
            query = query.filter(ClienteFiscal.ativo == True)
        
        return query.order_by(ClienteFiscal.nome_cliente)\
                   .offset(skip)\
                   .limit(limit)\
                   .all()
    
    @staticmethod
    def listar_nao_sincronizados(db: Session, skip: int = 0, limit: int = 100) -> List[ClienteFiscal]:
        """
        Lista clientes que ainda não foram sincronizados
        
        Args:
            db: Sessão do banco de dados
            skip: Número de registros a pular
            limit: Número máximo de registros
        
        Returns:
            List[ClienteFiscal]: Lista de clientes não sincronizados
        """
        return db.query(ClienteFiscal)\
                .filter(
                    and_(
                        ClienteFiscal.ativo == True,
                        ClienteFiscal.sincronizado == False
                    )
                )\
                .order_by(ClienteFiscal.criado_em)\
                .offset(skip)\
                .limit(limit)\
                .all()
    
    @staticmethod
    def contar_total(db: Session, ativo: bool = True) -> int:
        """
        Conta o total de clientes
        
        Args:
            db: Sessão do banco de dados
            ativo: Se True, conta apenas clientes ativos
        
        Returns:
            int: Total de clientes
        """
        query = db.query(ClienteFiscal)
        
        if ativo:
            query = query.filter(ClienteFiscal.ativo == True)
            
        return query.count()
    
    @staticmethod
    def atualizar(db: Session, id: int, dados: Dict[str, Any]) -> Optional[ClienteFiscal]:
        """
        Atualiza um cliente fiscal
        
        Args:
            db: Sessão do banco de dados
            id: ID do cliente a atualizar
            dados: Dicionário com os dados a atualizar
        
        Returns:
            Optional[ClienteFiscal]: Cliente atualizado ou None se não encontrado
        
        Raises:
            Exception: Se houver erro na atualização
        """
        cliente = ClienteFiscalCRUD.obter_por_id(db, id, ativo=False)
        if not cliente:
            return None
        
        try:
            # Trata os dados antes de atualizar
            dados_tratados = ClienteFiscalCRUD._tratar_dados_atualizacao(dados)
            
            # Atualiza campos permitidos
            campos_atualizaveis = [
                # Identificação
                'nome_cliente', 'nome_fantasia',
                
                # Dados Fiscais
                'indicador_ie', 'inscricao_estadual', 'inscricao_municipal', 
                'inscricao_suframa',
                
                # Endereço
                'cep', 'logradouro', 'numero', 'complemento', 'bairro',
                'codigo_municipio', 'municipio', 'uf', 'codigo_pais', 'pais',
                
                # Contato
                'telefone', 'celular', 'email', 'fax',
                
                # Informações Adicionais
                'observacoes', 'tipo_cliente', 'regime_tributario',
                
                # Controle
                'ativo', 'sincronizado'
            ]
            
            for key, value in dados_tratados.items():
                if key in campos_atualizaveis and value is not None:
                    # Tratamento específico para CPF/CNPJ
                    if key == 'cpf_cnpj':
                        # Verifica se não está sendo alterado para um CPF/CNPJ existente
                        existente = db.query(ClienteFiscal).filter(
                            and_(
                                ClienteFiscal.cpf_cnpj == value,
                                ClienteFiscal.id != id
                            )
                        ).first()
                        if existente:
                            raise ValueError(f"CPF/CNPJ {value} já está em uso por outro cliente")
                    
                    setattr(cliente, key, value)
            
            cliente.atualizado_em = datetime.now()
            db.commit()
            db.refresh(cliente)
            return cliente
            
        except ValueError as e:
            db.rollback()
            raise ValueError(f"Erro ao atualizar cliente: {str(e)}")
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro inesperado ao atualizar cliente: {str(e)}")
    
    @staticmethod
    def excluir(db: Session, id: int, soft_delete: bool = True) -> bool:
        """
        Exclui um cliente fiscal
        
        Args:
            db: Sessão do banco de dados
            id: ID do cliente a excluir
            soft_delete: Se True, realiza soft delete (desativa), se False exclui permanentemente
        
        Returns:
            bool: True se excluído com sucesso, False se não encontrado
        
        Raises:
            Exception: Se houver erro na exclusão
        """
        cliente = ClienteFiscalCRUD.obter_por_id(db, id, ativo=False)
        if not cliente:
            return False
        
        try:
            if soft_delete:
                # Soft delete - apenas desativa
                cliente.ativo = False
                cliente.atualizado_em = datetime.now()
                db.commit()
            else:
                # Hard delete - remove permanentemente
                db.delete(cliente)
                db.commit()
                
            return True
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao excluir cliente: {str(e)}")
    
    @staticmethod
    def reativar(db: Session, id: int) -> Optional[ClienteFiscal]:
        """
        Reativa um cliente fiscal
        
        Args:
            db: Sessão do banco de dados
            id: ID do cliente a reativar
        
        Returns:
            Optional[ClienteFiscal]: Cliente reativado ou None se não encontrado
        
        Raises:
            Exception: Se houver erro na reativação
        """
        cliente = ClienteFiscalCRUD.obter_por_id(db, id, ativo=False)
        if not cliente:
            return None
        
        try:
            cliente.ativo = True
            cliente.atualizado_em = datetime.now()
            db.commit()
            db.refresh(cliente)
            return cliente
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao reativar cliente: {str(e)}")
    
    @staticmethod
    def marcar_sincronizado(db: Session, id: int) -> Optional[ClienteFiscal]:
        """
        Marca um cliente como sincronizado
        
        Args:
            db: Sessão do banco de dados
            id: ID do cliente
        
        Returns:
            Optional[ClienteFiscal]: Cliente atualizado ou None se não encontrado
        """
        cliente = ClienteFiscalCRUD.obter_por_id(db, id)
        if not cliente:
            return None
        
        try:
            cliente.sincronizado = True
            cliente.atualizado_em = datetime.now()
            db.commit()
            db.refresh(cliente)
            return cliente
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao marcar como sincronizado: {str(e)}")
    
    @staticmethod
    def marcar_todos_sincronizados(db: Session, ids: List[int]) -> bool:
        """
        Marca múltiplos clientes como sincronizados
        
        Args:
            db: Sessão do banco de dados
            ids: Lista de IDs dos clientes
        
        Returns:
            bool: True se todos foram marcados com sucesso
        """
        try:
            db.query(ClienteFiscal)\
                .filter(ClienteFiscal.id.in_(ids))\
                .update(
                    {
                        'sincronizado': True,
                        'atualizado_em': datetime.now()
                    },
                    synchronize_session=False
                )
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise Exception(f"Erro ao marcar múltiplos como sincronizados: {str(e)}")
    
    @staticmethod
    def validar_dados_nfe(cliente: ClienteFiscal) -> Dict[str, List[str]]:
        """
        Valida os dados do cliente para emissão de NFe
        
        Args:
            cliente: Cliente fiscal a validar
        
        Returns:
            Dict[str, List[str]]: Dicionário com erros e warnings
        """
        erros = []
        warnings = []
        
        # Validações básicas
        if not cliente.cpf_cnpj:
            erros.append("CPF/CNPJ é obrigatório")
        elif len(cliente.cpf_cnpj) not in [11, 14]:
            erros.append("CPF/CNPJ inválido")
        
        if not cliente.nome_cliente:
            erros.append("Nome do cliente é obrigatório")
        
        if not cliente.cep:
            erros.append("CEP é obrigatório")
        elif len(cliente.cep) != 8:
            warnings.append("CEP pode estar incompleto")
        
        if not cliente.logradouro:
            erros.append("Logradouro é obrigatório")
        
        if not cliente.numero:
            warnings.append("Número do endereço não informado")
        
        if not cliente.bairro:
            erros.append("Bairro é obrigatório")
        
        if not cliente.municipio:
            erros.append("Município é obrigatório")
        
        if not cliente.uf:
            erros.append("UF é obrigatória")
        elif len(cliente.uf) != 2:
            erros.append("UF inválida")
        
        if not cliente.codigo_municipio:
            erros.append("Código do município é obrigatório")
        
        # Validações específicas para pessoa jurídica
        if cliente.tipo_cliente == 'juridica':
            if not cliente.inscricao_estadual and cliente.indicador_ie in [1, 2]:
                warnings.append("Inscrição Estadual não informada para pessoa jurídica")
        
        # Validação de email
        if cliente.email and '@' not in cliente.email:
            warnings.append("Email pode estar mal formatado")
        
        return {
            'erros': erros,
            'warnings': warnings
        }
    
    @staticmethod
    def _tratar_dados_criacao(dados: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trata os dados antes da criação
        
        Args:
            dados: Dicionário com dados brutos
        
        Returns:
            Dict[str, Any]: Dados tratados
        """
        tratados = dados.copy()
        
        # Trata CPF/CNPJ - remove caracteres não numéricos
        if 'cpf_cnpj' in tratados:
            tratados['cpf_cnpj'] = ''.join(filter(str.isdigit, str(tratados['cpf_cnpj'])))
        
        # Trata CEP - remove caracteres não numéricos
        if 'cep' in tratados:
            tratados['cep'] = ''.join(filter(str.isdigit, str(tratados['cep'])))
        
        # Trata telefones - remove caracteres não numéricos
        for campo in ['telefone', 'celular', 'fax']:
            if campo in tratados and tratados[campo]:
                tratados[campo] = ''.join(filter(str.isdigit, str(tratados[campo])))
        
        # Trata UF - maiúsculas
        if 'uf' in tratados and tratados['uf']:
            tratados['uf'] = tratados['uf'].upper()
        
        # Trata email - minúsculas
        if 'email' in tratados and tratados['email']:
            tratados['email'] = tratados['email'].lower()
        
        # Define valores padrão para campos opcionais
        campos_opcionais = {
            'indicador_ie': 9,
            'inscricao_municipal': '',
            'inscricao_suframa': '',
            'telefone': '',
            'celular': '',
            'email': '',
            'fax': '',
            'observacoes': '',
            'tipo_cliente': 'fisica',
            'regime_tributario': '1',
            'ativo': True,
            'sincronizado': False
        }
        
        for campo, valor_padrao in campos_opcionais.items():
            if campo not in tratados or tratados[campo] is None:
                tratados[campo] = valor_padrao
        
        return tratados
    
    @staticmethod
    def _tratar_dados_atualizacao(dados: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trata os dados antes da atualização
        
        Args:
            dados: Dicionário com dados brutos
        
        Returns:
            Dict[str, Any]: Dados tratados
        """
        tratados = dados.copy()
        
        # Trata CPF/CNPJ - remove caracteres não numéricos
        if 'cpf_cnpj' in tratados and tratados['cpf_cnpj']:
            tratados['cpf_cnpj'] = ''.join(filter(str.isdigit, str(tratados['cpf_cnpj'])))
        
        # Trata CEP - remove caracteres não numéricos
        if 'cep' in tratados and tratados['cep']:
            tratados['cep'] = ''.join(filter(str.isdigit, str(tratados['cep'])))
        
        # Trata telefones - remove caracteres não numéricos
        for campo in ['telefone', 'celular', 'fax']:
            if campo in tratados and tratados[campo]:
                tratados[campo] = ''.join(filter(str.isdigit, str(tratados[campo])))
        
        # Trata UF - maiúsculas
        if 'uf' in tratados and tratados['uf']:
            tratados['uf'] = tratados['uf'].upper()
        
        # Trata email - minúsculas
        if 'email' in tratados and tratados['email']:
            tratados['email'] = tratados['email'].lower()
        
        return tratados
    
    @staticmethod
    def importar_de_dict(db: Session, dados_dict: Dict[str, Any]) -> ClienteFiscal:
        """
        Importa um cliente a partir de um dicionário no formato padrão do sistema
        
        Args:
            db: Sessão do banco de dados
            dados_dict: Dicionário com dados no formato padrão
        
        Returns:
            ClienteFiscal: Cliente importado/criado
        """
        # Converte do formato padrão para o formato interno
        dados_internos = {}
        
        # Mapeamento de campos
        mapeamento = {
            'CpfCnpj': 'cpf_cnpj',
            'NmCliente': 'nome_cliente',
            'IndicadorIe': 'indicador_ie',
            'Ie': 'inscricao_estadual',
            'IsUf': 'uf'
        }
        
        for origem, destino in mapeamento.items():
            if origem in dados_dict:
                dados_internos[destino] = dados_dict[origem]
        
        # Trata endereço
        if 'Endereco' in dados_dict:
            endereco = dados_dict['Endereco']
            mapeamento_endereco = {
                'Cep': 'cep',
                'Logradouro': 'logradouro',
                'Complemento': 'complemento',
                'Numero': 'numero',
                'Bairro': 'bairro',
                'CodMunicipio': 'codigo_municipio',
                'Municipio': 'municipio',
                'Uf': 'uf',
                'CodPais': 'codigo_pais',
                'Pais': 'pais'
            }
            
            for origem, destino in mapeamento_endereco.items():
                if origem in endereco and endereco[origem]:
                    dados_internos[destino] = endereco[origem]
        
        # Trata contato
        if 'Contato' in dados_dict:
            contato = dados_dict['Contato']
            mapeamento_contato = {
                'Telefone': 'telefone',
                'Email': 'email',
                'Fax': 'fax'
            }
            
            for origem, destino in mapeamento_contato.items():
                if origem in contato and contato[origem]:
                    dados_internos[destino] = contato[origem]
        
        # Verifica se já existe
        if 'cpf_cnpj' in dados_internos:
            existente = ClienteFiscalCRUD.obter_por_cpf_cnpj(db, dados_internos['cpf_cnpj'], ativo=False)
            if existente:
                # Atualiza o existente
                return ClienteFiscalCRUD.atualizar(db, existente.id, dados_internos)
        
        # Cria novo
        return ClienteFiscalCRUD.criar(db, dados_internos)


# ============================================
# FACADE PARA ACESSO SIMPLIFICADO
# ============================================
class ClienteFiscalManager:
    """
    Facade para gerenciamento de clientes fiscais unificado
    """
    
    def __init__(self, db):
        self.db = db
    
    # Métodos de conveniência
    def obter_cliente(self, cliente_id: int) -> Optional[ClienteFiscal]:
        """Obtém cliente por ID"""
        return ClienteFiscalCRUD.obter_por_id(self.db.session, cliente_id)
    
    def obter_cliente_por_documento(self, documento: str) -> Optional[ClienteFiscal]:
        """Busca cliente por CPF ou CNPJ"""
        return ClienteFiscalCRUD.obter_por_cpf_cnpj(self.db.session, documento)
    
    def buscar_clientes(self, termo: str, limit: int = 20) -> List[ClienteFiscal]:
        """Busca clientes por nome ou documento"""
        # Tenta buscar por documento primeiro
        if termo.isdigit():
            cliente = ClienteFiscalCRUD.obter_por_cpf_cnpj(self.db.session, termo)
            if cliente:
                return [cliente]
        
        # Busca por nome
        return ClienteFiscalCRUD.buscar_por_nome(self.db.session, termo, limit=limit)
    
    def criar_cliente(self, dados: Dict[str, Any]) -> ClienteFiscal:
        """Cria um novo cliente"""
        return ClienteFiscalCRUD.criar(self.db.session, dados)
    
    def atualizar_cliente(self, cliente_id: int, dados: Dict[str, Any]) -> Optional[ClienteFiscal]:
        """Atualiza um cliente existente"""
        return ClienteFiscalCRUD.atualizar(self.db.session, cliente_id, dados)
    
    def desativar_cliente(self, cliente_id: int) -> bool:
        """Desativa um cliente (soft delete)"""
        return ClienteFiscalCRUD.excluir(self.db.session, cliente_id, soft_delete=True)
    
    def reativar_cliente(self, cliente_id: int) -> Optional[ClienteFiscal]:
        """Reativa um cliente desativado"""
        return ClienteFiscalCRUD.reativar(self.db.session, cliente_id)
    
    def validar_cliente_nfe(self, cliente_id: int) -> Dict[str, List[str]]:
        """Valida cliente para emissão de NFe"""
        cliente = self.obter_cliente(cliente_id)
        if not cliente:
            return {'erros': ['Cliente não encontrado'], 'warnings': []}
        
        return ClienteFiscalCRUD.validar_dados_nfe(cliente)
    
    def marcar_sincronizado(self, cliente_id: int) -> Optional[ClienteFiscal]:
        """Marca cliente como sincronizado"""
        return ClienteFiscalCRUD.marcar_sincronizado(self.db.session, cliente_id)
    
    def listar_para_sincronizacao(self, limit: int = 50) -> List[ClienteFiscal]:
        """Lista clientes que precisam ser sincronizados"""
        return ClienteFiscalCRUD.listar_nao_sincronizados(self.db.session, limit=limit)