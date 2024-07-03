# services/banco_service.py
from datetime import datetime, timedelta
from .. import db, models
import requests
from flask import jsonify
import asyncio
from ..models import Cliente, Seletor, Transacao
import aiohttp

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
            data = {
                "transacoesId" : transacaoId,
                "seletorId" : seletor.id
            }
            
            task = asyncio.create_task(enviar_transacao(url, data))
            tasks.append(task)

        # Aguardar todas as tarefas completarem
        result = await asyncio.gather(*tasks)

        print(result)
        

        return True, "Transação distribuída com sucesso para os seletores."

    except Exception as e:
        return False, str(e)
    
async def distribuir_transacoes_para_seletor_unit(transacaoId):
    try:
        # Simula a distribuição de transações para os seletores
        seletor = Seletor.query.first()

        # Exemplo de como enviar a transação para o seletor via requisição HTTP
        url = f"http://{seletor.ip}/seletor/process"
        print(url)
        
        # Criar uma tarefa assíncrona para enviar a transação para cada seletor
        data = {
            "transacoesId" : transacaoId,
            "seletorId" : seletor.id
        }
        
        result, mensagem = await enviar_transacao(url, data)
        
        print(f"url:{url}\nresponse enviar_transacao para seletor: {mensagem}")
        
        return result, mensagem

    except Exception as e:
        return False, str(e)

async def enviar_transacao(url, data):
  async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    try:
                        response_data = await response.json()
                        return True, response_data
                    except aiohttp.ContentTypeError:
                        error_text = await response.text()
                        return False, f"Falha ao distribuir transação para {url}. Tipo de conteúdo inesperado: {response.content_type}. Resposta: {error_text}"
                else:
                    error_text = await response.text()
                    return False, f"Falha ao distribuir transação para {url}.\nStatus code: {response.status}\nerror:{error_text}"
        except Exception as e:
            return False, f"Falha ao enviar transação para {url}. Erro: {str(e)}"

def create_transaction(remetente, recebedor, valor):
    transacao = Transacao(remetente=remetente, recebedor=recebedor, valor=valor, status=0, horario=datetime.now())
    db.session.add(transacao)
    db.session.commit()
    
    return transacao
