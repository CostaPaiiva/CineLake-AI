# Bloco principal de configuração do Terraform
terraform {
  # Define a versão mínima do Terraform necessária para executar este projeto (1.5.0 ou superior)
  required_version = ">= 1.5.0"

  # Declaração dos provedores (providers) necessários para a infraestrutura
  required_providers {
    # Configura o provedor da Hetzner Cloud
    hcloud = {
      # Origem oficial do plugin/provedor no Terraform Registry
      source  = "hetznercloud/hcloud"
      # Restrição de versão do provedor Hetzner Cloud (versão 1.45.x compatível)
      version = "~> 1.45"
    }
  }

  # Backend remoto (opcional). Descomente e configure quando tiver bucket S3/MinIO.
  # Configuração do estado remoto utilizando backend S3/MinIO
  # backend "s3" {
  #   # Nome do bucket onde o arquivo de estado (.tfstate) será armazenado
  #   bucket = "cinelake-terraform-state"
  #   # Caminho/chave dentro do bucket para identificar este arquivo de estado
  #   key    = "vps/terraform.tfstate"
  #   # Região do S3 (usado para compatibilidade com o protocolo S3)
  #   region = "us-east-1"
  #   # Endpoints customizados (utilizado quando usamos MinIO em vez do AWS S3)
  #   endpoints = {
  #     # URL do serviço MinIO/S3 customizado
  #     s3 = "https://minio.seudominio.com"
  #   }
  #   # Ignora a validação das credenciais da AWS (necessário para MinIO)
  #   skip_credentials_validation = true
  #   # Ignora a validação da região da AWS (necessário para MinIO)
  #   skip_region_validation      = true
  #   # Ignora a requisição do ID da conta AWS (necessário para MinIO)
  #   skip_requesting_account_id  = true
  #   # Força o uso do estilo de caminho (ex: domain.com/bucket em vez de bucket.domain.com)
  #   use_path_style              = true
  # }
}
