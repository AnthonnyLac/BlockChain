from ..models import Seletor, Transacao, Validador
import asyncio
import requests
from datetime import datetime, timedelta
import random
from flask import jsonify
from .. import db
from .. import services
import aiohttp



transacoes_em_espera = {}

async def distribuir_transacoes_para_validadores(seletorId, transacaoId):
    try:
        print("\ndistribuir_transacoes_para_validadores")
        # Escolhe os validadores para a transação
        validadores = await escolher_validadores()
        
        if len(validadores) < 3:
            return False, "validadores insuficientes após espera. Operação cancelada!"

        
        # Lista para armazenar tarefas de envio de transação
        tasks = []
        
        result, taxa = calcular_taxa(transacaoId, validadores)
        
        if(result == False):
            return False, "Erro ao calcular taxa. Operação cancelada!"

        # Envia a transação para os validadores escolhidos
        for validador in validadores:
            
            url = f"http://{validador.ip}/validador/process"
            
            data = {
                "transacaoId" : transacaoId,
                "validador_id" : validador.id,
                "chave_unica": validador.chave_unica,
                "taxa" : taxa
            }
            
            print(data)
            
            # Cria uma tarefa assíncrona para enviar a transação para cada validador
            task = asyncio.create_task(enviar_transacao_com_resposta(url, data))
            tasks.append(task)

        # Aguarda todas as tarefas completarem
        responses = await asyncio.gather(*tasks)
        

        # Verifica o consenso da transação baseado nas respostas dos validadores
        if verificar_consenso(responses):
            print("verificar_consenso")
            
            transacao = services.get_transaction_by_id(transacaoId)
            iniciar_pagamento(transacao, validadores=validadores, selectorId=seletorId)
            
            return True, "Transação aprovada pelos validadores."
        else:
            return False, "Transação não aprovada pelos validadores."
        
    except Exception as e:
        return False, str(e)

async def enviar_transacao_com_resposta(url, data):
    async with aiohttp.ClientSession() as session:
        try:
            print(f"Enviando dados para {url}: {data}")
            async with session.post(url, json=data) as response:
                print(f"Recebida resposta de {url}: {response.status}")
                if response.status == 200:
                    response_data = await response.json()
                    print(f"Resposta JSON recebida: {response_data}")
                    return response_data
                else:
                    return {"status": "erro", "mensagem": f"Falha ao enviar para {url}, código de status: {response.status}"}
        except Exception as e:
            print(f"Erro ao enviar transação para {url}: {str(e)}")
            return {"status": "erro", "mensagem": str(e)}



def verificar_consenso(responses) -> bool:
    """ Verifica o consenso baseado nas respostas dos validadores """

    print("\nverificando consenso")
    
     # Conta o total de validadores e o número que aprovaram a transação
    total_validadores = len(responses)
    aprovacoes = sum(1 for response in responses if response and response.get('status') == 1)

    # Calcula a porcentagem de validadores que aprovaram
    porcentagem_aprovacao = (aprovacoes / total_validadores) * 100

    print(f"porcentagem_aprovacao: {porcentagem_aprovacao}\n")
    
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


def calcular_taxa(transacaoId, validadores):
    """
    Calcula a taxa total retida pelo sistema (seletor e validadores) da transação com base nos critérios estabelecidos.
    
    Args:
    - transacaoId: ID da transação que está sendo processada.
    - validadores: Lista de validadores selecionados para a transação, contendo objetos Validador.

    Returns:
    - float: O valor total retido pelo sistema (seletor e validadores).
    """
    try:
        # Busca a transação pelo ID para obter o valor
        transacao = Transacao.query.get(transacaoId)
        if not transacao:
            raise ValueError("Transação não encontrada.")
        
        valor_transacao = transacao.valor
        
        # Calcula a taxa total retida pelo sistema
        taxa_seletor = valor_transacao * 0.015  # 1,5% para o seletor
        taxa_validador = valor_transacao * 0.005  # 0,5% para cada validador
        taxa_total_retida = taxa_seletor + (len(validadores) * taxa_validador)
        
        # Retorna o valor total retido pelo sistema
        return True, taxa_total_retida
    
    except Exception as e:
        print(f"Erro ao calcular taxa: {str(e)}")
        return False, str(e)
    

def iniciar_pagamento(transacao, validadores, selectorId):
    """ Inicia o pagamento ao seletor, validadores, remetente e recebedor com base na porcentagem de aprovação """

    # Valor total da transação
    valor_transacao = transacao.valor
    
    # Calcula as taxas retidas pelo sistema
    taxa_seletor = valor_transacao * 0.015  # 1,5% para o seletor
    taxa_validador = valor_transacao * 0.005  # 0,5% para cada validador

    # Exemplo de como realizar o pagamento ao seletor
    seletor = services.get_selector_by_id(selectorId)  # Exemplo: busca o primeiro seletor no banco de dados
    if seletor:
        seletor.saldo += round(taxa_seletor,2)
        print(f"Pagamento iniciado ao seletor {seletor.nome}. Valor: {taxa_seletor} NoNameCoins.")

    # Exemplo de como realizar o pagamento aos validadores
    for validador in validadores:
        validador.saldo += taxa_validador
        db.session.commit()
        print(f"Pagamento iniciado ao validador {validador.nome}. Valor: {taxa_validador} NoNameCoins.")

    # Atualiza as contas do remetente e do recebedor
    
    
    remetente = services.get_client_by_id(transacao.remetente)
    recebedor = services.get_client_by_id(transacao.recebedor)

    # Calcula o valor líquido a ser recebido pelo recebedor
    valor_recebedor = valor_transacao - taxa_seletor - (len(validadores) * taxa_validador)

    # Subtrai o valor da transação mais as taxas da conta do remetente
    remetente.qtdMoeda -= round(valor_transacao + taxa_seletor + (len(validadores) * taxa_validador),2)
    print(f"Valor da transação e taxas deduzidos da conta do remetente {remetente.nome}. Valor total: {valor_transacao + taxa_seletor + (len(validadores) * taxa_validador)} NoNameCoins.")

    # Adiciona o valor líquido da transação à conta do recebedor
    recebedor.qtdMoeda += round(valor_recebedor,2)
    print(f"Valor líquido da transação creditado na conta do recebedor {recebedor.nome}. Valor: {valor_recebedor} NoNameCoins.")
    
    db.session.commit()
    
