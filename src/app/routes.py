from flask import request, jsonify, render_template
from datetime import datetime
from app import services

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

    @app.route('/transacoes/<int:rem>/<int:reb>/<int:valor>', methods=['POST'])
    def CriaTransacao(rem, reb, valor):
        transacao = services.create_transaction(rem, reb, valor)
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

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('page_not_found.html'), 404
