from ..models import Seletor, Transacao, Validador
import asyncio
import requests


async def distribuir_transacoes_para_validadores(transacao):
    try:
        # Escolhe os validadores para a transação
        validadores = escolher_validadores()

        # Verifica se há pelo menos três validadores disponíveis
        if len(validadores) < 3:
            return False, "Não há validadores suficientes disponíveis. Transação em espera."

        # Lista para armazenar tarefas de envio de transação
        tasks = []

        # Envia a transação para os validadores escolhidos
        for validador in validadores:
            url = f"http://{validador.ip}/validador/process"
            
            # Cria uma tarefa assíncrona para enviar a transação para cada validador
            task = asyncio.create_task(enviar_transacao_com_resposta(url, transacao))
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

async def enviar_transacao_com_resposta(url, transacaoId):
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

def escolher_validadores():
     """ Escolhe os validadores para a transação """

     # Busca os validadores disponíveis
     validadores_disponiveis = Validador.query.all()

     # Filtra validadores com saldo mínimo de 50 NoNameCoins
     validadores_disponiveis = [v for v in validadores_disponiveis if v.saldo >= 50]
     
     # Verifica se há pelo menos três validadores escolhidos
     if len(validadores_disponiveis) < 3:
         # Coloca a transação em espera por até um minuto
        return []

     return validadores_disponiveis