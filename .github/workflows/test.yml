name: TorrentDia URL Finder

on:
  workflow_dispatch:
  schedule:
    - cron: "*/30 * * * *"

permissions:
  contents: write

jobs:
  find-url:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Find latest TorrentDia URL
        run: |
          python parser.py > finder_output.txt
          cat finder_output.txt

          URL=$(grep '^LATEST_URL=' finder_output.txt | cut -d= -f2-)

          if [ -z "$URL" ]; then
            echo "No valid TorrentDia URL found."
            exit 1
          fi

          python - "$URL" <<'PY'
          import json
          import sys

          url = sys.argv[1]

          data = {
              "success": True,
              "url": url
          }

          with open("result.json", "w", encoding="utf-8") as f:
              json.dump(data, f, ensure_ascii=False, indent=2)
              f.write("\n")
          PY

      - name: Update result.json
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

          git add result.json

          if git diff --cached --quiet; then
            echo "No URL change."
          else
            git commit -m "Update latest TorrentDia URL"
            git push
          fi
