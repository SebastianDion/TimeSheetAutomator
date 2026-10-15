import os
import io
import calendar
from datetime import datetime, date
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, Query, Body, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from timesheet_generator import TimesheetGenerator, INDONESIAN_MONTHS, generate_timesheet, load_json
from attendance_parser import parse_attendance_file

app = FastAPI(title="BNI Timesheet Automator Web App")

DAY_NAMES_ID = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

class TimesheetGenerateRequest(BaseModel):
    year: int
    month: int
    activities: Dict[str, Any]

@app.get("/script.js")
async def get_script():
    js_path = os.path.join(os.path.dirname(__file__), "templates", "script.js")
    if os.path.exists(js_path):
        return FileResponse(js_path, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="script.js not found")

app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "templates")), name="static")

@app.post("/api/upload_attendance")
async def upload_attendance(file: UploadFile = File(...)):
    try:
        content = await file.read()
        res = parse_attendance_file(io.BytesIO(content), file.filename)
        return res
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Template not found</h1>"

@app.get("/api/config")
async def get_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    return load_json(config_path)

@app.get("/api/calendar")
async def get_calendar(year: int = Query(...), month: int = Query(...)):
    gen = TimesheetGenerator()
    num_days = calendar.monthrange(year, month)[1]
    month_name = INDONESIAN_MONTHS.get(month, calendar.month_name[month])
    
    # Check if existing draft exists in inputs/draft_{year}_{month}.json or inputs/{year}-{month}.txt
    draft_path = os.path.join(os.path.dirname(__file__), "inputs", f"draft_{year}_{month:02d}.json")
    draft_data = load_json(draft_path)

    days = []
    for day in range(1, num_days + 1):
        curr_date = date(year, month, day)
        date_str = curr_date.strftime("%Y-%m-%d")
        weekday_idx = curr_date.weekday()
        weekday_name = DAY_NAMES_ID[weekday_idx]
        is_weekend = (weekday_idx in (5, 6))
        holiday_name = gen.get_holiday_name(date_str)

        saved_item = draft_data.get(str(day), {})
        if isinstance(saved_item, str):
            saved_item = {"activity": saved_item}

        days.append({
            "day": day,
            "date": date_str,
            "display_date": curr_date.strftime("%d-%b-%y"),
            "weekday": weekday_name,
            "is_weekend": is_weekend,
            "holiday": holiday_name,
            "activity": saved_item.get("activity", ""),
            "status": saved_item.get("status", "P" if not is_weekend and not holiday_name else ""),
            "start": saved_item.get("start", ""),
            "end": saved_item.get("end", "")
        })

    return {
        "year": year,
        "month": month,
        "month_name": month_name,
        "days": days
    }

@app.post("/api/save_draft")
async def save_draft(payload: TimesheetGenerateRequest):
    os.makedirs(os.path.join(os.path.dirname(__file__), "inputs"), exist_ok=True)
    draft_path = os.path.join(os.path.dirname(__file__), "inputs", f"draft_{payload.year}_{payload.month:02d}.json")
    import json
    with open(draft_path, "w", encoding="utf-8") as f:
        json.dump(payload.activities, f, indent=2, ensure_ascii=False)
    return {"status": "saved", "path": draft_path}

@app.post("/api/generate")
async def generate_file(payload: TimesheetGenerateRequest):
    # Convert string keys to int
    activities_dict = {}
    for k, v in payload.activities.items():
        try:
            day_num = int(k)
            activities_dict[day_num] = v
        except ValueError:
            pass

    month_name = INDONESIAN_MONTHS.get(payload.month, calendar.month_name[payload.month])
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    output_filename = f"Timesheet_{month_name}_{payload.year}.xlsx"
    output_path = os.path.join(output_dir, output_filename)

    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    holidays_path = os.path.join(os.path.dirname(__file__), "holidays.json")

    generate_timesheet(config_path, holidays_path, payload.year, payload.month, activities_dict, output_path)

    # Also auto-save draft
    await save_draft(payload)

    return FileResponse(
        path=output_path,
        filename=output_filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def run_server(port: int = 8000):
    print(f"\n===========================================================")
    print(f" Web UI BNI Timesheet Automator berjalan di:")
    print(f" http://127.0.0.1:{port}")
    print(f" Buka link di atas di browser Anda!")
    print(f"===========================================================\n")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

if __name__ == "__main__":
    run_server()
