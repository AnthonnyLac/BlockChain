from flask import request, jsonify, render_template
from datetime import datetime
from app import services
from .service import banco_service, seletor_service, validador_service

def init_app(app):
    @app.route("/")
    def index():
        return jsonify(['API sem interface do banco!'])

    @app.route('/cliente', methods=['GET'])
    def ListarCliente():
        clientes = services.get_all_clients()
        return jsonify(clientes)

    @app.route('/cliente/<string:nome>/<string:senha>/<int:qtdMoeda>', methods=['POST'])
    def InserirCliente(nome, senha, qtdMoeda):
        if nome and senha and qtdMoeda:
            cliente = services.create_client(nome, senha, qtdMoeda)
            return jsonify(cliente)
        else:
            return jsonify(['Method Not Allowed'])

    @app.route('/cliente/<int:id>', methods=['GET'])
    def UmCliente(id):
        cliente = services.get_client_by_id(id)
        return jsonify(cliente)

    @app.route('/cliente/<int:id>/<int:qtdMoedas>', methods=["POST"])
    def EditarCliente(id, qtdMoedas):
        try:
            services.update_client(id, qtdMoedas)
            return jsonify(['Alteração feita com sucesso'])
        except Exception as e:
            data = {"message": "Atualização não realizada"}
            return jsonify(data)

    @app.route('/cliente/<int:id>', methods=['DELETE'])
    def ApagarCliente(id):
        try:
            services.delete_client(id)
            data = {"message": "Cliente Deletado com Sucesso"}
            return jsonify(data)
        except Exception as e:
            data = {"message": "Erro ao deletar cliente"}
            return jsonify(data)

    @app.route('/seletor', methods=['GET'])
    def ListarSeletor():
        seletores = services.get_all_selectors()
        return jsonify(seletores)

    @app.route('/seletor/<string:nome>/<string:ip>', methods=['POST'])
    def InserirSeletor(nome, ip):
        if nome and ip:
            seletor = services.create_selector(nome, ip)
            return jsonify(seletor)
        else:
            return jsonify(['Method Not Allowed'])

    @app.route('/seletor/<int:id>', methods=['GET'])
    def UmSeletor(id):
        seletor = services.get_selector_by_id(id)
        return jsonify(seletor)

    @app.route('/seletor/<int:id>/<string:nome>/<string:ip>', methods=["POST"])
    def EditarSeletor(id, nome, ip):
        try:
            services.update_selector(id, nome, ip)
            return jsonify({"message": "Atualização realizada com sucesso"})
        except Exception as e:
            data = {"message": "Atualização não realizada"}
            return jsonify(data)

    @app.route('/seletor/<int:id>', methods=['DELETE'])
    def ApagarSeletor(id):
        try:
            services.delete_selector(id)
            data = {"message": "Validador Deletado com Sucesso"}
            return jsonify(data)
        except Exception as e:
            data = {"message": "Erro ao deletar validador"}
            return jsonify(data)

    @app.route('/hora', methods=['GET'])
    def horario():
        objeto = datetime.now()
        return jsonify(objeto)

    @app.route('/transacoes', methods=['GET'])
    def ListarTransacoes():
        transacoes = services.get_all_transactions()
        return jsonify(transacoes)

    @app.route('/transacoes', methods=['POST'])
    async def CriaTransacao():
        
        data = request.json
        
        transacao = services.create_transaction(data["remetente"], data["recebedor"], data["valor"])
        
        result, message = await banco_service.distribuir_transacoes_para_seletor_unit(transacao.id)
        
        if(result == False):
            return(message), 500
        
        return jsonify(transacao)

    @app.route('/transacoes/<int:id>', methods=['GET'])
    def UmaTransacao(id):
        transacao = services.get_transaction_by_id(id)
        return jsonify(transacao)

    @app.route('/transacoes/<int:id>/<int:status>', methods=["POST"])
    def EditaTransacao(id, status):
        try:
            services.update_transaction(id, status)
            return jsonify({"message": "Transação atualizada com sucesso"})
        except Exception as e:
            data = {"message": "Transação não atualizada"}
            return jsonify(data)
        
         
    @app.route('/validador', methods=['GET'])
    def listar_validadores():
        validadores = validador_service.get_all_validators()
        return jsonify(validadores)

    @app.route('/validador', methods=['POST'])
    def inserir_validador():
        data = request.json
        validador = validador_service.create_validator(data['nome'], data['chave_unica'], data['saldo'], data['ip'])
        return jsonify(validador)

    @app.route('/validador/<int:id>', methods=['GET'])
    def obter_validador_por_id(id):
        validador =  validador_service.get_validator_by_id(id)
        return jsonify(validador)

    @app.route('/validador/<int:id>/<int:saldo>', methods=["POST"])
    def editar_validador(id, saldo):
        try:
            validador_service.update_validator(id, saldo)
            return jsonify(['Alteração feita com sucesso'])
        except Exception as e:
            data = {"message": "Atualização não realizada"}
            return jsonify(data)

    @app.route('/validador/<int:id>', methods=['DELETE'])
    def apagar_validador(id):
        try:
            validador_service.delete_validator(id)
            data = {"message": "Validador Deletado com Sucesso"}
            return jsonify(data)
        except Exception as e:
            data = {"message": "Erro ao deletar validador"}
            return jsonify(data)


    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('page_not_found.html'), 404

    @app.route('/seletor/process', methods=['POST'])
    async def ProcessarTransacoes():
        data = request.json
        
        result, mensage = await seletor_service.distribuir_transacoes_para_validadores(data["seletorId"], data["transacoesId"])
        
        response = {
            "mensage": mensage
        }
        
        if(result is not None):
            return response, 200
        
        return response, 500
    
    @app.route('/validador/process', methods=['POST'])
    async def validarTransacoes():
        
        print("\ncaiu validador -> ok")
        data = request.json
        
        transacoesId = data["transacaoId"]
        transacao = services.get_transaction_by_id(transacoesId)
        validador = validador_service.get_validator_by_id(data['validador_id'])
        remetente = services.get_client_by_id(transacao.remetente)
        taxa = data['taxa']
        
        status, mensageValidacao = validador_service.validar_transacao(transacao, validador, remetente, taxa)
        
        response = {
            "status" : status,
            "mesageValidation" : mensageValidacao
        }
        
        # if status == 1:
        #     services.update_transaction(transacao.id, status=status)
        #     validador_service.update_validator(transacao.remetente, transacao.valor)
        # else:
        #     services.update_transaction(transacao.id, status=status)
        #
        # return jsonify({'status': transacao.status})      
        
        return jsonify(response)