import json
import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.agents import job_agent as job_agent_module
from backend.agents.job_agent import job_agent

import pandas as pd

from datasets import Dataset
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from ragas import evaluate
from ragas.metrics import (
    answer_relevancy,
    answer_correctness,
    faithfulness,
)

CASES_FILE = Path(__file__).parent / "job_edge_cases.json"


class StaticTool:
    """Simple fixture-based replacement for a real tool."""

    def __init__(self, result):
        self.result = result

    def invoke(self, args=None):
        return self.result


def load_cases():
    with open(CASES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def run_case(case):
    print(f"\nRunning: {case['id']}")

    # Save original tools
    original_search = job_agent_module.search_jobs
    original_onet = job_agent_module.get_occupation_information
    original_resume = job_agent_module.get_required_skills

    try:
        # Replace real tools with static fixtures
        job_agent_module.search_jobs = StaticTool(
            case.get("job_results", [])
        )

        job_agent_module.get_occupation_information = StaticTool(
            case.get("onet_result", {})
        )

        job_agent_module.get_required_skills = StaticTool(
            case.get("resume_result", {})
        )

        # Run the REAL Job Agent
        result = job_agent(case["state"])

        return {
            "case_id": case["id"],
            "description": case.get("description", ""),
            "question": case["state"]["query"],
            "answer": result.get("job_analysis", ""),
            "ground_truth": case.get("reference", ""),
            "job_results": case.get("job_results", []),
            "onet_result": case.get("onet_result", {}),
            "resume_result": case.get("resume_result", {}),
        }

    finally:
        # Restore original tools
        job_agent_module.search_jobs = original_search
        job_agent_module.get_occupation_information = original_onet
        job_agent_module.get_required_skills = original_resume

def build_ragas_dataset(results):
    rows = []

    for result in results:
        contexts = []

        # Add job information
        if result.get("job_results"):
            contexts.append(
                "Job Search Results:\n"
                + json.dumps(
                    result["job_results"],
                    ensure_ascii=False,
                    default=str,
                )
            )

        # Add O*NET information
        if result.get("onet_result"):
            contexts.append(
                "O*NET Information:\n"
                + json.dumps(
                    result["onet_result"],
                    ensure_ascii=False,
                    default=str,
                )
            )

        # Add Resume information
        if result.get("resume_result"):
            contexts.append(
                "Resume Dataset Information:\n"
                + json.dumps(
                    result["resume_result"],
                    ensure_ascii=False,
                    default=str,
                )
            )

        rows.append(
            {
                "question": result["question"],
                "answer": result["answer"],
                "contexts": contexts,
                "reference": result["ground_truth"],
            }
        )

    return Dataset.from_list(rows)

if __name__ == "__main__":
    cases = load_cases()

    results = []

    for case in cases:
        results.append(run_case(case))

    print("\nEvaluation cases completed.")

    # Build RAGAS dataset
    dataset = build_ragas_dataset(results)

    # Evaluation models
    evaluator_llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
    )

    evaluator_embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small"
    )

    print("\nRunning RAGAS evaluation...")

    evaluation_result = evaluate(
        dataset=dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            answer_correctness,
        ],
        llm=evaluator_llm,
        embeddings=evaluator_embeddings,
    )

    # Convert results to DataFrame
    results_df = evaluation_result.to_pandas()

    # Add case IDs
    results_df.insert(
        0,
        "case_id",
        [result["case_id"] for result in results]
    )

    # Save results
    output_file = Path(__file__).parent / "job_ragas_results.csv"
    results_df.to_csv(output_file, index=False)

    print("\nRAGAS evaluation completed.")
    print(f"Results saved to: {output_file}")

    print("\nScores:")
    print(
        results_df[
            [
                "case_id",
                "faithfulness",
                "answer_relevancy",
                "answer_correctness",
            ]
        ].to_string(index=False)
    )