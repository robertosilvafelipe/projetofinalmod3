# **Projeto: Implementação Kubernetes para Detecção de Fraudes Bancárias**

## **Requisitos**

1. **Kubernetes Cluster**: Configuração de um cluster Kubernetes que hospedará todos os componentes do sistema, incluindo a aplicação de detecção de fraudes, Redis, RabbitMQ, e Minio.
2. **Deployment de Serviços**:
    - Crie deployments Kubernetes para cada um dos serviços mencionados, garantindo que eles possam ser escalados horizontalmente conforme necessário.
    - Utilize ConfigMaps e Secrets para gerenciar configurações sensíveis e não-sensíveis separadamente.
3. **Persistência de Dados**:
    - Implemente Persistent Volumes (PVs) e Persistent Volume Claims (PVCs) para garantir a persistência de dados críticos, como o armazenamento de objetos do Minio e a base de dados do Redis.
4. **Network e Exposição de Serviços**:
    - Defina e configure adequadamente os serviços Kubernetes (LoadBalancers, NodePorts, etc.) para garantir a comunicação eficaz entre os componentes do sistema e a exposição segura da aplicação ao mundo externo.
5. **Documentação**:
    - Forneça uma documentação detalhada do projeto, incluindo a arquitetura do sistema, como configurar e lançar o cluster Kubernetes, e como escalar os serviços conforme necessário.

## **Entrega**

O projeto deve ser entregue em um repositório no GitHub contendo todos os arquivos de configuração do Kubernetes, scripts de deploy, e a documentação. A documentação deve incluir instruções passo a passo sobre como configurar o ambiente, implantar a aplicação, e validar a implementação.

## **Opcional**

- Uso de Helm Charts para empacotamento das aplicações
- Implemente soluções de monitoramento e logging para acompanhar o estado do cluster e dos aplicativos, facilitando a detecção e a solução de problemas.

## **Avaliação**

Os projetos serão avaliados com base na correta implementação dos requisitos, na qualidade da documentação fornecida, e na eficácia com que o sistema implementado atende às demandas de escalabilidade, disponibilidade, e resiliência em um ambiente de produção real.



## 1º Parte

- Subir cluster minikube
### **Parte 1: Iniciando o Cluster Minikube com 3 Nós**

**Objetivo**: Subir um cluster Minikube com um nó de controle e dois nós worker.

**Comando**:

```bash
minikube start --nodes 3
```

**Explicação**:
Este comando inicializa o Minikube com um total de 3 nós: um nó de controle (control-plane) e dois nós worker. O Minikube automaticamente configura o primeiro nó como control-plane e os demais como nós worker.

O termo "control-plane" em um contexto de cluster Kubernetes refere-se ao conjunto de componentes que gerenciam o estado do cluster, decisões de orquestração e configurações.

### **Parte 2: Verificando o Estado dos Nós**

Após a criação do cluster, é importante verificar se todos os nós estão funcionando corretamente.

**Comando**:

```bash
kubectl get nodes
```

**Explicação**:
Este comando lista todos os nós no cluster junto com seu status, roles, idade e versão do Kubernetes. Ele permite verificar rapidamente se todos os nós estão no estado **`Ready`**, o que indica que eles estão configurados corretamente e operacionais.

### **Parte 3: Verificando as Métricas do Cluster**

Para obter métricas detalhadas sobre o uso de recursos por cada nó, como CPU e memória, precisamos garantir que o **`metrics-server`** esteja habilitado e funcionando.

**Habilitar Metrics-Server**:

```bash
minikube addons enable metrics-serv
```

**Explicação**:
Este comando ativa o addon **`metrics-server`** no Minikube, que é necessário para coletar métricas de uso de recursos dos nós e pods.

**Comando para Verificar Métricas dos Nós**:

```bash
kubectl top nodes
```

**Explicação**:
Este comando mostra o uso de CPU e memória para cada nó no cluster. É útil para monitorar a saúde do sistema e a utilização de recursos.

### **Parte 4: Verificando a Saúde do Cluster**

Para uma inspeção mais aprofundada da saúde do cluster, você pode utilizar o comando de verificação de saúde.

**Comando**:

```bash
kubectl get componentstatus
```

**Explicação**:
Este comando verifica o status dos componentes principais do cluster, como o scheduler e o controller-manager. Isso ajuda a identificar quaisquer problemas com os componentes críticos do Kubernetes.

Para garantir que seu arquivo de deployment do Redis rode especificamente nos nodes workers e não no control-plane (neste caso, o **`minikube`** é o control-plane e **`minikube-m02`** e **`minikube-m03`** são os workers), você pode utilizar a funcionalidade de **taints and tolerations** do Kubernetes, juntamente com **node affinity**.

você precisa garantir que o node control-plane (**`minikube`**) tenha um taint que previna que os pods sejam agendados nele

```bash
kubectl taint nodes minikube key=value:NoSchedule
kubectl taint nodes minikube-m02 worker=true:NoSchedule
kubectl taint nodes minikube-m03 worker=true:NoSchedule
```

Verificando se o taints foi aplicado:

```bash
kubectl describe node minikube | Select-String -Pattern "Taints"

Taints:             key=value:NoSchedule

kubectl describe node minikube-m02 | Select-String -Pattern "Taints"

Taints:             worker=true:NoSchedule

kubectl describe node minikube-m03 | Select-String -Pattern "Taints"

Taints:             worker=true:NoSchedule
```

### **Verificar a Tolerância**

Depois de aplicar a configuração, você pode verificar se o pod do MinIO foi de fato agendado em um nó com o taint correspondente:

```bash

kubectl get pods -o wide -n projetoadamod3
```



## 2º Parte

- Aplicar os deployments dos serviços:

  Redis 

Aplicar o yaml 

```go
kubectl apply -f redis-deployment.yaml

Output:
statefulset.apps/redis created
persistentvolumeclaim/redis-pvc created
service/redis-svc created
```

Verificar o StatefulSet:

```go
kubectl get statefulsets

NAME    READY   AGE
redis   0/1     86s
```

Verificar PersistentVolumeClaim (PVC):

```go
kubectl get pvc

NAME        STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
redis-pvc   Pending                                      local-path     98s
```

```go
kubectl get services

NAME               TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
kubernetes         ClusterIP      10.96.0.1        <none>        443/TCP        7d1h
nginx-deployment   LoadBalancer   10.109.122.30    <pending>     80:31032/TCP   7d1h
nginx-service      NodePort       10.105.179.110   <none>        80:32269/TCP   2d9h
redis-svc          ClusterIP      10.110.148.13    <none>        6379/TCP       2m10s
```

Para acessar o Redis dentro do cluster, você pode usar o comando **`kubectl port-forward`**. 

```go
kubectl port-forward svc/redis-svc 6379:6379

kubectl port-forward svc/redis-svc 6379:6379 > /dev/null 2>&1 &

Id     Name            PSJobTypeName   State         HasMoreData     Location             Command
--     ----            -------------   -----         -----------     --------             -------
1      Job1            BackgroundJob   Running       True            localhost            kubectl port-forward svc…
```

**Testar o Redis**:

```go
kubectl exec -it redis-0 -- redis-cli PING

PONG
```

Você pode listar todos os StatefulSets com o seguinte comando:

```bash
kubectl get statefulsets

NAME    READY   AGE
redis   2/2     6d12h
```

você pode escalar para qualquer valor de statefulset com este comando:

```bash
kubectl scale statefulsets redis --replicas=0

statefulset.apps/redis scaled
```

você pode verificar se os pods foram criados e estão rodando corretamente com:

```bash
kubectl get pods -l app=redis
```

Se você quiser ver os detalhes e o status atualizado do StatefulSet, você pode usar:

```bash
kubectl get statefulset redis
```


RabbitMQ

aplicar o yaml

```go
kubectl apply -f rabbitmq-deployment.yaml

deployment.apps/rabbitmq-deployment created
service/rabbitmq-service created
```

Acessar o serviço 

```go
kubectl get svc rabbitmq-service

NAME               TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)                          AGE
rabbitmq-service   LoadBalancer   10.107.52.63   <pending>     15672:30001/TCP,5672:30002/TCP   2d12h
```

**Identifique o Pod do RabbitMQ**

```bash
kubectl get pods -l app=rabbitmq

NAME                                   READY   STATUS    RESTARTS      AGE
rabbitmq-deployment-794df9f4d8-x47mw   1/1     Running   1 (48m ago)   2d12h
```

Fazer o port-foward 

```bash
nohup kubectl port-forward pod/rabbitmq-deployment-1234567890-abcde 15672:15672 &

Id     Name            PSJobTypeName   State         HasMoreData     Location             Command
--     ----            -------------   -----         -----------     --------             -------
3      Job3            BackgroundJob   Running       True            localhost            nohup kubectl port-f…
```

Para abrir o RabbitMQ Management UI no seu navegador, execute:

```

minikube service rabbitmq-service

|-----------|------------------|------------------|---------------------------|
| NAMESPACE |       NAME       |   TARGET PORT    |            URL            |
|-----------|------------------|------------------|---------------------------|
| default   | rabbitmq-service | management/15672 | http://192.168.49.2:30001 |
|           |                  | amqp/5672        | http://192.168.49.2:30002 |
|-----------|------------------|------------------|---------------------------|
🏃  Starting tunnel for service rabbitmq-service.
|-----------|------------------|-------------|------------------------|
| NAMESPACE |       NAME       | TARGET PORT |          URL           |
|-----------|------------------|-------------|------------------------|
| default   | rabbitmq-service |             | http://127.0.0.1:49798 |
|           |                  |             | http://127.0.0.1:49799 |
|-----------|------------------|-------------|------------------------|
[default rabbitmq-service  http://127.0.0.1:49798
http://127.0.0.1:49799]
```

Verificar logs 

```go
kubectl logs -l app=rabbitmq
```

 
Miniio

Apply

```yaml
kubectl apply -f minio-deployment.yaml

persistentvolumeclaim/minio-pvc unchanged
deployment.apps/minio unchanged
service/minio created
```

Verificar portas 

```bash
kubectl get service minio

NAME    TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)                         AGE
minio   NodePort   10.106.99.40   <none>        9000:31252/TCP,9001:32733/TCP   45s
```

```bash
kubectl get pods

minio-65b97566fb-nxxjn                 1/1     Running            0             14m
nginx1-17                              0/1     ImagePullBackOff   0             12d
nginx1-18                              0/1     ImagePullBackOff   0             12d
rabbitmq-deployment-794df9f4d8-x47mw   1/1     Running            1 (15m ago)   2d12h
redis-0                                1/1     Running            4 (15m ago)   6d12h
```

Rodar o port-foward para acessar o serviço localmente

```powershell
nohup kubectl port-forward pod/minio-65b97566fb-nxxjn 9000:9000 9001:9001 &

Id     Name            PSJobTypeName   State         HasMoreData     Location             Command
--     ----            -------------   -----         -----------     --------             -------
1      Job1            BackgroundJob   Running       True            localhost            nohup kubectl port-forwa… 
```

![image](https://github.com/robertosilvafelipe/projetofinalmod3/assets/101230256/f5ddf63b-e3ac-45f8-ac6e-42ca10b45bd9)




## Verificar se os serviços estão no ar

```bash
kubectl get pods
NAME                                   READY   STATUS    RESTARTS      AGE
minio-65b97566fb-nxxjn                 1/1     Running   3 (80m ago)   3h26m
rabbitmq-deployment-794df9f4d8-bs65h   1/1     Running   0             40s
redis-0                                1/1     Running   0             40s
```

Verificar distrbuição dos pods 

```bash
kubectl get pods -o wide
```


# Configurar o port-foward para subida dos serviços

```bash
.\port-foward.ps1
```



