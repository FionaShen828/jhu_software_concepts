import sys
import json
import subprocess
from pathlib import Path

import pytest

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import clean


@pytest.mark.analysis
def test_load_and_save_data(tmp_path):
    file_path = tmp_path / "data.json"

    data = [
        {
            "program": "Computer Science",
            "university": "Johns Hopkins University",
        }
    ]

    clean._save_data(data, file_path)

    loaded = clean._load_data(file_path)

    assert loaded == data


@pytest.mark.analysis
def test_make_key():
    key = clean._make_key(
        " Computer Science ",
        " Johns Hopkins University ",
    )

    expected = json.dumps(
        [
            "Computer Science",
            "Johns Hopkins University",
        ],
        ensure_ascii=False,
    )

    assert key == expected

    empty_key = clean._make_key(None, None)

    assert empty_key == json.dumps(
        ["", ""],
        ensure_ascii=False,
    )


@pytest.mark.analysis
def test_load_checkpoint_missing(
    monkeypatch,
    tmp_path,
):
    checkpoint_file = tmp_path / "missing.json"

    monkeypatch.setattr(
        clean,
        "CHECKPOINT_FILE",
        checkpoint_file,
    )

    assert clean._load_checkpoint() == {}


@pytest.mark.analysis
def test_load_checkpoint_valid(
    monkeypatch,
    tmp_path,
):
    checkpoint_file = tmp_path / "checkpoint.json"

    checkpoint = {
        "test-key": {
            "llm-generated-program": "Computer Science",
            "llm-generated-university": "JHU",
        }
    }

    with open(
        checkpoint_file,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(checkpoint, file)

    monkeypatch.setattr(
        clean,
        "CHECKPOINT_FILE",
        checkpoint_file,
    )

    assert clean._load_checkpoint() == checkpoint


@pytest.mark.analysis
def test_load_checkpoint_invalid(
    monkeypatch,
    tmp_path,
):
    checkpoint_file = tmp_path / "checkpoint.json"

    checkpoint_file.write_text(
        "not valid json",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        clean,
        "CHECKPOINT_FILE",
        checkpoint_file,
    )

    assert clean._load_checkpoint() == {}


@pytest.mark.analysis
def test_save_checkpoint(
    monkeypatch,
    tmp_path,
):
    checkpoint_file = tmp_path / "checkpoint.json"

    monkeypatch.setattr(
        clean,
        "CHECKPOINT_FILE",
        checkpoint_file,
    )

    checkpoint = {
        "key": {
            "llm-generated-program": "Data Science",
            "llm-generated-university": "JHU",
        }
    }

    clean._save_checkpoint(checkpoint)

    with open(
        checkpoint_file,
        "r",
        encoding="utf-8",
    ) as file:
        saved = json.load(file)

    assert saved == checkpoint


@pytest.mark.analysis
def test_build_unique_rows():
    data = [
        {
            "program": "Computer Science",
            "university": "JHU",
        },
        {
            "program": "Computer Science",
            "university": "JHU",
        },
        {
            "program": "Data Science",
            "university": "Stanford",
        },
        {
            "program": None,
            "university": "MIT",
        },
    ]

    completed_key = clean._make_key(
        "Data Science",
        "Stanford",
    )

    checkpoint = {
        completed_key: {
            "llm-generated-program": "Data Science",
            "llm-generated-university": "Stanford University",
        }
    }

    rows = clean._build_unique_rows(
        data,
        checkpoint,
    )

    assert len(rows) == 2

    assert rows[0]["program"] == (
        "Computer Science, JHU"
    )

    assert rows[1]["program"] == "MIT"

    assert "_cleaning_key" in rows[0]
    assert "_cleaning_key" in rows[1]


@pytest.mark.analysis
def test_run_llm_empty_rows():
    assert clean._run_llm([]) == []


@pytest.mark.analysis
def test_run_llm_missing_app(
    monkeypatch,
    tmp_path,
):
    missing_app = tmp_path / "missing_app.py"

    monkeypatch.setattr(
        clean,
        "LLM_APP",
        missing_app,
    )

    with pytest.raises(
        FileNotFoundError,
        match="Could not find llm_hosting/app.py",
    ):
        clean._run_llm(
            [
                {
                    "_cleaning_key": "key",
                    "program": "Computer Science, JHU",
                }
            ]
        )


@pytest.mark.analysis
def test_run_llm_success(
    monkeypatch,
    tmp_path,
):
    llm_dir = tmp_path / "llm_hosting"
    llm_dir.mkdir()

    llm_app = llm_dir / "app.py"
    llm_app.write_text(
        "# fake app",
        encoding="utf-8",
    )

    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.jsonl"

    monkeypatch.setattr(
        clean,
        "LLM_DIR",
        llm_dir,
    )

    monkeypatch.setattr(
        clean,
        "LLM_APP",
        llm_app,
    )

    monkeypatch.setattr(
        clean,
        "LLM_INPUT_FILE",
        input_file,
    )

    monkeypatch.setattr(
        clean,
        "LLM_OUTPUT_FILE",
        output_file,
    )

    llm_result = [
        {
            "_cleaning_key": "key-1",
            "llm-generated-program": "Computer Science",
            "llm-generated-university": (
                "Johns Hopkins University"
            ),
        }
    ]

    def fake_run(command, cwd, check):
        with open(
            output_file,
            "w",
            encoding="utf-8",
        ) as file:
            for row in llm_result:
                file.write(
                    json.dumps(row) + "\n"
                )

    monkeypatch.setattr(
        clean.subprocess,
        "run",
        fake_run,
    )

    rows = [
        {
            "_cleaning_key": "key-1",
            "program": (
                "Computer Science, "
                "Johns Hopkins University"
            ),
        }
    ]

    result = clean._run_llm(rows)

    assert result == llm_result
    assert input_file.exists()


@pytest.mark.analysis
def test_load_jsonl(tmp_path):
    jsonl_file = tmp_path / "output.jsonl"

    jsonl_file.write_text(
        '{"value": 1}\n\n{"value": 2}\n',
        encoding="utf-8",
    )

    result = clean._load_jsonl(jsonl_file)

    assert result == [
        {"value": 1},
        {"value": 2},
    ]


@pytest.mark.analysis
def test_update_checkpoint(
    monkeypatch,
):
    checkpoint = {}

    saved = {}

    def fake_save(value):
        saved["checkpoint"] = value.copy()

    monkeypatch.setattr(
        clean,
        "_save_checkpoint",
        fake_save,
    )

    rows = [
        {
            "_cleaning_key": "key-1",
            "llm-generated-program": "Computer Science",
            "llm-generated-university": "JHU",
        },
        {
            "_cleaning_key": None,
            "llm-generated-program": "Ignored",
            "llm-generated-university": "Ignored",
        },
    ]

    clean._update_checkpoint(
        rows,
        checkpoint,
    )

    assert "key-1" in checkpoint
    assert len(checkpoint) == 1

    assert (
        checkpoint["key-1"][
            "llm-generated-program"
        ]
        == "Computer Science"
    )

    assert saved["checkpoint"] == checkpoint


@pytest.mark.analysis
def test_build_final_output():
    data = [
        {
            "program": "Computer Science",
            "university": "JHU",
            "url": "https://example.com/1",
        },
        {
            "program": "Data Science",
            "university": "MIT",
            "url": "https://example.com/2",
        },
    ]

    key = clean._make_key(
        "Computer Science",
        "JHU",
    )

    checkpoint = {
        key: {
            "llm-generated-program": (
                "Computer Science"
            ),
            "llm-generated-university": (
                "Johns Hopkins University"
            ),
        }
    }

    result = clean._build_final_output(
        data,
        checkpoint,
    )

    assert len(result) == 2

    assert (
        result[0]["llm-generated-program"]
        == "Computer Science"
    )

    assert (
        result[0]["llm-generated-university"]
        == "Johns Hopkins University"
    )

    assert (
        result[1]["llm-generated-program"]
        is None
    )

    assert (
        result[1]["llm-generated-university"]
        is None
    )


@pytest.mark.integration
@pytest.mark.analysis
def test_clean_data(
    monkeypatch,
    tmp_path,
    capsys,
):
    input_file = tmp_path / "applicant_data.json"
    final_file = tmp_path / "final.json"
    checkpoint_file = tmp_path / "checkpoint.json"

    data = [
        {
            "program": "Computer Science",
            "university": "JHU",
            "url": "https://example.com/1",
        },
        {
            "program": "Data Science",
            "university": "MIT",
            "url": "https://example.com/2",
        },
        {
            "program": "Computer Science",
            "university": "JHU",
            "url": "https://example.com/3",
        },
    ]

    with open(
        input_file,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(data, file)

    monkeypatch.setattr(
        clean,
        "INPUT_FILE",
        input_file,
    )

    monkeypatch.setattr(
        clean,
        "FINAL_OUTPUT_FILE",
        final_file,
    )

    monkeypatch.setattr(
        clean,
        "CHECKPOINT_FILE",
        checkpoint_file,
    )

    def fake_run_llm(rows):
        results = []

        for row in rows:
            results.append(
                {
                    "_cleaning_key": (
                        row["_cleaning_key"]
                    ),
                    "llm-generated-program": (
                        "Clean Program"
                    ),
                    "llm-generated-university": (
                        "Clean University"
                    ),
                }
            )

        return results

    monkeypatch.setattr(
        clean,
        "_run_llm",
        fake_run_llm,
    )

    result = clean.clean_data(
        limit=3,
        batch_size=1,
    )

    output = capsys.readouterr().out

    assert len(result) == 3

    assert (
        result[0]["llm-generated-program"]
        == "Clean Program"
    )

    assert (
        result[0]["llm-generated-university"]
        == "Clean University"
    )

    assert final_file.exists()
    assert checkpoint_file.exists()

    assert "Applicant records: 3" in output
    assert "Cleaning finished." in output
    assert "Total cleaned applicants: 3" in output