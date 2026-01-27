from flask import Blueprint, request, jsonify
from app.models import db
from app.decorators.decorators import admin_required
from app.models.fiscal_models import ConfiguracaoFiscal, NotaFiscalEvento
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
        
        return jsonify({
            "success": True,
            "data": config_dict
        }), 200
        
    except Exception as e:
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
    """Cria dados fiscais para um produto"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400
        
        if 'produto_id' not in dados:
            return jsonify({"success": False, "message": "ID do produto é obrigatório"}), 400
        
         
        produto_fiscal = ProdutoFiscalCRUD.criar(db.session, dados)
        
        return jsonify({
            "success": True,
            "message": "Dados fiscais criados com sucesso",
            "data": {
                "id": produto_fiscal.id,
                "produto_id": produto_fiscal.produto_id,
                "codigo_ncm": produto_fiscal.codigo_ncm
            }
        }), 201
        
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/produtos-fiscais/<int:id>', methods=['GET'])
@admin_required
def obter_produto_fiscal_por_id(id):
    """Obtém dados fiscais do produto por ID"""
    try:
         
        produto_fiscal = ProdutoFiscalCRUD.obter_por_id(db.session, id)
        
        if not produto_fiscal:
            return jsonify({"success": False, "message": "Dados fiscais não encontrados"}), 404
        
        return jsonify({
            "success": True,
            "data": produto_fiscal.__dict__
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/produtos-fiscais/produto/<int:produto_id>', methods=['GET'])
@admin_required
def obter_produto_fiscal_por_produto(produto_id):
    """Obtém dados fiscais por ID do produto"""
    try:
         
        produto_fiscal = ProdutoFiscalCRUD.obter_por_produto_id(db.session, produto_id)
        
        if not produto_fiscal:
            return jsonify({"success": False, "message": "Dados fiscais não encontrados"}), 404
        
        return jsonify({
            "success": True,
            "data": produto_fiscal.__dict__
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@fiscal_bp.route('/produtos-fiscais/<int:id>', methods=['PUT'])
@admin_required
def atualizar_produto_fiscal(id):
    """Atualiza dados fiscais do produto"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400
        
         
        produto_fiscal = ProdutoFiscalCRUD.atualizar(db.session, id, dados)
        
        if not produto_fiscal:
            return jsonify({"success": False, "message": "Dados fiscais não encontrados"}), 404
        
        return jsonify({
            "success": True,
            "message": "Dados fiscais atualizados com sucesso",
            "data": {
                "id": produto_fiscal.id,
                "produto_id": produto_fiscal.produto_id
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
        
         
        produtos = ProdutoFiscalCRUD.listar_homologados(db.session, skip, limit)
        
        return jsonify({
            "success": True,
            "data": [{
                "id": p.id,
                "produto_id": p.produto_id,
                "codigo_ncm": p.codigo_ncm,
                "cst_icms": p.cst_icms,
                "data_homologacao": p.data_homologacao
            } for p in produtos]
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

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
                "cnpj": t.cnpj,
                "cpf": t.cpf,
                "municipio": t.municipio,
                "uf": t.uf
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
        
        return jsonify({
            "success": True,
            "data": transportadora.__dict__
        }), 200
        
    except Exception as e:
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

# ============================================
# 4. ROTAS VEÍCULO DE TRANSPORTE
# ============================================

@fiscal_bp.route('/veiculos', methods=['POST'])
@admin_required
def criar_veiculo():
    """Cria um novo veículo de transporte"""
    try:
        dados = request.get_json()
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
                "transportadora_id": v.transportadora_id
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
        
        return jsonify({
            "success": True,
            "data": veiculo.__dict__
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