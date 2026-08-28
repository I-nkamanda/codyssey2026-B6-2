"""Configuration management for AI Git Generator."""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


@dataclass
class Config:
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    provider: str = "openai"  # openai, gemini, or mock
    model: str = "gpt-4o-mini"
    temperature: float = 0.2
    max_tokens: int = 1000
    safe_mode: bool = True
    max_diff_files: int = 10
    max_diff_lines: int = 200
    language: str = "ko"
    convention: str = "conventional_commits"
    commit_max_title_len: int = 72
    commit_rec_title_len: int = 50
    pr_max_title_len: int = 80
    custom_instructions: str = ""

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Config":
        config = cls()

        # 1. Load from config file if exists
        search_paths = []
        if config_path:
            search_paths.append(Path(config_path))
        else:
            search_paths.extend([
                Path(".ai-gitgen.yml"),
                Path(".ai-gitgen.yaml"),
                Path.home() / ".ai-gitgen.yml"
            ])

        for p in search_paths:
            if p.is_file():
                config._merge_file(p)
                break

        # 2. Environment variables override
        api_key = os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if api_key:
            config.api_key = api_key

        if os.getenv("AI_API_BASE_URL"):
            config.api_base_url = os.getenv("AI_API_BASE_URL")
        
        if os.getenv("AI_PROVIDER"):
            config.provider = os.getenv("AI_PROVIDER")
        elif os.getenv("GEMINI_API_KEY") and not os.getenv("OPENAI_API_KEY") and not os.getenv("AI_API_KEY"):
            config.provider = "gemini"

        if os.getenv("AI_MODEL"):
            config.model = os.getenv("AI_MODEL")

        return config

    def _merge_file(self, file_path: Path):
        data: Dict[str, Any] = {}
        try:
            content = file_path.read_text(encoding="utf-8")
            if HAS_YAML:
                parsed = yaml.safe_load(content)
                if isinstance(parsed, dict):
                    data = parsed
            else:
                # Basic key-value parser fallback
                for line in content.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if ":" in line:
                        k, v = line.split(":", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if v.lower() in ("true", "yes", "on"):
                            data[k] = True
                        elif v.lower() in ("false", "no", "off"):
                            data[k] = False
                        elif v.isdigit():
                            data[k] = int(v)
                        else:
                            try:
                                data[k] = float(v)
                            except ValueError:
                                data[k] = v
        except Exception:
            pass

        if "model" in data:
            self.model = str(data["model"])
        if "provider" in data:
            self.provider = str(data["provider"])
        if "api_base_url" in data:
            self.api_base_url = str(data["api_base_url"])
        if "temperature" in data:
            self.temperature = float(data["temperature"])
        if "max_tokens" in data:
            self.max_tokens = int(data["max_tokens"])
        if "safe_mode" in data:
            self.safe_mode = bool(data["safe_mode"])
        if "max_diff_files" in data:
            self.max_diff_files = int(data["max_diff_files"])
        if "max_diff_lines" in data:
            self.max_diff_lines = int(data["max_diff_lines"])
        if "language" in data:
            self.language = str(data["language"])
        if "convention" in data:
            self.convention = str(data["convention"])
        if "custom_instructions" in data:
            self.custom_instructions = str(data["custom_instructions"])
