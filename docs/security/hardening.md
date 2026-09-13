# Hardening da VPS

## Atualização de pacotes e ferramentas de segurança

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y ufw fail2ban unattended-upgrades
```

## Firewall (UFW)

- Apenas portas 22, 80 e 443 abertas.
- Todo o tráfego restante de entrada é bloqueado por padrão.

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
```

## Fail2ban

- Bane automaticamente endereços IP após tentativas repetidas e falhas de login via SSH.
- Configuração personalizada em `/etc/fail2ban/jail.local`.

```bash
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## Atualizações automáticas de segurança

- `unattended-upgrades` instalado e ativado para patches contínuos do sistema operacional.

```bash
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

## Acesso SSH

- Desabilitar autenticação por senha (permitir apenas chaves SSH públicas como ED25519 ou RSA).
- Desabilitar login direto do usuário root quando houver usuário sudoer configurado.

## Segurança em Containers Docker

- Executar serviços com usuários não-root dedicados sempre que possível.
- Definir limites de uso de hardware (`cpu_limit`, `mem_limit`) nos arquivos compose.
- Não expor portas internas de banco de dados ou mensageria diretamente para a internet aberta (manter na rede virtual interna do Docker).
