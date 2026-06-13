# Planer Feishu 20260412 Template

基于 `planer_20260408` 增强，新增**飞书机器人集成**。

## 模板血缘

```
default → default_20260406 → planer_20260408 → planer_feishu_20260412  ← 当前
```

## 核心新增功能

### 飞书机器人

支持飞书群消息接入与自动回复：

| 文件 | 说明 |
|------|------|
| `app/core/feishu.py` | 飞书 SDK 封装，提供消息发送能力 |
| `app/routers/feishu.py` | Webhook 路由，解析消息并调用 Agent 处理 |

### 消息流程

```
飞书群消息 → POST /api/v1/feishu/webhook → Agent 处理 → 回复到飞书
```

### 环境配置

在 `.env` 文件中添加：

```env
FEISHU_APP_ID=cli_xxxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxx
```

### 飞书开放平台配置

1. 创建应用后，开启 **机器人** 能力
2. 配置 **消息事件订阅**：
   - `im.message.receive_v1` - 接收消息
3. 配置 **请求地址** 为：`https://你的服务器地址/api/v1/feishu/webhook`

## API 接口

```
GET  /api/v1/feishu/webhook  - 飞书验证回调
POST /api/v1/feishu/webhook  - 接收飞书消息
```

## 继承特性

### Plan 任务计划（来自 planer_20260408）
`create_plan` · `add_task_to_plan` · `get_plan_status` · `update_task_progress` · `execute_next_plan_task`

### 原子化编辑工具（来自 default_20260406）
`replace_string_in_file` · `append_to_file` · `read_file_range` · `tail_file` · `grep_file`

## 完整工具集（16 个）

基础工具 + Plan 工具（5）+ 原子化编辑工具（5）

飞书消息通过独立 Webhook 路由处理，不作为 LLM Tool。

## 替换范围配置

由 `.template` 文件定义：
- `replace`：替换 `app/`、`run.py`、`requirements.txt`
- `exclude`：替换时排除的目录/文件

## 目录结构

```
planer_feishu_20260412/
├── app/
│   ├── core/            # Agent Core、Plan、Feishu
│   └── routers/         # API 路由（含 feishu.py）
├── readme.md
├── requirements.txt
├── run.py
└── .template             # 模板元信息
```
