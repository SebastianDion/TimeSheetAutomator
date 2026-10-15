#Timesheet Automator

Aplikasi otomatisasi pembuatan timesheet bulanan format resmi.

Dibuat khusus agar **Anda tidak perlu lagi membuat sheet Excel baru secara manual setiap bulan**. Cukup input catatan kegiatan harian Anda, dan seluruh dokumen Excel (tanggal kalender, penyesuaian akhir pekan & tanggal merah, kalkulasi total jam kerja, status absensi, metadata proyek, rekap total, serta blok tanda tangan) akan dibuat otomatis dengan format yang 100% presisi.

---

## 🚀 Pilihan Cara Input (Pilih yang Paling Nyaman)

### Opsi 1: Lewat Web UI Lokal (Paling Visual & Praktis) ⭐
Buka antarmuka tabel interaktif di browser:
```powershell
python cli.py web
```
1. Buka `http://127.0.0.1:8000` di browser Anda.
2. Pilih Bulan & Tahun (misal: *Oktober 2026*).
3. Tanggal merah dan akhir pekan otomatis ditandai dan di-highlight.
4. Ketik aktivitas harian Anda pada baris hari kerja.
5. Klik **"📥 Download Excel (.xlsx)"** — file Excel resmi langsung terunduh siap pakai!

---

### Opsi 2: Lewat File Teks Kalender (Sangat Cepat)
Jika Anda lebih suka mencatat atau copy-paste dari catatan harian:

1. Buat file template bulan target:
   ```powershell
   python cli.py init --month 2026-10
   ```
   *File `inputs/2026-10.txt` otomatis dibuat dengan seluruh daftar hari kerja dan keterangan hari libur.*

2. Buka file `inputs/2026-10.txt`, lalu ketik kegiatan di samping tanda titik dua (`:`), contoh:
   ```text
   2026-10-01 (Kamis): Slicing UI kalkulasi simulasi dan integrasi API
   2026-10-02 (Jumat): Menambahkan unit test coverage pada servis
   2026-10-08 (Kamis) [08:00-19:30]: Lembur menyelesaikan defect simulasi
   2026-10-13 (Selasa) [S]: Sakit flu dan istirahat
   ```

3. Generate file Excel-nya:
   ```powershell
   python cli.py generate --month 2026-10
   ```
   File Excel akan tersimpan di `output/Timesheet_Oktober_2026.xlsx`.

---

### Opsi 3: Lewat Terminal Interaktif
Isi hari demi hari langsung di PowerShell/terminal:
```powershell
python cli.py interactive --month 2026-10
```
Sistem akan menampilkan hari kerja satu per satu dan menanyakan kegiatan Anda. Hari libur dan weekend akan otomatis dilewati.

---

## ⚙️ Konfigurasi Profil & Metadata (`config.json`)

Data profil dan detail proyek disimpan di `config.json` (dibuat dari salinan `config.example.json`) sehingga tidak perlu diisi ulang setiap bulan:
- **Nama Pegawai & ID**: Nama lengkap dan ID konsultan/karyawan
- **Site & Unit/Divisi**: Informasi penempatan kantor & unit divisi
- **Project Default**: Nama & ID project penempatan
- **Atasan/Pemeriksa**: Nama pemeriksa dan penyetujui timesheet
- **Jam Kerja Default**: Rentang jam masuk default (misal ~08:00 - 08:15) dan jam pulang (~17:05 - 17:30) yang otomatis divariasikan agar terlihat natural.


---

## 📅 Penyesuaian Tanggal Merah & Libur Nasional (`holidays.json`)

Daftar hari libur nasional Indonesia (SKB 3 Menteri) untuk tahun 2025, 2026, hingga 2027 sudah terpasang di `holidays.json`:
- 1 Januari (Tahun Baru)
- Hari Raya Idul Fitri & Cuti Bersama
- 1 Mei (Hari Buruh)
- 1 Juni (Hari Lahir Pancasila)
- 17 Agustus (Hari Kemerdekaan RI)
- Maulid Nabi, Natal, dsb.

Jika ada cuti bersama mendadak atau hari libur khusus internal, Anda cukup menambahkannya di `holidays.json` pada bagian `"custom_holidays"`.

---

## 📁 Struktur Direktori & File yang Di-Push ke Repo

```text
timesheet-automator/
├── config.example.json      # Template konfigurasi publik (salin ke config.json)

├── holidays.json            # Daftar tanggal merah resmi Indonesia
├── timesheet_generator.py   # Engine generator Excel (openpyxl)
├── attendance_parser.py     # Parser PDF Laporan Kehadiran Karyawan (Check In/Out)
├── cli.py                   # Script CLI (init, generate, interactive, web)
├── web_app.py               # Backend Web UI lokal (FastAPI)
├── requirements.txt         # Daftar dependency Python
├── start.bat                # Shortcut 1-klik jalankan server di Windows
├── .gitignore               # Konfigurasi ignore file cache & data personal
├── assets/
│   └── mii_logo.png         # Logo resmi MII untuk header Excel
├── templates/
│   ├── index.html           # Tampilan Web UI (Dark Tavern Theme)
│   └── script.js            # Frontend logic Web UI
├── inputs/
│   └── .gitkeep             # Folder input bulanan (draft di-ignore oleh git)
├── output/
│   └── .gitkeep             # Folder hasil Excel (file xlsx di-ignore oleh git)
└── tests/
    └── test_generator.py    # Unit test otomasi
```

---

## 📦 Instalasi & Cara Push ke GitHub

### 1. Instalasi Dependency
```bash
pip install -r requirements.txt
```

### 2. Push ke Git Repository
```bash
# Inisialisasi git (jika belum)
git init

# Tambahkan semua file yang aman untuk di-push
git add .

# Buat commit pertama
git commit -m "feat: initial commit BNI MII timesheet automator"

# Hubungkan dengan remote repository GitHub Anda
git branch -M main
git remote add origin https://github.com/USERNAME/REPO_NAME.git
git push -u origin main
```

> [!TIP]
> **Catatan Keamanan (`config.json`):**
> - Jika repo Anda bersifat **Private**, Anda bisa langsung mengikutkan `config.json` agar pengaturan NIK & nama atasan langsung tersimpan.
> - Jika repo Anda bersifat **Public**, uncomment `# config.json` di file `.gitignore` agar NIK dan identitas internal Anda tidak terekspos ke publik, dan orang lain bisa menggunakan `config.example.json`.

