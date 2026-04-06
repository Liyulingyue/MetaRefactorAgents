# Default Template

标准 Agent 模板，包含基础的 Agent 核心实现。

## 特性
- 基础工具集（execute_bash, write_file, read_file, call_peer_agent, list_peers, publish_to_shared）
- 简单的 thoughts.md 日志记录
- 与其他 Agent 协作的 P2P 协议

## 替换范围配置
由 `.template` 文件定义（JSON 格式）：
- `replace`：要替换的目录/文件列表（相对于模板根目录）
- `exclude`：替换时要排除的目录/文件（不影响备份）

当前配置：仅替换 `app/` 目录，Agent 的工作文件不受影响。
