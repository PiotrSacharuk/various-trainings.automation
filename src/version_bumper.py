"""
Smart version bumping based on conventional commits
Usage: python version_bumper.py
"""

import os
import re
from typing import Tuple

from git import Repo


def parse_version(tag_str: str) -> Tuple[int, int, int]:
    """Parse semantic version from tag string."""
    version = tag_str.lstrip("v")
    try:
        parts = version.split(".")
        return (int(parts[0]), int(parts[1]), int(parts[2]))
    except (IndexError, ValueError):
        return (0, 0, 0)


def get_last_tag() -> str:
    """Get the last git tag, or return v0.0.0 if none exists"""
    try:
        repo = Repo(".")
        if not repo.tags:
            return "v0.0.0"

        # Sort by semantic version, not by date
        sorted_tags = sorted(repo.tags, key=lambda t: parse_version(str(t)))
        return str(sorted_tags[-1])
    except Exception as e:
        print(f"Error getting last tag: {e}")
        return "v0.0.0"


def get_commits_since_tag(tag: str) -> str:
    """Get all commits since the given tag."""
    try:
        repo = Repo(".")
        if tag == "v0.0.0":
            # Get all commits
            commits = list(repo.iter_commits())
        else:
            # Get commits since tag
            commits = list(repo.iter_commits(f"{tag}..HEAD"))

        # Reverse to show oldest first (chronological order)
        commits = list(reversed(commits))

        # Extract commit messages
        commit_messages = [commit.message.split("\n")[0] for commit in commits]
        return "\n".join(commit_messages)
    except Exception as e:
        print(f"Error getting commits: {e}")
        return ""


def analyze_commits(commits: str) -> Tuple[bool, bool, bool]:
    """
    Analyze commits and return (has_release, has_feat, has_fix).

    - release: → MAJOR
    - feat: → MINOR
    - fix: → PATCH
    """
    has_release = False
    has_feat = False
    has_fix = False

    if not commits:
        return has_release, has_feat, has_fix

    for line in commits.split("\n"):
        line = line.strip()
        if not line:
            continue

        print(f"  {line}")

        if re.match(r"^release(\(.+\))?:", line):
            has_release = True
            print("    → RELEASE detected (MAJOR)")
        elif re.match(r"^feat(\(.+\))?:", line):
            has_feat = True
            print("    → FEAT detected (MINOR)")
        elif re.match(r"^fix(\(.+\))?:", line):
            has_fix = True
            print("    → FIX detected (PATCH)")

    return has_release, has_feat, has_fix


def bump_version(version: str, bump_type: str) -> str:
    """
    Bump version based on type.

    Args:
        version: Current version without 'v' prefix (e.g., "1.2.3")
        bump_type: One of 'major', 'minor', 'patch'

    Returns:
        New version without 'v' prefix
    """
    parts = version.split(".")
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1

    return f"{major}.{minor}.{patch}"


def main():
    print("Smart Version Bumper")
    print("=" * 50)

    # Get last tag
    last_tag = get_last_tag()
    last_version = last_tag.lstrip("v")
    print(f"Last tag: {last_tag} (version: {last_version})")

    # Get commits since tag
    print(f"\nCommits since {last_tag}:")
    commits = get_commits_since_tag(last_tag)

    if not commits:
        print("  (no commits)")
        new_version = last_version
        bump_reason = "no changes"
    else:
        # Analyze commits
        print("\nAnalysis:")
        has_release, has_feat, has_fix = analyze_commits(commits)

        # Determine bump type
        if has_release:
            new_version = bump_version(last_version, "major")
            bump_reason = "RELEASE"
        elif has_feat:
            new_version = bump_version(last_version, "minor")
            bump_reason = "FEAT"
        elif has_fix:
            new_version = bump_version(last_version, "patch")
            bump_reason = "FIX"
        else:
            new_version = last_version
            bump_reason = "no version bump needed"

    # Output results
    print("\nResults:")
    print(f"Old version: {last_version}")
    print(f"New version: {new_version}")
    print(f"Reason: {bump_reason}")

    # Write to GitHub Actions environment
    print("\nOutputs:")
    print(f"version={new_version}")
    print(f"version_tag=v{new_version}")

    try:
        output_file = os.environ.get("GITHUB_OUTPUT")
        if output_file:
            with open(output_file, "a") as f:
                f.write(f"version={new_version}\n")
                f.write(f"version_tag=v{new_version}\n")
    except Exception:  # nosec B110
        # Silently ignore if GITHUB_OUTPUT is not available (local execution)
        pass


if __name__ == "__main__":
    main()
