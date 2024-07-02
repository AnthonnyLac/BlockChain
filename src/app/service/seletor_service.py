from ..models import Seletor, Transacao, Validador
import asyncio
import requests
from datetime import datetime, timedelta
import random
from flask import jsonify

transacoes_em_espera = {}

async def distribuir_transacoes_para_validadores(transacaoId):
    try:
        # Escolhe os validadores para a transação
        validadores = await escolher_validadores()
        
        if len(validadores) < 3:
            return False, "validadores insuficientes após espera. Operação cancelada!"

        # Lista para armazenar tarefas de envio de transação
        tasks = []

        # Envia a transação para os validadores escolhidos
        for validador in validadores:
            url = f"http://{validador.ip}/validador/process"
            
            data = {
                "transacaoId" : transacaoId,
                "validador_id" : validador.id,
                "chave_unica": validador.chave_unica
            }
            
            print(data)
            
            # Cria uma tarefa assíncrona para enviar a transação para cada validador
            task = asyncio.create_task(enviar_transacao_com_resposta(url, data))
            tasks.append(task)

        # Aguarda todas as tarefas completarem
        responses = await asyncio.gather(*tasks)

        # Verifica o consenso da transação baseado nas respostas dos validadores
        if verificar_consenso(responses):
            return True, "Transação aprovada pelos validadores."
        else:
            return False, "Transação não aprovada pelos validadores."

    except Exception as e:
        return False, str(e)

async def enviar_transacao_com_resposta(url, data):
    try:
        
        response = requests.post(url, json=data)
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



def verificar_consenso(responses) -> bool:
    """ Verifica o consenso baseado nas respostas dos validadores """

     # Conta o total de validadores e o número que aprovaram a transação
    total_validadores = len(responses)
    aprovacoes = sum(1 for response in responses if response and response.get('status') == 'aprovado')

    # Calcula a porcentagem de validadores que aprovaram
    porcentagem_aprovacao = (aprovacoes / total_validadores) * 100

    # Verifica se a transação é aprovada se mais de 50% dos validadores aprovarem
    if porcentagem_aprovacao > 50:
        return True
    else:
        return False

# Histórico de seleções para controlar a frequência
validador_historico = {}

async def escolher_validadores():
    """Escolhe os validadores para a transação"""

    # Busca os validadores disponíveis
    validadores_disponiveis = Validador.query.all()

    # Filtra validadores com saldo mínimo de 50 NoNameCoins e com menos de 3 flags
    validadores_disponiveis = [v for v in validadores_disponiveis if v.saldo >= 50 and v.flags < 3]

    # Verifica se há pelo menos três validadores disponíveis
    if len(validadores_disponiveis) < 3:
        print(f"validadores disponiveis: {len(validadores_disponiveis)}\nProcesso pausado")
        await asyncio.sleep(60)
            
        # Tentar novamente após um minuto
        # Busca os validadores disponíveis
        validadores_disponiveis = Validador.query.all()

        # Filtra validadores com saldo mínimo de 50 NoNameCoins e com menos de 3 flags
        validadores_disponiveis = [v for v in validadores_disponiveis if v.saldo >= 50 and v.flags < 3]
        
        if len(validadores_disponiveis) < 3:
            return False, "validadores insuficientes após espera. Operação cancelada!"
            
    # Ajusta a chance de escolha baseada nas flags
    validadores_com_peso = []
    for validador in validadores_disponiveis:
        peso = validador.saldo
        if validador.flags == 1:
            peso *= 0.5
        elif validador.flags == 2:
            peso *= 0.25
        
        validadores_com_peso.append((validador, peso))

    # Garantir que o percentual máximo de escolha de um validador seja de 20%
    total_peso = sum(peso for _, peso in validadores_com_peso)
    validadores_com_peso = [(v, min(peso, total_peso * 0.2)) for v, peso in validadores_com_peso]

    # Evitar selecionar o mesmo validador cinco vezes seguidas
    validadores_selecionados = []
    for validador, peso in validadores_com_peso:
        historico = validador_historico.get(validador.id, [])
        if len(historico) < 5 or all(x != 'selecionado' for x in historico[-5:]):
            validadores_selecionados.append((validador, peso))

    # Verifica se há pelo menos três validadores escolhidos
    if len(validadores_selecionados) < 3:
        # Coloca a transação em espera por até um minuto
        return []

    # Selecionar validadores com base no peso ajustado
    selecionados = random.choices(
        [v for v, _ in validadores_selecionados],
        [peso for _, peso in validadores_selecionados],
        k=3
    )

    # Atualizar histórico de seleções
    for validador in selecionados:
        if validador.id not in validador_historico:
            validador_historico[validador.id] = []
        validador_historico[validador.id].append('selecionado')
        if len(validador_historico[validador.id]) > 10:
            validador_historico[validador.id].pop(0)

    return selecionados