from . import db
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Cliente(db.Model):
    id: int
    nome: str
    senha: int
    qtdMoeda: int

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(20), unique=False, nullable=False)
    senha = db.Column(db.String(20), unique=False, nullable=False)
    qtdMoeda = db.Column(db.Integer, unique=False, nullable=False)

@dataclass
class Seletor(db.Model):
    id: int
    nome: str
    ip: str
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(20), unique=False, nullable=False)
    ip = db.Column(db.String(15), unique=False, nullable=False)

@dataclass
class Transacao(db.Model):
    id: int
    remetente: int
    recebedor: int
    valor: int
    horario : datetime
    status: int
    
    id = db.Column(db.Integer, primary_key=True)
    remetente = db.Column(db.Integer, unique=False, nullable=False)
    recebedor = db.Column(db.Integer, unique=False, nullable=False)
    valor = db.Column(db.Integer, unique=False, nullable=False)
    horario = db.Column(db.DateTime, unique=False, nullable=False)
    status = db.Column(db.Integer, unique=False, nullable=False)
    
@dataclass
class Validador(db.Model):
    id: int
    nome: str
    chave_unica: str
    saldo: int
    flags: int
    ip: str
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(20), unique=False, nullable=False)
    chave_unica = db.Column(db.String(50), unique=True, nullable=False)
    saldo = db.Column(db.Integer, unique=False, nullable=False)
    flags = db.Column(db.Integer, unique=False, nullable=False)
    ip = db.Column(db.String(15), unique=False, nullable=False)
    