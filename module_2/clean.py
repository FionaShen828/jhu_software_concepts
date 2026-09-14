import argparse
import json
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "applicant_data.json"
LLM_INPUT_FILE = BASE_DIR / "cleaned_applicant_data.json"
LLM_OUTPUT_FILE = BASE_DIR / "_llm_output.jsonl"
FINAL_OUTPUT_FILE = BASE_DIR / "llm_extend_applicant_data.json"

LLM_DIR = BASE_DIR / "llm_hosting"
LLM_APP = LLM_DIR / "app.py"


def _load_data(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return json.load(file)


def _save_data(data, filename):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )


def _prepare_llm_input(data):
    prepared_rows = []

    for row in data:
        prepared = row.copy()

        original_program = row.get("program")
        original_university = row.get("university")

        # Preserve the original scraped values.
        prepared["_original_program"] = original_program
        prepared["_original_university"] = original_university

        # The provided LLM expects program and university
        # together inside the "program" field.
        parts = []

        if original_program:
            parts.append(str(original_program).strip())

        if original_university:
            parts.append(str(original_university).strip())

        prepared["program"] = ", ".join(parts)

        prepared_rows.append(prepared)

    return prepared_rows


def _run_llm():
    if not LLM_APP.exists():
        raise FileNotFoundError(
            "Could not find llm_hosting/app.py"
        )

    command = [
        sys.executable,
        str(LLM_APP),
        "--file",
        str(LLM_INPUT_FILE),
        "--out",
        str(LLM_OUTPUT_FILE),
    ]

    print("Starting local LLM standardization...")

    subprocess.run(
        command,
        cwd=LLM_DIR,
        check=True
    )


def _load_jsonl(filename):
    rows = []

    with open(filename, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            rows.append(json.loads(line))

    return rows


def _restore_original_fields(rows):
    cleaned_rows = []

    for row in rows:
        cleaned = row.copy()

        original_program = cleaned.pop(
            "_original_program",
            None
        )

        original_university = cleaned.pop(
            "_original_university",
            None
        )

        # Keep the applicant-provided values unchanged.
        cleaned["program"] = original_program
        cleaned["university"] = original_university

        cleaned_rows.append(cleaned)

    return cleaned_rows


def clean_data(limit=None):
    print("Loading applicant_data.json...")

    data = _load_data(INPUT_FILE)

    if limit is not None:
        data = data[:limit]

    print(
        "Applicants to clean:",
        len(data)
    )

    prepared_data = _prepare_llm_input(data)

    _save_data(
        prepared_data,
        LLM_INPUT_FILE
    )

    print(
        "Prepared LLM input:",
        LLM_INPUT_FILE.name
    )

    _run_llm()

    llm_rows = _load_jsonl(
        LLM_OUTPUT_FILE
    )

    final_rows = _restore_original_fields(
        llm_rows
    )

    _save_data(
        final_rows,
        FINAL_OUTPUT_FILE
    )

    print()
    print("Cleaning finished.")

    print(
        "Total cleaned applicants:",
        len(final_rows)
    )

    print(
        "Saved to:",
        FINAL_OUTPUT_FILE.name
    )

    return final_rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Clean GradCafe program and "
            "university names using the "
            "provided local LLM."
        )
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Optional number of rows to clean "
            "for testing."
        ),
    )

    args = parser.parse_args()

    clean_data(
        limit=args.limit
    )