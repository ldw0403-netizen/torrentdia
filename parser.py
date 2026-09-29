#!/usr/bin/env python3

import json
import re
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

TELEGRAPH_URL = "https://telegra.ph/torrentdia-url-06-13"

DOMAIN_PATTERN = re.compile(
    r"https?://(?:www\.)?([a-zA-Z0-9-]+)\.torrentdia\.org"
    r"(?::\d+)?(?:/[^\s\"'<>)\]]*)?",
    re.IGNORECASE
)

HOST_PATTERN = re.compile(
    r"\b([a-zA-Z0-9-]+)\.torrentdia\.org\b",
    re.IGNORECASE
)


def fetch_telegraph():
    request = Request(
        TELEGRAPH_URL,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    with urlopen(request, timeout=10) as response:
        return response.read().decode("utf-8", errors="ignore")


def extract_candidates(html):
    candidates = []

    for match in DOMAIN_PATTERN.finditer(html):
        url = match.group(0).rstrip("/")
        candidates.append(url)

    for match in HOST_PATTERN.finditer(html):
        url = "https://" + match.group(1) + ".torrentdia.org"
        candidates.append(url)

    result = []

    for url in candidates:
        if url not in result:
            result.append(url)

    return result


def check_url(url):
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
        method="GET"
    )

    try:
        with urlopen(request, timeout=6) as response:
            status = response.getcode()

            return {
                "url": url,
                "valid": 200 <= status < 400,
                "status": status
            }

    except HTTPError as error:
        return {
            "url": url,
            "valid": False,
            "status": error.code
        }

    except (URLError, TimeoutError, OSError):
        return {
            "url": url,
            "valid": False,
            "status": None
        }


def find_latest_url():
    html = fetch_telegraph()
    candidates = extract_candidates(html)

    if not candidates:
        raise RuntimeError(
            "Telegraph에서 TorrentDia 주소를 찾지 못했습니다."
        )

    results = []

    for url in candidates:
        result = check_url(url)
        results.append(result)

        if result["valid"]:
            return {
                "success": True,
                "source": TELEGRAPH_URL,
                "url": url,
                "candidates": results
            }

    return {
        "success": False,
        "source": TELEGRAPH_URL,
        "url": None,
        "candidates": results
    }


def main():
    try:
        result = find_latest_url()

        print(json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        ))

        if result["success"]:
            print()
            print("LATEST_URL=" + result["url"])

    except Exception as error:
        print(json.dumps({
            "success": False,
            "source": TELEGRAPH_URL,
            "url": None,
            "error": str(error)
        }, ensure_ascii=False, indent=2))

        sys.exit(1)


if __name__ == "__main__":
    main()
