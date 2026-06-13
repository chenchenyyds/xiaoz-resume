#!/usr/bin/env bash
# ============================================================
# 从后端 OpenAPI 自动生成前端 TypeScript 类型
# ============================================================
# 用法:
#   1) 起后端(uvicorn app.main:app)
#   2) bash scripts/gen-frontend-types.sh
#   3) 前端就有完整的 API 类型了
#
# 工具:
#   - openapi-typescript:把 OpenAPI 3 → TypeScript 类型
#   - openapi-fetch:类型安全的 fetch 客户端(可选)
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8000}"
OPENAPI_URL="$BACKEND_URL/openapi.json"
TYPES_FILE="$PROJECT_ROOT/frontend-user/src/api/types.ts"

echo "➜ 检查后端连通..."
if ! curl -fsS "$BACKEND_URL/health" > /dev/null 2>&1; then
    echo "  ✗ 后端未启动,请先 uvicorn app.main:app"
    echo "  (或设置 BACKEND_URL 指向已部署的地址)"
    exit 1
fi

echo "➜ 拉取 OpenAPI Schema..."
curl -fsS "$OPENAPI_URL" -o /tmp/openapi.json
echo "  ✓ $(wc -c < /tmp/openapi.json) bytes"

# ---------- 方案 A:npx openapi-typescript(推荐)----------
echo "➜ 生成 TypeScript 类型..."
mkdir -p "$(dirname "$TYPES_FILE")"

if command -v npx &> /dev/null; then
    npx --yes openapi-typescript /tmp/openapi.json -o "$TYPES_FILE" 2>&1 | tail -5
    echo "  ✓ 类型已生成: $TYPES_FILE"
    echo ""
    echo "前端用法示例:"
    cat <<'EOF'
  import type { paths, components } from '@/api/types'

  // 类型化 API 调用
  type LoginResp = components['schemas']['LoginResp']
  type RewriteReq = components['schemas']['RewriteReq']

  // fetch 调用(配合 openapi-fetch)
  import createClient from 'openapi-fetch'
  const client = createClient<paths>({ baseUrl: '/api' })
  const { data, error } = await client.POST('/auth/login', {
    body: { phone: '138...', code: '123456' }
  })
EOF
else
    echo "  ⚠ npx 不可用,跳过"
fi

# ---------- 方案 B:用 docker(无需 node)----------
# docker run --rm -v "$PWD:/work" openapitools/openapi-generator-cli generate \
#   -i /tmp/openapi.json -g typescript-axios -o /work/frontend-user/src/api/

echo ""
echo "✅ 完成"
