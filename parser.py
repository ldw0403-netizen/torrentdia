#!/usr/bin/env python3

import json
import re
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# ============================================================
# TorrentDia URL Finder
# Source: Telegraph
# ============================================================

TELEGRAPH_URL = "https://telegra.ph/torrentdia-url-06-13"

# torrentdia.org의 서브도메인을 폭넓게 인식
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
    """Telegraph 원문 HTML 가져오기"""
    request = Request(
        TELEGRAPH_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Android) "
                "AppleWebKit/537.36 "
                "Chrome/154.0 Mobile Safari/537.36"
            )
        }
    )

    with urlopen(request, timeout=10) as response:
        return response.read().decode("utf-8", errors="ignore")


def extract_candidates(html):
    """Telegraph에서 TorrentDia 주소 후보 추출"""
    candidates = []

    # 1. 실제 href / 텍스트에 들어있는 https 주소
    for match in DOMAIN_PATTERN.finditer(html):
        full_url = match.group(0)

        if not full_url.startswith("https://"):
            full_url = "https://" + full_url[full_url.find("//") + 2:]

        candidates.append(full_url.rstrip("/"))

    # 2. 주소가 링크가 아닌 일반 텍스트로 적혀있는 경우
    for match in HOST_PATTERN.finditer(html):
        host = match.group(1) + ".torrentdia.org"
        candidates.append("https://" + host)

    # 중복 제거 + 순서 유지
    result = []

    for url in candidates:
        if url not in result:
            result.append(url)

    return result


def check_url(url):
    """실제 HTTPS 접속 가능한 TorrentDia 주소인지 확인"""
    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Android) "
                "AppleWebKit/537.36 "
                "Chrome/154.0 Mobile Safari/537.36"
            )
        },
        method="GET"
    )

    try:
        with urlopen(request, timeout=6) as response:
            status = response.getcode()

            return {
                "url": url,
                "valid": 200 <= status < 500,
                "status": status
            }

    except HTTPError as error:
        # 403/404 등도 서버 자체가 존재하는지는 확인 가능하지만
        # 최종 주소로는 2xx~3xx를 우선한다.
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
    """Telegraph → 후보 추출 → 주소 검증"""

    html = fetch_telegraph()
    candidates = extract_candidates(html)

    if not candidates:
        raise RuntimeError(
            "Telegraph에서 TorrentDia 주소를 찾지 못했습니다."
        )

    # Telegraph에 실제로 올라온 후보만 검증
    results = []

    for url in candidates:
        result = check_url(url)
        results.append(result)

        # 정상 응답이면 즉시 반환
        if result["valid"] and result["status"] < 400:
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
        result = {
            "success": False,
            "source": TELEGRAPH_URL,
            "url": None,
            "error": str(error)
        }

        print(json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        ))

        sys.exit(1)


if __name__ == "__main__":
    main()
