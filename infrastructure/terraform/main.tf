# Bloco de configuração do provedor Hetzner Cloud (hcloud)
provider "hcloud" {
  # Autentica na API da Hetzner utilizando o token definido na variável de entrada
  token = var.hcloud_token
}

# Chave SSH gerenciada pela Hetzner
# Recurso que registra a chave pública SSH no painel da Hetzner Cloud
resource "hcloud_ssh_key" "cinelake" {
  # Define o nome da chave SSH no painel combinando o nome do servidor com o sufixo '-key'
  name       = "${var.server_name}-key"
  # Lê o conteúdo do arquivo da chave pública no caminho informado, expandindo o atalho '~' se necessário
  public_key = file(pathexpand(var.ssh_public_key_path))
}

# Firewall
# Recurso que cria um Firewall virtual na Hetzner para controlar o tráfego de rede
resource "hcloud_firewall" "cinelake" {
  # Define o nome do Firewall no painel combinando o nome do servidor com o sufixo '-fw'
  name = "${var.server_name}-fw"

  # Regra de entrada para acesso via SSH
  rule {
    # Define a direção do tráfego de rede (entrada)
    direction = "in"
    # Define o protocolo de transporte de rede (TCP)
    protocol  = "tcp"
    # Porta de comunicação padrão para o serviço SSH
    port      = "22"
    # Restringe a origem dos IPs autorizados a conectar na porta SSH conforme variável
    source_ips = [var.allowed_ssh_cidr]
  }

  # Regra de entrada para tráfego web HTTP
  rule {
    # Define a direção do tráfego de rede (entrada)
    direction = "in"
    # Define o protocolo de transporte de rede (TCP)
    protocol  = "tcp"
    # Porta de comunicação padrão para tráfego web HTTP sem criptografia
    port      = "80"
    # Libera a porta 80 para qualquer endereço IP de origem (IPv4 e IPv6)
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  # Regra de entrada para tráfego web HTTPS
  rule {
    # Define a direção do tráfego de rede (entrada)
    direction = "in"
    # Define o protocolo de transporte de rede (TCP)
    protocol  = "tcp"
    # Porta de comunicação padrão para tráfego web seguro/criptografado HTTPS
    port      = "443"
    # Libera a porta 443 para qualquer endereço IP de origem (IPv4 e IPv6)
    source_ips = ["0.0.0.0/0", "::/0"]
  }
}

# VPS
# Recurso que cria e provisiona a máquina virtual (VPS) na Hetzner Cloud
resource "hcloud_server" "cinelake" {
  # Define o nome do servidor VPS conforme a variável
  name        = var.server_name
  # Define a imagem do sistema operacional a ser instalada na VPS (Ubuntu 22.04 LTS)
  image       = "ubuntu-22.04"
  # Define o plano/tamanho do servidor (quantidade de vCPU, RAM e SSD) conforme a variável
  server_type = var.server_type
  # Define a localização do datacenter onde a VPS será hospedada conforme a variável
  location    = var.location
  # Associa a chave SSH cadastrada anteriormente para permitir o login do usuário root
  ssh_keys    = [hcloud_ssh_key.cinelake.id]
  # Vincula o Firewall criado para proteger a VPS com as regras de portas definidas
  firewall_ids = [hcloud_firewall.cinelake.id]

  # Passa o script/arquivo de inicialização cloud-init para pré-configurar a VPS no primeiro boot
  user_data = file("${path.module}/cloud-init.yaml")

  # Mapeamento de tags/etiquetas organizacionais para identificação do servidor
  labels = {
    # Etiqueta indicando o nome do projeto
    project = "cinelake"
    # Etiqueta indicando o ambiente de implantação
    env     = "production"
  }
}
