import os
import re
import io
from typing import Dict, Any

INDONESIAN_MONTH_MAP = {
    "januari": 1, "january": 1,
    "februari": 2, "february": 2,
    "maret": 3, "march": 3,
    "april": 4,
    "mei": 5, "may": 5,
    "juni": 6, "june": 6,
    "juli": 7, "july": 7,
    "agustus": 8, "august": 8,
    "september": 9,
    "oktober": 10, "october": 10,
    "november": 11,
    "desember": 12, "december": 12
}

def parse_attendance_pdf(pdf_stream_or_path) -> Dict[str, Any]:
    from pypdf import PdfReader

    reader = PdfReader(pdf_stream_or_path)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text(extraction_mode="layout") + "\n"

    # Pattern for BNI attendance rows:
    # No, Tanggal, Tipe Work Time, Work Time, Jam Check In, Jam Check Out, Total Jam Kerja, Ket
    row_pattern = r"^\s*(\d{1,2})\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})\s+(.*?)\s+(\d{2}:\d{2}(?::\d{2})?-\d{2}:\d{2}(?::\d{2})?)\s+([0-9:]{5,8}|-)\s+([0-9:]{5,8}|-)\s+([0-9.]+)\s+([A-Za-z0-9]+)\s*$"

    days = {}
    detected_year = None
    detected_month = None

    for line in full_text.split("\n"):
        m = re.match(row_pattern, line.rstrip())
        if m:
            no_str, tgl_str, _, _, check_in_raw, check_out_raw, _, _ = m.groups()
            day_num = int(no_str)

            # Detect month and year from the first matched date string
            if not detected_month:
                date_parts = tgl_str.split()
                if len(date_parts) == 3:
                    m_name = date_parts[1].lower()
                    detected_month = INDONESIAN_MONTH_MAP.get(m_name)
                    try:
                        detected_year = int(date_parts[2])
                    except ValueError:
                        pass

            # ONLY extract Jam Check In and Jam Check Out
            check_in = check_in_raw.strip() if check_in_raw != "-" else ""
            check_out = check_out_raw.strip() if check_out_raw != "-" else ""

            # Simplify to HH:MM if in HH:MM:SS format
            if check_in and len(check_in.split(":")) >= 2:
                parts = check_in.split(":")
                check_in = f"{parts[0]}:{parts[1]}"
            if check_out and len(check_out.split(":")) >= 2:
                parts = check_out.split(":")
                check_out = f"{parts[0]}:{parts[1]}"

            days[day_num] = {
                "start": check_in,
                "end": check_out
            }

    return {
        "success": True,
        "year": detected_year,
        "month": detected_month,
        "total_days": len(days),
        "days": days
    }

def parse_attendance_file(file_content_or_path, filename: str) -> Dict[str, Any]:
    fn_lower = filename.lower()
    if fn_lower.endswith(".pdf"):
        return parse_attendance_pdf(file_content_or_path)
    else:
        return {
            "success": False,
            "error": "Format file tidak didukung. Harap gunakan file PDF absensi BNI."
        }
