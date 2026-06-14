import os
from pathlib import Path
from typing import Optional


class MemoryLoader:
    """
    Loads agent's long-term memory from MEMORY.md file.
    Memory is injected into system prompt like skills.
    """

    def __init__(self, workspace_dir: str = "."):
        self.workspace = Path(workspace_dir)
        self._memory_path: Optional[Path] = None

    def get_memory_path(self) -> Optional[Path]:
        from .config import settings
        if self._memory_path is None:
            memory_path = getattr(settings, 'MEMORY_FILE_PATH', None)
            if memory_path:
                self._memory_path = self.workspace / memory_path
            else:
                self._memory_path = self.workspace / "MEMORY.md"
        return self._memory_path

    def read_memory(self) -> str:
        path = self.get_memory_path()
        if path and path.exists():
            try:
                return path.read_text(encoding="utf-8")
            except Exception:
                pass
        return ""

    def append_memory(self, entry: str) -> str:
        """
        Append an entry to MEMORY.md.
        Returns confirmation message.
        """
        path = self.get_memory_path()
        if not path:
            return "Memory file path not configured."

        try:
            os.makedirs(path.parent, exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(entry + "\n")
            return f"Appended to {path}"
        except Exception as e:
            return f"Failed to append memory: {e}"

    def build_memory_summary(self) -> str:
        """
        Build memory content for system prompt injection.
        Returns empty string if no memory exists.
        """
        content = self.read_memory().strip()
        if not content:
            return ""
        return f"\n## LONG_TERM_MEMORY\n\n{content}\n"
