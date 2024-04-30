import pika
import redis
import os
import json
import time
from datetime import datetime, timedelta
from minio import Minio
from minio.error import S3Error
from io import BytesIO

# Configurações do RabbitMQ
RABBITMQ_HOST = 'rabbitmq'
QUEUE_NAME = 'transactionQueue'

# Configurações do Redis
REDIS_HOST = 'redis'
REDIS_PORT = 6379
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

# Configurações do MinIO
MINIO_URL = 'minio:9000'
ACCESS_KEY = os.environ.get('MINIO_ROOT_USER', 'minioadmin')
SECRET_KEY = os.environ.get('MINIO_ROOT_PASSWORD', 'minioadmin')
BUCKET_NAME = 'bucket-dadoscliente'

# Cliente MinIO
minio_client = Minio(
    MINIO_URL,
    access_key=ACCESS_KEY,
    secret_key=SECRET_KEY,
    secure=False
)

def generate_filename(transaction_data):
    # Extrai o timestamp e o utiliza para gerar um nome de arquivo único
    timestamp_str = transaction_data['datatransacao'].replace(':', '').replace('-', '').replace('+', '').replace(' ', '_')
    return f"{transaction_data['_id']}_{timestamp_str}.json"


def check_fraud(current_transaction, last_transaction):
    # Verifica se 'datatransacao' está presente em ambas as transações
    if 'datatransacao' not in current_transaction or 'datatransacao' not in last_transaction:
        print("Data de transação não encontrada em uma ou ambas as transações.")
        return False

    try:
        # Converte o timestamp da transação atual e da última transação para objetos datetime.
        current_time_str = current_transaction['datatransacao']
        last_time_str = last_transaction['datatransacao']

        # Remover o fuso horário da string de data e hora
        current_time_str = current_time_str[:-6]
        last_time_str = last_time_str[:-6]

        # Converter para objetos datetime
        current_time = datetime.strptime(current_time_str, "%Y-%m-%dT%H:%M:%S")
        last_time = datetime.strptime(last_time_str, "%Y-%m-%dT%H:%M:%S")

        # Verifica se a transação atual ocorreu em menos de duas horas desde a última transação.
        if current_time - last_time < timedelta(hours=2):
            # Se o endereço mudou, é considerado fraude.
            if current_transaction['endereco'] != last_transaction['endereco']:
                return True
    except Exception as e:
        print(f"Erro ao processar datas de transação: {e}")
    return False

def save_to_minio(transaction_data, is_fraud=False):
    
    try:
        # Certifique-se de que o bucket exista.
        if not minio_client.bucket_exists(BUCKET_NAME):
            minio_client.make_bucket(BUCKET_NAME)
        
        # Remove caracteres indesejados do timestamp e converte espaços e sinais para formar um nome de arquivo válido.
        timestamp_str = transaction_data['datatransacao'].replace(':', '').replace('-', '').replace('+', '').replace('T', '_').replace(' ', '_').replace('Z', '')
        
        # Adiciona prefixo se for fraude.
        fraud_prefix = "FRAUDE_DETECATADA_" if is_fraud else ""
        file_name = f"{fraud_prefix}{transaction_data['_id']}_{timestamp_str}.json"
        
        # Converte os dados da transação para JSON e bytes.
        data_bytes = json.dumps(transaction_data).encode('utf-8')
        data_stream = BytesIO(data_bytes)
        
        # Salva no MinIO.
        minio_client.put_object(
            BUCKET_NAME,
            file_name,
            data_stream,
            length=len(data_bytes),
            content_type='application/json'
        )
        
        print(f"Transaction data for transaction ID {transaction_data['_id']} saved to MinIO with the name {file_name}.")
    except S3Error as e:
        print(f"An error occurred while saving transaction data to MinIO: {str(e)}")
    finally:
        data_stream.close()


def save_fraud_to_minio(transaction_data):
    """
    Salva os dados da transação marcada como fraude no MinIO, incluindo o timestamp no nome do arquivo
    para garantir unicidade.
    """
    try:
        # Certifique-se de que o bucket exista.
        if not minio_client.bucket_exists(BUCKET_NAME):
            minio_client.make_bucket(BUCKET_NAME)
        
        # Extrai timestamp e usa no nome do arquivo para garantir unicidade
        timestamp_str = transaction_data['datatransacao'].replace(':', '').replace('-', '').replace(' ', '_')
        file_name = f"FRAUDE_DETECATADA_{transaction_data['_id']}_{timestamp_str}.json"
        
        # Converte os dados da transação para JSON e bytes.
        data_bytes = json.dumps(transaction_data).encode('utf-8')
        data_stream = BytesIO(data_bytes)
        
        # Salva no MinIO.
        minio_client.put_object(
            BUCKET_NAME,
            file_name,
            data_stream,
            length=len(data_bytes),
            content_type='application/json'
        )
        
        print(f"Fraudulent transaction data for transaction ID {transaction_data['_id']} saved to MinIO with the name {file_name}.")
    except S3Error as e:
        print(f"An error occurred while saving fraudulent transaction data to MinIO: {str(e)}")
    finally:
        data_stream.close()


def callback(ch, method, properties, body):
    transaction_data_list = json.loads(body)
    
    for transaction_data in transaction_data_list:
        transaction_id = transaction_data.get("_id")
        if transaction_id:
            last_transaction_str = redis_client.get(transaction_id)
            save_to_minio(transaction_data)  # Salva cada transação recebida como normal
            is_fraud_detected = False
            
            if last_transaction_str:
                last_transaction = json.loads(last_transaction_str)
                if check_fraud(transaction_data, last_transaction):
                    print(f"Fraud detected for transaction ID {transaction_id}.")
                    redis_client.set(f"fraud_{transaction_id}", "true", ex=7200)  # Expira em 2 horas
                    is_fraud_detected = True  # Marca a transação como fraude

            # Salva a transação como fraude se fraude foi detectada
            if is_fraud_detected:
                save_to_minio(transaction_data, is_fraud=True)
            
            # Atualiza com a última transação
            redis_client.set(transaction_id, json.dumps(transaction_data), ex=7200)
        
        ch.basic_ack(delivery_tag=method.delivery_tag)




def main():
    connection_params = pika.ConnectionParameters(host=RABBITMQ_HOST)
    
    # Loop de reconexão caso a conexão com o RabbitMQ seja perdida.
    while True:
        try:
            # Estabelece conexão com o RabbitMQ.
            connection = pika.BlockingConnection(connection_params)
            channel = connection.channel()
            
            # Declara a fila para garantir que ela exista.
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            
            # Informa ao RabbitMQ que o worker deseja receber mensagens da fila.
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
            
            # Inicia o consumo das mensagens.
            print(' [*] Waiting for messages. To exit press CTRL+C')
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError as e:
            print("Connection failed, trying to reconnect in 5 seconds...", str(e))
            time.sleep(5)
        except KeyboardInterrupt:
            print('Interrupted by user')
            try:
                if connection:
                    connection.close()
            except:
                pass
            break

if __name__ == '__main__':
    main()