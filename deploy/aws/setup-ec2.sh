#!/usr/bin/env bash
# One-time setup of a fresh Ubuntu EC2 server for Smart AI Academic Assistant.
# Run on the server:
#   curl -fsSL https://raw.githubusercontent.com/Teesha040905/smart-ai-academic-assistant/main/deploy/aws/setup-ec2.sh | bash
set -euo pipefail

REPO_URL="https://github.com/Teesha040905/smart-ai-academic-assistant.git"
APP_DIR="$HOME/app"

echo "==> 1/5 Adding 2 GB swap (free-tier servers have only 1 GB RAM; building the app needs more)"
if ! sudo swapon --show | grep -q /swapfile; then
  sudo fallocate -l 2G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile >/dev/null
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
fi

echo "==> 2/5 Installing Docker"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sudo sh
fi
sudo systemctl enable --now docker

echo "==> 3/5 Downloading the code"
if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" pull --ff-only
else
  git clone "$REPO_URL" "$APP_DIR"
fi

echo "==> 4/5 Creating deploy/aws/.env"
cd "$APP_DIR/deploy/aws"
PUBLIC_IP="$(curl -fsS https://checkip.amazonaws.com | tr -d '[:space:]')"
DOMAIN="${PUBLIC_IP//./-}.sslip.io"
if [ ! -f .env ]; then
  cp .env.example .env
  JWT="$(openssl rand -base64 48 | tr -d '\n/+=' | cut -c1-64)"
  sed -i "s|^DOMAIN=.*|DOMAIN=${DOMAIN}|; s|^FRONTEND_URL=.*|FRONTEND_URL=https://${DOMAIN}|; s|^CORS_ORIGINS=.*|CORS_ORIGINS=https://${DOMAIN}|; s|^JWT_SECRET=.*|JWT_SECRET=${JWT}|" .env
  chmod 600 .env
fi

echo "==> 5/5 Done"
echo
echo "Your website address will be:  https://${DOMAIN}"
echo
echo "Next steps:"
echo "  1. nano ~/app/deploy/aws/.env      # fill MONGODB_URL and AI_API_KEYS, then Ctrl+O Enter Ctrl+X"
echo "  2. cd ~/app/deploy/aws && sudo docker compose up -d --build     # first build takes 10-15 min"
