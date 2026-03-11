import re
import time
import requests


def parse_repo(url: str) -> tuple[str, str]:
    """Extract owner and repo name from a GitHub URL or 'owner/repo' string."""
    # Full URL
    match = re.search(r"github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/|$)", url)
    if match:
        return match.group(1), match.group(2)
    # Short form: owner/repo
    match = re.match(r"^([^/]+)/([^/]+)$", url.strip())
    if match:
        return match.group(1), match.group(2)
    raise ValueError(f"Could not parse GitHub repo from: {url!r}")


class GitHubClient:
    BASE = "https://api.github.com"

    def __init__(self, token: str | None = None):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def _get(self, path: str, params: dict = None) -> dict | list:
        url = f"{self.BASE}{path}"
        r = self.session.get(url, params=params, timeout=15)
        if r.status_code == 403 and "rate limit" in r.text.lower():
            reset = int(r.headers.get("X-RateLimit-Reset", time.time() + 60))
            wait = max(reset - time.time() + 2, 5)
            raise RuntimeError(f"GitHub rate limit hit. Add a --token or wait {int(wait)}s.")
        r.raise_for_status()
        return r.json()

    def _paginate(self, path: str, params: dict = None, max_items: int = 500) -> list:
        params = dict(params or {})
        params.setdefault("per_page", 100)
        results = []
        page = 1
        while len(results) < max_items:
            params["page"] = page
            batch = self._get(path, params)
            if not batch:
                break
            results.extend(batch)
            if len(batch) < params["per_page"]:
                break
            page += 1
        return results[:max_items]

    def repo(self, owner: str, name: str) -> dict:
        return self._get(f"/repos/{owner}/{name}")

    def commits(self, owner: str, name: str, max_items: int = 500) -> list:
        return self._paginate(f"/repos/{owner}/{name}/commits", max_items=max_items)

    def releases(self, owner: str, name: str) -> list:
        return self._paginate(f"/repos/{owner}/{name}/releases", max_items=50)

    def tags(self, owner: str, name: str) -> list:
        return self._paginate(f"/repos/{owner}/{name}/tags", max_items=50)

    def contributors(self, owner: str, name: str) -> list:
        return self._paginate(f"/repos/{owner}/{name}/contributors", max_items=30)

    def pulls(self, owner: str, name: str) -> list:
        """Fetch top merged PRs sorted by comments (proxy for significance)."""
        prs = self._paginate(
            f"/repos/{owner}/{name}/pulls",
            params={"state": "closed", "sort": "popularity", "direction": "desc"},
            max_items=50,
        )
        return [p for p in prs if p.get("merged_at")]


def fetch_all(owner: str, name: str, token: str | None = None, max_commits: int = 500) -> dict:
    client = GitHubClient(token=token)
    repo = client.repo(owner, name)
    commits = client.commits(owner, name, max_items=max_commits)
    releases = client.releases(owner, name)
    if not releases:
        releases = client.tags(owner, name)
    contributors = client.contributors(owner, name)
    pulls = client.pulls(owner, name)

    return {
        "repo": repo,
        "commits": commits,
        "releases": releases,
        "contributors": contributors,
        "pulls": pulls,
    }
