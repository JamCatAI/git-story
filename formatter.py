import os
import re
from datetime import datetime

from rich.console import Console
from rich.markdown import Markdown
from rich.rule import Rule
from rich.table import Table

console = Console()


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")[:60]


def print_story(stats: dict, story: str) -> None:
    console.print()
    console.print(Rule(f"[bold magenta]{stats['name']}[/bold magenta]"))

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="dim")
    table.add_column("Value")
    table.add_row("Language", stats["language"])
    table.add_row("Stars", f"{stats['stars']:,}")
    table.add_row("Age", f"{stats['age_years']} years ({stats['created']} → {stats['last_commit']})")
    table.add_row("Contributors", str(stats["contributor_count"]))
    table.add_row("Trend", stats["commit_trend"])
    table.add_row("License", stats["license"])
    console.print(table)
    console.print()
    console.print(Markdown(story))
    console.print()


def save_story(stats: dict, stats_text: str, story: str, output_dir: str = "./output") -> str:
    os.makedirs(output_dir, exist_ok=True)
    slug = slugify(stats["name"].replace("/", "-"))
    filepath = os.path.join(output_dir, f"{slug}-story.md")
    date = datetime.now().strftime("%Y-%m-%d")

    content = f"""# The Story of {stats['name']}

**Language:** {stats['language']} · **Stars:** {stats['stars']:,} · **License:** {stats['license']}
**Created:** {stats['created']} · **Last commit:** {stats['last_commit']}
**Generated:** {date}

---

{story}

---

## Raw Data

{stats_text}

---

*Generated with [git-story](https://github.com/JamCatAI/git-story)*
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath
