import pika
import json
import os  # Importe o módulo os

# Lê as variáveis de ambiente
rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))
rabbitmq_user = os.getenv('RABBITMQ_USER', 'guest')
rabbitmq_password = os.getenv('RABBITMQ_PASSWORD', 'guest')

# Configuração dos parâmetros de conexão para apontar para o endereço e porta corretos do RabbitMQ no Minikube
connection_parameters = pika.ConnectionParameters(
    host=rabbitmq_host,
    #port=rabbitmq_port,
    #credentials=pika.PlainCredentials(rabbitmq_user, rabbitmq_password)
)

# Conexão com o RabbitMQ
connection = pika.BlockingConnection(connection_parameters)
channel = connection.channel()

# Declara o exchange do tipo Fanout chamado "exchange_transacoes"
channel.exchange_declare(exchange='exchange_transacoes', exchange_type='fanout')

# Declaração da fila
channel.queue_declare(queue='fila_processa_eventos')

# Faz o bind da fila ao exchange
channel.queue_bind(exchange='exchange_transacoes', queue='fila_processa_eventos')

# Função para enviar eventos para a fila
def enviar_evento_from_json(file_path):
    # Abre o arquivo JSON e carrega os dados
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    # Envia cada evento para a fila
    for evento in data:
        channel.basic_publish(exchange='exchange_transacoes', routing_key='', body=json.dumps(evento))  # Ajuste na routing_key para ''
        print(f"Evento enviado para a fila: {evento}")

# Exemplo de uso
enviar_evento_from_json('DadosFraude.json')

# Fechar conexão após o envio 
connection.close()