import json
import os
import re
import shutil
from pathlib import Path
from typing import Optional

import yaml

SKILLS_DIR = "skills"
BUILTIN_SKILLS_DIR = Path(__file__).parent.parent.parent / SKILLS_DIR

_STRIP_SKILL_FRONTMATTER = re.compile(
    r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n?",
    re.DOTALL,
)


class SkillsLoader:
    """
    Loader for agent skills.

    Skills are markdown files (SKILL.md) that teach the agent how to use
    specific tools or perform certain tasks.
    """

    def __init__(self, workspace_dir: str = "."):
        self.workspace = Path(workspace_dir)
        self.workspace_skills = self.workspace / SKILLS_DIR
        self.builtin_skills = BUILTIN_SKILLS_DIR
        self._skills_cache: dict[str, str] = {}

    def list_skills(self, filter_unavailable: bool = True) -> list[dict[str, str]]:
        """
        List all available skills.

        Returns:
            List of skill info dicts with 'name', 'path', 'source' (builtin/workspace).
        """
        skills = self._skills_from_dir(self.workspace_skills, "workspace")
        workspace_names = {s["name"] for s in skills}
        if self.builtin_skills and self.builtin_skills.exists():
            skills.extend(self._skills_from_dir(self.builtin_skills, "builtin", skip=workspace_names))

        if filter_unavailable:
            skills = [s for s in skills if self._check_requirements(s["name"])]
        return skills

    def _skills_from_dir(self, base: Path, source: str, skip: Optional[set] = None) -> list[dict[str, str]]:
        if not base.exists():
            return []
        entries = []
        skip = skip or set()
        for skill_dir in base.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue
            name = skill_dir.name
            if name in skip:
                continue
            entries.append({"name": name, "path": str(skill_file), "source": source})
        return entries

    def load_skill(self, name: str) -> Optional[str]:
        """
        Load a skill by name (returns raw markdown content).

        Search order: workspace_skills -> builtin_skills
        """
        if name in self._skills_cache:
            return self._skills_cache[name]

        for root in [self.workspace_skills, self.builtin_skills]:
            if not root.exists():
                continue
            path = root / name / "SKILL.md"
            if path.exists():
                content = path.read_text(encoding="utf-8")
                self._skills_cache[name] = content
                return content
        return None

    def load_skills_for_context(self, skill_names: list[str]) -> str:
        """
        Load specific skills and format them for LLM context.
        """
        parts = []
        for name in skill_names:
            content = self.load_skill(name)
            if content:
                stripped = self._strip_frontmatter(content)
                parts.append(f"### Skill: {name}\n\n{stripped}")
        return "\n\n---\n\n".join(parts)

    def build_skills_summary(self) -> str:
        """
        Build a markdown summary of all available skills.
        Used to inject into the system prompt.
        """
        skills = self.list_skills(filter_unavailable=False)
        if not skills:
            return ""

        lines = ["## AVAILABLE SKILLS"]
        lines.append("")

        for entry in skills:
            name = entry["name"]
            meta = self._get_skill_meta(name)
            desc = meta.get("description", name)
            emoji = meta.get("emoji", "")
            available = self._check_requirements(name)
            requires = meta.get("requires", {})
            bins = requires.get("bins", [])
            envs = requires.get("env", [])

            status = ""
            if not available:
                missing = []
                for cmd in bins:
                    if not shutil.which(cmd):
                        missing.append(f"CLI: {cmd}")
                for env in envs:
                    if not os.environ.get(env):
                        missing.append(f"ENV: {env}")
                if missing:
                    status = f" *(unavailable: {', '.join(missing)})*"
                else:
                    status = " *(unavailable)*"

            marker = f"{emoji} " if emoji else ""
            lines.append(f"- **{name}** — {marker}{desc}{status}")

        lines.append("")
        lines.append("Use `read_file('skills/<name>/SKILL.md')` to load a skill's full instructions.")
        return "\n".join(lines)

    def _get_skill_meta(self, name: str) -> dict:
        """Get skill metadata from frontmatter."""
        content = self.load_skill(name)
        if not content or not content.startswith("---"):
            return {}
        match = _STRIP_SKILL_FRONTMATTER.match(content)
        if not match:
            return {}
        try:
            parsed = yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            return {}
        if not isinstance(parsed, dict):
            return {}
        nanobot_meta = parsed.get("metadata", {}).get("nanobot", {})
        return {
            "name": parsed.get("name", name),
            "description": parsed.get("description", ""),
            "emoji": parsed.get("emoji", ""),
            "requires": nanobot_meta.get("requires", {}),
        }

    def _check_requirements(self, name: str) -> bool:
        """Check if skill requirements (bins, env vars) are met."""
        meta = self._get_skill_meta(name)
        requires = meta.get("requires", {})
        bins = requires.get("bins", [])
        envs = requires.get("env", [])
        return all(shutil.which(cmd) for cmd in bins) and all(os.environ.get(var) for var in envs)

    def _strip_frontmatter(self, content: str) -> str:
        """Remove YAML frontmatter from markdown content."""
        if not content.startswith("---"):
            return content
        match = _STRIP_SKILL_FRONTMATTER.match(content)
        if match:
            return content[match.end():].strip()
        return content
