"""Refresh the recent-projects section in the profile README."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.request import Request, urlopen


USERNAME = "tpwls9494"
README_PATH = Path(__file__).resolve().parents[1] / "README.md"
START_MARKER = "<!-- RECENT-PROJECTS:START -->"
END_MARKER = "<!-- RECENT-PROJECTS:END -->"
PROJECT_LIMIT = 3


def fetch_repositories() -> list[dict[str, object]]:
    url = f"https://api.github.com/users/{USERNAME}/repos?type=owner&sort=pushed&per_page=100"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{USERNAME}-profile-readme",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    with urlopen(Request(url, headers=headers), timeout=20) as response:
        return json.load(response)


def clean(value: object, fallback: str) -> str:
    text = str(value or fallback).replace("\r", " ").replace("\n", " ")
    return " ".join(text.split()).replace("|", "\\|")


def select_projects(repositories: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        repo
        for repo in repositories
        if not repo.get("fork")
        and not repo.get("archived")
        and repo.get("name") != USERNAME
    ][:PROJECT_LIMIT]


def render_project(repo: dict[str, object]) -> str:
    name = clean(repo.get("name"), "Untitled repository")
    url = clean(repo.get("html_url"), f"https://github.com/{USERNAME}")
    description = clean(repo.get("description"), "A project in active development")
    language = clean(repo.get("language"), "Mixed")
    pushed_at = str(repo.get("pushed_at") or "")[:10]
    updated = f" · updated `{pushed_at}`" if pushed_at else ""
    return f"- **[{name}]({url})** — {description} · `{language}`{updated}"


def update_readme(projects: list[dict[str, object]]) -> None:
    readme = README_PATH.read_text(encoding="utf-8")
    if readme.count(START_MARKER) != 1 or readme.count(END_MARKER) != 1:
        raise RuntimeError("README must contain exactly one recent-project marker pair")

    before, remainder = readme.split(START_MARKER, maxsplit=1)
    _, after = remainder.split(END_MARKER, maxsplit=1)
    project_lines = "\n".join(render_project(repo) for repo in projects)
    refreshed = f"{before}{START_MARKER}\n{project_lines}\n{END_MARKER}{after}"
    README_PATH.write_text(refreshed, encoding="utf-8")


def main() -> None:
    projects = select_projects(fetch_repositories())
    if not projects:
        raise RuntimeError("GitHub API returned no eligible repositories")
    update_readme(projects)


if __name__ == "__main__":
    main()
