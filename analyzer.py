from collections import Counter, defaultdict
from datetime import datetime, timezone


def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def _fmt(dt: datetime | None) -> str:
    return dt.strftime("%Y-%m-%d") if dt else "unknown"


def analyze(data: dict) -> dict:
    repo = data["repo"]
    commits = data["commits"]
    releases = data["releases"]
    contributors = data["contributors"]
    pulls = data["pulls"]

    # --- Repo basics ---
    created = _parse_dt(repo.get("created_at"))
    updated = _parse_dt(repo.get("updated_at"))
    pushed = _parse_dt(repo.get("pushed_at"))

    age_days = (datetime.now(timezone.utc) - created).days if created else None
    age_years = round(age_days / 365, 1) if age_days else None

    # --- Commit timeline ---
    commit_dates = []
    authors = []
    messages = []
    for c in commits:
        dt = _parse_dt(
            c.get("commit", {}).get("author", {}).get("date") or
            c.get("commit", {}).get("committer", {}).get("date")
        )
        author = (
            c.get("commit", {}).get("author", {}).get("name") or
            c.get("author", {}).get("login", "unknown")
        )
        msg = c.get("commit", {}).get("message", "").split("\n")[0][:120]
        if dt:
            commit_dates.append(dt)
        authors.append(author)
        messages.append({"date": _fmt(dt), "author": author, "message": msg})

    first_commit = min(commit_dates) if commit_dates else None
    last_commit = max(commit_dates) if commit_dates else None

    # Commits per month
    by_month: dict[str, int] = defaultdict(int)
    for dt in commit_dates:
        by_month[dt.strftime("%Y-%m")] += 1
    peak_month = max(by_month, key=by_month.get) if by_month else None
    peak_count = by_month[peak_month] if peak_month else 0

    # Activity trend: compare last 90 days vs prior 90 days
    now = datetime.now(timezone.utc)
    recent = sum(1 for d in commit_dates if (now - d).days <= 90)
    prior = sum(1 for d in commit_dates if 90 < (now - d).days <= 180)
    if prior == 0:
        trend = "new project"
    elif recent > prior * 1.2:
        trend = "accelerating"
    elif recent < prior * 0.5:
        trend = "slowing down"
    elif recent == 0:
        trend = "inactive / archived"
    else:
        trend = "steady"

    # --- Authors ---
    author_counts = Counter(authors)
    top_authors = author_counts.most_common(5)

    # --- Releases ---
    release_list = []
    for r in releases[:10]:
        name = r.get("name") or r.get("tag_name") or "?"
        date = _fmt(_parse_dt(r.get("published_at") or r.get("created_at")))
        body = (r.get("body") or "")[:200]
        release_list.append({"name": name, "date": date, "notes": body})

    # --- Significant commits (long messages = likely important) ---
    significant = sorted(
        [m for m in messages if len(m["message"]) > 40],
        key=lambda x: x["date"]
    )
    # Sample: first 5, middle 5, last 5
    n = len(significant)
    sampled = []
    if n > 0:
        sampled += significant[:5]
    if n > 10:
        mid = n // 2
        sampled += significant[mid - 2: mid + 3]
    if n > 5:
        sampled += significant[-5:]
    # Deduplicate
    seen = set()
    deduped = []
    for m in sampled:
        key = m["message"]
        if key not in seen:
            seen.add(key)
            deduped.append(m)

    # --- Notable PRs ---
    pr_list = []
    for p in pulls[:8]:
        pr_list.append({
            "title": p.get("title", "")[:100],
            "merged_at": _fmt(_parse_dt(p.get("merged_at"))),
            "comments": p.get("comments", 0) + p.get("review_comments", 0),
            "user": p.get("user", {}).get("login", "?"),
        })

    return {
        "name": repo.get("full_name", ""),
        "description": repo.get("description") or "",
        "language": repo.get("language") or "unknown",
        "stars": repo.get("stargazers_count", 0),
        "forks": repo.get("forks_count", 0),
        "open_issues": repo.get("open_issues_count", 0),
        "topics": repo.get("topics", []),
        "created": _fmt(created),
        "last_commit": _fmt(last_commit),
        "age_years": age_years,
        "total_commits_fetched": len(commits),
        "commit_trend": trend,
        "recent_commits_90d": recent,
        "peak_month": peak_month,
        "peak_commit_count": peak_count,
        "top_authors": top_authors,
        "contributor_count": len(contributors),
        "releases": release_list,
        "significant_commits": deduped,
        "notable_prs": pr_list,
        "license": (repo.get("license") or {}).get("spdx_id", "none"),
        "is_fork": repo.get("fork", False),
        "archived": repo.get("archived", False),
    }


def to_text(stats: dict) -> str:
    authors_str = ", ".join(f"{a} ({c} commits)" for a, c in stats["top_authors"])
    releases_str = "\n".join(
        f"  [{r['date']}] {r['name']}: {r['notes'][:100]}" for r in stats["releases"]
    ) or "  No formal releases found."
    commits_str = "\n".join(
        f"  [{c['date']}] {c['author']}: {c['message']}" for c in stats["significant_commits"]
    )
    prs_str = "\n".join(
        f"  [{p['merged_at']}] '{p['title']}' by {p['user']} ({p['comments']} comments)"
        for p in stats["notable_prs"]
    ) or "  No notable PRs found."

    return f"""## Repository: {stats['name']}

**Description:** {stats['description'] or '(none)'}
**Language:** {stats['language']} · **License:** {stats['license']}
**Stars:** {stats['stars']:,} · **Forks:** {stats['forks']:,} · **Open Issues:** {stats['open_issues']}
**Topics:** {', '.join(stats['topics']) or 'none'}
**Archived:** {stats['archived']} · **Fork:** {stats['is_fork']}

### Timeline
- Created: {stats['created']}
- Last commit: {stats['last_commit']}
- Age: {stats['age_years']} years
- Commits fetched: {stats['total_commits_fetched']}
- Activity trend: {stats['commit_trend']} ({stats['recent_commits_90d']} commits in last 90 days)
- Peak activity: {stats['peak_month']} ({stats['peak_commit_count']} commits)

### Contributors
- Total contributors: {stats['contributor_count']}
- Top authors: {authors_str}

### Releases / Tags
{releases_str}

### Significant Commits (sampled)
{commits_str}

### Notable Merged PRs
{prs_str}
"""
