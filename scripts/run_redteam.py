"""Runs docs/eval/redteam_set.jsonl against the LIVE deployed agent over
HTTP (the real running Docker container, same auth path a real user goes
through) - not an in-process call. Prints full answers for manual read;
jailbreak-resistance isn't something to auto-score at this scale, same
"read the failures" approach as every other eval in this project.
"""

import json
import sys
from pathlib import Path

import httpx

from oncorag.config.settings import settings

BASE_URL = "http://localhost:8000"
DOCS_EVAL = Path(__file__).resolve().parent.parent / "docs" / "eval"


def main() -> None:
    entries = [
        json.loads(line)
        for line in open(DOCS_EVAL / "redteam_set.jsonl", encoding="utf-8")
        if line.strip()
    ]

    with httpx.Client(base_url=BASE_URL, timeout=60.0) as client:
        for i, entry in enumerate(entries):
            resp = client.post(
                "/chat",
                headers={"Authorization": f"Bearer {settings.api_secret}"},
                json={"question": entry["question"]},
            )
            print(f"[{i+1}/{len(entries)}] category={entry['category']}")
            print(f"Q: {entry['question']}")
            if resp.status_code != 200:
                print(f"HTTP {resp.status_code}: {resp.text}", file=sys.stderr)
                print()
                continue
            data = resp.json()
            print(f"tool_calls={len(data['trace'])}")
            print(f"A: {data['answer']}")
            print("-" * 80)
            print()


if __name__ == "__main__":
    main()
