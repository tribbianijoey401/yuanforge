#!/usr/bin/env bash
# distill-pitfall.sh — 从 BUG-NNN.md 自动生成 PIT-NNN.md
#
# 用法:
#   bash scripts/distill-pitfall.sh <BUG-NNN.md> [--auto]
#
# 参数:
#   BUG-NNN.md    — BUG 记录文件路径（相对或绝对）
#   --auto        — 自动编号，不交互式确认（Conductor 调用时用）
#
# 输出:
#   成功: 打印 PIT-NNN.md 的路径
#   失败: 打印错误信息，返回 1

set -euo pipefail

# ========== 配置 ==========
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
KNOWLEDGE_DIR="$PROJECT_ROOT/docs/knowledge/pitfalls"
EVENTS_DIR="$PROJECT_ROOT/docs/events"

# ========== 参数解析 ==========
if [[ $# -lt 1 ]]; then
    echo "用法: bash scripts/distill-pitfall.sh <BUG-NNN.md> [--auto]" >&2
    exit 1
fi

BUG_FILE="$1"
AUTO_MODE=false

if [[ "${2:-}" == "--auto" ]]; then
    AUTO_MODE=true
fi

# ========== 验证输入 ==========
if [[ ! -f "$BUG_FILE" ]]; then
    echo "错误: 文件不存在: $BUG_FILE" >&2
    exit 1
fi

# ========== 提取 BUG 信息 ==========
BUG_ID=""
BUG_TITLE=""
BUG_SEVERITY=""
BUG_SUMMARY=""
BUG_CAUSE=""
BUG_FIX=""
BUG_LESSON=""

# 读取 frontmatter（如果有）
in_frontmatter=false
frontmatter_end=false
while IFS= read -r line; do
    if [[ "$line" == "---" ]] && [[ "$in_frontmatter" == false ]]; then
        in_frontmatter=true
        continue
    fi
    if [[ "$line" == "---" ]] && [[ "$in_frontmatter" == true ]]; then
        in_frontmatter=false
        frontmatter_end=true
        continue
    fi
    if [[ "$in_frontmatter" == true ]]; then
        case "$line" in
            *"id:"*) BUG_ID=$(echo "$line" | sed 's/^id:[[:space:]]*//' | tr -d '"' | tr -d "'") ;;
            *"severity:"*) BUG_SEVERITY=$(echo "$line" | sed 's/^severity:[[:space:]]*//' | tr -d '"' | tr -d "'") ;;
        esac
    fi
done < "$BUG_FILE"

# 读取正文段落
section=""
while IFS= read -r line; do
    case "$line" in
        *"## 现象"*|*"## Phenomenon"*) section="phenomenon" ;;
        *"## 根因"*|*"## Root Cause"*) section="cause" ;;
        *"## 修复"*|*"## Fix"*) section="fix" ;;
        *"## 教训"*|*"## Lesson"*) section="lesson" ;;
        *"## 归档判断"*) section="archive" ;;
    esac
    
    case "$section" in
        "phenomenon")
            if [[ -n "$line" ]] && [[ ! "$line" =~ ^# ]] && [[ ! "$line" =~ ^- ]] && [[ ! "$line" =~ ^\| ]]; then
                BUG_SUMMARY="${BUG_SUMMARY}${line}\n"
            fi
            ;;
        "cause")
            if [[ -n "$line" ]] && [[ ! "$line" =~ ^# ]] && [[ ! "$line" =~ ^- ]] && [[ ! "$line" =~ ^\| ]]; then
                BUG_CAUSE="${BUG_CAUSE}${line}\n"
            fi
            ;;
        "fix")
            if [[ -n "$line" ]] && [[ ! "$line" =~ ^# ]] && [[ ! "$line" =~ ^- ]] && [[ ! "$line" =~ ^\| ]]; then
                BUG_FIX="${BUG_FIX}${line}\n"
            fi
            ;;
        "lesson")
            if [[ -n "$line" ]] && [[ ! "$line" =~ ^# ]] && [[ ! "$line" =~ ^- ]] && [[ ! "$line" =~ ^\| ]]; then
                BUG_LESSON="${BUG_LESSON}${line}\n"
            fi
            ;;
    esac
done < "$BUG_FILE"

# ========== 生成 PIT-NNN ID ==========
# 扫描已有 PIT 文件，取最大序号 +1
NEXT_NUM=1
if [[ -d "$KNOWLEDGE_DIR" ]]; then
    for f in "$KNOWLEDGE_DIR"/PIT-*.md; do
        if [[ -f "$f" ]]; then
            num=$(basename "$f" | sed 's/PIT-\([0-9]*\)\.md/\1/')
            if [[ $num -ge $NEXT_NUM ]]; then
                NEXT_NUM=$((num + 1))
            fi
        fi
    done
fi
PIT_ID=$(printf "PIT-%03d" $NEXT_NUM)

# ========== 确定 severity ==========
if [[ -z "$BUG_SEVERITY" ]]; then
    # 从 BUG frontmatter 或标题推断
    if echo "$BUG_FILE" | grep -qi "blocker\|critical\|🔴"; then
        BUG_SEVERITY="🔴 High"
    elif echo "$BUG_FILE" | grep -qi "warning\|🟡"; then
        BUG_SEVERITY="🟡 Medium"
    else
        BUG_SEVERITY="🟢 Low"
    fi
fi

# ========== 确定 modules ==========
# 从 BUG 文件路径提取模块标签
MODULES=""
if echo "$BUG_FILE" | grep -qi "frontend\|react\|table"; then
    MODULES="frontend,react,table"
elif echo "$BUG_FILE" | grep -qi "backend\|sdk\|aliyun"; then
    MODULES="backend,sdk,cloud"
elif echo "$BUG_FILE" | grep -qi "auth\|login\|permission"; then
    MODULES="auth,security"
else
    MODULES="general"
fi

# ========== 获取 verified_commit ==========
COMMIT_HASH=$(git -C "$PROJECT_ROOT" log -1 --oneline 2>/dev/null || echo "unknown")

# ========== 生成 PIT-NNN.md ==========
PIT_FILE="$KNOWLEDGE_DIR/${PIT_ID}.md"

mkdir -p "$KNOWLEDGE_DIR"

cat > "$PIT_FILE" << EOF
---
id: ${PIT_ID}
object_type: pitfall
lifecycle: knowledge
owner: conductor
status: active
severity: ${BUG_SEVERITY}
type: bug-pattern
summary: $(echo -e "$BUG_SUMMARY" | head -1 | cut -c1-80)
modules: [${MODULES}]
depends: [$(basename "$BUG_FILE" .md)]
verified_commit: ${COMMIT_HASH}
confidence: verified
updated_by: distill-pitfall.sh
updated_at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
---

# ${PIT_ID}: $(echo -e "$BUG_SUMMARY" | head -1 | cut -c1-80)

> 会话: $(basename "$(dirname "$BUG_FILE")")
> 源自: $(basename "$BUG_FILE")
> 严重程度: ${BUG_SEVERITY}

## 现象

$(echo -e "$BUG_SUMMARY" | sed '/^$/d' | head -3)

## 根因

$(echo -e "$BUG_CAUSE" | sed '/^$/d' | head -3)

## 修复

$(echo -e "$BUG_FIX" | sed '/^$/d' | head -3)

## 教训

$(echo -e "$BUG_LESSON" | sed '/^$/d' | head -3)
EOF

echo "✓ 已创建: $PIT_FILE"
echo "  ID: $PIT_ID"
echo "  Severity: $BUG_SEVERITY"
echo "  Modules: $MODULES"

# ========== 可选：写 Event ==========
if [[ -d "$EVENTS_DIR" ]]; then
    TODAY=$(date -u +"%Y%m%d")
    mkdir -p "$EVENTS_DIR/$TODAY"
    echo "{\"event\": \"KNOWLEDGE_UPDATED\", \"pitfall\": \"$PIT_ID\", \"source\": \"$(basename "$BUG_FILE")\", \"time\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"}" >> "$EVENTS_DIR/$TODAY/events.jsonl"
fi
