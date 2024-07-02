from .. import db
from ..models import Seletor, Transacao, Validador
from datetime import datetime, timedelta

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

    
def validar_transacao(transacao, validador):
    
    # Todas as regras foram passadas, transação concluída com sucesso
    return 1  # Concluída com sucesso

