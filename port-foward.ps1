# Script para fazer port-forward de todos os pods em um namespace

# Obtém os nomes dos pods usando kubectl
$pods = kubectl get pods -n projetoadamod3 --no-headers | ForEach-Object {
    $_.Split(" ")[0]
}

# Define o mapeamento de portas para cada tipo de pod
$portMappings = @{
    "minio" = "9000:9000 9001:9001"
    "rabbitmq-deployment" = "15672:15672 5672:5672"
    "redis" = "6379:6379"
}

# Faz o port-forward para cada pod
foreach ($pod in $pods) {
    # Encontra o mapeamento de porta correto com base no nome do pod
    foreach ($key in $portMappings.Keys) {
        if ($pod -like "*$key*") {
            $ports = $portMappings[$key]
            break
        }
    }

    # Inicia o port-forward em background se portas foram encontradas
    if ($ports) {
        $scriptBlock = [scriptblock]::Create("kubectl port-forward $pod $ports -n projetoadamod3")
        Start-Job -ScriptBlock $scriptBlock
        Write-Host "Iniciando port-forward para $pod nas portas $ports"
    }
}

# Lista todos os jobs para verificação
Get-Job
