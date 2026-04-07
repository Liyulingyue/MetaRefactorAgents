# Default 20260406 Template

升级版 Agent 模板，基于 default 增强。

## 新增特性
- **原子化编辑工具**：`replace_string_in_file`, `append_to_file`, `read_file_range`, `tail_file`, `grep_file`
- **日志滚动归档**：`thoughts.md` 超过 100KB 自动归档到 `logs/archived/`
- **错误独立追踪**：工具调用异常写入 `logs/error.log`

## 替换范围配置
由 `.template` 文件定义（JSON 格式）：
- `replace`：要替换的目录/文件列表（相对于模板根目录）
- `exclude`：替换时要排除的目录/文件（不影响备份）

当前配置：仅替换 `app/` 目录，Agent 的工作文件不受影响。
