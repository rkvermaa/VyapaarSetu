"""Skill loader — reads SKILL.md files and caches skill metadata."""

import os
import yaml
from typing import Any

from src.core.logging import log

_skills_cache: dict[str, dict[str, Any]] = {}
_skills_dir = os.path.join(os.path.dirname(__file__), "builtin")


class SkillLoader:
    """Loads and caches skill definitions from SKILL.md files."""

    @classmethod
    def load_all_skills(cls) -> dict[str, dict[str, Any]]:
        """Load all skills from builtin directory. Uses cache."""
        global _skills_cache
        if _skills_cache:
            return _skills_cache

        skills = {}
        if not os.path.exists(_skills_dir):
            log.warning(f"Skills directory not found: {_skills_dir}")
            return skills

        for skill_dir in os.listdir(_skills_dir):
            skill_path = os.path.join(_skills_dir, skill_dir, "SKILL.md")
            if not os.path.exists(skill_path):
                continue

            skill = cls._parse_skill_md(skill_path, skill_dir)
            if skill:
                skills[skill_dir] = skill
                log.debug(f"Loaded skill: {skill_dir} ({skill['name']})")

        _skills_cache = skills
        log.info(f"Loaded {len(skills)} skills: {list(skills.keys())}")
        return skills

    @classmethod
    def get_skill(cls, slug: str) -> dict[str, Any] | None:
        """Get a single skill by its directory slug."""
        skills = cls.load_all_skills()
        return skills.get(slug)

    @classmethod
    def _parse_skill_md(cls, path: str, slug: str) -> dict[str, Any] | None:
        """Parse a SKILL.md file and return skill metadata dict."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            if not content.startswith("---"):
                log.warning(f"SKILL.md missing frontmatter: {path}")
                return None

            parts = content.split("---", 2)
            if len(parts) < 3:
                log.warning(f"SKILL.md malformed frontmatter: {path}")
                return None

            frontmatter = yaml.safe_load(parts[1])
            system_prompt = parts[2].strip()

            if not frontmatter or not isinstance(frontmatter, dict):
                return None

            tools_raw = frontmatter.get("allowed-tools", "")
            if isinstance(tools_raw, str):
                tools = [t.strip() for t in tools_raw.split() if t.strip()]
            elif isinstance(tools_raw, list):
                tools = tools_raw
            else:
                tools = []

            return {
                "slug": slug,
                "name": frontmatter.get("name", slug),
                "description": frontmatter.get("description", ""),
                "category": frontmatter.get("category", "general"),
                "is_free": frontmatter.get("is_free", False),
                "tools": tools,
                "system_prompt": system_prompt,
            }

        except Exception as e:
            log.error(f"Failed to parse SKILL.md at {path}: {e}")
            return None

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the skills cache (useful for testing)."""
        global _skills_cache
        _skills_cache = {}
