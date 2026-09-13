# Nginx + TLS

## Pré-requisitos

- Domínio apontando para o IP da VPS (registro DNS tipo A).
- Portas 80 e 443 liberadas no firewall (UFW / Hetzner Cloud Firewall).

## Obter certificado Let's Encrypt

Use Certbot em modo standalone (fora do Docker) ou via webroot.

### Opção 1: Certbot no host (Standalone)

```bash
sudo apt install -y certbot
sudo certbot certonly --standalone -d cinelake.seudominio.com
```

Os certificados gerados ficam armazenados em `/etc/letsencrypt/live/cinelake.seudominio.com/`.

Copie os certificados para a pasta `infrastructure/nginx/certs/` mapeada no Docker:

```bash
sudo cp /etc/letsencrypt/live/cinelake.seudominio.com/fullchain.pem infrastructure/nginx/certs/
sudo cp /etc/letsencrypt/live/cinelake.seudominio.com/privkey.pem infrastructure/nginx/certs/
sudo chown -R $USER:$USER infrastructure/nginx/certs/
```

### Inicialização do Nginx

Após disponibilizar os certificados na pasta:

```bash
docker compose up -d nginx
```

## Renovação Automática

Os certificados Let's Encrypt têm validade de 90 dias. Para renovar automaticamente via cron:

```bash
sudo crontab -e
```

Adicione a linha de agendamento:

```text
0 3 * * * certbot renew --quiet && docker restart cinelake-nginx
```

## Sem Domínio

Se você não tiver um domínio próprio, configure o Nginx apenas na porta 80 (sem TLS) e mantenha o acesso seguro a dashboards sensíveis (como Grafana, MinIO e MLflow) através de túneis SSH:

```bash
ssh -L 3000:localhost:3000 -L 5000:localhost:5000 usuario@IP_DA_SUA_VPS
```

