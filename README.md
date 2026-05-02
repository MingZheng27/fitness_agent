# Fitness Recommendation Agent

运动健康领域的AI推荐Agent，提供饮食推荐、运动恢复建议、每日运动量建议和强度预估等功能。

## 技术栈

| 组件 | 技术选型 |
|------|---------|
| Agent框架 | LangGraph |
| LLM | MiniMax-M2.7 (OpenAI兼容API, temperature=0.2) |
| 向量数据库 | ChromaDB (内置embedding) |
| 结构化存储 | MySQL |
| API | REST API (FastAPI/uvicorn) |

## 项目结构

```
fitness_agent/
├── app/
│   ├── main.py              # FastAPI入口
│   ├── config.py            # 配置管理
│   ├── api/
│   │   ├── schemas.py       # Pydantic数据模型
│   │   └── routes.py        # API路由
│   ├── agent/
│   │   ├── graph.py         # LangGraph定义
│   │   ├── nodes.py         # 节点实现
│   │   ├── tools.py         # Agent工具集
│   │   └── prompts.py       # Prompt模板
│   ├── memory/
│   │   ├── short_term.py    # 短期记忆
│   │   └── long_term.py     # 长期记忆(ChromaDB RAG)
│   └── storage/
│       ├── mysql.py         # MySQL客户端
│       └── chromadb.py      # ChromaDB客户端
├── .venv/                   # Python虚拟环境
├── requirements.txt
└── README.md
```

## 环境配置

### 前置要求

- Python 3.9+
- MySQL 8.0+
- Homebrew (macOS)

### 快速开始 (使用 setup.sh)

```bash
cd fitness_agent
./setup.sh
# 根据提示编辑 config.yaml 填入真实配置
vim config.yaml
# 启动服务
source .venv/bin/activate
python -m app.main
```

### 1. MySQL 安装与启动

```bash
# 安装MySQL
brew install mysql

# 启动MySQL服务
brew services start mysql

# 创建数据库
mysql -u root -e "CREATE DATABASE IF NOT EXISTS fitness_agent;"
```

### 2. Python虚拟环境

```bash
cd fitness_agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. 环境变量（可选）

如需使用MiniMax LLM API，设置环境变量：
```bash
export MINIMAX_API_KEY="your_api_key_here"
```

## 启动服务

```bash
cd fitness_agent
source .venv/bin/activate
python -m app.main
```

服务运行于 `http://localhost:8000`

## API端点

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/chat` | Agent对话入口 |
| POST | `/api/v1/user/register` | 用户注册 |
| POST | `/api/v1/exercise/record` | 记录运动数据 |
| POST | `/api/v1/diet/record` | 记录饮食数据 |
| GET | `/api/v1/user/profile` | 获取用户画像 |
| PUT | `/api/v1/user/preferences` | 更新用户偏好 |

## 配置说明

配置文件: `config.yaml` (由 `config.yaml.example` 复制生成)

首次运行需执行 `./setup.sh` 生成配置文件。

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `mysql.host` | localhost | MySQL主机 |
| `mysql.port` | 3306 | MySQL端口 |
| `mysql.user` | root | MySQL用户名 |
| `mysql.password` | (empty) | MySQL密码 |
| `mysql.database` | fitness_agent | 数据库名 |
| `chroma.path` | ./chroma_data | ChromaDB数据目录 |
| `llm.base_url` | https://api.minimax.chat/v1 | LLM API地址 |
| `llm.api_key` | (empty) | MiniMax API密钥 |
| `llm.model` | MiniMax-M2.7 | LLM模型 |
| `agent.short_term_memory_size` | 10 | 短期记忆保留条数 |

## 数据隔离

每个用户拥有独立的数据空间：
- **MySQL**: 用户数据通过`user_id`字段隔离
- **ChromaDB**: 每个用户拥有独立的collection，命名格式: `user_{user_id}_fitness`

## 核心功能

### Agent工具集

- `get_user_profile` - 获取用户基本信息和偏好
- `search_exercise_history` - RAG检索历史运动记录
- `search_diet_history` - RAG检索历史饮食记录
- `get_recovery_status` - 获取用户当前恢复状态
- `calculate_recommended_calories` - 计算推荐每日卡路里摄入
- `generate_exercise_plan` - 生成运动计划
- `generate_diet_recommendation` - 生成饮食建议

### 记忆系统

- **短期记忆**: LangGraph State中的messages列表，保留最近10轮对话
- **长期记忆**: MySQL结构化存储 + ChromaDB向量化，用于RAG检索

## 注意事项

1. **首次运行**: 服务启动时会自动初始化MySQL表结构
2. **ChromaDB**: 首次使用时会在`./chroma_data`目录创建持久化存储
3. **LLM API**: 如未配置API_KEY，部分需要LLM推理的功能将不可用
4. **MySQL权限**: 确保root用户对`fitness_agent`数据库有完整权限