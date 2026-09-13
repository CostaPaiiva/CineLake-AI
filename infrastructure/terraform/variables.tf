# Definição da variável para o token de autenticação da API da Hetzner Cloud
variable "hcloud_token" {
  # Descrição em texto explicativo sobre a finalidade da variável
  description = "Token de API da Hetzner Cloud"
  # Tipo de dado esperado pela variável (texto/string)
  type        = string
  # Marca a variável como sensível para omitir seu valor dos logs do Terraform
  sensitive   = true
}

# Definição da variável para o nome da máquina virtual (VPS)
variable "server_name" {
  # Descrição em texto explicativo sobre a finalidade da variável
  description = "Nome da VPS"
  # Tipo de dado esperado pela variável (texto/string)
  type        = string
  # Valor padrão utilizado caso nenhum outro seja informado
  default     = "cinelake-vps"
}

# Definição da variável para o tipo/plano do servidor (CPU, memória e disco)
variable "server_type" {
  # Descrição em texto explicativo sobre a finalidade da variável
  description = "Tipo da VPS (CPU, RAM, disco)"
  # Tipo de dado esperado pela variável (texto/string)
  type        = string
  # Valor padrão correspondente ao plano de entrada na Hetzner (cx22)
  default     = "cx22"
}

# Definição da variável para a localização geográfica do datacenter da Hetzner
variable "location" {
  # Descrição em texto explicativo sobre a finalidade da variável
  description = "Localização do datacenter"
  # Tipo de dado esperado pela variável (texto/string)
  type        = string
  # Valor padrão correspondente ao datacenter de Nuremberg, Alemanha (nbg1)
  default     = "nbg1"
}

# Definição da variável para o caminho do arquivo de chave pública SSH local
variable "ssh_public_key_path" {
  # Descrição em texto explicativo sobre a finalidade da variável
  description = "Caminho da chave pública SSH"
  # Tipo de dado esperado pela variável (texto/string)
  type        = string
  # Valor padrão com o caminho padrão da chave SSH ED25519 no sistema do usuário
  default     = "~/.ssh/id_ed25519.pub"
}

# Definição da variável para a faixa de IPs (CIDR) com permissão de acesso via SSH
variable "allowed_ssh_cidr" {
  # Descrição em texto explicativo sobre a finalidade da variável
  description = "CIDR autorizado a acessar SSH"
  # Tipo de dado esperado pela variável (texto/string)
  type        = string
  # Valor padrão liberando acesso SSH para qualquer endereço IP (0.0.0.0/0)
  default     = "0.0.0.0/0"
}
