#!/bin/bash
# ============================================================================
# EC2 Deployment Script — 2026 Asia Demo Crawl Voting System
# ============================================================================
# Usage: ssh into your EC2 instance, then run:
#   git clone https://github.com/gongnq/VoteSystem.git
#   cd VoteSystem
#   chmod +x deploy.sh
#   sudo ./deploy.sh
# ============================================================================

set -e

APP_DIR="/opt/votesystem"
APP_USER="votesystem"

echo "==> Installing system dependencies..."
apt-get update -y
apt-get install -y python3 python3-pip python3-venv git nginx

echo "==> Creating app user..."
id -u $APP_USER &>/dev/null || useradd -r -s /bin/false $APP_USER

echo "==> Setting up application directory..."
mkdir -p $APP_DIR
cp -r . $APP_DIR/
cd $APP_DIR

echo "==> Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo "==> Setting permissions..."
chown -R $APP_USER:$APP_USER $APP_DIR

echo "==> Creating systemd service..."
cat > /etc/systemd/system/votesystem.service << 'EOF'
[Unit]
Description=2026 Asia Demo Crawl Voting System
After=network.target

[Service]
User=votesystem
Group=votesystem
WorkingDirectory=/opt/votesystem
Environment="ADMIN_PIN=2026"
ExecStart=/opt/votesystem/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:5000 app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

echo "==> Creating nginx config..."
cat > /etc/nginx/sites-available/votesystem << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/votesystem /etc/nginx/sites-enabled/votesystem
rm -f /etc/nginx/sites-enabled/default

echo "==> Starting services..."
systemctl daemon-reload
systemctl enable votesystem
systemctl restart votesystem
nginx -t && systemctl restart nginx

echo ""
echo "============================================"
echo "  Deployment complete!"
echo "  App running at http://$(curl -s ifconfig.me)"
echo "  Admin PIN: 2026"
echo "============================================"
