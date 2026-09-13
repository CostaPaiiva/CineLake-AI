# Declaração da saída (output) para exibir o IP público IPv4 da VPS
output "server_ip" {
  # Descrição explicativa da informação retornada por esta saída
  description = "IP público da VPS"
  # Obtém dinamicamente o endereço IPv4 atribuído à VPS criada no recurso hcloud_server
  value       = hcloud_server.cinelake.ipv4_address
}

# Declaração da saída (output) para exibir o identificador único (ID) da VPS
output "server_id" {
  # Descrição explicativa da informação retornada por esta saída
  description = "ID da VPS"
  # Obtém dinamicamente o ID atribuído pela Hetzner Cloud ao servidor criado
  value       = hcloud_server.cinelake.id
}

# Declaração da saída (output) para exibir o comando pronto de conexão SSH
output "ssh_command" {
  # Descrição explicativa da informação retornada por esta saída
  description = "Comando para conectar via SSH"
  # Monta a string do comando SSH interpolando o endereço IPv4 do servidor provisionado
  value       = "ssh root@${hcloud_server.cinelake.ipv4_address}"
}
