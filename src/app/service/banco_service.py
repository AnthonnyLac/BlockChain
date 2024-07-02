# services/banco_service.py
from datetime import datetime, timedelta
from .. import db, models
import requests
from flask import jsonify
import asyncio
from ..models import Cliente, Seletor, Transacao

# Dicionário para armazenar transações em espera
transacoes_em_espera = {}

async def distribuir_transacoes_para_seletor(transacaoId):
    try:
        # Simula a distribuição de transações para os seletores
        seletores = Seletor.query.all()

        print(f"quantidade de seletores cadastrados: {{len(seletores)}}")
        
        # Verificar se há pelo menos três seletores disponíveis
        if len(seletores) < 1:
            return False, "Seletores indisponíveis. Operação cancelada!"
        
        # Lista para armazenar tarefas de envio de transação
        tasks = []

        # Distribuir a transação para os seletores escolhidos
        for seletor in seletores:
            # Exemplo de como enviar a transação para o seletor via requisição HTTP
            url = f"http://{seletor.ip}/seletor/process"
            print(url)
            
            # Criar uma tarefa assíncrona para enviar a transação para cada seletor
            task = asyncio.create_task(enviar_transacao(url, transacaoId))
            tasks.append(task)

        # Aguardar todas as tarefas completarem
        await asyncio.gather(*tasks)

        return True, "Transação distribuída com sucesso para os seletores."

    except Exception as e:
        return False, str(e)

async def enviar_transacao(url, transacaoId):
    try:
        response = requests.post(url, json=transacaoId)
        if response.status_code == 200:
            print(f"Transação enviada com sucesso para {url}")
            print(response.json())
        else:
            print(f"Falha ao distribuir transação para {url}. Status code: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"Falha ao enviar transação para {url}. Erro: {str(e)}")
        return False

def create_transaction(remetente, recebedor, valor):
    transacao = Transacao(remetente=remetente, recebedor=recebedor, valor=valor, status=0, horario=datetime.now())
    db.session.add(transacao)
    db.session.commit()
    
    return transacao
