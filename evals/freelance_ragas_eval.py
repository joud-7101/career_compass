"""Ragas edge-case evaluation for the CareerCompass freelancer agent.

This runner keeps retrieval deterministic by replacing the live tools with
fixture values from freelance_edge_cases.json, then evaluates the generated
answer against those same contexts.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "evals" / "freelance_edge_cases.json"

sys.path.insert(0, str(ROOT))

from datasets import Dataset
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas import evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import answer_relevancy, answer_correctness, faithfulness

import backend.agents.freelance_agent as freelance_module


class StaticTool:
    """Small stand-in for LangChain StructuredTool fixtures."""

    def __init__(self, value: Any):
        self.value = value

    def invoke(self, payload: dict) -> Any:
        return self.value


def _as_context(case: dict) -> str:
    evidence = {
        "historical_market_analysis": case["market_analysis"],
        "live_freelancer_api_results": case["live_projects"],
        "live_web_search_results": case["web_opportunities"],
    }
    return json.dumps(evidence, ensure_ascii=False, indent=2)


def _run_agent_with_case(case: dict) -> str:
    original_market = freelance_module.analyze_historical_market
    original_api = freelance_module.search_freelancer_api
    original_web = freelance_module.search_freelance_projects

    try:
        freelance_module.analyze_historical_market = (
            lambda skills: case["market_analysis"]
        )
        freelance_module.search_freelancer_api = StaticTool(case["live_projects"])
        freelance_module.search_freelance_projects = StaticTool(
            case["web_opportunities"]
        )
        result = freelance_module.freelance_agent(case["state"])
        return result["freelance_analysis"]
    finally:
        freelance_module.analyze_historical_market = original_market
        freelance_module.search_freelancer_api = original_api
        freelance_module.search_freelance_projects = original_web


def _load_cases(path: Path, case_id: str | None) -> list[dict]:
    cases = json.loads(path.read_text(encoding="utf-8"))
    if case_id:
        cases = [case for case in cases if case["id"] == case_id]
        if not cases:
            raise ValueError(f"No freelance eval case found for id: {case_id}")
    return cases


def _guardrail_checks(case: dict, answer: str) -> list[str]:
    failures = []
    answer_lower = answer.lower()

    for text in case.get("must_include", []):
        if text.lower() not in answer_lower:
            failures.append(f"missing required text: {text!r}")

    for text in case.get("must_not_include", []):
        if text.lower() in answer_lower:
            failures.append(f"contains forbidden text: {text!r}")

    return failures


def _build_dataset(cases: list[dict], answers: list[str]) -> Dataset:
    return Dataset.from_dict(
        {
            "question": [
                case["state"].get("query", "")
                for case in cases
            ],
            "answer": answers,
            "contexts": [[_as_context(case)] for case in cases],
            "ground_truth": [case["reference"] for case in cases],
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Ragas edge-case evals for the freelancer agent."
    )
    parser.add_argument("--case-id", help="Run one case from the JSON fixture.")
    parser.add_argument(
        "--cases",
        type=Path,
        default=CASES_PATH,
        help="Path to the freelance edge-case JSON fixture.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "evals" / "freelance_ragas_results.csv",
        help="Where to write the per-case Ragas scores.",
    )
    args = parser.parse_args()

    cases = _load_cases(args.cases, args.case_id)
    answers = [_run_agent_with_case(case) for case in cases]

    dataset = _build_dataset(cases, answers)

    evaluator_llm = LangchainLLMWrapper(
        ChatOpenAI(model="gpt-4o-mini", temperature=0)
    )
    evaluator_embeddings = LangchainEmbeddingsWrapper(
        OpenAIEmbeddings(model="text-embedding-3-small")
    )

    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, answer_correctness],
        llm=evaluator_llm,
        embeddings=evaluator_embeddings,
        raise_exceptions=False,
    )

    df = result.to_pandas()
    df.insert(0, "case_id", [case["id"] for case in cases])
    df.insert(1, "description", [case["description"] for case in cases])
    df["guardrail_failures"] = [
        "; ".join(_guardrail_checks(case, answer))
        for case, answer in zip(cases, answers, strict=True)
    ]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)

    print(df[[
        "case_id",
        "faithfulness",
        "answer_relevancy",
        "answer_correctness",
        "guardrail_failures",
    ]].to_string(index=False))
    print(f"\nSaved detailed results to: {args.out}")


if __name__ == "__main__":
    main()
