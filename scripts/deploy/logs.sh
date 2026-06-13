#!/usr/bin/env bash
# 实时查看 5 服务日志
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"
docker compose logs -f --tail=100 "$@"
