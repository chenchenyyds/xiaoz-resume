#!/usr/bin/env bash
# ============================================================
# SSL 证书申请(Let's Encrypt + 腾讯云 DNS 验证)
# ============================================================
# 用法:
#   1) 把 DNSPod/腾讯云 API Token 填到下面
#   2) bash scripts/deploy/ssl.sh
#
# 流程:
#   - 装 certbot + 腾讯云 DNS 插件
#   - 申请 *.yourdomain.com 泛域名证书
#   - 自动 reload nginx
#   - 加 systemd 定时器:每 60 天自动续期
# ============================================================
set -e

# ---------- 配置(改成你的)----------
DOMAIN="${DOMAIN:-resume.yourdomain.com}"
WILDCARD_DOMAIN="*.${DOMAIN#*.}"
TENCENT_SECRET_ID="${TENCENT_SECRET_ID:-your-secret-id}"
TENCENT_SECRET_KEY="${TENCENT_SECRET_KEY:-your-secret-key}"
EMAIL="${EMAIL:-admin@yourdomain.com}"

# ---------- 1. 装 certbot ----------
log() { echo -e "\033[0;32m[$(date '+%H:%M:%S')]\033[0m $1"; }
if ! command -v certbot &> /dev/null; then
    log "装 certbot..."
    apt-get update -y
    apt-get install -y certbot
fi

# ---------- 2. 用腾讯云 DNS API 验证 ----------
log "申请证书 $WILDCARD_DOMAIN ..."
# 注:首次需要交互输入,可以用 acme.sh 替代 certbot 解决全自动化
# 这里给最简方案:用 acme.sh
if ! command -v acme.sh &> /dev/null; then
    log "装 acme.sh..."
    curl https://get.acme.sh | sh
fi

export Tencent_SecretId="$TENCENT_SECRET_ID"
export Tencent_SecretKey="$TENCENT_SECRET_KEY"

~/.acme.sh/acme.sh --issue \
    --dns dns_tencent \
    -d "$WILDCARD_DOMAIN" \
    --accountemail "$EMAIL"

# ---------- 3. 安装证书到 nginx ----------
CERT_DIR="/etc/nginx/ssl"
mkdir -p "$CERT_DIR"
~/.acme.sh/acme.sh --install-cert -d "$WILDCARD_DOMAIN" \
    --key-file       "$CERT_DIR/privkey.pem" \
    --fullchain-file "$CERT_DIR/fullchain.pem" \
    --reloadcmd      "docker compose -f $(pwd)/docker-compose.yml restart nginx"

log "✓ 证书已装到 $CERT_DIR"

# ---------- 4. 改 nginx 配置启用 HTTPS ----------
log "修改 nginx 配置启用 HTTPS..."
cat > "$(pwd)/nginx/conf.d/ssl.conf" <<EOF
server {
    listen 443 ssl http2;
    server_name $DOMAIN *.$DOMAIN;

    ssl_certificate     $CERT_DIR/fullchain.pem;
    ssl_certificate_key $CERT_DIR/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    # ...其他复用 80 端口的 location...
}
EOF
log "  ⚠️  请手动合并 nginx.conf + ssl.conf,或用 nginx/conf.d/ 目录拆分"

# ---------- 5. 自动续期 ----------
log "配置自动续期(60 天)..."
cat > /etc/systemd/system/acme-renew.service <<EOF
[Unit]
Description=Renew SSL cert

[Service]
Type=oneshot
ExecStart=/root/.acme.sh/acme.sh --cron --home /root/.acme.sh
EOF

cat > /etc/systemd/system/acme-renew.timer <<EOF
[Unit]
Description=Daily renew SSL cert check

[Timer]
OnCalendar=daily
RandomizedDelaySec=1day
Persistent=true

[Install]
WantedBy=timers.target
EOF
systemctl daemon-reload
systemctl enable --now acme-renew.timer

log "🎉 SSL 证书配置完成,自动续期已启用"
