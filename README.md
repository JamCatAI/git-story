# git-story 📖

**Turn any GitHub repository's commit history into a narrative.**

Give it a repo. Get back a documentary-style story — who built it, when it pivoted, where it peaked, who the key people were, and what it has become.

```
$ python main.py fastapi/fastapi

✓ fastapi/fastapi — 78,432 stars · Python
  502 commits · 12 releases · 89 contributors
  Trend: steady · Peak: 2020-06 (142 commits)

━━━━━━━━━━━━━ fastapi/fastapi ━━━━━━━━━━━━━

## Origin
In December 2018, Sebastián Ramírez pushed the first commit to what would
become one of the most starred Python projects of the decade. The message
was characteristically direct: "first commit." But what followed in the
next seven days told the real story...

## The People
Sebastián Ramírez is the unmistakable center of gravity — responsible for
over 90% of commits. But the project's hidden architecture lies in the
contributors who appeared in the summer of 2019...
```

---

## Quickstart

```bash
git clone https://github.com/JamCatAI/git-story
cd git-story
pip install -r requirements.txt

# Free Gemini key: https://aistudio.google.com/app/apikey
echo "GEMINI_API_KEY=your-key-here" > .env

python main.py https://github.com/fastapi/fastapi
```

---

## Commands

```bash
# By full URL
python main.py https://github.com/fastapi/fastapi

# By owner/repo shorthand
python main.py fastapi/fastapi

# Use Claude (best narrative quality) or OpenAI
python main.py fastapi/fastapi --provider claude

# Fetch more commits (default: 500)
python main.py torvalds/linux --limit 2000

# Skip LLM — output raw stats only
python main.py fastapi/fastapi --no-llm

# Add a GitHub token to avoid rate limits (60 → 5,000 req/hr)
python main.py fastapi/fastapi --token ghp_yourtoken
# or set GITHUB_TOKEN in .env
```

---

## What it reads

From the GitHub API (no local clone needed):

| Data | What it reveals |
|------|----------------|
| Commit history | Timeline, velocity, pivots, priorities |
| Commit messages | What the team was thinking at each stage |
| Contributors | Who built it and when they appeared |
| Releases / tags | Version milestones and evolution |
| Merged PRs | Major decisions and direction changes |
| Repo metadata | Stars, forks, language, topics, license |

---

## What it writes

Six narrative sections:

| Section | What it covers |
|---------|---------------|
| **Origin** | First commit, creator intent, initial problem |
| **Early Days** | First months, who showed up, early priorities |
| **The Build** | Growth, pivots, peak activity, key releases |
| **The People** | Portrait of top contributors from commit patterns |
| **The Present** | Current state — active, slowing, or dormant |
| **The Verdict** | What kind of project is this, in 2–3 sentences |

---

## GitHub rate limits

Without a token: **60 requests/hour** — enough for most repos under 500 commits.

With a free GitHub token: **5,000 requests/hour** — handles large repos comfortably.

Create a token: [github.com/settings/tokens](https://github.com/settings/tokens) (no special scopes needed for public repos). Add it to `.env` as `GITHUB_TOKEN`.

---

## AI providers

| Provider | Cost | Model | Best for |
|----------|------|-------|---------|
| `gemini` (default) | Free — 250 req/day | gemini-2.5-flash | Most repos |
| `claude` | ~$0.03–0.10/story | claude-sonnet-4-6 | Best writing quality |
| `openai` | ~$0.03–0.10/story | gpt-4o | Strong alternative |

---

## License

MIT
