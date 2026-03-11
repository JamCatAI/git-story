import argparse
import os
import sys

from dotenv import load_dotenv
from rich.console import Console

load_dotenv()

console = Console()

PROVIDERS = ["gemini", "claude", "openai", "groq"]
API_KEY_MAP = {
    "gemini": "GEMINI_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "groq": "GROQ_API_KEY",
}


def validate_key(provider: str):
    key = API_KEY_MAP[provider]
    if not os.environ.get(key):
        console.print(f"[red]Error: {key} not set. Add it to your .env file.[/red]")
        if provider == "gemini":
            console.print("[dim]Free key: https://aistudio.google.com/app/apikey[/dim]")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Turn any GitHub repo's commit history into a narrative story.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py https://github.com/fastapi/fastapi
  python main.py fastapi/fastapi
  python main.py torvalds/linux --limit 1000 --provider claude
  python main.py redis/redis --no-llm
        """,
    )
    parser.add_argument("repo", help="GitHub repo URL or owner/repo")
    parser.add_argument("--provider", choices=PROVIDERS, default="gemini")
    parser.add_argument("--token", default=None, help="GitHub personal access token (raises rate limit from 60 to 5000 req/hr)")
    parser.add_argument("--limit", type=int, default=500, help="Max commits to fetch (default: 500)")
    parser.add_argument("--no-llm", action="store_true", help="Output raw stats only, skip narrative")
    parser.add_argument("--output-dir", default="./output")
    args = parser.parse_args()

    token = args.token or os.environ.get("GITHUB_TOKEN")

    if not args.no_llm:
        validate_key(args.provider)

    from fetcher import parse_repo, fetch_all
    from analyzer import analyze, to_text
    from narrator import narrate
    from formatter import print_story, save_story

    # --- Fetch ---
    try:
        owner, name = parse_repo(args.repo)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)

    console.print(f"\n[bold cyan]Fetching:[/bold cyan] {owner}/{name}")
    if not token:
        console.print("[dim]No GitHub token — using unauthenticated API (60 req/hr limit). Set GITHUB_TOKEN in .env for more.[/dim]")

    try:
        data = fetch_all(owner, name, token=token, max_commits=args.limit)
    except Exception as e:
        console.print(f"[red]Fetch failed: {e}[/red]")
        sys.exit(1)

    repo = data["repo"]
    console.print(f"[green]✓[/green] {repo['full_name']} — {repo.get('stargazers_count', 0):,} stars · {repo.get('language', '?')}")
    console.print(f"[dim]{len(data['commits'])} commits · {len(data['releases'])} releases · {len(data['contributors'])} contributors[/dim]")

    # --- Analyze ---
    console.print(f"[bold cyan]Analyzing...[/bold cyan]")
    stats = analyze(data)
    stats_text = to_text(stats)
    console.print(f"[green]✓[/green] Trend: {stats['commit_trend']} · Peak: {stats['peak_month']} ({stats['peak_commit_count']} commits)")

    # --- Narrate ---
    if args.no_llm:
        story = stats_text
    else:
        console.print(f"[bold cyan]Writing story with {args.provider}...[/bold cyan]")
        try:
            story = narrate(stats_text, repo["full_name"], provider=args.provider)
            console.print(f"[green]✓[/green] Story complete")
        except Exception as e:
            console.print(f"[red]LLM failed: {e}[/red]")
            story = stats_text

    # --- Output ---
    print_story(stats, story)
    filepath = save_story(stats, stats_text, story, output_dir=args.output_dir)
    console.print(f"[dim]Saved to: {filepath}[/dim]\n")


if __name__ == "__main__":
    main()
