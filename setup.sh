#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config.yaml"

echo "=== Fitness Agent Setup ==="
echo ""

# 检查是否已有配置文件
if [ -f "$CONFIG_FILE" ]; then
    echo "配置文件已存在: $CONFIG_FILE"
    read -p "是否重新生成配置文件模板? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "跳过配置文件生成"
    else
        cp "$SCRIPT_DIR/config.yaml.example" "$CONFIG_FILE"
        echo "已重新生成配置文件模板，请编辑 $CONFIG_FILE 填入真实配置"
    fi
else
    # 复制配置文件模板
    if [ -f "$SCRIPT_DIR/config.yaml.example" ]; then
        cp "$SCRIPT_DIR/config.yaml.example" "$CONFIG_FILE"
        echo "已创建配置文件: $CONFIG_FILE"
        echo ""
        echo "=== 请编辑配置文件填入真实配置 ==="
        echo ""
        echo "编辑以下配置项:"
        echo "  1. mysql.password     - MySQL密码"
        echo "  2. llm.api_key       - MiniMax API Key"
        echo ""
        echo "编辑命令: vim $CONFIG_FILE"
        echo ""
    else
        echo "错误: 找不到 config.yaml.example"
        exit 1
    fi
fi

# 检查Python虚拟环境
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo "创建Python虚拟环境..."
    cd "$SCRIPT_DIR"
    python3 -m venv .venv
fi

echo ""
echo "=== 安装依赖 ==="
cd "$SCRIPT_DIR"
source .venv/bin/activate
pip install -q -r requirements.txt

echo ""
echo "=== 检查配置 ==="
python3 -c "
from app.config import get_settings
s = get_settings()
print('MySQL:', s.mysql_host, ':', s.mysql_port)
print('LLM Model:', s.llm_model)
if not s.llm_api_key or s.llm_api_key == 'your_key':
    print('警告: 请在config.yaml中配置llm.api_key')
if not s.mysql_password:
    print('警告: 请在config.yaml中配置mysql.password')
"

echo ""
echo "=== Setup 完成 ==="
echo "启动服务: source .venv/bin/activate && python -m app.main"