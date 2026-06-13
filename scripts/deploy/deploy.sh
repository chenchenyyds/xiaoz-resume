#!/usr/bin/env bash
# ============================================================
# 小Z简历 - 腾讯云轻量应用服务器一键部署
# ============================================================
# 适用:腾讯云轻量 4C8G(¥200/月)Ubuntu 22.04
#
# 用法:
#   1) ssh ubuntu@<your-server-ip>
#   2) git clone <repo> /opt/xiaoz && cd /opt/xiaoz/代码
#   3) cp backend/.env.example backend/.env && nano backend/.env  # 填生产配置
#   4) cp scripts/deploy/env.production.example scripts/deploy/env.production
#   5) bash scripts/deploy/deploy.sh
#
# 脚本会做:
#   ✓ 装 Docker + Docker Compose
#   ✓ 配置 swap(2G,小内存防 OOM)
#   ✓ 装防火墙(只开 80/443/22)
#   ✓ 配置 fail2ban(防 SSH 爆破)
#   ✓ 配置 logrotate(日志切割)
#   ✓ 拉起 5 服务 + nginx
#   ✓ 配置 systemd 自启动
#   ✓ 打印健康检查结果
# ============================================================
set -e
set -u

# ---------- 路径 ----------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

# ---------- 颜色 ----------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"; }
warn() { echo -e "${YELLOW}[$(date '+%H:%M:%S')]${NC} $1"; }
err() { echo -e "${RED}[$(date '+%H:%M:%S')]${NC} $1"; exit 1; }

# ---------- 检查 root ----------
if [ "$EUID" -ne 0 ]; then
    err "请用 root 运行: sudo bash $0"
fi

# ---------- 检查环境 ----------
log "检查环境..."
if ! command -v lsb_release &> /dev/null; then
    warn "未检测到 lsb_release,假设是 Ubuntu 22.04"
fi
if [ ! -f "backend/.env" ]; then
    err "未找到 backend/.env,请先 cp .env.example .env 并填生产配置"
fi

# ---------- 1. 装 Docker ----------
log "[1/8] 装 Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl enable --now docker
    rm get-docker.sh
    log "  ✓ Docker 装好"
else
    log "  ↻ Docker 已装: $(docker --version)"
fi

# ---------- 2. 装 Docker Compose plugin ----------
log "[2/8] 装 Docker Compose plugin..."
if ! docker compose version &> /dev/null; then
    apt-get update -y
    apt-get install -y docker-compose-plugin
    log "  ✓ Docker Compose 装好"
else
    log "  ↻ Docker Compose 已装: $(docker compose version)"
fi

# ---------- 3. 配置 swap(防 OOM)----------
log "[3/8] 配置 2G swap..."
if [ ! -f /swapfile ]; then
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    log "  ✓ swap 配置完成(2G)"
else
    log "  ↻ swap 已存在"
fi

# ---------- 4. 配置防火墙 ----------
log "[4/8] 配置防火墙(只开 22/80/443)..."
if command -v ufw &> /dev/null; then
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow 22/tcp   # SSH
    ufw allow 80/tcp   # HTTP
    ufw allow 443/tcp  # HTTPS
    ufw --force enable
    log "  ✓ ufw 已启用: 22/80/443"
else
    warn "  ufw 未装,跳过"
fi

# ---------- 5. 装 fail2ban(防 SSH 爆破)----------
log "[5/8] 装 fail2ban..."
if ! command -v fail2ban-client &> /dev/null; then
    apt-get install -y fail2ban
    cat > /etc/fail2ban/jail.local <<EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
EOF
    systemctl enable --now fail2ban
    log "  ✓ fail2ban 已启用"
else
    log "  ↻ fail2ban 已装"
fi

# ---------- 6. 配置 logrotate(日志切割)----------
log "[6/8] 配置 logrotate..."
mkdir -p /var/log/xiaoz
cat > /etc/logrotate.d/xiaoz <<EOF
/var/log/xiaoz/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 root root
    sharedscripts
    postrotate
        docker compose -f $PROJECT_ROOT/docker-compose.yml restart backend > /dev/null 2>&1 || true
    endscript
}
EOF
log "  ✓ logrotate 已配(保留 14 天)"

# ---------- 7. 拉起服务 ----------
log "[7/8] docker compose up..."
docker compose pull || true  # 镜像不存在时跳过
docker compose build --no-cache
docker compose up -d
log "  ✓ 5 服务已起"

# ---------- 8. 健康检查 ----------
log "[8/8] 健康检查..."
sleep 8
echo ""
docker compose ps
echo ""

# 测后端
if curl -fsS http://localhost:8000/health > /dev/null 2>&1; then
    log "  ✓ 后端 health OK"
    curl -s http://localhost:8000/health | python3 -m json.tool
else
    err "  ✗ 后端 health 失败,看日志: docker compose logs backend"
fi

# 测 DB
DB_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' xiaoz-db 2>/dev/null || echo "unknown")
[ "$DB_HEALTH" = "healthy" ] && log "  ✓ DB healthy" || warn "  ⚠ DB 状态: $DB_HEALTH"

# 测 Redis
REDIS_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' xiaoz-redis 2>/dev/null || echo "unknown")
[ "$REDIS_HEALTH" = "healthy" ] && log "  ✓ Redis healthy" || warn "  ⚠ Redis 状态: $REDIS_HEALTH"

# ---------- 9. 配 systemd(服务器重启后自动起)----------
log "[9/9] 配置 systemd 自启动..."
cat > /etc/systemd/system/xiaoz.service <<EOF
[Unit]
Description=Xiaoz Resume SaaS
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_ROOT
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable xiaoz.service
log "  ✓ xiaoz.service 已 enable"

# ---------- 总结 ----------
echo ""
echo "================================================"
log "🎉 部署完成!"
echo "================================================"
echo ""
echo "  用户端:http://<your-server-ip>/"
echo "  后台:  http://<your-server-ip>/admin/"
echo "  API:   http://<your-server-ip>/api/docs"
echo ""
echo "  后续:"
echo "  - 申请 SSL 证书:bash scripts/deploy/ssl.sh  (Let's Encrypt)"
echo "  - 看日志:bash scripts/deploy/logs.sh"
echo "  - 备份:bash scripts/deploy/backup.sh"
echo "  - 升级:bash scripts/deploy/deploy.sh  (再跑一次)"
echo ""
echo "  ⚠️  别忘了:"
echo "  - 备案(国内必须,7-20 天)"
echo "  - 设管理员:cd backend && python scripts/create_admin.py"
echo "  - 改 JWT_SECRET_KEY: nano backend/.env"
echo ""
