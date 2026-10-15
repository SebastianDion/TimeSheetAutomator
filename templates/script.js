let currentData = {
  year: 2026,
  month: 10,
  days: []
};

function showToast(msg, icon = '✅') {
  const toast = document.getElementById('toast');
  document.getElementById('toast-msg').textContent = msg;
  document.getElementById('toast-icon').textContent = icon;
  toast.classList.remove('hidden');
  setTimeout(() => {
    toast.classList.add('hidden');
  }, 3000);
}

async function loadConfig() {
  try {
    const res = await fetch('/api/config');
    const cfg = await res.json();
    const emp = cfg.employee || {};
    const client = cfg.client || {};
    const proj = cfg.project_defaults || {};
    document.getElementById('profile-subtitle').textContent = 
      `${emp.name || 'Timesheet'} ${emp.mii_id ? '(' + emp.mii_id + ')' : ''} • ${client.unit_division || 'RMS/WDL'} • ${proj.project_name || 'CPR'} (${proj.project_id || 'CR260028'})`;
  } catch (e) {

    console.error(e);
  }
}

async function loadCalendar() {
  const year = document.getElementById('select-year').value;
  const month = document.getElementById('select-month').value;

  try {
    const res = await fetch(`/api/calendar?year=${year}&month=${month}`);
    currentData = await res.json();
    renderTable();
  } catch (e) {
    showToast('Gagal memuat kalender', '❌');
  }
}

function renderTable() {
  const tbody = document.getElementById('days-table-body');
  tbody.innerHTML = '';

  let workdaysCount = 0;
  let holidaysCount = 0;
  let filledCount = 0;

  currentData.days.forEach(d => {
    const isOff = d.is_weekend || d.holiday;
    if (isOff) {
      holidaysCount++;
    } else {
      workdaysCount++;
      if (d.activity && d.activity.trim()) filledCount++;
    }

    const tr = document.createElement('tr');
    tr.className = isOff 
      ? 'bg-[#0E1412]/80 text-tavern-dimmed hover:bg-[#121916] transition-colors' 
      : 'bg-tavern-surface hover:bg-tavern-surfaceLighter transition-colors';

    // Column 1: Date & Weekday Badge
    const tdDate = document.createElement('td');
    tdDate.className = 'py-2.5 px-4 whitespace-nowrap font-medium';
    let badge = '';
    if (d.holiday) {
      badge = `<span class="inline-flex items-center gap-1 text-[10px] font-semibold text-rose-300 bg-rose-950/60 border border-rose-800/50 px-1.5 py-0.5 rounded-md mt-0.5">🏖️ ${d.holiday}</span>`;
    } else if (d.is_weekend) {
      badge = `<span class="inline-block text-[10px] font-semibold text-tavern-muted bg-tavern-surfaceDim border border-tavern-border px-1.5 py-0.5 rounded-md mt-0.5 font-mono">${d.weekday}</span>`;
    } else {
      badge = `<span class="inline-block text-[10px] font-semibold text-emerald-300 bg-emerald-950/50 border border-emerald-800/40 px-1.5 py-0.5 rounded-md mt-0.5 font-mono">${d.weekday}</span>`;
    }
    tdDate.innerHTML = `<div class="font-bold text-tavern-ivory font-mono">${d.display_date}</div>${badge}`;
    tr.appendChild(tdDate);

    // Column 2: Status Attendance
    const tdStatus = document.createElement('td');
    tdStatus.className = 'py-2.5 px-3 whitespace-nowrap';
    const selectStatus = document.createElement('select');
    selectStatus.className = 'w-full text-xs font-semibold border border-tavern-border rounded-lg px-2 py-1.5 bg-[#121916] text-tavern-ivory focus:border-tavern-gold focus:ring-1 focus:ring-tavern-gold focus:outline-none transition shadow-inner cursor-pointer';
    selectStatus.dataset.day = d.day;
    selectStatus.dataset.type = 'status';

    const statuses = [
      { val: 'P', label: '🟢 Present (P)' },
      { val: 'S', label: '🟡 Sakit (S)' },
      { val: 'V', label: '🔵 Cuti (V)' },
      { val: 'BT', label: '🟣 Dinas (BT)' },
      { val: 'PM', label: '🟠 Izin (PM)' },
      { val: 'X', label: '⚪ Non-Aktif (X)' },
      { val: '', label: '- Kosong -' }
    ];

    statuses.forEach(s => {
      const opt = document.createElement('option');
      opt.value = s.val;
      opt.textContent = s.label;
      opt.className = 'bg-tavern-surface text-tavern-ivory';
      if (d.status === s.val) opt.selected = true;
      selectStatus.appendChild(opt);
    });
    selectStatus.addEventListener('change', () => {
      applyRowStyling(d.day);
      updateStats();
    });
    tdStatus.appendChild(selectStatus);
    tr.appendChild(tdStatus);

    // Column 3: Hours Start & End
    const tdHours = document.createElement('td');
    tdHours.className = 'py-2.5 px-3 whitespace-nowrap';
    tdHours.innerHTML = `
      <div class="flex items-center gap-1.5">
        <input type="text" placeholder="08:00" value="${d.start || ''}" data-day="${d.day}" data-type="start" class="w-14 text-center text-xs font-mono font-medium border border-tavern-border rounded-lg px-1.5 py-1.5 bg-[#121916] text-tavern-ivory placeholder-tavern-dimmed focus:outline-none focus:border-tavern-gold focus:ring-1 focus:ring-tavern-gold shadow-inner" title="Jam Masuk (HH:MM)">
        <span class="text-tavern-dimmed font-bold">-</span>
        <input type="text" placeholder="17:15" value="${d.end || ''}" data-day="${d.day}" data-type="end" class="w-14 text-center text-xs font-mono font-medium border border-tavern-border rounded-lg px-1.5 py-1.5 bg-[#121916] text-tavern-ivory placeholder-tavern-dimmed focus:outline-none focus:border-tavern-gold focus:ring-1 focus:ring-tavern-gold shadow-inner" title="Jam Pulang (HH:MM)">
      </div>
    `;
    tr.appendChild(tdHours);

    // Column 4: Activity Remark Input
    const tdAct = document.createElement('td');
    tdAct.className = 'py-2 px-4';
    const inputAct = document.createElement('input');
    inputAct.type = 'text';
    inputAct.dataset.day = d.day;
    inputAct.dataset.type = 'activity';
    inputAct.value = d.activity || '';
    inputAct.placeholder = isOff ? (d.holiday ? `Libur: ${d.holiday}` : 'Akhir pekan (opsional diisi jika ada lembur)') : 'Tulis catatan tugas kerja hari ini...';
    inputAct.className = `w-full text-xs font-medium border ${isOff ? 'border-tavern-border/50 bg-[#0E1412] text-tavern-dimmed placeholder-tavern-dimmed' : 'border-tavern-border bg-[#121916] text-tavern-ivory placeholder-tavern-dimmed'} rounded-lg px-3 py-2 focus:outline-none focus:border-tavern-gold focus:ring-1 focus:ring-tavern-gold transition shadow-inner`;
    inputAct.addEventListener('input', updateStats);
    tdAct.appendChild(inputAct);
    tr.appendChild(tdAct);

    tbody.appendChild(tr);

    // Set initial row styling based on status
    applyRowStyling(d.day);
  });

  // Update Header Stats
  updateStats();
}

function applyRowStyling(day) {
  const tr = document.querySelector(`#days-table-body tr[data-day="${day}"]`);
  const statusEl = document.querySelector(`#days-table-body select[data-type="status"][data-day="${day}"]`);
  const actInput = document.querySelector(`#days-table-body input[data-type="activity"][data-day="${day}"]`);
  const startInput = document.querySelector(`#days-table-body input[data-type="start"][data-day="${day}"]`);
  const endInput = document.querySelector(`#days-table-body input[data-type="end"][data-day="${day}"]`);

  if (!tr || !statusEl) return;

  const isKosong = (statusEl.value === '');
  if (isKosong) {
    // Dimmed / Gray State for - Kosong -
    tr.className = 'bg-[#0E1412]/85 text-tavern-dimmed hover:bg-[#121916] transition-colors';
    statusEl.className = 'w-full text-xs font-semibold border border-tavern-border/40 rounded-lg px-2 py-1.5 bg-[#0E1412] text-tavern-dimmed focus:border-tavern-gold focus:ring-1 focus:ring-tavern-gold focus:outline-none transition cursor-pointer';
    if (actInput) {
      actInput.className = 'w-full text-xs font-medium border border-tavern-border/30 bg-[#0A0E0C] text-tavern-dimmed placeholder-tavern-dimmed rounded-lg px-3 py-2 focus:outline-none focus:border-tavern-gold focus:ring-1 focus:ring-tavern-gold transition shadow-inner';
    }
    if (startInput) {
      startInput.className = 'w-14 text-center text-xs font-mono font-medium border border-tavern-border/30 rounded-lg px-1.5 py-1.5 bg-[#0A0E0C] text-tavern-dimmed placeholder-tavern-dimmed focus:outline-none focus:border-tavern-gold focus:ring-1 focus:ring-tavern-gold shadow-inner';
    }
    if (endInput) {
      endInput.className = 'w-14 text-center text-xs font-mono font-medium border border-tavern-border/30 rounded-lg px-1.5 py-1.5 bg-[#0A0E0C] text-tavern-dimmed placeholder-tavern-dimmed focus:outline-none focus:border-tavern-gold focus:ring-1 focus:ring-tavern-gold shadow-inner';
    }
  } else {
    // Active State (P / S / V / BT / PM / X)
    tr.className = 'bg-tavern-surface hover:bg-tavern-surfaceLighter transition-colors';
    statusEl.className = 'w-full text-xs font-semibold border border-tavern-border rounded-lg px-2 py-1.5 bg-[#121916] text-tavern-ivory focus:border-tavern-gold focus:ring-1 focus:ring-tavern-gold focus:outline-none transition shadow-inner cursor-pointer';
    if (actInput) {
      actInput.className = 'w-full text-xs font-medium border border-tavern-border bg-[#121916] text-tavern-ivory placeholder-tavern-dimmed rounded-lg px-3 py-2 focus:outline-none focus:border-tavern-gold focus:ring-1 focus:ring-tavern-gold transition shadow-inner';
    }
    if (startInput) {
      startInput.className = 'w-14 text-center text-xs font-mono font-medium border border-tavern-border rounded-lg px-1.5 py-1.5 bg-[#121916] text-tavern-ivory placeholder-tavern-dimmed focus:outline-none focus:border-tavern-gold focus:ring-1 focus:ring-tavern-gold shadow-inner';
    }
    if (endInput) {
      endInput.className = 'w-14 text-center text-xs font-mono font-medium border border-tavern-border rounded-lg px-1.5 py-1.5 bg-[#121916] text-tavern-ivory placeholder-tavern-dimmed focus:outline-none focus:border-tavern-gold focus:ring-1 focus:ring-tavern-gold shadow-inner';
    }
  }
}

function collectActivities() {
  const activities = {};
  const inputs = document.querySelectorAll('#days-table-body input[data-type="activity"]');

  inputs.forEach(input => {
    const day = input.dataset.day;
    const act = input.value.trim();
    const statusEl = document.querySelector(`#days-table-body select[data-type="status"][data-day="${day}"]`);
    const startEl = document.querySelector(`#days-table-body input[data-type="start"][data-day="${day}"]`);
    const endEl = document.querySelector(`#days-table-body input[data-type="end"][data-day="${day}"]`);

    const status = statusEl ? statusEl.value : '';
    const start = startEl ? startEl.value.trim() : '';
    const end = endEl ? endEl.value.trim() : '';

    if (act || status || start || end) {
      activities[day] = {
        activity: act,
        status: status,
        start: start,
        end: end
      };
    }
  });
  return activities;
}

function updateStats() {
  const activities = collectActivities();
  let filled = 0;
  let totalWorkdays = 0;
  let holidaysCount = 0;

  currentData.days.forEach(d => {
    const statusEl = document.querySelector(`#days-table-body select[data-type="status"][data-day="${d.day}"]`);
    const status = statusEl ? statusEl.value : d.status;
    const isKosong = (!status);

    if (isKosong) {
      holidaysCount++;
    } else {
      totalWorkdays++;
      const item = activities[d.day];
      if (item && item.activity && item.activity.trim()) filled++;
    }
  });

  document.getElementById('stat-period').textContent = `${currentData.month_name} ${currentData.year}`;
  document.getElementById('stat-workdays').textContent = `${totalWorkdays} Hari`;
  document.getElementById('stat-holidays').textContent = `${holidaysCount} Hari`;
  document.getElementById('stat-filled').textContent = `${filled} / ${totalWorkdays} Hari`;
}

function fillRealisticHours() {
  currentData.days.forEach(d => {
    if (!d.is_weekend && !d.holiday) {
      const startEl = document.querySelector(`#days-table-body input[data-type="start"][data-day="${d.day}"]`);
      const endEl = document.querySelector(`#days-table-body input[data-type="end"][data-day="${d.day}"]`);
      
      if (startEl && !startEl.value.trim()) {
        const startMins = Math.floor(Math.random() * 20) - 5; // 07:55 - 08:15
        const h = startMins < 0 ? 7 : 8;
        const m = startMins < 0 ? 60 + startMins : startMins;
        startEl.value = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
      }
      if (endEl && !endEl.value.trim()) {
        const endMins = Math.floor(Math.random() * 25) + 5; // 17:05 - 17:30
        endEl.value = `17:${String(endMins).padStart(2, '0')}`;
      }
    }
  });
  showToast('Jam masuk dan pulang acak berhasil diterapkan!');
}

function openBulkModal() {
  document.getElementById('bulk-modal').classList.remove('hidden');
  document.getElementById('bulk-text').focus();
}

function closeBulkModal() {
  document.getElementById('bulk-modal').classList.add('hidden');
}

function applyBulkPaste() {
  const text = document.getElementById('bulk-text').value;
  const lines = text.split('\n').map(l => l.trim()).filter(l => l.length > 0);
  if (lines.length === 0) {
    closeBulkModal();
    return;
  }

  let lineIdx = 0;
  currentData.days.forEach(d => {
    if (!d.is_weekend && !d.holiday && lineIdx < lines.length) {
      const actInput = document.querySelector(`#days-table-body input[data-type="activity"][data-day="${d.day}"]`);
      if (actInput) {
        actInput.value = lines[lineIdx++];
      }
    }
  });

  updateStats();
  closeBulkModal();
  showToast(`${lineIdx} kegiatan berhasil diterapkan ke tabel!`);
}

async function saveDraft() {
  const activities = collectActivities();
  const payload = {
    year: parseInt(document.getElementById('select-year').value),
    month: parseInt(document.getElementById('select-month').value),
    activities: activities
  };

  try {
    const res = await fetch('/api/save_draft', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      showToast('Draf kegiatan berhasil disimpan di disk!');
    } else {
      showToast('Gagal menyimpan draf', '❌');
    }
  } catch (e) {
    showToast('Terjadi kesalahan koneksi', '❌');
  }
}

async function generateExcel() {
  const btn = document.getElementById('btn-generate');
  const originalHTML = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-tavern-bg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg> Memproses...`;

  const activities = collectActivities();
  const year = parseInt(document.getElementById('select-year').value);
  const month = parseInt(document.getElementById('select-month').value);

  const payload = {
    year: year,
    month: month,
    activities: activities
  };

  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Timesheet_${currentData.month_name}_${year}.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      showToast('File Excel resmi berhasil di-download!');
    } else {
      showToast('Gagal men-generate file Excel', '❌');
    }
  } catch (e) {
    showToast('Terjadi kesalahan koneksi', '❌');
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalHTML;
  }
}

async function handleAttendanceUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('file', file);

  showToast('⏳ Membaca Jam Check In & Check Out dari PDF...', '⏱️');

  try {
    const res = await fetch('/api/upload_attendance', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();

    if (!data.success) {
      showToast(data.error || 'Gagal membaca file absensi', '❌');
      return;
    }

    // Switch month & year if detected from the PDF
    if (data.year && data.month) {
      const yearSelect = document.getElementById('select-year');
      const monthSelect = document.getElementById('select-month');
      if (yearSelect.value != data.year || monthSelect.value != data.month) {
        yearSelect.value = data.year;
        monthSelect.value = data.month;
        await loadCalendar();
      }
    }

    // ONLY populate Jam Check In and Jam Check Out! Nothing else!
    let updatedCount = 0;
    for (const [day, times] of Object.entries(data.days)) {
      const startInput = document.querySelector(`#days-table-body input[data-type="start"][data-day="${day}"]`);
      const endInput = document.querySelector(`#days-table-body input[data-type="end"][data-day="${day}"]`);

      if (startInput) {
        startInput.value = times.start || '';
      }
      if (endInput) {
        endInput.value = times.end || '';
      }
      if (times.start || times.end) {
        updatedCount++;
      }
    }

    showToast(`✅ Jam Check In & Check Out (${updatedCount} hari) berhasil diisi!`);
  } catch (err) {
    showToast('Terjadi kesalahan saat upload file absensi', '❌');
  } finally {
    event.target.value = '';
  }
}

document.getElementById('select-year').addEventListener('change', loadCalendar);
document.getElementById('select-month').addEventListener('change', loadCalendar);

// Initial load
loadConfig();
loadCalendar();