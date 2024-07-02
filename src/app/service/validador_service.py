from .. import db
from ..models import Seletor, Transacao, Validador
from datetime import datetime, timedelta
from .. import services


def get_all_validators():
    return Validador.query.all()

def create_validator(nome, chave_unica, saldo, ip):
    validador = Validador(nome=nome, chave_unica=chave_unica, saldo=saldo, flags=0, ip=ip)
    db.session.add(validador)
    db.session.commit()
    return validador

def get_validator_by_id(id):
    return Validador.query.get(id)

def update_validator(id, saldo):
    validador = Validador.query.filter_by(id=id).first()
    validador.saldo = saldo
    db.session.commit()

def delete_validator(id):
    validador = Validador.query.get(id)
    db.session.delete(validador)
    db.session.commit()

    
def validar_transacao(transacao, validador, remetente, taxa):
    try:     
        
        # Verifica se o remetente tem saldo suficiente para a transação
        if transacao.valor + taxa > remetente.qtdMoeda:
            return 2 , "Não aprovada (erro de saldo insuficiente)"

        # Verifica o horário da transação
        if transacao.horario > datetime.now() or transacao.horario <= datetime.now() - timedelta(minutes=1):
            return 2 , "Não aprovada (erro de horário)"

        # Verifica se o remetente excedeu o limite de transações no último minuto
        if contar_transacoes_ultimo_minuto(remetente) > 100:
            return 2, "Não aprovada (limite de transações excedido)"

        # Verifica se a chave única do validador corresponde à chave recebida
        #if validador.chave_unica != transacao.chave_unica:
        #    return 2, "Não aprovada (chave única inválida)"

        # Todas as validações passaram, transação concluída com sucesso
        return 1, "transação concluída com sucesso"
    
    except Exception as e:
        # Se ocorrer qualquer exceção durante as validações, retorna código de erro
        print(f"Erro ao validar transação: {str(e)}")
        return 2, "Não aprovada (erro genérico)" # Não aprovada (erro genérico)

def contar_transacoes_ultimo_minuto(remetente):
    # Obtém a data e hora atual menos 1 minuto
    um_minuto_atras = datetime.now() - timedelta(minutes=1)
    
    # Conta as transações do remetente no último minuto
    count = Transacao.query.filter(
        Transacao.remetente == remetente.id,
        Transacao.horario >= um_minuto_atras
    ).count()

    return count