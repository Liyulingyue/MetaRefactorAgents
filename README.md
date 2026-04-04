一份优秀的 `README.md` 不仅是项目的脸面，更是 MRA 这种具有“自我意识”倾向框架的**操作手册**。

既然 MRA 是基于 **FastAPI + React** 且具备 **Bash** 权限的自重构系统，我为你拟定了一个既硬核又具前瞻性的版本。

---

# 📝 MRA (MetaRefact Agents) 

> **"Code is not a statue; it is a living, breathing process."**

**MRA (MetaRefact Agents)** 是一个基于 **Bash** 驱动、能够实现**源码级自演化与自重构**的智能体框架。与传统的静态 AI Agent 不同，MRA 能够通过指令触发，自主完成“读取源码 -> 逻辑反思 -> 自动化重构 -> 进程热重启 -> 异常回退”的完整演化闭环。

---

## 🚀 核心愿景：从 1 到 N 的自展式进化
MRA 启动时仅需两个初始节点（Lineage-1 & Lineage-2）。通过不断的**指令驱动（Instruction-driven）**，系统会根据任务复杂度自主决定：
* **分化 (Speciation):** 克隆并修改自身源码，创造 Lineage-3/4... 等专用节点。
* **重构 (Refactoring):** 实时优化既有代码架构，修复 Bug 或增加新功能。
* **收敛 (Convergence):** 像手机市场的大统一一样，将零散的优化逻辑合并回核心主干。

---

## 🛠 技术架构



* **Engine Core:** 基于 Python 的 `RefactorEngine`，掌握系统级 Bash 权限。
* **Backend:** 使用 **FastAPI** 构建的分布式节点通讯骨架。
* **Frontend:** 基于 **React** 的演化看板，实时可视化节点拓扑与演化成功率。
* **Safety Layer:** 强制性的 `Atomic Backup & Rollback` 机制，确保“手术”失败时系统不宕机。

---

## 📂 项目结构 (Refactorable Directory)

```bash
MRA/
├── app/             # Gateway: 统一路由与 Agent 进程生命周期管理
├── template/        # Seeds: Agent 的初始源码模板
│   └── default/     # 默认 Python/FastAPI 智能体模板
├── workspace/       # Agents: 活跃智能体的生存空间 (Agent-01, Agent-02...)
├── web/             # Dashboard: 基于 React 的上帝视角看板
├── run.py           # 入口脚本：启动 Gateway
└── requirements.txt # 全局依赖
```


---

## 🔄 演化生命周期 (The Loop)

1.  **Read (感知):** Agent 通过 `inspect` 或文件 IO 读取自身的 `.py` 源码。
2.  **Plan (反思):** 结合用户指令与 MEA (MetaEvoAgents) 参考逻辑，利用 LLM 规划重构方案。
3.  **Patch (注入):** * 自动执行 `cp source.py source.py.bak`。
    * 将新逻辑注入源码文件。
4.  **Verify (验证):** 尝试通过 Bash 唤醒新进程。
    * **Success:** 切换流量至新节点，记录演化日志。
    * **Failure:** 触发 `mv source.py.bak source.py`，执行回退并分析报错日志（Retry）。

---

## ⚡ 快速开始

### 1. 环境准备
确保你的环境中已安装 `docker` (推荐) 或具备 Python 3.10+ 环境，并赋予执行权限：
```bash
pip install -r requirements.txt
chmod +x ./scripts/init_mra.sh
```

### 2. 启动初始节点
```bash
python main.py --init
```
此时 Lineage-1 与 Lineage-2 将在 FastAPI 端口（默认 8000/8001）上线。

### 3. 下达演化指令
你可以通过终端或 Web UI 输入：
> *"MRA，参考 MEA 的 WebSocket 逻辑，为自己重构一个专门处理实时流数据的 Lineage-3 节点。"*

---

## ⚠️ 安全警告 (Safety Warning)
**MRA 具备修改宿主机文件的权限。** 请务必在隔离的 Docker 容器或虚拟机中运行，并确保 `backups/` 目录的写权限，以防止因意外的自重构逻辑导致的代码丢失。

---

## 🤝 开发者备注
MRA 是从 **MetaEvoAgents (MEA)** 项目中提取出的“自改进”核心。如果你发现系统进入了死循环或逻辑冲突，请手动触发 `scripts/emergency_reset.sh` 以恢复至初始 `Lineage-0` 状态。

---

**Built by Developer with ❤️ and Meta-Logic.**