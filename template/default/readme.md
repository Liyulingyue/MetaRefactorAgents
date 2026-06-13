# Default Template

基础 Agent 模板，包含最小可用功能集。

## 模板血缘

```
default  ← 当前（无父模板）
```

## 工具集

| Tool | 功能 |
|------|------|
| `execute_bash` | 执行 Bash 命令 |
| `write_file` | 写入文件（全量覆盖） |
| `read_file` | 读取文件全文 |
| `call_peer_agent` | 向其他 Agent 发送任务并获取回复 |
| `list_peers` | 列出当前活跃的同伴 Agent |
| `publish_to_shared` | 将文件发布到公共共享区 |

## 替换范围配置

由 `.template` 文件定义：
- `replace`：替换的目录/文件列表
- `exclude`：替换时排除的目录/文件

当前配置：替换 `app/` 和 `run.py`，Agent 的工作文件不受影响。

## 目录结构

```
default/
├── app/                  # FastAPI 应用（含 Agent Core、Tools）
├── readme.md
├── requirements.txt
├── run.py
└── .template             # 模板元信息
```
