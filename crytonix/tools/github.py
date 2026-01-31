from crytonix.tools.core import Toolbox
import shutil

class GitHubToolbox:
    @staticmethod
    def _check_gh_installed() -> bool:
        return shutil.which("gh") is not None

    @staticmethod
    def list_issues(limit: int = 10) -> str:
        if not GitHubToolbox._check_gh_installed():
            return "Error: GitHub CLI (gh) is not installed."
        return Toolbox.run_command(f"gh issue list --limit {limit}")

    @staticmethod
    def get_issue(issue_number: int) -> str:
        if not GitHubToolbox._check_gh_installed(): return "Error: gh not installed."
        return Toolbox.run_command(f"gh issue view {issue_number} --json title,body,comments")

    @staticmethod
    def create_pr(title: str, body: str, branch: str = "") -> str:
        if not GitHubToolbox._check_gh_installed(): return "Error: gh not installed."
        cmd = f"gh pr create --title \"{title}\" --body \"{body}\""
        if branch: cmd += f" --head {branch}"
        return Toolbox.run_command(cmd)

    @staticmethod
    def list_prs(limit: int = 5) -> str:
        if not GitHubToolbox._check_gh_installed(): return "Error: gh not installed."
        return Toolbox.run_command(f"gh pr list --limit {limit}")

class CollaborationToolbox:
    @staticmethod
    def _check_gh() -> bool:
        return shutil.which("gh") is not None

    @staticmethod
    def review_pr(pr_number: int) -> str:
        if not CollaborationToolbox._check_gh(): return "Error: gh CLI not installed."
        return Toolbox.run_command(f"gh pr view {pr_number} --json title,body,files,reviews,comments")
