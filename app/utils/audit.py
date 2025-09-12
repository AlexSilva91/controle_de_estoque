# app/utils/audit.py
import json
import inspect
from datetime import datetime
from functools import wraps
from flask import request, g
from flask_login import current_user
from sqlalchemy import event
from sqlalchemy.inspection import inspect as sqlalchemy_inspect
from app.models import db
from app.models.entities import Log

class AuditLogger:
    """Classe responsável pelo sistema de auditoria detalhado"""
    
    @staticmethod
    def get_client_ip():
        """Obtém o IP do cliente considerando proxies"""
        if request.headers.get("X-Forwarded-For"):
            return request.headers.get("X-Forwarded-For").split(",")[0].strip()
        return request.remote_addr or "127.0.0.1"
    
    @staticmethod
    def get_user_info():
        """Obtém informações do usuário atual"""
        try:
            if current_user and current_user.is_authenticated:
                return {
                    'id': current_user.id,
                    'nome': current_user.nome,
                    'cpf': current_user.cpf,
                    'tipo': current_user.tipo.value if current_user.tipo else None
                }
        except:
            pass
        return None
    
    @staticmethod
    def serialize_object(obj):
        """Serializa um objeto SQLAlchemy para dicionário"""
        if obj is None:
            return None
            
        result = {}
        mapper = sqlalchemy_inspect(obj.__class__)
        
        for column in mapper.columns:
            value = getattr(obj, column.key)
            
            # Converte tipos especiais para JSON serializável
            if isinstance(value, datetime):
                result[column.key] = value.isoformat()
            elif hasattr(value, 'value'):  # Enums
                result[column.key] = value.value
            elif isinstance(value, (int, float, str, bool)) or value is None:
                result[column.key] = value
            else:
                result[column.key] = str(value)
                
        return result
    
    @staticmethod
    def get_changes(old_state, new_state):
        """Compara dois estados e retorna apenas os campos alterados"""
        if not old_state or not new_state:
            return new_state or old_state
            
        changes = {}
        all_keys = set(old_state.keys()) | set(new_state.keys())
        
        for key in all_keys:
            old_value = old_state.get(key)
            new_value = new_state.get(key)
            
            if old_value != new_value:
                changes[key] = {
                    'anterior': old_value,
                    'atual': new_value
                }
                
        return changes
    
    @classmethod
    def log_action(cls, acao, entidade, entidade_id=None, estado_anterior=None, 
                   estado_atual=None, mensagem=None, detalhes_extras=None):
        """
        Registra uma ação no sistema de auditoria
        
        Args:
            acao (str): Tipo da ação (criar, atualizar, deletar, etc.)
            entidade (str): Nome da entidade/tabela afetada
            entidade_id (int): ID da entidade
            estado_anterior (dict): Estado anterior do objeto
            estado_atual (dict): Estado atual do objeto
            mensagem (str): Mensagem descritiva
            detalhes_extras (dict): Detalhes adicionais
        """
        try:
            # Prepara os detalhes do log
            detalhes = {
                'timestamp': datetime.now().isoformat(),
                'usuario': cls.get_user_info(),
                'ip': cls.get_client_ip(),
                'user_agent': request.headers.get('User-Agent', '') if request else '',
                'url': request.url if request else '',
                'metodo_http': request.method if request else '',
            }
            
            # Adiciona estados se fornecidos
            if estado_anterior or estado_atual:
                if acao == 'atualizar' and estado_anterior and estado_atual:
                    detalhes['alteracoes'] = cls.get_changes(estado_anterior, estado_atual)
                    detalhes['estado_anterior'] = estado_anterior
                    detalhes['estado_atual'] = estado_atual
                elif acao == 'criar' and estado_atual:
                    detalhes['estado_criado'] = estado_atual
                elif acao == 'deletar' and estado_anterior:
                    detalhes['estado_deletado'] = estado_anterior
                    
            # Adiciona detalhes extras
            if detalhes_extras:
                detalhes['extras'] = detalhes_extras
            
            # Gera mensagem automática se não fornecida
            if not mensagem:
                user_info = detalhes.get('usuario', {})
                usuario_nome = user_info.get('nome', 'Sistema') if user_info else 'Sistema'
                
                if acao == 'criar':
                    mensagem = f"{usuario_nome} criou {entidade}"
                elif acao == 'atualizar':
                    if 'alteracoes' in detalhes and detalhes['alteracoes']:
                        campos_alterados = list(detalhes['alteracoes'].keys())
                        mensagem = f"{usuario_nome} atualizou {entidade} - Campos: {', '.join(campos_alterados)}"
                    else:
                        mensagem = f"{usuario_nome} atualizou {entidade}"
                elif acao == 'deletar':
                    mensagem = f"{usuario_nome} deletou {entidade}"
                else:
                    mensagem = f"{usuario_nome} executou '{acao}' em {entidade}"
                    
                if entidade_id:
                    mensagem += f" (ID: {entidade_id})"
            
            # Cria o log
            log_entry = Log(
                nivel='INFO',
                modulo=entidade,
                mensagem=mensagem,
                acao=acao,
                entidade=entidade,
                entidade_id=entidade_id,
                usuario_id=detalhes.get('usuario', {}).get('id') if detalhes.get('usuario') else None,
                detalhes=json.dumps(detalhes, ensure_ascii=False, indent=2),
                ip=detalhes['ip'],
                criado_em=datetime.now()
            )
            
            db.session.add(log_entry)
            # Não faz commit aqui - deixa para a transação principal
            
        except Exception as e:
            print(f"Erro ao registrar log de auditoria: {e}")


def audit_changes(entidade_nome):
    """
    Decorator para auditar automaticamente mudanças em métodos
    
    Args:
        entidade_nome (str): Nome da entidade para o log
    
    Usage:
        @audit_changes('Usuario')
        def criar_usuario(dados):
            # código aqui
            return usuario_criado
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Captura informações antes da execução
            frame = inspect.currentframe()
            caller_frame = frame.f_back
            
            # Tenta inferir a ação baseada no nome da função
            func_name = func.__name__.lower()
            if 'criar' in func_name or 'create' in func_name:
                acao = 'criar'
            elif 'atualizar' in func_name or 'update' in func_name or 'editar' in func_name:
                acao = 'atualizar'
            elif 'deletar' in func_name or 'delete' in func_name or 'remover' in func_name:
                acao = 'deletar'
            else:
                acao = func_name
            
            try:
                # Executa a função original
                result = func(*args, **kwargs)
                
                # Registra o sucesso
                if hasattr(result, 'id'):
                    entidade_id = result.id
                    estado_atual = AuditLogger.serialize_object(result)
                else:
                    entidade_id = None
                    estado_atual = None
                
                AuditLogger.log_action(
                    acao=acao,
                    entidade=entidade_nome,
                    entidade_id=entidade_id,
                    estado_atual=estado_atual,
                    mensagem=f"Operação '{acao}' executada com sucesso em {entidade_nome}",
                    detalhes_extras={'funcao': func.__name__, 'modulo': func.__module__}
                )
                
                return result
                
            except Exception as e:
                # Registra o erro
                AuditLogger.log_action(
                    acao=f"{acao}_erro",
                    entidade=entidade_nome,
                    mensagem=f"Erro ao executar '{acao}' em {entidade_nome}: {str(e)}",
                    detalhes_extras={
                        'funcao': func.__name__,
                        'modulo': func.__module__,
                        'erro': str(e),
                        'args': str(args) if args else None,
                        'kwargs': str(kwargs) if kwargs else None
                    }
                )
                raise
                
        return wrapper
    return decorator


# Event Listeners para SQLAlchemy
def setup_sqlalchemy_audit():
    """Configura listeners automáticos para auditoria no SQLAlchemy"""
    
    @event.listens_for(db.session, 'before_commit')
    def before_commit(session):
        """Captura mudanças antes do commit"""
        
        # Armazena informações sobre as mudanças pendentes
        g.audit_info = {
            'new': [],
            'dirty': [],
            'deleted': []
        }
        
        # Objetos novos
        for obj in session.new:
            if hasattr(obj, '__tablename__'):
                g.audit_info['new'].append({
                    'object': obj,
                    'table': obj.__tablename__,
                    'state': AuditLogger.serialize_object(obj)
                })
        
        # Objetos modificados
        for obj in session.dirty:
            if hasattr(obj, '__tablename__'):
                # Captura estado atual
                current_state = AuditLogger.serialize_object(obj)
                
                # Tenta capturar estado anterior dos atributos modificados
                history_data = {}
                mapper = sqlalchemy_inspect(obj.__class__)
                for attr in mapper.attrs:
                    hist = getattr(sqlalchemy_inspect(obj).attrs, attr.key).history
                    if hist.has_changes():
                        if hist.deleted:
                            history_data[attr.key] = hist.deleted[0]
                
                g.audit_info['dirty'].append({
                    'object': obj,
                    'table': obj.__tablename__,
                    'current_state': current_state,
                    'history': history_data
                })
        
        # Objetos deletados
        for obj in session.deleted:
            if hasattr(obj, '__tablename__'):
                g.audit_info['deleted'].append({
                    'object': obj,
                    'table': obj.__tablename__,
                    'state': AuditLogger.serialize_object(obj)
                })
    
    @event.listens_for(db.session, 'after_commit')
    def after_commit(session):
        """Registra logs após commit bem-sucedido"""
        
        if not hasattr(g, 'audit_info'):
            return
        
        try:
            # Objetos criados
            for info in g.audit_info['new']:
                AuditLogger.log_action(
                    acao='criar',
                    entidade=info['table'],
                    entidade_id=getattr(info['object'], 'id', None),
                    estado_atual=info['state']
                )
            
            # Objetos atualizados
            for info in g.audit_info['dirty']:
                obj = info['object']
                current_state = info['current_state']
                history = info['history']
                
                # Reconstrói estado anterior
                previous_state = current_state.copy()
                for field, old_value in history.items():
                    if hasattr(old_value, 'value'):  # Enum
                        previous_state[field] = old_value.value
                    elif isinstance(old_value, datetime):
                        previous_state[field] = old_value.isoformat()
                    else:
                        previous_state[field] = old_value
                
                AuditLogger.log_action(
                    acao='atualizar',
                    entidade=info['table'],
                    entidade_id=getattr(obj, 'id', None),
                    estado_anterior=previous_state,
                    estado_atual=current_state
                )
            
            # Objetos deletados
            for info in g.audit_info['deleted']:
                AuditLogger.log_action(
                    acao='deletar',
                    entidade=info['table'],
                    entidade_id=getattr(info['object'], 'id', None),
                    estado_anterior=info['state']
                )
                
        except Exception as e:
            print(f"Erro ao processar audit após commit: {e}")
        finally:
            # Limpa informações temporárias
            if hasattr(g, 'audit_info'):
                delattr(g, 'audit_info')


# Funções utilitárias para logs específicos
class BusinessAuditLogger:
    """Logs específicos para regras de negócio"""
    
    @staticmethod
    def log_venda(nota_fiscal, itens, pagamentos=None):
        """Log específico para vendas"""
        detalhes = {
            'nota_fiscal': AuditLogger.serialize_object(nota_fiscal),
            'itens': [AuditLogger.serialize_object(item) for item in itens],
            'total_itens': len(itens),
            'valor_total': float(nota_fiscal.valor_total),
            'cliente_id': nota_fiscal.cliente_id,
            'operador_id': nota_fiscal.operador_id,
            'caixa_id': nota_fiscal.caixa_id
        }
        
        if pagamentos:
            detalhes['pagamentos'] = [AuditLogger.serialize_object(p) for p in pagamentos]
        
        AuditLogger.log_action(
            acao='venda',
            entidade='NotaFiscal',
            entidade_id=nota_fiscal.id,
            estado_atual=detalhes,
            mensagem=f"Venda realizada - NF #{nota_fiscal.id} - Valor: R$ {nota_fiscal.valor_total}"
        )
    
    @staticmethod
    def log_movimentacao_estoque(movimentacao, produto_anterior=None, produto_atual=None):
        """Log específico para movimentações de estoque"""
        detalhes = {
            'movimentacao': AuditLogger.serialize_object(movimentacao),
            'tipo': movimentacao.tipo.value,
            'quantidade': float(movimentacao.quantidade),
            'produto_id': movimentacao.produto_id
        }
        
        if produto_anterior and produto_atual:
            # Calcula mudanças nos estoques
            estoques_antes = {
                'loja': float(produto_anterior.estoque_loja),
                'deposito': float(produto_anterior.estoque_deposito),
                'fabrica': float(produto_anterior.estoque_fabrica)
            }
            
            estoques_depois = {
                'loja': float(produto_atual.estoque_loja),
                'deposito': float(produto_atual.estoque_deposito),
                'fabrica': float(produto_atual.estoque_fabrica)
            }
            
            detalhes['estoque_anterior'] = estoques_antes
            detalhes['estoque_atual'] = estoques_depois
        
        AuditLogger.log_action(
            acao='movimentacao_estoque',
            entidade='MovimentacaoEstoque',
            entidade_id=movimentacao.id,
            estado_atual=detalhes,
            mensagem=f"Movimentação de estoque - {movimentacao.tipo.value} - {movimentacao.quantidade} {movimentacao.produto.unidade.value if movimentacao.produto else ''}"
        )
    
    @staticmethod
    def log_caixa_operacao(caixa, operacao, valor=None, observacoes=None):
        """Log específico para operações de caixa"""
        detalhes = {
            'caixa': AuditLogger.serialize_object(caixa),
            'operacao': operacao,
            'status_anterior': caixa.status.value if hasattr(caixa.status, 'value') else str(caixa.status)
        }
        
        if valor:
            detalhes['valor'] = float(valor)
        if observacoes:
            detalhes['observacoes'] = observacoes
        
        mensagem = f"Caixa #{caixa.id} - {operacao}"
        if valor:
            mensagem += f" - Valor: R$ {valor}"
        
        AuditLogger.log_action(
            acao=f'caixa_{operacao}',
            entidade='Caixa',
            entidade_id=caixa.id,
            estado_atual=detalhes,
            mensagem=mensagem
        )

# Exemplo de uso em uma view
# def exemplo_uso_em_view():
#     """Exemplo de como usar o sistema de auditoria em uma view"""
    
#     @audit_changes('Produto')
#     def criar_produto(dados):
#         produto = Produto(**dados)
#         db.session.add(produto)
#         db.session.commit()
#         return produto
    
    # O decorator automaticamente criará um log detalhado
    # produto = criar_produto({'nome': 'Produto Teste', 'valor_unitario': 10.50})
    
    # Para logs manuais mais específicos:
    # BusinessAuditLogger.log_venda(nota_fiscal, itens, pagamentos)