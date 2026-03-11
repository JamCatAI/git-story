SYSTEM_PROMPT = """You are a technology historian and narrative journalist who specializes in
writing about open source software. You write in the style of a documentary narrator —
clear, compelling, specific, and human. You find the story inside the data.

You do not write bullet points. You write prose. Each section should read like a chapter
in a book about this project. Reference actual commit messages, dates, and contributors
by name where possible. Make it feel alive.
"""

STORY_PROMPT = """Write the story of this GitHub repository based on the data below.

{stats_text}

Write the following sections as narrative prose (not bullet points):

## Origin
When did this project start, and why? What does the first commit tell us about the
creator's intent? What problem were they trying to solve?

## Early Days
What happened in the first months? Who showed up to help? What were the early
priorities based on the commit messages?

## The Build
How did the project grow? Were there pivots in direction? What do the releases and
major PRs reveal about how thinking evolved? Where was the peak of activity?

## The People
Who built this? Write a brief portrait of the top contributors based on their
commit patterns, timing, and messages. What do they seem to care about?

## The Present
What is the current state of the project? Is it active, dormant, or archived?
What does the recent commit trend tell us?

## The Verdict
In 2-3 sentences: what kind of project is this? Is it a scrappy experiment, a
quiet workhorse, an abandoned dream, or something that genuinely changed how
people work?
"""


def narrate(stats_text: str, repo_name: str, provider: str = "gemini") -> str:
    prompt = STORY_PROMPT.format(stats_text=stats_text)
    return _call(prompt, provider)


def _call(prompt: str, provider: str) -> str:
    if provider == "gemini":
        return _gemini(prompt)
    elif provider == "claude":
        return _claude(prompt)
    elif provider == "openai":
        return _openai(prompt)
    elif provider == "groq":
        return _groq(prompt)
    raise ValueError(f"Unknown provider: {provider}")


def _gemini(prompt: str) -> str:
    import os
    from google import genai
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[{"role": "user", "parts": [{"text": SYSTEM_PROMPT + "\n\n" + prompt}]}],
    )
    return response.text.strip()


def _claude(prompt: str) -> str:
    import os
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def _openai(prompt: str) -> str:
    import os
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=4096,
    )
    return response.choices[0].message.content.strip()


def _groq(prompt: str) -> str:
    import os
    from groq import Groq
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=4096,
    )
    return response.choices[0].message.content.strip()
