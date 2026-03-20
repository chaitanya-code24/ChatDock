from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.chat_service import retrieve_sections_only


def normalize(text: str) -> str:
    return text.lower().strip()


def evaluate() -> None:
    dataset_path = Path(__file__).with_name("rag_eval.json")
    with dataset_path.open("r", encoding="utf-8") as f:
        tests = json.load(f)

    total_score = 0
    results = []

    for test in tests:
        query = test["query"]
        expected = [normalize(section) for section in test["expected_sections"]]

        try:
            retrieved = retrieve_sections_only(query)
        except Exception as e:
            print(f"Error for query '{query}': {e}")
            retrieved = []

        retrieved_norm = [normalize(section) for section in retrieved]

        match_count = 0
        for expected_section in expected:
            if any(expected_section in retrieved_section for retrieved_section in retrieved_norm):
                match_count += 1

        if match_count == len(expected):
            score = 3
        elif match_count > 0:
            score = 2
        else:
            score = 0

        total_score += score
        results.append(
            {
                "query": query,
                "expected": expected,
                "retrieved": retrieved_norm,
                "score": score,
            }
        )

    print("\n===== RESULTS =====\n")
    for result in results:
        print(f"{result['query']} -> {result['score']}")
        print(f"expected -> {result['expected']}")
        print(f"retrieved -> {result['retrieved']}\n")

    max_score = len(tests) * 3
    print(f"TOTAL SCORE: {total_score} / {max_score}")

    if total_score < 40:
        print("LEVEL: Broken")
    elif total_score < 50:
        print("LEVEL: Basic")
    else:
        print("LEVEL: Production Ready")


if __name__ == "__main__":
    evaluate()
