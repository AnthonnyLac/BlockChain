from .models import Cliente, Seletor, Transacao
from app import db
from datetime import datetime
import requests

def get_all_clients():
    return Cliente.query.all()

def create_client(nome, senha, qtdMoeda):
    cliente = Cliente(nome=nome, senha=senha, qtdMoeda=qtdMoeda)
    db.session.add(cliente)
    db.session.commit()
    return cliente

def get_client_by_id(id):
    return Cliente.query.get(id)

def update_client(id, qtdMoedas):
    cliente = Cliente.query.filter_by(id=id).first()
    cliente.qtdMoedas = qtdMoedas
    db.session.commit()

def delete_client(id):
    cliente = Cliente.query.get(id)
    db.session.delete(cliente)
    db.session.commit()

def get_all_selectors():
    return Seletor.query.all()

def create_selector(nome, ip):
    seletor = Seletor(nome=nome, ip=ip)
    db.session.add(seletor)
    db.session.commit()
    return seletor

def get_selector_by_id(id):
    return Seletor.query.get(id)

def update_selector(id, nome, ip):
    seletor = Seletor.query.filter_by(id=id).first()
    seletor.nome = nome
    seletor.ip = ip
    db.session.commit()

def delete_selector(id):
    seletor = Seletor.query.get(id)
    db.session.delete(seletor)
    db.session.commit()

def get_all_transactions():
    return Transacao.query.all()

def create_transaction(remetente, recebedor, valor):
    transacao = Transacao(remetente=remetente, recebedor=recebedor, valor=valor, status=0, horario=datetime.now())
    db.session.add(transacao)
    db.session.commit()
    
    seletores = Seletor.query.all()
    for seletor in seletores:
        url = f"http://{seletor.ip}/transacoes/"
        requests.post(url, json=transacao)
        
    return transacao

def get_transaction_by_id(id):
    return Transacao.query.get(id)

def update_transaction(id, status):
    transacao = Transacao.query.filter_by(id=id).first()
    transacao.status = status
    db.session.commit()
