# MRA Agent - Lightweight CLI Agent

A minimal, zero-dependency CLI agent for code exploration and execution, designed for resource-limited environments.

## Features

- **Pure CLI interaction** - No HTTP server, no ports, direct terminal chat
- **Zero runtime dependencies** - Single binary, works anywhere
- **6 built-in tools** - execute_bash, read_file, write_file, call_peer_agent, list_peers, publish_to_shared
- **OpenAI compatible** - Works with any OpenAI-compatible API endpoint

## Quick Start

### Build

**Native build:**
```bash
cargo build --release
```

**Cross-compilation (requires `rustup target add <target>`):**

| Target | Use Case | Install Target |
|--------|----------|----------------|
| `x86_64-unknown-linux-gnu` | Standard Linux x86_64 | `rustup target add x86_64-unknown-linux-gnu` |
| `aarch64-unknown-linux-gnu` | Raspberry Pi 5, ARM64 boards | `rustup target add aarch64-unknown-linux-gnu` |
| `armv7-unknown-linux-gnueabihf` | Raspberry Pi 3/4 (32-bit) | `rustup target add armv7-unknown-linux-gnueabihf` |
| `x86_64-pc-windows-gnu` | Windows x86_64 | (included by default) |

**Build examples:**
```bash
# Linux x86_64
cargo build --target x86_64-unknown-linux-gnu --release

# Raspberry Pi 5 (ARM64)
cargo build --target aarch64-unknown-linux-gnu --release

# ARM32 (Raspberry Pi 3/4)
cargo build --target armv7-unknown-linux-gnueabihf --release
```

The binary will be at `target/<target>/release/agent` (or `agent.exe` on Windows).

**Note:** `.cargo/config.toml` constrains CPU features to ensure compatibility across devices (e.g., `cortex-a53` for ARM64).

### Run

**Option 1: Environment variables**
```bash
export OPENAI_API_KEY=sk-xxx
export OPENAI_BASE_URL=https://api.openai.com/v1
export OPENAI_MODEL_NAME=gpt-4o
./agent
```

**Option 2: .env file**
```bash
cp .env.example .env
# Edit .env with your settings
./agent
```

**Option 3: Direct arguments**
```bash
./agent --api-key sk-xxx
```

## Commands

| Command | Description |
|---------|-------------|
| `exit`, `quit` | End the session |
| `clear` | Clear conversation history |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | Your API key (required) |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | API endpoint |
| `OPENAI_MODEL_NAME` | `gpt-4o` | Model name |
| `GATEWAY_URL` | `http://localhost:8000` | MRA gateway for peer agents |
| `AGENT_ID` | `agent` | Agent identifier for shared publishing |

## Tools

| Tool | Description |
|------|-------------|
| `execute_bash` | Run shell commands |
| `read_file` | Read file contents |
| `write_file` | Write/create files |
| `call_peer_agent` | Send message to another MRA agent |
| `list_peers` | List active peer agents |
| `publish_to_shared` | Copy file to shared workspace |

## Binary Size

With `lto = true`, `codegen-units = 1`, `panic = "abort"`, and `strip = true`:
- ~2-5 MB (depending on platform)

## License

MIT
