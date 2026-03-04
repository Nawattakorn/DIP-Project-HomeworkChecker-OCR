"""
checker_corr2.py - Load answer key, run OCR (corr2), return grading result.
"""

import json
import re
from pathlib import Path

from ocr_corr2 import extract_answers


ANSWER_KEY_PATH = Path(__file__).parent / "answer_key.json"


def _normalise(text: str) -> str:
    """Strip whitespace, uppercase — for comparison."""
    return re.sub(r"\s+", "", str(text).strip().upper())


def _postprocess(raw: str, q_type: str) -> str:
    """Extract the final answer from raw OCR text."""
    if q_type == "number":
        nums = re.findall(r"\d+", raw)
        return nums[-1] if nums else ""
    return _normalise(raw)


def grade(image_path: str, key_path: str = None, provided_key: list = None) -> dict:
    """
    ตรวจการบ้าน โดยใช้เฉลยจากไฟล์ หรือจากที่ user กรอกมาโดยตรง
    """
    if provided_key:
        # ถ้ามีเฉลยส่งมาจากหน้าเว็บ ให้สร้างโครงสร้างคำถามจำลองขึ้นมา
        questions = [{"id": i+1, "answer": str(ans), "type": "number"} 
                     for i, ans in enumerate(provided_key)]
    else:
        # ถ้าไม่มี ให้ไปอ่านจากไฟล์เดิม
        key_path = key_path or ANSWER_KEY_PATH
        with open(key_path, encoding="utf-8") as f:
            key = json.load(f)
        questions = key.get("questions", [])

    try:
        raw_lines = extract_answers(image_path)
    except Exception as e:
        return {"success": False, "error": str(e), "score": 0, "results": []}

    # จับคู่คำตอบที่อ่านได้กับเฉลย
    raw_lines = (raw_lines + [""] * len(questions))[: len(questions)]
    results = []
    correct_count = 0

    for i, q in enumerate(questions):
        expected = _normalise(q.get("answer", ""))
        got = _postprocess(raw_lines[i], q.get("type", "number"))
        ok = (got == expected)
        if ok: correct_count += 1

        results.append({
            "id": q.get("id", i + 1),
            "expected": expected,
            "got": got,
            "correct": ok
        })

    score = round(correct_count / len(questions) * 100, 1) if questions else 0
    return {
        "success": True,
        "score": score,
        "correct": correct_count,
        "total": len(questions),
        "results": results,
        "extracted_raw": raw_lines,
    }
