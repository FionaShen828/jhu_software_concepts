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

CHECKPOINT_FILE = BASE_DIR / "_llm_cleaning_checkpoint.json"

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


def _make_key(program, university):
    program = str(program or "").strip()
    university = str(university or "").strip()

    return json.dumps(
        [program, university],
        ensure_ascii=False
    )


def _load_checkpoint():
    if not CHECKPOINT_FILE.exists():
        return {}

    try:
        with open(
            CHECKPOINT_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_checkpoint(checkpoint):
    with open(
        CHECKPOINT_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            checkpoint,
            file,
            ensure_ascii=False,
            indent=2
        )


def _build_unique_rows(data, checkpoint):
    unique_rows = []
    seen = set()

    for row in data:
        program = row.get("program")
        university = row.get("university")

        key = _make_key(program, university)

        if key in checkpoint:
            continue

        if key in seen:
            continue

        seen.add(key)

        parts = []

        if program:
            parts.append(str(program).strip())

        if university:
            parts.append(str(university).strip())

        unique_rows.append(
            {
                "_cleaning_key": key,
                "program": ", ".join(parts)
            }
        )

    return unique_rows


def _run_llm(rows):
    if not rows:
        return []

    if not LLM_APP.exists():
        raise FileNotFoundError(
            "Could not find llm_hosting/app.py"
        )

    _save_data(
        rows,
        LLM_INPUT_FILE
    )

    command = [
        sys.executable,
        str(LLM_APP),
        "--file",
        str(LLM_INPUT_FILE),
        "--out",
        str(LLM_OUTPUT_FILE),
    ]

    print(
        "Starting local LLM standardization "
        f"for {len(rows)} unique combinations..."
    )

    subprocess.run(
        command,
        cwd=LLM_DIR,
        check=True
    )

    return _load_jsonl(
        LLM_OUTPUT_FILE
    )


def _load_jsonl(filename):
    rows = []

    with open(
        filename,
        "r",
        encoding="utf-8"
    ) as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            rows.append(
                json.loads(line)
            )

    return rows


def _update_checkpoint(llm_rows, checkpoint):
    for row in llm_rows:
        key = row.get("_cleaning_key")

        if not key:
            continue

        checkpoint[key] = {
            "llm-generated-program":
                row.get("llm-generated-program"),
            "llm-generated-university":
                row.get("llm-generated-university"),
        }

    _save_checkpoint(checkpoint)


def _build_final_output(data, checkpoint):
    final_rows = []

    for row in data:
        cleaned = row.copy()

        key = _make_key(
            row.get("program"),
            row.get("university")
        )

        result = checkpoint.get(key)

        if result:
            cleaned["llm-generated-program"] = (
                result.get(
                    "llm-generated-program"
                )
            )

            cleaned["llm-generated-university"] = (
                result.get(
                    "llm-generated-university"
                )
            )
        else:
            cleaned["llm-generated-program"] = None
            cleaned["llm-generated-university"] = None

        final_rows.append(cleaned)

    return final_rows


def clean_data(limit=None, batch_size=100):
    print("Loading applicant_data.json...")

    data = _load_data(INPUT_FILE)

    if limit is not None:
        data = data[:limit]

    print(
        "Applicant records:",
        len(data)
    )

    checkpoint = _load_checkpoint()

    print(
        "Previously cleaned unique combinations:",
        len(checkpoint)
    )

    remaining = _build_unique_rows(
        data,
        checkpoint
    )

    print(
        "Unique combinations remaining:",
        len(remaining)
    )

    while remaining:
        batch = remaining[:batch_size]

        print()
        print(
            f"Cleaning next batch of "
            f"{len(batch)} combinations..."
        )

        llm_rows = _run_llm(batch)

        _update_checkpoint(
            llm_rows,
            checkpoint
        )

        print(
            "Checkpoint saved. "
            f"Total unique combinations cleaned: "
            f"{len(checkpoint)}"
        )

        remaining = _build_unique_rows(
            data,
            checkpoint
        )

        print(
            "Unique combinations remaining:",
            len(remaining)
        )

    final_rows = _build_final_output(
        data,
        checkpoint
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
            "Clean GradCafe program and university "
            "names using the provided local LLM."
        )
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Optional number of applicant records "
            "to clean for testing."
        ),
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help=(
            "Number of unique program/university "
            "combinations processed per checkpoint batch."
        ),
    )

    args = parser.parse_args()

    clean_data(
        limit=args.limit,
        batch_size=args.batch_size
    )