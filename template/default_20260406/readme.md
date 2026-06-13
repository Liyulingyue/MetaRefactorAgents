# Default 20260406 Template

基于 `default` 增强，引入原子化编辑工具和日志管理。

## 模板血缘

```
default → default_20260406  ← 当前
```

## 新增特性

### 原子化编辑工具
| Tool | 功能 |
|------|------|
| `replace_string_in_file` | 基于字符串匹配精确替换文件内容 |
| `append_to_file` | 追加内容到文件末尾 |
| `read_file_range` | 按行号范围读取文件（避免全量读大文件） |
| `tail_file` | 读取文件末尾 N 行（快速获取日志状态） |
| `grep_file` | 在文件中搜索特定关键词 |

### 日志管理
- `thoughts.md` 超过 100KB 自动归档到 `logs/archived/`
- 工具调用异常写入 `logs/error.log`

## 完整工具集（11 个）

`execute_bash` · `write_file` · `read_file` · `call_peer_agent` · `list_peers` · `publish_to_shared` + 5 个原子化编辑工具

## 替换范围配置

由 `.template` 文件定义：
- `replace`：替换的目录/文件列表
- `exclude`：替换时排除的目录/文件

当前配置：替换 `app/` 和 `run.py`，Agent 的工作文件不受影响。

## 目录结构

```
default_20260406/
├── app/                  # FastAPI 应用（含增强版 Tools）
├── readme.md
├── requirements.txt
├── run.py
└── .template             # 模板元信息
```
