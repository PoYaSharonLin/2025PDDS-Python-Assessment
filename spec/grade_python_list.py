#!/usr/bin/env python3
import ast
import glob
import os
import re
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, Tuple, Optional, List
import sys

import pandas as pd

SRC_DIR = "python_list_src"
OUTPUT_CSV = "output/python_list_grades.csv"
TIMEOUT_SECS = 8

# Expected answers
EXPECTED = {
    "joined": [
        {"name": "Alice", "total": 100},
        {"name": "Alice", "total": 150},
        {"name": "Bob",   "total": 200},
    ],
    "grouped": {
        "Alice": {"num_orders": 2, "total_spent": 250},
        "Bob":   {"num_orders": 1, "total_spent": 200},
    },
    "sorted_result": [
        ("Alice", {"num_orders": 2, "total_spent": 250}),
        ("Bob",   {"num_orders": 1, "total_spent": 200}),
    ],
    "top_user": ("Alice", {"num_orders": 2, "total_spent": 250}),
}

# Points
POINTS = {
    "joined": 15,
    "grouped": 30,
    "sorted_result": 15,
    "top_user": 10,
}

HEADERS = {
    "joined": "✅ Joined Result:",
    "grouped": "✅ Grouped Result:",
    "sorted_result": "✅ Sorted Result:",
    "top_user": "🏆 Top User:",
}


@dataclass
class GradeResult:
    student_id: str
    filename: str
    total: int
    breakdown: Dict[str, int]
    remarks: str
    raw_stdout: str
    raw_stderr: str


def safe_literal_eval(s: str) -> Any:
    """Safely evaluate a Python literal; returns None on failure."""
    try:
        return ast.literal_eval(s.strip())
    except Exception:
        return None


def extract_after_header(stdout: str, header: str) -> Optional[Any]:
    """
    Find `header` line, then parse the next non-empty line as a Python literal.
    Returns the parsed object or None if not found/parseable.
    """
    lines = stdout.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == header:
            # Find next non-empty line
            for j in range(i + 1, len(lines)):
                nxt = lines[j].strip()
                if nxt:
                    return safe_literal_eval(nxt)
            break
    return None


def compare_deep(a: Any, b: Any) -> bool:
    """
    Strict deep comparison allowing list/tuple equivalence only
    where expected uses that exact type.
    (i.e., order-sensitive for lists/tuples; dicts compared by value.)
    """
    return a == b


def grade_from_stdout(stdout: str) -> Tuple[int, Dict[str, int], List[str]]:
    breakdown: Dict[str, int] = {k: 0 for k in POINTS}
    remarks: List[str] = []

    # Extract each block
    parsed = {}
    for key, header in HEADERS.items():
        obj = extract_after_header(stdout, header)
        parsed[key] = obj
        if obj is None:
            remarks.append(f"Missing or unparsable output for: {key}")

    # Score each part if correct
    for key in POINTS:
        obj = parsed.get(key)
        exp = EXPECTED[key]
        if obj is not None and compare_deep(obj, exp):
            breakdown[key] = POINTS[key]
        else:
            remarks.append(f"{key}: expected {exp}, got {obj}")

    total = sum(breakdown.values())
    return total, breakdown, remarks


def student_id_from_filename(path: str) -> str:
    """
    Extract StudentID from 'StudentID_python_list.py'
    (everything before first underscore).
    """
    base = os.path.basename(path)
    m = re.match(r"^(.+?)_", base)
    return m.group(1) if m else os.path.splitext(base)[0]


def run_student_file(path: str) -> Tuple[str, str, int]:
    """
    Run a student script in a clean subprocess;
    return (stdout, stderr, exit_code).
    """
    abs_path = os.path.abspath(path)
    try:
        proc = subprocess.run(
            [sys.executable, abs_path],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECS,
            cwd=os.path.dirname(path) or None
        )
        return proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as e:
        return e.stdout or "", e.stderr or "Timed out", 124
    except Exception as e:
        return "", str(e), 1


def main():
    files = sorted(glob.glob(os.path.join(SRC_DIR, "*.py")))
    results: List[GradeResult] = []

    for fpath in files:
        # Skip this grading script if it lives in src
        if os.path.basename(fpath) == os.path.abspath(__file__):
            continue

        sid = student_id_from_filename(fpath)
        stdout, stderr, code = run_student_file(fpath)

        if code != 0:
            total = 0
            breakdown = {k: 0 for k in POINTS}
            remarks = [f"Script failed (exit {code}). Stderr: {stderr[:500]}"]
        else:
            total, breakdown, rmk = grade_from_stdout(stdout)
            remarks = rmk

        results.append(
            GradeResult(
                student_id=sid,
                filename=os.path.basename(fpath),
                total=total,
                breakdown=breakdown,
                remarks=" | ".join(remarks),
                raw_stdout=stdout,
                raw_stderr=stderr,
            )
        )

    # Build DataFrame
    rows = []
    for r in results:
        row = {
            "student_id": r.student_id,
            "filename": r.filename,
            "grade": r.total,
            "joined_pts": r.breakdown["joined"],
            "grouped_pts": r.breakdown["grouped"],
            "sorted_pts": r.breakdown["sorted_result"],
            "top_user_pts": r.breakdown["top_user"],
            "remarks": r.remarks,
        }
        rows.append(row)

    df = pd.DataFrame(rows).sort_values(["student_id", "filename"])
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"✅ Wrote {OUTPUT_CSV} with {len(df)} rows.")


if __name__ == "__main__":
    main()
