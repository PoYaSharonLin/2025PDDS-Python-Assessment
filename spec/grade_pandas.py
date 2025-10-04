#!/usr/bin/env python3
import ast
import glob
import os
import re
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, Tuple, Optional, List

import pandas as pd

# === Paths / Config ===
SRC_DIR = "pandas_src"
OUTPUT_CSV = "output/pandas_grades.csv"
TIMEOUT_SECS = 8

# === Expected answers (literal form, if students print Python objects) ===
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

# === Points ===
POINTS = {
    "joined": 5,
    "grouped": 10,
    "sorted_result": 20,
    "top_user": 5,
}

# === Headers students are asked to print ===
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

# ------------ Parsing helpers ------------
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
            for j in range(i + 1, len(lines)):
                nxt = lines[j].strip()
                if nxt:
                    return safe_literal_eval(nxt)
            break
    return None

def compare_deep(a: Any, b: Any) -> bool:
    """Strict deep comparison."""
    return a == b

# Regex patterns for pandas-text fallbacks
RE_JOINED_A1 = re.compile(r"Alice.*100")
RE_JOINED_A2 = re.compile(r"Alice.*150")
RE_JOINED_B1 = re.compile(r"Bob.*200")

RE_G_A = re.compile(r"Alice\s+2\s+250")
RE_G_B = re.compile(r"Bob\s+1\s+200")

RE_TOP_NAME = re.compile(r"Name:\s*Alice", re.IGNORECASE)
RE_TOP_VAL  = re.compile(r"total_spent\s+250", re.IGNORECASE)

def joined_fallback(stdout: str) -> bool:
    """
    Accept if we can see the merged/joined rows anywhere in output
    (works for pandas DataFrame prints).
    """
    return all(p.search(stdout) for p in [RE_JOINED_A1, RE_JOINED_A2, RE_JOINED_B1])

def grouped_fallback(stdout: str) -> bool:
    """Accept correct aggregate numbers (order-agnostic) in any table/block."""
    return (RE_G_A.search(stdout) is not None) and (RE_G_B.search(stdout) is not None)

def sorted_fallback(stdout: str) -> bool:
    """
    Ensure Alice line appears before Bob line (descending by total_spent)
    somewhere in the 'Sorted Result' area or generally.
    """
    # Restrict to "Sorted Result" section if present
    section = stdout
    if "✅ Sorted Result:" in stdout:
        section = stdout.split("✅ Sorted Result:", 1)[1]

    ma = RE_G_A.search(section)
    mb = RE_G_B.search(section)
    return bool(ma and mb and ma.start() < mb.start())

def top_user_fallback(stdout: str) -> bool:
    """
    Accept typical pandas Series-like print for top user:
    lines containing total_spent 250 and Name: Alice in the Top User block.
    """
    # Prefer checking inside the 'Top User' block if present
    block = stdout
    if "🏆 Top User:" in stdout:
        block = stdout.split("🏆 Top User:", 1)[1]
    return bool(RE_TOP_NAME.search(block) and RE_TOP_VAL.search(block))

# ------------ Grading ------------
def grade_from_stdout(stdout: str) -> Tuple[int, Dict[str, int], List[str]]:
    breakdown: Dict[str, int] = {k: 0 for k in POINTS}
    remarks: List[str] = []

    # 1) Try strict literal parsing after each header
    parsed = {}
    for key, header in HEADERS.items():
        obj = extract_after_header(stdout, header)
        parsed[key] = obj

    # 2) Score each key with literal compare OR fallbacks for pandas prints
    # joined
    if parsed["joined"] is not None and compare_deep(parsed["joined"], EXPECTED["joined"]):
        breakdown["joined"] = POINTS["joined"]
    elif joined_fallback(stdout):
        breakdown["joined"] = POINTS["joined"]
    else:
        remarks.append("joined mismatch")

    # grouped
    if parsed["grouped"] is not None and compare_deep(parsed["grouped"], EXPECTED["grouped"]):
        breakdown["grouped"] = POINTS["grouped"]
    elif grouped_fallback(stdout):
        breakdown["grouped"] = POINTS["grouped"]
    else:
        remarks.append("grouped mismatch")

    # sorted_result
    if parsed["sorted_result"] is not None and compare_deep(parsed["sorted_result"], EXPECTED["sorted_result"]):
        breakdown["sorted_result"] = POINTS["sorted_result"]
    elif sorted_fallback(stdout):
        breakdown["sorted_result"] = POINTS["sorted_result"]
    else:
        remarks.append("sorted_result mismatch")

    # top_user
    if parsed["top_user"] is not None and compare_deep(parsed["top_user"], EXPECTED["top_user"]):
        breakdown["top_user"] = POINTS["top_user"]
    elif top_user_fallback(stdout):
        breakdown["top_user"] = POINTS["top_user"]
    else:
        remarks.append("top_user mismatch")

    total = sum(breakdown.values())
    return total, breakdown, remarks

def student_id_from_filename(path: str) -> str:
    """
    Extract StudentID from 'StudentID_pandas.py' (everything before first underscore).
    Works for any '<id>_*.py'.
    """
    base = os.path.basename(path)
    m = re.match(r"^(.+?)_", base)
    return m.group(1) if m else os.path.splitext(base)[0]

def run_student_file(path: str) -> Tuple[str, str, int]:
    """
    Run a student script in a subprocess and capture output.
    """
    abs_path = os.path.abspath(path)
    try:
        proc = subprocess.run(
            ["python3", abs_path],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECS,
            cwd=os.path.dirname(abs_path) or None,
            env={},  # cleaner env
        )
        return proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as e:
        return e.stdout or "", e.stderr or f"Timed out after {TIMEOUT_SECS}s", 124
    except Exception as e:
        return "", str(e), 1

def main():
    os.makedirs(os.path.dirname(OUTPUT_CSV) or ".", exist_ok=True)
    files = sorted(glob.glob(os.path.join(SRC_DIR, "*.py")))
    results: List[GradeResult] = []

    for fpath in files:
        # Don’t accidentally grade the grader if it sits in SRC_DIR
        if os.path.abspath(fpath) == os.path.abspath(__file__):
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

    # Build CSV rows
    rows = []
    for r in results:
        rows.append({
            "student_id": r.student_id,
            "filename": r.filename,
            "grade": r.total,
            "joined_pts": r.breakdown["joined"],
            "grouped_pts": r.breakdown["grouped"],
            "sorted_pts": r.breakdown["sorted_result"],
            "top_user_pts": r.breakdown["top_user"],
            "remarks": r.remarks,
        })

    df = pd.DataFrame(rows).sort_values(["student_id", "filename"])
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"✅ Wrote {OUTPUT_CSV} with {len(df)} rows.")

if __name__ == "__main__":
    main()
