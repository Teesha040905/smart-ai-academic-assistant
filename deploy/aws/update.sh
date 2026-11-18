#!/usr/bin/env bash
# Deploy the latest code from GitHub (run on the EC2 server): bash ~/app/deploy/aws/update.sh
set -euo pipefail
cd "$HOME/app"
git pull --ff-only
cd deploy/aws
sudo docker compose up -d --build
sudo docker image prune -f >/dev/null
echo "Updated. Status:"
sudo docker compose ps
