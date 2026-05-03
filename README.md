# Fitness Recommendation Agent

运动健康领域的 AI 推荐 Agent，提供饮食推荐、运动恢复建议、每日运动量建议和强度预估等功能。基于 RAG 架构和 LangGraph Agent 框架构建。

## 技术栈

| 组件 | 技术选型 |
|------|---------|
| Agent 框架 | LangGraph |
| LLM | MiniMax-M2.7 (OpenAI 兼容 API, temperature=0.2) |
| 向量数据库 | ChromaDB (内置 embedding) |
| 结构化存储 | MySQL |
| API | REST API (FastAPI/uvicorn) |

## 项目结构

```
fitness_agent/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置管理
│   ├── api/
│   │   ├── schemas.py       # Pydantic 数据模型
│   │   └── routes.py        # API 路由
│   ├── agent/
│   │   ├── graph.py         # LangGraph 定义
│   │   ├── nodes.py         # 节点实现
│   │   ├── tools.py         # Agent 工具集
│   │   └── prompts.py       # Prompt 模板
│   ├── memory/
│   │   ├── short_term.py    # 短期记忆
│   │   └── long_term.py     # 长期记忆 (ChromaDB RAG)
│   └── storage/
│       ├── mysql.py         # MySQL 客户端
│       └── chromadb.py      # ChromaDB 客户端
├── requirements.txt
└── README.md
```

## 快速开始

### 环境要求

- Python 3.9+
- MySQL 8.0+
- Homebrew (macOS)

### 1. MySQL 安装与启动

```bash
# 安装 MySQL
brew install mysql

# 启动 MySQL 服务
brew services start mysql

# 创建数据库
mysql -u root -e "CREATE DATABASE IF NOT EXISTS fitness_agent;"
```

### 2. 安装依赖

```bash
cd fitness_agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. 配置

复制配置文件并编辑：

```bash
cp config.yaml.example config.yaml
vim config.yaml
```

### 4. 设置环境变量（如使用 MiniMax LLM）

```bash
export MINIMAX_API_KEY="your_api_key_here"
```

### 5. 启动服务

```bash
source .venv/bin/activate
python -m app.main
```

服务运行于 `http://localhost:8000`

---

## API 接口文档

所有接口前缀为 `/api/v1`，健康检查接口为 `/health`。

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/chat` | Agent 对话入口 |
| POST | `/api/v1/user/register` | 用户注册 |
| POST | `/api/v1/exercise/record` | 记录运动数据 |
| POST | `/api/v1/diet/record` | 记录饮食数据 |
| GET | `/api/v1/user/profile` | 获取用户画像 |
| PUT | `/api/v1/user/preferences` | 更新用户偏好 |
| GET | `/health` | 健康检查 |

---

### 1. POST `/api/v1/chat` - Agent 对话入口

与 Agent 进行自然语言对话，获取个性化的运动、饮食和恢复建议。

**Request:**

```json
{
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "message": "我今天跑了5公里，感觉有点累，明天该怎么运动？",
    "conversation_id": "550e8400-e29b-41d4-a716-446655440002"
}
```

**Response:**

```json
{
    "response": "根据您的运动记录，您今天完成了5公里跑步，消耗约400卡路里。按照您目前的训练强度，明天建议进行低强度恢复运动，如瑜伽或30分钟徒步，帮助肌肉恢复。",
    "recommendations": {
        "exercise": {
            "type": "hiking",
            "duration": 30,
            "intensity": 3,
            "reason": "促进恢复，增强心肺功能"
        },
        "diet": {
            "breakfast": "燕麦+香蕉+牛奶，补充碳水化合物",
            "lunch": "鸡胸肉+糙米+蔬菜，高蛋白低脂",
            "dinner": "鱼类+蔬菜沙拉，轻食助恢复",
            "snacks": "坚果+水果",
            "total_calories": 1800
        },
        "recovery": {
            "sleep_hours": 8,
            "water_intake": 2.5,
            "stretching": "建议睡前做15分钟拉伸"
        }
    },
    "sources": [
        "exercise_history:running_20260501",
        "exercise_history:running_20260428",
        "diet_history:diet_20260428"
    ],
    "conversation_id": "550e8400-e29b-41d4-a716-446655440002"
}
```

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `user_id` | string (UUID) | 用户唯一标识 |
| `message` | string | 用户消息内容 |
| `conversation_id` | string (UUID) | 会话 ID（可选，用于连续对话） |
| `response` | string | Agent 回复文本 |
| `recommendations.exercise` | object | 运动建议 |
| `recommendations.diet` | object | 饮食建议 |
| `recommendations.recovery` | object | 恢复建议 |
| `sources` | array | 检索来源（用于 RAG trace） |
| `conversation_id` | string (UUID) | 会话 ID |

---

### 2. POST `/api/v1/user/register` - 用户注册

注册新用户，创建用户档案。

**Request:**

```json
{
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "张三",
    "age": 28,
    "gender": "male",
    "height": 175,
    "weight": 70,
    "fitness_goals": ["weight_loss", "strength"],
    "constraints": {
        "injury_history": [],
        "available_time": "weekday_evening"
    }
}
```

**Response:**

```json
{
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "message": "用户注册成功",
    "created_at": "2026-05-02T10:30:00Z"
}
```

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `tenant_id` | string (UUID) | 租户 ID |
| `username` | string | 用户名 |
| `age` | integer | 年龄 |
| `gender` | string | 性别 (male/female/other) |
| `height` | integer | 身高 (cm) |
| `weight` | float | 体重 (kg) |
| `fitness_goals` | array | 健身目标列表 (weight_loss/strength/endurance/flexibility) |
| `constraints` | object | 约束条件 |

---

### 3. POST `/api/v1/exercise/record` - 记录运动数据

记录用户的运动记录，数据会同时存储到 MySQL 和 ChromaDB。

**Request:**

```json
{
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "date": "2026-05-01",
    "exercise_type": "running",
    "duration_minutes": 45,
    "intensity": 7,
    "calories_burned": 420,
    "recovery_status": "normal",
    "notes": "跑步过程中天气很好，状态不错"
}
```

**Response:**

```json
{
    "id": "550e8400-e29b-41d4-a716-446655440003",
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "date": "2026-05-01",
    "exercise_type": "running",
    "duration_minutes": 45,
    "intensity": 7,
    "calories_burned": 420,
    "recovery_status": "normal",
    "notes": "跑步过程中天气很好，状态不错",
    "created_at": "2026-05-01T20:15:00Z"
}
```

**exercise_type 可选值：**

`running`, `swimming`, `hiking`, `cycling`, `strength_training`, `yoga`, `basketball`, `football`, `tennis`, `badminton`, `walking`, `skipping`, `dance`, `other`

---

### 4. POST `/api/v1/diet/record` - 记录饮食数据

记录用户的饮食摄入，数据会同时存储到 MySQL 和 ChromaDB。

**Request:**

```json
{
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "date": "2026-05-01",
    "meal_type": "breakfast",
    "foods": [
        {"name": "燕麦", "portion": "100g"},
        {"name": "香蕉", "portion": "1根"},
        {"name": "牛奶", "portion": "200ml"}
    ],
    "calories": 350,
    "nutrients": {
        "protein": 15,
        "carbs": 60,
        "fat": 8,
        "fiber": 5
    }
}
```

**Response:**

```json
{
    "id": "550e8400-e29b-41d4-a716-446655440004",
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "date": "2026-05-01",
    "meal_type": "breakfast",
    "foods": [
        {"name": "燕麦", "portion": "100g"},
        {"name": "香蕉", "portion": "1根"},
        {"name": "牛奶", "portion": "200ml"}
    ],
    "calories": 350,
    "nutrients": {
        "protein": 15,
        "carbs": 60,
        "fat": 8,
        "fiber": 5
    },
    "created_at": "2026-05-01T08:30:00Z"
}
```

**meal_type 可选值：**

`breakfast`, `lunch`, `dinner`, `snack`

---

### 5. GET `/api/v1/user/profile` - 获取用户画像

获取用户的完整档案、统计数据和近期摘要。

**Query Parameters:**

```
user_id=550e8400-e29b-41d4-a716-446655440001
```

**Response:**

```json
{
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "username": "张三",
    "age": 28,
    "gender": "male",
    "height": 175,
    "weight": 70,
    "fitness_goals": ["weight_loss", "strength"],
    "exercise_preferences": {
        "favorite_sports": ["running", "cycling"],
        "preferred_intensity": 6,
        "available_days": ["monday", "wednesday", "friday"]
    },
    "diet_preferences": {
        "diet_type": "balanced",
        "allergies": [],
        "calorie_target": 2000
    },
    "stats": {
        "total_exercises": 45,
        "total_calories_burned": 18500,
        "avg_weekly_exercises": 3,
        "current_streak": 5
    },
    "recent_summary": {
        "last_exercise": "2026-05-01",
        "last_diet": "2026-05-02",
        "weekly_goal_progress": 0.7
    }
}
```

---

### 6. PUT `/api/v1/user/preferences` - 更新用户偏好

更新用户的运动偏好、饮食偏好和健身目标。

**Query Parameters:**

```
user_id=550e8400-e29b-41d4-a716-446655440001
```

**Request:**

```json
{
    "exercise_preferences": {
        "favorite_sports": ["running", "swimming", "cycling"],
        "preferred_intensity": 7,
        "available_days": ["monday", "tuesday", "wednesday", "friday", "saturday"]
    },
    "diet_preferences": {
        "diet_type": "high_protein",
        "allergies": ["peanut"],
        "calorie_target": 2200
    },
    "fitness_goals": ["muscle_gain", "weight_loss", "endurance"],
    "constraints": {
        "injury_history": ["ankle_sprain_2025"],
        "available_time": "weekday_morning"
    }
}
```

**Response:**

```json
{
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "message": "用户偏好更新成功",
    "updated_fields": [
        "exercise_preferences",
        "diet_preferences",
        "fitness_goals",
        "constraints"
    ],
    "updated_at": "2026-05-02T14:00:00Z"
}
```

---

### 7. GET `/health` - 健康检查

服务健康检查接口。

**Response:**

```json
{
    "status": "healthy"
}
```

---

## 配置说明

配置文件: `config.yaml` (由 `config.yaml.example` 复制生成)

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `mysql.host` | localhost | MySQL 主机 |
| `mysql.port` | 3306 | MySQL 端口 |
| `mysql.user` | root | MySQL 用户名 |
| `mysql.password` | (empty) | MySQL 密码 |
| `mysql.database` | fitness_agent | 数据库名 |
| `chroma.path` | ./chroma_data | ChromaDB 数据目录 |
| `llm.base_url` | https://api.minimax.chat/v1 | LLM API 地址 |
| `llm.api_key` | (empty) | MiniMax API 密钥 |
| `llm.model` | MiniMax-M2.7 | LLM 模型 |
| `agent.short_term_memory_size` | 10 | 短期记忆保留条数 |

---

## 数据隔离

每个用户拥有独立的数据空间：

- **MySQL**: 用户数据通过 `user_id` 字段隔离
- **ChromaDB**: 每个用户拥有独立的 collection，命名格式: `user_{user_id}_fitness`

---

## 核心功能

### Agent 工具集

| Tool | 说明 |
|------|------|
| `get_user_profile` | 获取用户基本信息和偏好 |
| `search_exercise_history` | RAG 检索历史运动记录 |
| `search_diet_history` | RAG 检索历史饮食记录 |
| `get_recovery_status` | 获取用户当前恢复状态 |
| `calculate_recommended_calories` | 计算推荐每日卡路里摄入 |
| `generate_exercise_plan` | 生成运动计划 |
| `generate_diet_recommendation` | 生成饮食建议 |

### 记忆系统

- **短期记忆**: LangGraph State 中的 messages 列表，保留最近 10 轮对话
- **长期记忆**: MySQL 结构化存储 + ChromaDB 向量化，用于 RAG 检索

---

## 注意事项

1. **首次运行**: 服务启动时会自动初始化 MySQL 表结构
2. **ChromaDB**: 首次使用时会在 `./chroma_data` 目录创建持久化存储
3. **LLM API**: 如未配置 API_KEY，部分需要 LLM 推理的功能将不可用
4. **MySQL 权限**: 确保 root 用户对 `fitness_agent` 数据库有完整权限