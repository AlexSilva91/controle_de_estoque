from datetime import datetime
from flask import Blueprint, request, jsonify
from app.models import db
from app.decorators.decorators import admin_required
from app.models.fiscal_models import ClienteFiscal, ConfiguracaoFiscal, NotaFiscalEvento
from app.services.cliente_fiscal_crud import ClienteFiscalCRUD
from app.services.fiscal_crud import (
    ConfiguracaoFiscalCRUD,
    ProdutoFiscalCRUD,
    TransportadoraCRUD,
    VeiculoTransporteCRUD,
    NotaFiscalHistoricoCRUD,
    NotaFiscalEventoCRUD,
    NotaFiscalVolumeCRUD,
    FiscalManager
)
from app.models.entities import Produto
from app.utils.fiscal.helpers import NFeHelpers


fiscal_bp = Blueprint('fiscal', __name__, url_prefix='/admin/fiscal')

# ============================================
# 1. ROTAS CONFIGURAÇÃO FISCAL
# ============================================
@fiscal_bp.route('/configuracoes', methods=['POST'])
@admin_required
def criar_configuracao_fiscal():
    """Cria uma nova configuração fiscal"""
    try:
        dados = request.get_json()
        print(f'Dados recebidos para criar configuração fiscal: {dados}')
        
        if not dados:
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400
        
        campos_obrigatorios = ['razao_social', 'cnpj', 'logradouro', 'numero', 'bairro', 'municipio', 'uf', 'cep']
        for campo in campos_obrigatorios:
            if campo not in dados or not dados[campo]:
                return jsonify({"success": False, "message": f"Campo obrigatório faltando: {campo}"}), 400
        
        config = ConfiguracaoFiscalCRUD.criar(db.session, dados)
        
        return jsonify({
            "success": True,
            "message": "Configuração fiscal criada com sucesso",
            "data": {
                "id": config.id,
                "razao_social": config.razao_social,
                "cnpj": config.cnpj
            }
        }), 201
        
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        import traceback
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/configuracoes', methods=['GET'])
@admin_required
def listar_configuracoes_fiscais():
    """Lista todas as configurações fiscais"""
    try:
        skip = request.args.get('skip', 0, type=int)
        limit = request.args.get('limit', 100, type=int)
     
        configs = ConfiguracaoFiscalCRUD.listar_todas(db.session, skip, limit)
        
        return jsonify({
            "success": True,
            "data": [{
                "id": c.id,
                "razao_social": c.razao_social,
                "cnpj": c.cnpj,
                "ativo": c.ativo,
                "ambiente": c.ambiente
            } for c in configs]
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/configuracoes/ativa', methods=['GET'])
@admin_required
def obter_configuracao_ativa():
    """Obtém a configuração fiscal ativa"""
    try:
        config = ConfiguracaoFiscalCRUD.obter_ativa(db)
        
        if not config:
            return jsonify({"success": False, "message": "Nenhuma configuração ativa encontrada"}), 404
        
        return jsonify({
            "success": True,
            "data": {
                "id": config.id,
                "razao_social": config.razao_social,
                "cnpj": config.cnpj,
                "ambiente": config.ambiente,
                "ultimo_numero_nfe": config.ultimo_numero_nfe,
                "ultimo_numero_nfce": config.ultimo_numero_nfce
            }
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/configuracoes/<int:id>', methods=['GET'])
@admin_required
def obter_configuracao_por_id(id):
    """Obtém configuração fiscal por ID"""
    try:
        config = ConfiguracaoFiscalCRUD.obter_por_id(db.session, id)
        
        if not config:
            return jsonify({"success": False, "message": "Configuração não encontrada"}), 404
        
        config_dict = {
            "id": config.id,
            "razao_social": config.razao_social,
            "nome_fantasia": config.nome_fantasia,
            "cnpj": config.cnpj,
            "inscricao_estadual": config.inscricao_estadual,
            "inscricao_municipal": config.inscricao_municipal,
            "cnae_principal": config.cnae_principal,
            "regime_tributario": config.regime_tributario,
            "logradouro": config.logradouro,
            "numero": config.numero,
            "complemento": config.complemento,
            "bairro": config.bairro,
            "codigo_municipio": config.codigo_municipio,
            "municipio": config.municipio,
            "uf": config.uf,
            "cep": config.cep,
            "telefone": config.telefone,
            "email": config.email,
            "serie_nfe": config.serie_nfe,
            "serie_nfce": config.serie_nfce,
            "ambiente": config.ambiente,
            "ultimo_numero_nfe": config.ultimo_numero_nfe,
            "ultimo_numero_nfce": config.ultimo_numero_nfce,
            "ativo": config.ativo,
            "criado_em": config.criado_em.isoformat() if config.criado_em else None,
            "atualizado_em": config.atualizado_em.isoformat() if config.atualizado_em else None
        }
        
        config_dict_formatado = NFeHelpers.formatar_dados_para_frontend(config_dict, tipo='configuracao')
        
        return jsonify({
            "success": True,
            "data": config_dict_formatado
        }), 200
        
    except Exception as e:
        import traceback
        print(f"Erro detalhado: {traceback.format_exc()}")
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/configuracoes/<int:id>', methods=['PUT'])
@admin_required
def atualizar_configuracao(id):
    """Atualiza configuração fiscal"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400
        
        config = ConfiguracaoFiscalCRUD.atualizar(db.session, id, dados)
        
        if not config:
            return jsonify({"success": False, "message": "Configuração não encontrada"}), 404
        
        return jsonify({
            "success": True,
            "message": "Configuração atualizada com sucesso",
            "data": {
                "id": config.id,
                "razao_social": config.razao_social
            }
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500


@fiscal_bp.route('/configuracoes/<int:id>', methods=['DELETE'])
@admin_required
def excluir_configuracao(id):
    """Desativa (soft delete) uma configuração fiscal"""
    try:
        sucesso = ConfiguracaoFiscalCRUD.excluir(db.session, id)
        
        if not sucesso:
            return jsonify({"success": False, "message": "Configuração não encontrada"}), 404
        
        return jsonify({
            "success": True,
            "message": "Configuração fiscal desativada com sucesso"
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500


@fiscal_bp.route('/configuracoes/<int:id>/reativar', methods=['POST'])
@admin_required
def reativar_configuracao(id):
    """Reativa uma configuração fiscal desativada"""
    try:
        config = ConfiguracaoFiscalCRUD.reativar(db.session, id)
        
        if not config:
            return jsonify({"success": False, "message": "Configuração não encontrada"}), 404
        
        return jsonify({
            "success": True,
            "message": "Configuração fiscal reativada com sucesso",
            "data": {
                "id": config.id,
                "razao_social": config.razao_social,
                "ativo": config.ativo
            }
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500


@fiscal_bp.route('/configuracoes/<int:id>/incrementar-nfe', methods=['POST'])
@admin_required
def incrementar_numero_nfe(id):
    """Incrementa número da NFe"""
    try:
        numero = ConfiguracaoFiscalCRUD.incrementar_numero_nfe(db.session, id)
        
        return jsonify({
            "success": True,
            "message": "Número incrementado com sucesso",
            "data": {"proximo_numero": numero}
        }), 200
        
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/configuracoes/<int:id>/incrementar-nfce', methods=['POST'])
@admin_required
def incrementar_numero_nfce(id):
    """Incrementa número da NFCe"""
    try:
        numero = ConfiguracaoFiscalCRUD.incrementar_numero_nfce(db.session, id)
        
        return jsonify({
            "success": True,
            "message": "Número incrementado com sucesso",
            "data": {"proximo_numero": numero}
        }), 200
        
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

# ============================================
# 2. ROTAS PRODUTO FISCAL
# ============================================

@fiscal_bp.route('/produtos-fiscais', methods=['POST'])
@admin_required
def criar_produto_fiscal():
    """Cria dados fiscais para um produto com múltiplos produtos associados"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400
        
        # Verifica se há produtos para associar
        produto_ids = dados.get('produto_ids', [])
        if not produto_ids:
            return jsonify({"success": False, "message": "Lista de IDs de produtos é obrigatória"}), 400
        
        # Cria o produto fiscal com os produtos associados
        produto_fiscal = ProdutoFiscalCRUD.criar_produto_fiscal(db.session, dados, produto_ids)
        
        return jsonify({
            "success": True,
            "message": "Produto fiscal criado com sucesso",
            "data": {
                "id": produto_fiscal.id,
                "codigo_ncm": produto_fiscal.codigo_ncm,
                "produtos_associados": produto_ids
            }
        }), 201
        
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/produtos-fiscais', methods=['GET'])
@admin_required
def listar_produtos_fiscais():
    """Lista todos os produtos fiscais com seus produtos associados"""
    try:
        skip = request.args.get('skip', 0, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        produtos_fiscais = ProdutoFiscalCRUD.listar_todos(db.session, skip, limit)
        
        resultado = []
        for pf in produtos_fiscais:
            # Obtém os produtos associados
            produtos_associados_ids = ProdutoFiscalCRUD.obter_produtos_associados(db.session, pf.id)
            
            # Busca nomes dos produtos
            nomes_produtos = {}
            if produtos_associados_ids:
                produtos = db.session.query(Produto.id, Produto.nome)\
                                    .filter(Produto.id.in_(produtos_associados_ids))\
                                    .all()
                nomes_produtos = {p.id: p.nome or f"Produto {p.id}" for p in produtos}
            
            resultado.append({
                "id": pf.id,
                "codigo_ncm": pf.codigo_ncm,
                "codigo_cest": pf.codigo_cest,
                "origem": pf.origem,
                "tipo_item": pf.tipo_item,
                "cst_icms": pf.cst_icms,
                "cfop": pf.cfop,
                "aliquota_icms": float(pf.aliquota_icms) if pf.aliquota_icms else None,
                "cst_pis": pf.cst_pis,
                "aliquota_pis": float(pf.aliquota_pis) if pf.aliquota_pis else None,
                "cst_cofins": pf.cst_cofins,
                "aliquota_cofins": float(pf.aliquota_cofins) if pf.aliquota_cofins else None,
                "status": pf.status,
                "homologado": pf.homologado,
                "data_homologacao": pf.data_homologacao.isoformat() if pf.data_homologacao else None,
                "criado_em": pf.criado_em.isoformat() if pf.criado_em else None,
                "atualizado_em": pf.atualizado_em.isoformat() if pf.atualizado_em else None,
                "quantidade_produtos_associados": len(produtos_associados_ids),
                "produtos_associados_ids": produtos_associados_ids,
                "produtos_associados_nomes": nomes_produtos  # Adicionado aqui
            })
        
        return jsonify({
            "success": True,
            "data": resultado
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500
    
@fiscal_bp.route('/produtos-fiscais/<int:id>', methods=['GET'])
@admin_required
def obter_produto_fiscal_por_id(id):
    """Obtém dados fiscais do produto por ID com todos os campos e produtos associados"""
    try:
        produto_fiscal = ProdutoFiscalCRUD.obter_por_id(db.session, id)
        if not produto_fiscal:
            return jsonify({"success": False, "message": "Dados fiscais não encontrados"}), 404
        
        # Obtém os produtos associados
        produtos_associados_ids = ProdutoFiscalCRUD.obter_produtos_associados(db.session, id)
        
        return jsonify({
            "success": True,
            "data": {
                "id": produto_fiscal.id,
                "codigo_ncm": produto_fiscal.codigo_ncm,
                "codigo_cest": produto_fiscal.codigo_cest,
                "codigo_ean": produto_fiscal.codigo_ean,
                "codigo_gtin_trib": produto_fiscal.codigo_gtin_trib,
                "unidade_tributaria": produto_fiscal.unidade_tributaria,
                "valor_unitario_trib": float(produto_fiscal.valor_unitario_trib) if produto_fiscal.valor_unitario_trib else None,
                "origem": produto_fiscal.origem,
                "tipo_item": produto_fiscal.tipo_item,
                "cst_icms": produto_fiscal.cst_icms,
                "cfop": produto_fiscal.cfop,
                "aliquota_icms": float(produto_fiscal.aliquota_icms) if produto_fiscal.aliquota_icms else None,
                "cst_pis": produto_fiscal.cst_pis,
                "aliquota_pis": float(produto_fiscal.aliquota_pis) if produto_fiscal.aliquota_pis else None,
                "cst_cofins": produto_fiscal.cst_cofins,
                "aliquota_cofins": float(produto_fiscal.aliquota_cofins) if produto_fiscal.aliquota_cofins else None,
                "informacoes_fisco": produto_fiscal.informacoes_fisco,
                "informacoes_complementares": produto_fiscal.informacoes_complementares,
                "homologado": produto_fiscal.homologado,
                "status": produto_fiscal.status,
                "data_homologacao": produto_fiscal.data_homologacao.isoformat() if produto_fiscal.data_homologacao else None,
                "justificativa_homologacao": produto_fiscal.justificativa_homologacao,
                "criado_em": produto_fiscal.criado_em.isoformat() if produto_fiscal.criado_em else None,
                "atualizado_em": produto_fiscal.atualizado_em.isoformat() if produto_fiscal.atualizado_em else None,
                "sincronizado": produto_fiscal.sincronizado,
                "produtos_associados_ids": produtos_associados_ids
            }
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/produtos', methods=['GET'])
@admin_required
def listar_produtos_sistema():
    """Lista produtos do sistema principal"""
    try:
        incluir_inativos = request.args.get('incluir_inativos', 'false').lower() == 'true'
        
        query = db.session.query(Produto)
        if not incluir_inativos:
            query = query.filter(Produto.ativo == True)
        
        produtos = query.order_by(Produto.nome.asc()).all()
        
        produtos_data = []
        for p in produtos:
            # Obtém produtos fiscais associados
            produtos_fiscais = ProdutoFiscalCRUD.obter_produtos_fiscais_por_produto(db.session, p.id)
            
            produto_data = {
                "id": p.id,
                "codigo": p.codigo or "",
                "nome": p.nome or "",
                "tipo": p.tipo or "",
                "marca": p.marca or "",
                "unidade": p.unidade.value if hasattr(p.unidade, 'value') else str(p.unidade) if p.unidade else None,
                "valor_unitario": float(p.valor_unitario) if p.valor_unitario else None,
                "valor_unitario_compra": float(p.valor_unitario_compra) if p.valor_unitario_compra else None,
                "foto": p.foto or "",
                "estoque_loja": float(p.estoque_loja) if p.estoque_loja else 0,
                "estoque_deposito": float(p.estoque_deposito) if p.estoque_deposito else 0,
                "estoque_fabrica": float(p.estoque_fabrica) if p.estoque_fabrica else 0,
                "ativo": p.ativo if hasattr(p, 'ativo') else True,
                "tem_produtos_fiscais": len(produtos_fiscais) > 0,
                "quantidade_produtos_fiscais": len(produtos_fiscais),
                "produtos_fiscais_ids": [pf.id for pf in produtos_fiscais]
            }
            produtos_data.append(produto_data)
        
        return jsonify({
            "success": True,
            "data": produtos_data
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False, 
            "message": f"Erro interno: {str(e)}"
        }), 500
    
@fiscal_bp.route('/produtos-fiscais/produto/<int:produto_id>', methods=['GET'])
@admin_required
def obter_produto_fiscal_por_produto(produto_id):
    """Obtém produtos fiscais por ID do produto"""
    try:
        # Obtém todos os produtos fiscais associados ao produto
        produtos_fiscais = ProdutoFiscalCRUD.obter_produtos_fiscais_por_produto(db.session, produto_id)
        
        if not produtos_fiscais:
            return jsonify({"success": False, "message": "Nenhum produto fiscal encontrado"}), 404
        
        resultado = []
        for pf in produtos_fiscais:
            resultado.append({
                "id": pf.id,
                "codigo_ncm": pf.codigo_ncm,
                "codigo_cest": pf.codigo_cest,
                "origem": pf.origem,
                "tipo_item": pf.tipo_item,
                "cst_icms": pf.cst_icms,
                "cfop": pf.cfop,
                "aliquota_icms": float(pf.aliquota_icms) if pf.aliquota_icms else None,
                "homologado": pf.homologado,
                "status":pf.status,
                "data_homologacao": pf.data_homologacao.isoformat() if pf.data_homologacao else None
            })
        
        return jsonify({
            "success": True,
            "produto_id": produto_id,
            "quantidade_produtos_fiscais": len(produtos_fiscais),
            "data": resultado
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/produtos-fiscais/<int:id>', methods=['PUT'])
@admin_required
def atualizar_produto_fiscal(id):
    """Atualiza dados fiscais do produto e seus produtos associados"""
    try:
        dados = request.get_json()
        print(dados)
        if not dados:
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400
        
        # Se houver produto_ids, atualiza os produtos associados
        produto_ids = dados.get('produto_ids')
        
        # Remove produto_ids dos dados para não tentar atualizar no produto fiscal
        dados_fiscais = {k: v for k, v in dados.items() if k != 'produto_ids'}
        
        # Atualiza o produto fiscal e produtos associados
        produto_fiscal = ProdutoFiscalCRUD.atualizar_produto_fiscal(db.session, id, dados_fiscais, produto_ids)
        
        if not produto_fiscal:
            return jsonify({"success": False, "message": "Dados fiscais não encontrados"}), 404
        
        # Obtém os produtos associados atualizados
        produtos_associados = ProdutoFiscalCRUD.obter_produtos_associados(db.session, id)
        
        return jsonify({
            "success": True,
            "message": "Produto fiscal atualizado com sucesso",
            "data": {
                "id": produto_fiscal.id,
                "codigo_ncm": produto_fiscal.codigo_ncm,
                "produtos_associados_ids": produtos_associados
            }
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/produtos-fiscais/<int:id>/homologar', methods=['POST'])
@admin_required
def homologar_produto_fiscal(id):
    """Homologa dados fiscais do produto"""
    try:
        dados = request.get_json()
        justificativa = dados.get('justificativa') if dados else None
        
        produto_fiscal = ProdutoFiscalCRUD.homologar(db.session, id, justificativa)
        
        if not produto_fiscal:
            return jsonify({"success": False, "message": "Dados fiscais não encontrados"}), 404
        
        return jsonify({
            "success": True,
            "message": "Produto homologado com sucesso",
            "data": {
                "id": produto_fiscal.id,
                "homologado": produto_fiscal.homologado,
                "data_homologacao": produto_fiscal.data_homologacao
            }
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/produtos-fiscais/homologados', methods=['GET'])
@admin_required
def listar_produtos_fiscais_homologados():
    """Lista produtos fiscais homologados"""
    try:
        skip = request.args.get('skip', 0, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        produtos = ProdutoFiscalCRUD.listar_todos(db.session, skip, limit)
        produtos_homologados = [p for p in produtos if p.homologado]
        
        resultado = []
        for p in produtos_homologados:
            produtos_associados = ProdutoFiscalCRUD.obter_produtos_associados(db.session, p.id)
            resultado.append({
                "id": p.id,
                "codigo_ncm": p.codigo_ncm,
                "cst_icms": p.cst_icms,
                "data_homologacao": p.data_homologacao.isoformat() if p.data_homologacao else None,
                "quantidade_produtos_associados": len(produtos_associados)
            })
        
        return jsonify({
            "success": True,
            "data": resultado
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/produtos-fiscais/listar-nao-homologados', methods=['GET'])
@admin_required
def listar_produtos_nao_homologados():
    """Lista produtos fiscais não homologados"""
    try:
        skip = request.args.get('skip', 0, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        produtos = ProdutoFiscalCRUD.listar_todos(db.session, skip, limit)
        produtos_nao_homologados = [p for p in produtos if not p.homologado]
        
        resultado = []
        for p in produtos_nao_homologados:
            produtos_associados = ProdutoFiscalCRUD.obter_produtos_associados(db.session, p.id)
            
            # Busca nomes dos produtos associados
            produtos_com_nomes = []
            if produtos_associados:
                produtos_info = db.session.query(Produto.id, Produto.nome)\
                                         .filter(Produto.id.in_(produtos_associados))\
                                         .all()
                produtos_com_nomes = [
                    {"id": prod.id, "nome": prod.nome or f"Produto {prod.id}"}
                    for prod in produtos_info
                ]
            
            resultado.append({
                "id": p.id,
                "codigo_ncm": p.codigo_ncm,
                "codigo_cest": p.codigo_cest,
                "origem": p.origem,
                "cfop": p.cfop,
                "cst_icms": p.cst_icms,
                "homologado": p.homologado,
                "quantidade_produtos_associados": len(produtos_associados),
                "produtos_associados": produtos_com_nomes  # Agora com nomes
            })
        
        return jsonify({
            "success": True,
            "data": resultado
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/produtos-fiscais/ncm/<string:ncm>', methods=['GET'])
@admin_required
def buscar_produtos_por_ncm(ncm):
    """Busca produtos fiscais por NCM"""
    try:
        # Filtra por NCM
        filtros = {'ncm': ncm}
        produtos_fiscais = ProdutoFiscalCRUD.buscar_por_filtros(db.session, filtros)
        
        resultado = []
        for p in produtos_fiscais:
            produtos_associados = ProdutoFiscalCRUD.obter_produtos_associados(db.session, p.id)
            resultado.append({
                "id": p.id,
                "codigo_ncm": p.codigo_ncm,
                "codigo_cest": p.codigo_cest,
                "origem": p.origem,
                "cst_icms": p.cst_icms,
                "homologado": p.homologado,
                "quantidade_produtos_associados": len(produtos_associados)
            })
        
        return jsonify({
            "success": True,
            "data": resultado
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500
    
@fiscal_bp.route('/produtos-fiscais/<int:id>', methods=['DELETE'])
@admin_required
def desativar_produto_fiscal(id):
    """Exclui dados fiscais do produto e suas associações"""
    try:
        sucesso = ProdutoFiscalCRUD.desativar_produto_fiscal(db.session, id)
        
        if not sucesso:
            return jsonify({"success": False, "message": "Dados fiscais não encontrados"}), 404
        
        return jsonify({
            "success": True,
            "message": "Produto fiscal excluído com sucesso"
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/produtos-fiscais/<int:id>/produtos', methods=['GET'])
@admin_required
def listar_produtos_do_produto_fiscal(id):
    """Lista todos os produtos associados a um produto fiscal específico"""
    try:
        # Obtém os IDs dos produtos associados
        produtos_associados_ids = ProdutoFiscalCRUD.obter_produtos_associados(db.session, id)
        
        if not produtos_associados_ids:
            return jsonify({
                "success": True,
                "produto_fiscal_id": id,
                "data": []
            }), 200
        
        # Converter para lista de inteiros
        produtos_ids = []
        for produto_id in produtos_associados_ids:
            try:
                produtos_ids.append(int(produto_id))
            except (ValueError, TypeError):
                continue  # Ignora valores inválidos
        
        # Buscar apenas os IDs e nomes dos produtos
        produtos = db.session.query(Produto.id, Produto.nome, Produto.codigo)\
                            .filter(Produto.id.in_(produtos_ids))\
                            .all()
        
        # Formatar dados
        produtos_data = []
        for p in produtos:
            produto_data = {
                "id": p.id,
                "nome": p.nome or "",
                "codigo": p.codigo or ""
            }
            produtos_data.append(produto_data)
        
        # Garantir que retorna todos os IDs, mesmo que algum produto não exista mais
        ids_encontrados = [p["id"] for p in produtos_data]
        for produto_id in produtos_ids:
            if produto_id not in ids_encontrados:
                produtos_data.append({
                    "id": produto_id,
                    "nome": "Produto não encontrado",
                    "codigo": ""
                })
        
        return jsonify({
            "success": True,
            "produto_fiscal_id": id,
            "data": produtos_data
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False, 
            "message": f"Erro interno: {str(e)}"
        }), 500

@fiscal_bp.route('/produtos/<int:id>', methods=['GET'])
@admin_required
def obter_produto_por_id(id):
    """Obtém um produto específico pelo ID"""
    try:
        produto = db.session.query(Produto).filter(Produto.id == id).first()
        
        if not produto:
            return jsonify({
                "success": False,
                "message": f"Produto com ID {id} não encontrado"
            }), 404
        
        # Obtém produtos fiscais associados
        produtos_fiscais = ProdutoFiscalCRUD.obter_produtos_fiscais_por_produto(db.session, id)
        
        produto_data = {
            "id": produto.id,
            "codigo": produto.codigo or "",
            "nome": produto.nome or "",
            "tipo": produto.tipo or "",
            "marca": produto.marca or "",
            "unidade": produto.unidade.value if hasattr(produto.unidade, 'value') else str(produto.unidade) if produto.unidade else None,
            "valor_unitario": float(produto.valor_unitario) if produto.valor_unitario else None,
            "valor_unitario_compra": float(produto.valor_unitario_compra) if produto.valor_unitario_compra else None,
            "foto": produto.foto or "",
            "estoque_loja": float(produto.estoque_loja) if produto.estoque_loja else 0,
            "estoque_deposito": float(produto.estoque_deposito) if produto.estoque_deposito else 0,
            "estoque_fabrica": float(produto.estoque_fabrica) if produto.estoque_fabrica else 0,
            "ativo": produto.ativo if hasattr(produto, 'ativo') else True,
            "tem_produtos_fiscais": len(produtos_fiscais) > 0,
            "quantidade_produtos_fiscais": len(produtos_fiscais),
            "produtos_fiscais_ids": [pf.id for pf in produtos_fiscais]
        }
        
        return jsonify({
            "success": True,
            "data": produto_data
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False, 
            "message": f"Erro interno: {str(e)}"
        }), 500

# ============================================
# 3. ROTAS TRANSPORTADORA
# ============================================

@fiscal_bp.route('/transportadoras', methods=['POST'])
@admin_required
def criar_transportadora():
    """Cria uma nova transportadora"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400
        
        if not dados.get('cnpj') and not dados.get('cpf'):
            return jsonify({"success": False, "message": "CNPJ ou CPF é obrigatório"}), 400
        
         
        transportadora = TransportadoraCRUD.criar(db.session, dados)
        
        return jsonify({
            "success": True,
            "message": "Transportadora criada com sucesso",
            "data": {
                "id": transportadora.id,
                "razao_social": transportadora.razao_social,
                "cnpj": transportadora.cnpj,
                "cpf": transportadora.cpf
            }
        }), 201
        
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/transportadoras', methods=['GET'])
@admin_required
def listar_transportadoras():
    """Lista transportadoras ativas"""
    try:
        skip = request.args.get('skip', 0, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        transportadoras = TransportadoraCRUD.listar_ativas(db.session, skip, limit)
        
        return jsonify({
            "success": True,
            "data": [{
                "id": t.id,
                "razao_social": t.razao_social,
                "nome_fantasia": t.nome_fantasia,
                "cnpj": t.cnpj,
                "cpf": t.cpf,
                "municipio": t.municipio,
                "uf": t.uf,
                "ativo": t.ativo, 
                "placa_veiculo": t.placa_veiculo,
                "uf_veiculo": t.uf_veiculo,
                "rntc": t.rntc
            } for t in transportadoras]
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/transportadoras/<int:id>', methods=['GET'])
@admin_required
def obter_transportadora(id):
    """Obtém transportadora por ID"""
    try:
        transportadora = TransportadoraCRUD.obter_por_id(db.session, id)
        
        if not transportadora:
            return jsonify({"success": False, "message": "Transportadora não encontrada"}), 404
        
        transportadora_dict = {
            "id": transportadora.id,
            "razao_social": transportadora.razao_social,
            "nome_fantasia": transportadora.nome_fantasia,
            "cnpj": transportadora.cnpj,
            "cpf": transportadora.cpf,
            "inscricao_estadual": transportadora.inscricao_estadual,
            "logradouro": transportadora.logradouro,
            "numero": transportadora.numero,
            "complemento": transportadora.complemento,
            "bairro": transportadora.bairro,
            "municipio": transportadora.municipio,
            "uf": transportadora.uf,
            "cep": transportadora.cep,
            "telefone": transportadora.telefone,
            "email": transportadora.email,
            "modalidade_frete": transportadora.modalidade_frete,
            "placa_veiculo": transportadora.placa_veiculo,
            "uf_veiculo": transportadora.uf_veiculo,
            "rntc": transportadora.rntc,
            "ativo": transportadora.ativo,
            "criado_em": transportadora.criado_em.isoformat() if transportadora.criado_em else None,
            "atualizado_em": transportadora.atualizado_em.isoformat() if transportadora.atualizado_em else None,
            "sincronizado": transportadora.sincronizado
        }
        
        return jsonify({
            "success": True,
            "data": transportadora_dict
        }), 200
        
    except Exception as e:
        import traceback
        print(f"Erro detalhado: {traceback.format_exc()}")
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/transportadoras/buscar', methods=['GET'])
@admin_required
def buscar_transportadoras():
    """Busca transportadoras por nome"""
    try:
        nome = request.args.get('nome', '')
        if not nome:
            return jsonify({"success": False, "message": "Parâmetro 'nome' é obrigatório"}), 400
        
        skip = request.args.get('skip', 0, type=int)
        limit = request.args.get('limit', 50, type=int)
        
         
        transportadoras = TransportadoraCRUD.buscar_por_nome(db.session, nome, skip, limit)
        
        return jsonify({
            "success": True,
            "data": [{
                "id": t.id,
                "razao_social": t.razao_social,
                "nome_fantasia": t.nome_fantasia,
                "cnpj": t.cnpj,
                "cpf": t.cpf,
                "municipio": t.municipio
            } for t in transportadoras]
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/transportadoras/<int:id>', methods=['PUT'])
@admin_required
def atualizar_transportadora(id):
    """Atualiza transportadora"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400
        
         
        transportadora = TransportadoraCRUD.atualizar(db.session, id, dados)
        
        if not transportadora:
            return jsonify({"success": False, "message": "Transportadora não encontrada"}), 404
        
        return jsonify({
            "success": True,
            "message": "Transportadora atualizada com sucesso",
            "data": {
                "id": transportadora.id,
                "razao_social": transportadora.razao_social
            }
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/transportadoras/<int:id>', methods=['DELETE'])
@admin_required
def excluir_transportadora(id):
    """Desativa (soft delete) uma transportadora"""
    try:
        sucesso = TransportadoraCRUD.excluir(db.session, id)
        
        if not sucesso:
            return jsonify({"success": False, "message": "Transportadora não encontrada"}), 404
        
        return jsonify({
            "success": True,
            "message": "Transportadora desativada com sucesso"
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500


@fiscal_bp.route('/transportadoras/<int:id>/reativar', methods=['POST'])
@admin_required
def reativar_transportadora(id):
    """Reativa uma transportadora desativada"""
    try:
        transportadora = TransportadoraCRUD.obter_por_id(db.session, id)
        if not transportadora:
            return jsonify({"success": False, "message": "Transportadora não encontrada"}), 404
        
        transportadora.ativo = True
        transportadora.atualizado_em = datetime.now()
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Transportadora reativada com sucesso",
            "data": {
                "id": transportadora.id,
                "razao_social": transportadora.razao_social,
                "ativo": transportadora.ativo
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

# ============================================
# 4. ROTAS VEÍCULO DE TRANSPORTE
# ============================================

@fiscal_bp.route('/veiculos', methods=['POST'])
@admin_required
def criar_veiculo():
    """Cria um novo veículo de transporte"""
    try:
        dados = request.get_json()
        print(dados)
        if not dados:
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400
        
        if 'placa' not in dados:
            return jsonify({"success": False, "message": "Placa é obrigatória"}), 400
        
        veiculo = VeiculoTransporteCRUD.criar(db.session, dados)
        
        return jsonify({
            "success": True,
            "message": "Veículo criado com sucesso",
            "data": {
                "id": veiculo.id,
                "placa": veiculo.placa,
                "uf": veiculo.uf,
                "transportadora_id": veiculo.transportadora_id
            }
        }), 201
        
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/veiculos', methods=['GET'])
@admin_required
def listar_veiculos():
    """Lista veículos ativos"""
    try:
        skip = request.args.get('skip', 0, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        veiculos = VeiculoTransporteCRUD.listar_ativos(db.session, skip, limit)
        
        return jsonify({
            "success": True,
            "data": [{
                "id": v.id,
                "placa": v.placa,
                "uf": v.uf,
                "rntc": v.rntc,
                "transportadora_id": v.transportadora_id,
                "transportadora_nome": v.transportadora.razao_social if v.transportadora else None,
                "ativo": v.ativo,
                "proprietario": v.proprietario
            } for v in veiculos]
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/veiculos/<int:id>', methods=['GET'])
@admin_required
def obter_veiculo(id):
    """Obtém veículo por ID"""
    try:
        veiculo = VeiculoTransporteCRUD.obter_por_id(db.session, id)
        
        if not veiculo:
            return jsonify({"success": False, "message": "Veículo não encontrado"}), 404
        
        capacidade_carga = None
        if veiculo.capacidade_carga:
            capacidade_carga = str(veiculo.capacidade_carga)
        
        veiculo_dict = {
            "id": veiculo.id,
            "transportadora_id": veiculo.transportadora_id,
            "transportadora_nome": veiculo.transportadora.razao_social if veiculo.transportadora else None,
            "placa": veiculo.placa,
            "uf": veiculo.uf,
            "rntc": veiculo.rntc,
            "tipo_veiculo": veiculo.tipo_veiculo.capitalize(),
            "capacidade_carga": capacidade_carga,
            "proprietario": veiculo.proprietario,
            "ativo": veiculo.ativo,
            "criado_em": veiculo.criado_em.isoformat() if veiculo.criado_em else None,
            "atualizado_em": veiculo.atualizado_em.isoformat() if veiculo.atualizado_em else None,
            "sincronizado": veiculo.sincronizado
        }
        return jsonify({
            "success": True,
            "data": veiculo_dict
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/veiculos/placa/<string:placa>', methods=['GET'])
@admin_required
def obter_veiculo_por_placa(placa):
    """Obtém veículo por placa"""
    try:
         
        veiculo = VeiculoTransporteCRUD.obter_por_placa(db.session, placa)
        
        if not veiculo:
            return jsonify({"success": False, "message": "Veículo não encontrado"}), 404
        
        return jsonify({
            "success": True,
            "data": veiculo.__dict__
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/veiculos/transportadora/<int:transportadora_id>', methods=['GET'])
@admin_required
def listar_veiculos_por_transportadora(transportadora_id):
    """Lista veículos de uma transportadora"""
    try:
         
        veiculos = VeiculoTransporteCRUD.listar_por_transportadora(db.session, transportadora_id)
        
        return jsonify({
            "success": True,
            "data": [{
                "id": v.id,
                "placa": v.placa,
                "uf": v.uf,
                "rntc": v.rntc
            } for v in veiculos]
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/veiculos/<int:id>', methods=['PUT'])
@admin_required
def atualizar_veiculo(id):
    """Atualiza veículo de transporte"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400
        
         
        veiculo = VeiculoTransporteCRUD.atualizar(db.session, id, dados)
        
        if not veiculo:
            return jsonify({"success": False, "message": "Veículo não encontrado"}), 404
        
        return jsonify({
            "success": True,
            "message": "Veículo atualizado com sucesso",
            "data": {
                "id": veiculo.id,
                "placa": veiculo.placa
            }
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/veiculos/<int:id>', methods=['DELETE'])
@admin_required
def excluir_veiculo(id):
    """Desativa (soft delete) um veículo"""
    try:
        sucesso = VeiculoTransporteCRUD.excluir(db.session, id)
        
        if not sucesso:
            return jsonify({"success": False, "message": "Veículo não encontrado"}), 404
        
        return jsonify({
            "success": True,
            "message": "Veículo desativado com sucesso"
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500


@fiscal_bp.route('/veiculos/<int:id>/reativar', methods=['POST'])
@admin_required
def reativar_veiculo(id):
    """Reativa um veículo desativado"""
    try:
        veiculo = VeiculoTransporteCRUD.reativar(db.session, id)
        
        if not veiculo:
            return jsonify({"success": False, "message": "Veículo não encontrado"}), 404
        
        return jsonify({
            "success": True,
            "message": "Veículo reativado com sucesso",
            "data": {
                "id": veiculo.id,
                "placa": veiculo.placa,
                "ativo": veiculo.ativo
            }
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500
    
# ============================================
# 5. ROTAS HISTÓRICO DA NOTA FISCAL
# ============================================

@fiscal_bp.route('/notas-fiscais/<int:nota_fiscal_id>/historico', methods=['GET'])
@admin_required
def listar_historico_nota(nota_fiscal_id):
    """Lista histórico de uma nota fiscal"""
    try:
        skip = request.args.get('skip', 0, type=int)
        limit = request.args.get('limit', 100, type=int)
        
         
        historicos = NotaFiscalHistoricoCRUD.listar_por_nota(db.session, nota_fiscal_id, skip, limit)
        
        return jsonify({
            "success": True,
            "data": [{
                "id": h.id,
                "tipo_alteracao": h.tipo_alteracao,
                "descricao": h.descricao,
                "data_alteracao": h.data_alteracao,
                "sucesso": h.sucesso,
                "usuario_id": h.usuario_id
            } for h in historicos]
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/historico/registrar', methods=['POST'])
@admin_required
def registrar_historico():
    """Registra um novo histórico"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400
        
        required_fields = ['nota_fiscal_id', 'usuario_id', 'tipo_alteracao', 'descricao']
        for field in required_fields:
            if field not in dados:
                return jsonify({"success": False, "message": f"Campo {field} é obrigatório"}), 400
        
         
        historico = NotaFiscalHistoricoCRUD.criar(db.session, dados)
        
        return jsonify({
            "success": True,
            "message": "Histórico registrado com sucesso",
            "data": {
                "id": historico.id,
                "nota_fiscal_id": historico.nota_fiscal_id,
                "tipo_alteracao": historico.tipo_alteracao
            }
        }), 201
        
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

# ============================================
# 6. ROTAS EVENTO DA NOTA FISCAL
# ============================================

@fiscal_bp.route('/notas-fiscais/<int:nota_fiscal_id>/eventos', methods=['GET'])
@admin_required
def listar_eventos_nota(nota_fiscal_id):
    """Lista eventos de uma nota fiscal"""
    try:
         
        eventos = NotaFiscalEventoCRUD.listar_por_nota(db.session, nota_fiscal_id)
        
        return jsonify({
            "success": True,
            "data": [{
                "id": e.id,
                "tipo_evento": e.tipo_evento,
                "descricao_evento": e.descricao_evento,
                "data_registro": e.data_registro,
                "processado": e.processado,
                "sucesso": e.sucesso
            } for e in eventos]
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/eventos/registrar-cancelamento', methods=['POST'])
@admin_required
def registrar_cancelamento():
    """Registra cancelamento de nota fiscal"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400
        
        required_fields = ['nota_fiscal_id', 'justificativa']
        for field in required_fields:
            if field not in dados:
                return jsonify({"success": False, "message": f"Campo {field} é obrigatório"}), 400
        
         
        evento = NotaFiscalEventoCRUD.registrar_cancelamento(
            db.session,
            dados['nota_fiscal_id'],
            dados['justificativa'],
            dados.get('protocolo'),
            dados.get('xml_evento')
        )
        
        return jsonify({
            "success": True,
            "message": "Cancelamento registrado com sucesso",
            "data": {
                "id": evento.id,
                "nota_fiscal_id": evento.nota_fiscal_id,
                "sequencia_evento": evento.sequencia_evento
            }
        }), 201
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/eventos/registrar-carta-correcao', methods=['POST'])
@admin_required
def registrar_carta_correcao():
    """Registra carta de correção"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400
        
        required_fields = ['nota_fiscal_id', 'correcoes']
        for field in required_fields:
            if field not in dados:
                return jsonify({"success": False, "message": f"Campo {field} é obrigatório"}), 400
        
         
        evento = NotaFiscalEventoCRUD.registrar_carta_correcao(
            db.session,
            dados['nota_fiscal_id'],
            dados['correcoes'],
            dados.get('sequencia', 1),
            dados.get('protocolo'),
            dados.get('xml_evento')
        )
        
        return jsonify({
            "success": True,
            "message": "Carta de correção registrada com sucesso",
            "data": {
                "id": evento.id,
                "nota_fiscal_id": evento.nota_fiscal_id,
                "sequencia_evento": evento.sequencia_evento
            }
        }), 201
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/eventos/<int:id>/processar', methods=['POST'])
@admin_required
def marcar_evento_processado(id):
    """Marca evento como processado"""
    try:
        dados = request.get_json() or {}
        sucesso = dados.get('sucesso', True)
        xml_retorno = dados.get('xml_retorno')
        
         
        evento = NotaFiscalEventoCRUD.marcar_processado(db.session, id, sucesso, xml_retorno)
        
        if not evento:
            return jsonify({"success": False, "message": "Evento não encontrado"}), 404
        
        return jsonify({
            "success": True,
            "message": "Evento marcado como processado",
            "data": {
                "id": evento.id,
                "processado": evento.processado,
                "sucesso": evento.sucesso
            }
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

# ============================================
# 7. ROTAS VOLUMES DA NOTA FISCAL
# ============================================

@fiscal_bp.route('/notas-fiscais/<int:nota_fiscal_id>/volumes', methods=['POST'])
@admin_required
def criar_volumes_nota(nota_fiscal_id):
    """Cria volumes para uma nota fiscal"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400
        
         
        
        # Verifica se é um único volume ou múltiplos
        if isinstance(dados, dict):
            dados['nota_fiscal_id'] = nota_fiscal_id
            volume = NotaFiscalVolumeCRUD.criar(db.session, dados)
            volumes = [volume]
        elif isinstance(dados, list):
            volumes = NotaFiscalVolumeCRUD.criar_multiplos(db.session, nota_fiscal_id, dados)
        else:
            return jsonify({"success": False, "message": "Formato de dados inválido"}), 400
        
        return jsonify({
            "success": True,
            "message": f"{len(volumes)} volume(s) criado(s) com sucesso",
            "data": [{
                "id": v.id,
                "quantidade": v.quantidade,
                "especie": v.especie
            } for v in volumes]
        }), 201
        
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/notas-fiscais/<int:nota_fiscal_id>/volumes', methods=['GET'])
@admin_required
def listar_volumes_nota(nota_fiscal_id):
    """Lista volumes de uma nota fiscal"""
    try:
         
        volumes = NotaFiscalVolumeCRUD.listar_por_nota(db.session, nota_fiscal_id)
        
        return jsonify({
            "success": True,
            "data": [{
                "id": v.id,
                "quantidade": v.quantidade,
                "especie": v.especie,
                "marca": v.marca,
                "peso_liquido": v.peso_liquido,
                "peso_bruto": v.peso_bruto
            } for v in volumes]
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/volumes/<int:id>', methods=['PUT'])
@admin_required
def atualizar_volume(id):
    """Atualiza volume da nota fiscal"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400
        
         
        volume = NotaFiscalVolumeCRUD.atualizar(db.session, id, dados)
        
        if not volume:
            return jsonify({"success": False, "message": "Volume não encontrado"}), 404
        
        return jsonify({
            "success": True,
            "message": "Volume atualizado com sucesso",
            "data": {
                "id": volume.id,
                "quantidade": volume.quantidade,
                "especie": volume.especie
            }
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/volumes/<int:id>', methods=['DELETE'])
@admin_required
def excluir_volume(id):
    """Exclui volume da nota fiscal"""
    try:
         
        sucesso = NotaFiscalVolumeCRUD.excluir(db.session, id)
        
        if not sucesso:
            return jsonify({"success": False, "message": "Volume não encontrado"}), 404
        
        return jsonify({
            "success": True,
            "message": "Volume excluído com sucesso"
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

# ============================================
# 8. ROTAS DO FISCAL MANAGER (FACADE)
# ============================================

@fiscal_bp.route('/manager/configuracao-ativa', methods=['GET'])
@admin_required
def manager_obter_configuracao_ativa():
    """Obtém configuração fiscal ativa usando FiscalManager"""
    try:
         
        manager = FiscalManager(db)
        config = manager.obter_configuracao_ativa()
        
        if not config:
            return jsonify({"success": False, "message": "Nenhuma configuração ativa encontrada"}), 404
        
        return jsonify({
            "success": True,
            "data": {
                "id": config.id,
                "razao_social": config.razao_social,
                "cnpj": config.cnpj,
                "ambiente": config.ambiente
            }
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/manager/produto/<int:produto_id>', methods=['GET'])
@admin_required
def manager_obter_produto_fiscal(produto_id):
    """Obtém dados fiscais de um produto usando FiscalManager"""
    try:
         
        manager = FiscalManager(db)
        produto_fiscal = manager.obter_produto_fiscal(produto_id)
        
        if not produto_fiscal:
            return jsonify({"success": False, "message": "Dados fiscais não encontrados"}), 404
        
        return jsonify({
            "success": True,
            "data": produto_fiscal.__dict__
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/manager/transportadora/documento', methods=['GET'])
@admin_required
def manager_buscar_transportadora_por_documento():
    """Busca transportadora por documento usando FiscalManager"""
    try:
        documento = request.args.get('documento', '')
        if not documento:
            return jsonify({"success": False, "message": "Parâmetro 'documento' é obrigatório"}), 400
        
         
        manager = FiscalManager(db)
        transportadora = manager.buscar_transportadora_por_documento(documento)
        
        if not transportadora:
            return jsonify({"success": False, "message": "Transportadora não encontrada"}), 404
        
        return jsonify({
            "success": True,
            "data": {
                "id": transportadora.id,
                "razao_social": transportadora.razao_social,
                "cnpj": transportadora.cnpj,
                "cpf": transportadora.cpf
            }
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/manager/evento/registrar', methods=['POST'])
@admin_required
def manager_registrar_evento_nota():
    """Registra evento para nota fiscal usando FiscalManager"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400
        
        required_fields = ['nota_fiscal_id', 'tipo_evento', 'descricao_evento']
        for field in required_fields:
            if field not in dados:
                return jsonify({"success": False, "message": f"Campo {field} é obrigatório"}), 400
        
         
        manager = FiscalManager(db)
        evento = manager.registrar_evento_nota(
            dados['nota_fiscal_id'],
            dados['tipo_evento'],
            dados['descricao_evento'],
            **{k: v for k, v in dados.items() if k not in required_fields}
        )
        
        return jsonify({
            "success": True,
            "message": "Evento registrado com sucesso",
            "data": {
                "id": evento.id,
                "nota_fiscal_id": evento.nota_fiscal_id,
                "tipo_evento": evento.tipo_evento
            }
        }), 201
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/eventos', methods=['GET'])
@admin_required
def listar_eventos():
    """Lista todos os eventos (com filtros)"""
    try:
        skip = request.args.get('skip', 0, type=int)
        limit = request.args.get('limit', 100, type=int)
        tipo_evento = request.args.get('tipo_evento')
        processado = request.args.get('processado', type=bool)
        
         
        # Crie um query base
        query = db.session.query(NotaFiscalEvento)
        
        # Aplique filtros
        if tipo_evento:
            query = query.filter(NotaFiscalEvento.tipo_evento == tipo_evento)
        if processado is not None:
            query = query.filter(NotaFiscalEvento.processado == processado)
        
        # Execute query
        eventos = query.order_by(NotaFiscalEvento.data_registro.desc())\
                      .offset(skip).limit(limit).all()
        
        return jsonify({
            "success": True,
            "data": [{
                "id": e.id,
                "tipo_evento": e.tipo_evento,
                "descricao_evento": e.descricao_evento,
                "data_registro": e.data_registro.isoformat() if e.data_registro else None,
                "processado": e.processado,
                "sucesso": e.sucesso,
                "nota_fiscal_id": e.nota_fiscal_id
            } for e in eventos]
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500
    

@fiscal_bp.route('/health', methods=['GET'])
@admin_required
def health_check():
    """Endpoint para verificar se as rotas fiscais estão funcionando"""
    try:
        # Teste básico de conexão com banco
        count_configs = db.session.query(ConfiguracaoFiscal).count()
        
        return jsonify({
            "success": True,
            "message": "Rotas fiscais operacionais",
            "data": {
                "configuracoes_count": count_configs,
                "status": "online"
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erro de saúde: {str(e)}",
            "status": "offline"
        }), 500
        
# ============================================
# 8. ROTAS CLIENTE FISCAL
# ============================================

@fiscal_bp.route('/clientes-fiscais', methods=['POST'])
@admin_required
def criar_cliente_fiscal():
    """Cria um novo cliente fiscal"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400
        
        # Validações básicas
        if 'cpf_cnpj' not in dados:
            return jsonify({"success": False, "message": "CPF/CNPJ é obrigatório"}), 400
        if 'nome_cliente' not in dados:
            return jsonify({"success": False, "message": "Nome do cliente é obrigatório"}), 400
        if 'cep' not in dados:
            return jsonify({"success": False, "message": "CEP é obrigatório"}), 400
        
        cliente = ClienteFiscalCRUD.criar(db.session, dados)
        
        return jsonify({
            "success": True,
            "message": "Cliente fiscal criado com sucesso",
            "data": {
                "id": cliente.id,
                "cpf_cnpj": cliente.cpf_cnpj,
                "nome_cliente": cliente.nome_cliente
            }
        }), 201
        
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/clientes-fiscais', methods=['GET'])
@admin_required
def listar_clientes_fiscais():
    """Lista todos os clientes fiscais"""
    try:
        skip = request.args.get('skip', 0, type=int)
        limit = request.args.get('limit', 100, type=int)
        ativo = request.args.get('ativo', type=lambda v: v.lower() == 'true')
        tipo_cliente = request.args.get('tipo_cliente')
        uf = request.args.get('uf')
        
        # Aplica filtros
        if tipo_cliente:
            clientes = ClienteFiscalCRUD.listar_por_tipo(
                db.session, tipo_cliente, ativo, skip, limit
            )
        elif uf:
            clientes = ClienteFiscalCRUD.listar_por_uf(
                db.session, uf, ativo, skip, limit
            )
        else:
            clientes = ClienteFiscalCRUD.listar_todos(db.session, ativo, skip, limit)
        
        return jsonify({
            "success": True,
            "data": [{
                "id": c.id,
                "cpf_cnpj": c.cpf_cnpj,
                "nome_cliente": c.nome_cliente,
                "nome_fantasia": c.nome_fantasia,
                "tipo_cliente": c.tipo_cliente,
                "inscricao_estadual": c.inscricao_estadual,
                "municipio": c.municipio,
                "uf": c.uf,
                "telefone": c.telefone,
                "email": c.email,
                "ativo": c.ativo,
                "sincronizado": c.sincronizado,
                "criado_em": c.criado_em.isoformat() if c.criado_em else None
            } for c in clientes]
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/clientes-fiscais/<int:id>', methods=['GET'])
@admin_required
def obter_cliente_fiscal_por_id(id):
    """Obtém cliente fiscal por ID"""
    try:
        cliente = ClienteFiscalCRUD.obter_por_id(db.session, id)
        
        if not cliente:
            return jsonify({"success": False, "message": "Cliente fiscal não encontrado"}), 404
        
        return jsonify({
            "success": True,
            "data": {
                # Identificação
                "id": cliente.id,
                "cpf_cnpj": cliente.cpf_cnpj,
                "nome_cliente": cliente.nome_cliente,
                "nome_fantasia": cliente.nome_fantasia,
                
                # Dados Fiscais
                "indicador_ie": cliente.indicador_ie,
                "inscricao_estadual": cliente.inscricao_estadual,
                "inscricao_municipal": cliente.inscricao_municipal,
                "inscricao_suframa": cliente.inscricao_suframa,
                
                # Endereço
                "endereco": {
                    "cep": cliente.cep,
                    "logradouro": cliente.logradouro,
                    "numero": cliente.numero,
                    "complemento": cliente.complemento,
                    "bairro": cliente.bairro,
                    "codigo_municipio": cliente.codigo_municipio,
                    "municipio": cliente.municipio,
                    "uf": cliente.uf,
                    "codigo_pais": cliente.codigo_pais,
                    "pais": cliente.pais
                },
                
                # Contato
                "contato": {
                    "telefone": cliente.telefone,
                    "celular": cliente.celular,
                    "email": cliente.email,
                    "fax": cliente.fax
                },
                
                # Informações Adicionais
                "observacoes": cliente.observacoes,
                "tipo_cliente": cliente.tipo_cliente,
                "regime_tributario": cliente.regime_tributario,
                
                # Controle
                "ativo": cliente.ativo,
                "sincronizado": cliente.sincronizado,
                "criado_em": cliente.criado_em.isoformat() if cliente.criado_em else None,
                "atualizado_em": cliente.atualizado_em.isoformat() if cliente.atualizado_em else None
            }
        }), 200
        
    except Exception as e:
        import traceback
        print(f"Erro detalhado: {traceback.format_exc()}")
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/clientes-fiscais/cpf-cnpj/<string:documento>', methods=['GET'])
@admin_required
def obter_cliente_fiscal_por_cpf_cnpj(documento):
    """Obtém cliente fiscal por CPF/CNPJ"""
    try:
        cliente = ClienteFiscalCRUD.obter_por_cpf_cnpj(db.session, documento)
        
        if not cliente:
            return jsonify({"success": False, "message": "Cliente fiscal não encontrado"}), 404
        
        return jsonify({
            "success": True,
            "data": cliente.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/clientes-fiscais/buscar', methods=['GET'])
@admin_required
def buscar_clientes_fiscais():
    """Busca clientes fiscais por nome ou documento"""
    try:
        termo = request.args.get('termo', '')
        limit = request.args.get('limit', 20, type=int)
        
        if not termo:
            return jsonify({"success": False, "message": "Parâmetro 'termo' é obrigatório"}), 400
        
        # Tenta buscar por documento primeiro
        if termo.isdigit():
            cliente = ClienteFiscalCRUD.obter_por_cpf_cnpj(db.session, termo)
            if cliente:
                return jsonify({
                    "success": True,
                    "data": [cliente.to_dict()]
                }), 200
        
        # Busca por nome
        clientes = ClienteFiscalCRUD.buscar_por_nome(db.session, termo, limit=limit)
        print(f'Clientes encontrados: {clientes}')
        return jsonify({
            "success": True,
            "data": [c.to_dict() for c in clientes]
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/clientes-fiscais/<int:id>', methods=['PUT'])
@admin_required
def atualizar_cliente_fiscal(id):
    """Atualiza um cliente fiscal"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400
        
        cliente = ClienteFiscalCRUD.atualizar(db.session, id, dados)
        
        if not cliente:
            return jsonify({"success": False, "message": "Cliente fiscal não encontrado"}), 404
        
        return jsonify({
            "success": True,
            "message": "Cliente fiscal atualizado com sucesso",
            "data": {
                "id": cliente.id,
                "cpf_cnpj": cliente.cpf_cnpj,
                "nome_cliente": cliente.nome_cliente
            }
        }), 200
        
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/clientes-fiscais/<int:id>', methods=['DELETE'])
@admin_required
def excluir_cliente_fiscal(id):
    """Desativa (soft delete) um cliente fiscal"""
    try:
        sucesso = ClienteFiscalCRUD.excluir(db.session, id, soft_delete=True)
        
        if not sucesso:
            return jsonify({"success": False, "message": "Cliente fiscal não encontrado"}), 404
        
        return jsonify({
            "success": True,
            "message": "Cliente fiscal desativado com sucesso"
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/clientes-fiscais/<int:id>/reativar', methods=['POST'])
@admin_required
def reativar_cliente_fiscal(id):
    """Reativa um cliente fiscal desativado"""
    try:
        cliente = ClienteFiscalCRUD.reativar(db.session, id)
        
        if not cliente:
            return jsonify({"success": False, "message": "Cliente fiscal não encontrado"}), 404
        
        return jsonify({
            "success": True,
            "message": "Cliente fiscal reativado com sucesso",
            "data": {
                "id": cliente.id,
                "cpf_cnpj": cliente.cpf_cnpj,
                "nome_cliente": cliente.nome_cliente,
                "ativo": cliente.ativo
            }
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/clientes-fiscais/<int:id>/validar-nfe', methods=['GET'])
@admin_required
def validar_cliente_fiscal_nfe(id):
    """Valida dados do cliente para emissão de NFe"""
    try:
        cliente = ClienteFiscalCRUD.obter_por_id(db.session, id)
        
        if not cliente:
            return jsonify({"success": False, "message": "Cliente fiscal não encontrado"}), 404
        
        validacao = ClienteFiscalCRUD.validar_dados_nfe(cliente)
        
        return jsonify({
            "success": True,
            "data": {
                "cliente_id": cliente.id,
                "cliente_nome": cliente.nome_cliente,
                "validacao": validacao,
                "valido_para_nfe": len(validacao['erros']) == 0
            }
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/clientes-fiscais/<int:id>/marcar-sincronizado', methods=['POST'])
@admin_required
def marcar_cliente_sincronizado(id):
    """Marca cliente como sincronizado"""
    try:
        cliente = ClienteFiscalCRUD.marcar_sincronizado(db.session, id)
        
        if not cliente:
            return jsonify({"success": False, "message": "Cliente fiscal não encontrado"}), 404
        
        return jsonify({
            "success": True,
            "message": "Cliente marcado como sincronizado",
            "data": {
                "id": cliente.id,
                "cpf_cnpj": cliente.cpf_cnpj,
                "sincronizado": cliente.sincronizado
            }
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/clientes-fiscais/sincronizados/marcar-multiplos', methods=['POST'])
@admin_required
def marcar_multiplos_clientes_sincronizados():
    """Marca múltiplos clientes como sincronizados"""
    try:
        dados = request.get_json()
        if not dados or 'ids' not in dados:
            return jsonify({"success": False, "message": "Lista de IDs é obrigatória"}), 400
        
        ids = dados['ids']
        if not isinstance(ids, list):
            return jsonify({"success": False, "message": "IDs deve ser uma lista"}), 400
        
        sucesso = ClienteFiscalCRUD.marcar_todos_sincronizados(db.session, ids)
        
        if not sucesso:
            return jsonify({"success": False, "message": "Erro ao marcar clientes como sincronizados"}), 500
        
        return jsonify({
            "success": True,
            "message": f"{len(ids)} cliente(s) marcado(s) como sincronizado(s)"
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/clientes-fiscais/importar', methods=['POST'])
@admin_required
def importar_cliente_fiscal():
    """Importa cliente a partir de dicionário no formato padrão"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400
        
        cliente = ClienteFiscalCRUD.importar_de_dict(db.session, dados)
        
        if isinstance(cliente, ClienteFiscal):
            action = "atualizado" if 'id' in request.get_json() else "criado"
        else:
            action = "importado"
        
        return jsonify({
            "success": True,
            "message": f"Cliente fiscal {action} com sucesso",
            "data": {
                "id": cliente.id,
                "cpf_cnpj": cliente.cpf_cnpj,
                "nome_cliente": cliente.nome_cliente,
                "tipo_cliente": cliente.tipo_cliente
            }
        }), 201
        
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/clientes-fiscais/estatisticas', methods=['GET'])
@admin_required
def obter_estatisticas_clientes():
    """Obtém estatísticas dos clientes fiscais"""
    try:
        total_clientes = ClienteFiscalCRUD.contar_total(db.session, ativo=True)
        total_inativos = ClienteFiscalCRUD.contar_total(db.session, ativo=False)
        total_pessoas_fisicas = db.session.query(ClienteFiscal).filter(
            ClienteFiscal.tipo_cliente == 'fisica',
            ClienteFiscal.ativo == True
        ).count()
        total_pessoas_juridicas = db.session.query(ClienteFiscal).filter(
            ClienteFiscal.tipo_cliente == 'juridica',
            ClienteFiscal.ativo == True
        ).count()
        nao_sincronizados = db.session.query(ClienteFiscal).filter(
            ClienteFiscal.sincronizado == False,
            ClienteFiscal.ativo == True
        ).count()
        
        # Contagem por UF
        uf_counts = db.session.query(
            ClienteFiscal.uf,
            db.func.count(ClienteFiscal.id).label('total')
        ).filter(
            ClienteFiscal.ativo == True
        ).group_by(ClienteFiscal.uf).all()
        
        return jsonify({
            "success": True,
            "data": {
                "totais": {
                    "ativos": total_clientes,
                    "inativos": total_inativos,
                    "pessoas_fisicas": total_pessoas_fisicas,
                    "pessoas_juridicas": total_pessoas_juridicas,
                    "nao_sincronizados": nao_sincronizados
                },
                "por_uf": [{"uf": uf, "total": total} for uf, total in uf_counts],
                "por_regime": {
                    "simples": db.session.query(ClienteFiscal).filter(
                        ClienteFiscal.regime_tributario == '1',
                        ClienteFiscal.ativo == True
                    ).count(),
                    "normal": db.session.query(ClienteFiscal).filter(
                        ClienteFiscal.regime_tributario == '2',
                        ClienteFiscal.ativo == True
                    ).count(),
                    "mei": db.session.query(ClienteFiscal).filter(
                        ClienteFiscal.regime_tributario == '3',
                        ClienteFiscal.ativo == True
                    ).count()
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/clientes-fiscais/listar-nao-sincronizados', methods=['GET'])
@admin_required
def listar_clientes_nao_sincronizados():
    """Lista clientes que não foram sincronizados"""
    try:
        skip = request.args.get('skip', 0, type=int)
        limit = request.args.get('limit', 50, type=int)
        
        clientes = ClienteFiscalCRUD.listar_nao_sincronizados(db.session, skip, limit)
        
        return jsonify({
            "success": True,
            "data": [{
                "id": c.id,
                "cpf_cnpj": c.cpf_cnpj,
                "nome_cliente": c.nome_cliente,
                "tipo_cliente": c.tipo_cliente,
                "municipio": c.municipio,
                "uf": c.uf,
                "criado_em": c.criado_em.isoformat() if c.criado_em else None,
                "atualizado_em": c.atualizado_em.isoformat() if c.atualizado_em else None
            } for c in clientes]
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/clientes-fiscais/exportar-nfe/<int:id>', methods=['GET'])
@admin_required
def exportar_cliente_para_nfe(id):
    """Exporta cliente no formato esperado pela NFe"""
    try:
        cliente = ClienteFiscalCRUD.obter_por_id(db.session, id)
        
        if not cliente:
            return jsonify({"success": False, "message": "Cliente fiscal não encontrado"}), 404
        
        # Valida antes de exportar
        validacao = ClienteFiscalCRUD.validar_dados_nfe(cliente)
        
        if len(validacao['erros']) > 0:
            return jsonify({
                "success": False,
                "message": "Cliente com dados inválidos para NFe",
                "data": {
                    "cliente_id": cliente.id,
                    "cliente_nome": cliente.nome_cliente,
                    "erros": validacao['erros'],
                    "warnings": validacao['warnings']
                }
            }), 400
        
        nfe_data = cliente.to_nfe_dict()
        
        return jsonify({
            "success": True,
            "data": nfe_data
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500