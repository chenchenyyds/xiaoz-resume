#!/usr/bin/env bash
# ============================================================
# 小Z简历 - 数据库自动备份
# ============================================================
# 策略:
#   - 本地保留 7 天
#   - 每周日同步到阿里云 OSS(异地容灾)
#   - 文件名带时间戳,防止覆盖
#
# 用法:
#   1) 手动跑:bash scripts/backup/backup.sh
#   2) 自动跑:加到 crontab
#
# 配置(写到 .env):
#   BACKUP_LOCAL_DIR=/var/backups/xiaoz
#   BACKUP_KEEP_DAYS=7
#   BACKUP_OSS_ENABLED=true
#   BACKUP_OSS_BUCKET=xiaoz-backups
#   BACKUP_OSS_ENDPOINT=oss-cn-shanghai.aliyuncs.com
#   BACKUP_OSS_ACCESS_KEY=xxx
#   BACKUP_OSS_SECRET_KEY=xxx
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

BACKUP_LOCAL_DIR="${BACKUP_LOCAL_DIR:-/var/backups/xiaoz}"
BACKUP_KEEP_DAYS="${BACKUP_KEEP_DAYS:-7}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE_ONLY=$(date +%Y%m%d)
BACKUP_FILE="xiaoz_resume_${TIMESTAMP}.sql.gz"

DB_CONTAINER="${DB_CONTAINER:-xiaoz-db}"
DB_USER="${DB_USER:-xiaoz}"
DB_NAME="${DB_NAME:-xiaoz_resume}"

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'
log() { echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"; }
err() { echo -e "${RED}[$(date '+%H:%M:%S')]${NC} $1"; exit 1; }

mkdir -p "$BACKUP_LOCAL_DIR"

# ---------- 1. pg_dump ----------
log "[1/4] 备份数据库 $DB_NAME ..."
if docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
    docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" --no-owner --clean --if-exists \
        | gzip > "$BACKUP_LOCAL_DIR/$BACKUP_FILE"
    log "  ✓ 备份完成:$BACKUP_FILE"
else
    err "  ✗ 容器 $DB_CONTAINER 未运行"
fi

# ---------- 2. 验证 ----------
log "[2/4] 验证备份完整性..."
SIZE=$(stat -c%s "$BACKUP_LOCAL_DIR/$BACKUP_FILE")
if [ "$SIZE" -lt 1024 ]; then
    err "  ✗ 备份文件过小(${SIZE}B),可能失败"
fi
if ! gunzip -t "$BACKUP_LOCAL_DIR/$BACKUP_FILE" 2>/dev/null; then
    err "  ✗ 备份文件损坏"
fi
log "  ✓ 备份文件 ${SIZE} bytes,gzip 校验通过"

# ---------- 3. 清理旧备份 ----------
log "[3/4] 清理 $BACKUP_KEEP_DAYS 天前的本地备份..."
DELETED=$(find "$BACKUP_LOCAL_DIR" -name "xiaoz_resume_*.sql.gz" -mtime +$BACKUP_KEEP_DAYS -delete -print 2>/dev/null | wc -l)
log "  ✓ 删了 $DELETED 个旧备份"

# ---------- 4. OSS 同步(周日)----------
if [ "${BACKUP_OSS_ENABLED:-false}" = "true" ] && [ "$(date +%u)" = "7" ]; then
    log "[4/4] 同步到阿里云 OSS(周日)..."
    if command -v ossutil &> /dev/null; then
        ossutil cp "$BACKUP_LOCAL_DIR/$BACKUP_FILE" \
            "oss://${BACKUP_OSS_BUCKET}/postgres/${DATE_ONLY}/${BACKUP_FILE}" \
            --endpoint "https://${BACKUP_OSS_ENDPOINT}" \
            --access-key-id "$BACKUP_OSS_ACCESS_KEY" \
            --access-key-secret "$BACKUP_OSS_SECRET_KEY" 2>/dev/null \
            && log "  ✓ 已上传到 OSS" \
            || log "  ⚠ OSS 上传失败,查看 ossutil 配置"
    else
        log "  ⚠ ossutil 未装,跳过(apt install ossutil)"
    fi
else
    log "[4/4] 跳过 OSS 同步(非周日或未启用)"
fi

# ---------- 总结 ----------
echo ""
log "✅ 备份完成"
echo "  本地:$BACKUP_LOCAL_DIR/$BACKUP_FILE"
echo "  大小:$(du -h "$BACKUP_LOCAL_DIR/$BACKUP_FILE" | awk '{print $1}')"
echo "  恢复:gunzip -c $BACKUP_LOCAL_DIR/$BACKUP_FILE | docker exec -i $DB_CONTAINER psql -U $DB_USER -d $DB_NAME"
echo ""
echo "  crontab(每天 3 点):0 3 * * * $PROJECT_ROOT/scripts/backup/backup.sh >> /var/log/xiaoz/backup.log 2>&1"
