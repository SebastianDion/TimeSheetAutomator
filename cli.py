import os
import sys
import re
import argparse
import calendar
from datetime import datetime, date
from typing import Dict, Any

from timesheet_generator import TimesheetGenerator, INDONESIAN_MONTHS, generate_timesheet

DAY_NAMES_ID = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

def get_default_year_month(month_arg: str = None) -> tuple[int, int]:
    if month_arg:
        # Expected format YYYY-MM or YYYY/MM
        parts = re.split(r"[-/]", month_arg)
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
    now = datetime.now()
    return now.year, now.month

def init_input_file(year: int, month: int, holidays_path: str = "holidays.json", force: bool = False) -> str:
    os.makedirs("inputs", exist_ok=True)
    filename = f"inputs/{year}-{month:02d}.txt"
    if os.path.exists(filename) and not force:
        print(f"File {filename} sudah ada. Gunakan flag --force jika ingin menimpa.")
        return filename

    gen = TimesheetGenerator(holidays_path=holidays_path)
    num_days = calendar.monthrange(year, month)[1]
    month_name = INDONESIAN_MONTHS.get(month, calendar.month_name[month])

    lines = [
        f"# ===================================================================",
        f"# TIMESHEET INPUT: {month_name.upper()} {year}",
        f"# ===================================================================",
        f"# CARA PAKAI:",
        f"# 1. Tulis kegiatan harian Anda di samping tanda ':' pada baris tanggal.",
        f"# 2. Jam kerja default (~08:00 - 17:15) dan status 'P' otomatis terisi.",
        f"# 3. Opsi khusus (jika ada):",
        f"#    - Jam lembur/khusus: tambahkan [HH:MM-HH:MM], misal: [08:00-19:30]",
        f"#    - Status absen lain: tambahkan [S] (Sakit), [V] (Cuti), [BT] (Dinas), [PM] (Izin)",
        f"#    Contoh: {year}-{month:02d}-15 [08:00-20:00]: Deploy fitur dan testing",
        f"#    Contoh: {year}-{month:02d}-16 [S]: Sakit demam",
        f"# 4. Baris weekend / tanggal merah yang diawali '#' otomatis dilewati.",
        f"# ===================================================================\n"
    ]

    for day in range(1, num_days + 1):
        curr_date = date(year, month, day)
        date_str = curr_date.strftime("%Y-%m-%d")
        weekday_idx = curr_date.weekday()
        weekday_name = DAY_NAMES_ID[weekday_idx]
        is_weekend = (weekday_idx in (5, 6))
        holiday_name = gen.get_holiday_name(date_str)

        prefix = f"{date_str} ({weekday_name})"
        if holiday_name:
            lines.append(f"# {prefix} [LIBUR: {holiday_name}]: ")
        elif is_weekend:
            lines.append(f"# {prefix} [WEEKEND]: ")
        else:
            lines.append(f"{prefix}: ")

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"File input berhasil dibuat: {filename}")
    print(f"Silakan buka file tersebut dan ketik kegiatan harian Anda.")
    return filename

def parse_input_file(filepath: str, year: int, month: int) -> Dict[int, Any]:
    activities = {}
    if not os.path.exists(filepath):
        print(f"File {filepath} tidak ditemukan!")
        return activities

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or (line_str.startswith("#") and not line_str.startswith("#!")):
                continue

            # Remove leading '#!' if user forced a commented line
            if line_str.startswith("#!"):
                line_str = line_str[2:].strip()

            # Parse line: extract date, optional tags, and activity text
            if "]:" in line_str:
                left_part, act_text = line_str.split("]:", 1)
                left_part = left_part.strip() + "]"
                act_text = act_text.strip()
            elif ":" in line_str:
                left_part, act_text = line_str.split(":", 1)
                left_part = left_part.strip()
                act_text = act_text.strip()
            else:
                continue

            # Extract day
            # Patterns: YYYY-MM-DD or DD
            date_match = re.search(r"(\d{4}-\d{2}-\d{2})", left_part)
            day_num = None
            if date_match:
                d_str = date_match.group(1)
                try:
                    d_obj = datetime.strptime(d_str, "%Y-%m-%d")
                    day_num = d_obj.day
                except ValueError:
                    pass
            else:
                day_match = re.search(r"^\s*(\d{1,2})\b", left_part)
                if day_match:
                    day_num = int(day_match.group(1))

            if not day_num or day_num < 1 or day_num > 31:
                continue

            # Check for tags in left_part or act_text: [08:00-19:00], [S], [V], [BT], [PM], [X]
            combined = left_part + " " + act_text
            entry_dict = {"activity": act_text}

            # Check status
            status_match = re.search(r"\[(P|S|V|BT|PM|X)\]", combined, re.IGNORECASE)
            if status_match:
                entry_dict["status"] = status_match.group(1).upper()
                # Clean tag from act_text
                entry_dict["activity"] = re.sub(r"\[(P|S|V|BT|PM|X)\]", "", entry_dict["activity"], flags=re.IGNORECASE).strip()

            # Check custom times [HH:MM-HH:MM]
            time_match = re.search(r"\[(\d{1,2}:\d{2}(?::\d{2})?)\s*-\s*(\d{1,2}:\d{2}(?::\d{2})?)\]", combined)
            if time_match:
                start_raw = time_match.group(1)
                end_raw = time_match.group(2)
                # Ensure HH:MM:SS
                if len(start_raw.split(":")) == 2:
                    start_raw += ":00"
                if len(end_raw.split(":")) == 2:
                    end_raw += ":00"
                entry_dict["start"] = start_raw
                entry_dict["end"] = end_raw
                entry_dict["activity"] = re.sub(r"\[\d{1,2}:\d{2}(?::\d{2})?\s*-\s*\d{1,2}:\d{2}(?::\d{2})?\]", "", entry_dict["activity"]).strip()

            activities[day_num] = entry_dict

    return activities

def interactive_input(year: int, month: int, holidays_path: str = "holidays.json") -> Dict[int, Any]:
    gen = TimesheetGenerator(holidays_path=holidays_path)
    num_days = calendar.monthrange(year, month)[1]
    month_name = INDONESIAN_MONTHS.get(month, calendar.month_name[month])

    print(f"\n=== INPUT TIMESHEET INTERAKTIF: {month_name.upper()} {year} ===")
    print("Ketik kegiatan harian Anda. Tekan Enter untuk lewati/default.")
    print("Ketik 'exit' atau 'selesai' jika sudah cukup.\n")

    activities = {}
    for day in range(1, num_days + 1):
        curr_date = date(year, month, day)
        date_str = curr_date.strftime("%Y-%m-%d")
        weekday_idx = curr_date.weekday()
        weekday_name = DAY_NAMES_ID[weekday_idx]
        is_weekend = (weekday_idx in (5, 6))
        holiday_name = gen.get_holiday_name(date_str)

        info = f"{date_str} ({weekday_name})"
        if holiday_name:
            print(f"{info} -> [LIBUR NASIONAL: {holiday_name}] (Dilewati)")
            continue
        elif is_weekend:
            # check if user wants to log weekend work
            ans = input(f"{info} -> [WEEKEND]. Ada lembur akhir pekan? (y/N): ").strip().lower()
            if ans != "y":
                continue

        prompt = f"{info} Kegiatan: "
        user_input = input(prompt).strip()
        if user_input.lower() in ("exit", "selesai", "quit"):
            break

        if user_input:
            activities[day] = {"activity": user_input}

    return activities

def main():
    parser = argparse.ArgumentParser(description="BNI / MII Excel Timesheet Automator")
    subparsers = parser.add_subparsers(dest="command")

    # init command
    init_parser = subparsers.add_parser("init", help="Buat file template input teks untuk bulan tertentu")
    init_parser.add_argument("--month", "-m", type=str, help="Periode YYYY-MM (contoh: 2026-10)")
    init_parser.add_argument("--force", "-f", action="store_true", help="Timpa file jika sudah ada")

    # generate command
    gen_parser = subparsers.add_parser("generate", help="Generate file Excel dari file input teks")
    gen_parser.add_argument("--month", "-m", type=str, help="Periode YYYY-MM (contoh: 2026-10)")
    gen_parser.add_argument("--input", "-i", type=str, help="Path ke file input teks (default: inputs/YYYY-MM.txt)")
    gen_parser.add_argument("--output", "-o", type=str, help="Path output file Excel (.xlsx)")

    # interactive command
    inter_parser = subparsers.add_parser("interactive", help="Input kegiatan harian secara interaktif di terminal")
    inter_parser.add_argument("--month", "-m", type=str, help="Periode YYYY-MM (contoh: 2026-10)")
    inter_parser.add_argument("--output", "-o", type=str, help="Path output file Excel (.xlsx)")

    # web command
    web_parser = subparsers.add_parser("web", help="Buka Web UI lokal untuk input visual di browser")
    web_parser.add_argument("--port", "-p", type=int, default=8000, help="Port lokal web (default: 8000)")

    # import-attendance command
    att_parser = subparsers.add_parser("import-attendance", help="Ambil Jam Check In & Check Out dari file PDF absensi kantor")
    att_parser.add_argument("file", type=str, help="Path ke file PDF Laporan Kehadiran Karyawan")

    args = parser.parse_args()

    if args.command == "init":
        year, month = get_default_year_month(args.month)
        init_input_file(year, month, force=args.force)

    elif args.command == "generate":
        year, month = get_default_year_month(args.month)
        input_file = args.input or f"inputs/{year}-{month:02d}.txt"
        if not os.path.exists(input_file):
            print(f"File input {input_file} belum ada! Menjalankan 'init' terlebih dahulu...")
            init_input_file(year, month)
            print(f"Silakan isi kegiatan di file {input_file}, lalu jalankan kembali 'generate'.")
            return

        activities = parse_input_file(input_file, year, month)
        month_name = INDONESIAN_MONTHS.get(month, calendar.month_name[month])
        output_file = args.output or f"output/Timesheet_{month_name}_{year}.xlsx"

        print(f"Memproses {len(activities)} catatan kegiatan untuk {month_name} {year}...")
        res = generate_timesheet("config.json", "holidays.json", year, month, activities, output_file)
        print(f"BERHASIL! Timesheet Excel tersimpan di: {res}")

    elif args.command == "interactive":
        year, month = get_default_year_month(args.month)
        activities = interactive_input(year, month)
        month_name = INDONESIAN_MONTHS.get(month, calendar.month_name[month])
        output_file = args.output or f"output/Timesheet_{month_name}_{year}.xlsx"

        res = generate_timesheet("config.json", "holidays.json", year, month, activities, output_file)
        print(f"\nBERHASIL! Timesheet Excel tersimpan di: {res}")

    elif args.command == "import-attendance":
        from attendance_parser import parse_attendance_file
        pdf_path = args.file
        if not os.path.exists(pdf_path):
            print(f"File {pdf_path} tidak ditemukan!")
            return
        res = parse_attendance_file(pdf_path, os.path.basename(pdf_path))
        if not res.get("success"):
            print("Gagal:", res.get("error"))
            return
        
        y, m = res.get("year"), res.get("month")
        print(f"Berhasil parse {res.get('total_days')} hari absensi untuk periode {y}-{m:02d}!")
        for day, times in sorted(res.get("days", {}).items()):
            if times.get("start") or times.get("end"):
                print(f"  Hari {day:02d}: Check In={times.get('start', '-')} | Check Out={times.get('end', '-')}")

    elif args.command == "web":
        from web_app import run_server
        run_server(port=args.port)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
