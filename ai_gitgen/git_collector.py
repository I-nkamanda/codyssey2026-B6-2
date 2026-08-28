"""Git repository inspection and change collection module."""

import subprocess
import os
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class FileStatus:
    status_code: str
    path: str
    is_staged: bool
    is_untracked: bool


@dataclass
class GitChanges:
    is_repo: bool
    branch: str
    changed_files: List[FileStatus] = field(default_factory=list)
    diff_text: str = ""
    total_files_changed: int = 0
    total_diff_lines: int = 0
    has_changes: bool = False
    error_message: Optional[str] = None


class GitCollector:
    def __init__(self, repo_dir: Optional[str] = None):
        self.repo_dir = repo_dir or os.getcwd()

    def _run_git(self, args: List[str]) -> Tuple[int, str, str]:
        try:
            res = subprocess.run(
                ["git"] + args,
                cwd=self.repo_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            return res.returncode, res.stdout, res.stderr
        except FileNotFoundError:
            return -1, "", "git executable not found in PATH"
        except Exception as e:
            return -1, "", str(e)

    def is_git_repo(self) -> bool:
        code, out, _ = self._run_git(["rev-parse", "--is-inside-work-tree"])
        return code == 0 and out.strip() == "true"

    def get_current_branch(self) -> str:
        code, out, _ = self._run_git(["branch", "--show-current"])
        if code == 0 and out.strip():
            return out.strip()
        # Fallback for detached HEAD or older git versions
        code, out, _ = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        if code == 0 and out.strip():
            return out.strip()
        return "main"

    def collect_status(self) -> List[FileStatus]:
        code, out, _ = self._run_git(["status", "--porcelain"])
        if code != 0 or not out.strip():
            return []

        file_statuses = []
        for line in out.splitlines():
            if len(line) < 4:
                continue
            index_status = line[0]
            work_tree_status = line[1]
            path = line[3:].strip()
            if " -> " in path:
                path = path.split(" -> ")[1].strip()

            is_untracked = (index_status == "?" and work_tree_status == "?")
            is_staged = (index_status not in (" ", "?"))

            file_statuses.append(FileStatus(
                status_code=line[:2].strip(),
                path=path,
                is_staged=is_staged,
                is_untracked=is_untracked
            ))
        return file_statuses

    def collect_diff(self, include_untracked: bool = True) -> str:
        # Check if HEAD exists
        code_head, _, _ = self._run_git(["rev-parse", "--verify", "HEAD"])
        has_head = (code_head == 0)

        # 1. Collect staged diff
        code_staged, out_staged, _ = self._run_git(["diff", "--cached"])
        staged_diff = out_staged if code_staged == 0 else ""

        # 2. Collect unstaged diff
        code_unstaged, out_unstaged, _ = self._run_git(["diff"])
        unstaged_diff = out_unstaged if code_unstaged == 0 else ""

        # Combine diffs
        if staged_diff and unstaged_diff:
            diff_text = f"{staged_diff}\n{unstaged_diff}"
        elif staged_diff:
            diff_text = staged_diff
        elif unstaged_diff:
            diff_text = unstaged_diff
        else:
            diff_text = ""

        # 3. If there are untracked files and diff is empty or short, include untracked files diff/preview
        if include_untracked:
            statuses = self.collect_status()
            untracked = [s for s in statuses if s.is_untracked]
            for u in untracked:
                filepath = os.path.join(self.repo_dir, u.path)
                if os.path.isfile(filepath):
                    try:
                        # Check file size (only preview small text files < 50KB)
                        size = os.path.getsize(filepath)
                        if size < 50 * 1024:
                            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                                content = f.read()
                            lines = content.splitlines()
                            preview_lines = lines[:100]
                            diff_text += f"\n--- /dev/null\n+++ b/{u.path}\n@@ -0,0 +1,{len(preview_lines)} @@ (Untracked file)\n"
                            diff_text += "\n".join(f"+{l}" for l in preview_lines) + "\n"
                    except Exception:
                        pass

        return diff_text.strip()

    def collect_changes(self) -> GitChanges:
        if not self.is_git_repo():
            return GitChanges(
                is_repo=False,
                branch="",
                error_message="Git이 초기화된 프로젝트 루트 디렉토리가 아닙니다. (git init 필요)"
            )

        branch = self.get_current_branch()
        status_files = self.collect_status()
        diff_text = self.collect_diff(include_untracked=True)

        total_files = len(status_files)
        total_lines = len(diff_text.splitlines()) if diff_text else 0
        has_changes = total_files > 0 or bool(diff_text)

        return GitChanges(
            is_repo=True,
            branch=branch,
            changed_files=status_files,
            diff_text=diff_text,
            total_files_changed=total_files,
            total_diff_lines=total_lines,
            has_changes=has_changes
        )
