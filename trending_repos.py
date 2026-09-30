import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DURATIONS = {
    "day": 1,
    "week": 7,
    "month": 30,
    "year": 365
}


def get_start_date(duration):
    today = datetime.now(timezone.utc).date()
    return today - timedelta(days=DURATIONS[duration])


def fetch_repositories(duration, limit):
    start_date = get_start_date(duration)

    params = urlencode({
        "q": f"created:>={start_date}",
        "sort": "stars",
        "order": "desc",
        "per_page": limit
    })

    url = f"https://api.github.com/search/repositories?{params}"

    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "github-trending-cli"
        }
    )

    try:
        with urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("items", [])

    except HTTPError as error:
        if error.code == 403:
            print("Error: GitHub API rate limit exceeded.")
        elif error.code == 422:
            print("Error: Invalid GitHub API request.")
        else:
            print(f"Error: GitHub API returned status {error.code}.")
        sys.exit(1)

    except URLError:
        print("Error: Unable to connect to GitHub.")
        sys.exit(1)

    except TimeoutError:
        print("Error: Request timed out.")
        sys.exit(1)

    except json.JSONDecodeError:
        print("Error: Invalid response from GitHub.")
        sys.exit(1)


def display_repositories(repositories):
    if not repositories:
        print("No repositories found.")
        return

    for index, repo in enumerate(repositories, start=1):
        name = repo.get("full_name", "Unknown")
        description = repo.get("description") or "No description"
        stars = repo.get("stargazers_count", 0)
        language = repo.get("language") or "Not specified"

        print(f"{index}. {name}")
        print(f"   Description: {description}")
        print(f"   Stars: {stars}")
        print(f"   Language: {language}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Show trending GitHub repositories."
    )

    parser.add_argument(
        "--duration",
        choices=["day", "week", "month", "year"],
        default="week",
        help="Time range (default: week)"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of repositories to display (default: 10)"
    )

    args = parser.parse_args()

    if args.limit < 1 or args.limit > 100:
        print("Error: limit must be between 1 and 100.")
        sys.exit(1)

    print(
        f"\nTrending repositories for the past {args.duration}"
        f" ({args.limit} results)\n"
    )

    repositories = fetch_repositories(
        args.duration,
        args.limit
    )

    display_repositories(repositories)


if __name__ == "__main__":
    main()