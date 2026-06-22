/* Stress Calendar — academic event manager + 30-day AI stress forecast */
(function () {
  const gridEl = document.getElementById('scGrid');
  const monthLabel = document.getElementById('scMonthLabel');
  const prevBtn = document.getElementById('scPrevMonth');
  const nextBtn = document.getElementById('scNextMonth');
  const spikeBanner = document.getElementById('scSpikeBanner');
  const spikeText = document.getElementById('scSpikeText');
  const addBtn = document.getElementById('scAddBtn');
  const addStatus = document.getElementById('scAddStatus');
  const eventsList = document.getElementById('scEventsList');
  const eventsEmpty = document.getElementById('scEventsEmpty');
  const dayDetail = document.getElementById('scDayDetail');
  const dayDetailTitle = document.getElementById('scDayDetailTitle');
  const dayDetailBody = document.getElementById('scDayDetailBody');

  const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  const TYPE_COLORS = { exam: '#ff6b6b', assignment: '#74c0fc', presentation: '#ffa94d', quiz: '#a9e34b' };
  const TYPE_ICONS = { exam: '📝', assignment: '📋', presentation: '🎤', quiz: '❓' };

  let forecastData = [];   // [{date, stress_score, risk_level, events}]
  let eventsData = [];     // [{id, title, event_type, event_date}]
  let viewYear, viewMonth;
  let chart = null;

  const today = new Date();
  viewYear = today.getFullYear();
  viewMonth = today.getMonth();

  // Pre-fill today as min date
  const dateInput = document.getElementById('scEventDate');
  if (dateInput) dateInput.min = today.toISOString().slice(0, 10);

  // ── Fetch forecast ─────────────────────────────────────────────────────────
  async function loadForecast() {
    try {
      const res = await fetch('/api/stress-forecast');
      const data = await res.json();
      forecastData = data.forecast || [];

      // Spike banner
      const spikes = data.spikes || [];
      if (spikes.length > 0) {
        const spikeDate = new Date(spikes[0].date).toLocaleDateString('en-BD', { month: 'short', day: 'numeric' });
        spikeText.textContent = `High stress predicted on ${spikeDate} — ${spikes[0].events.map(e => e.title).join(', ')}`;
        spikeBanner.style.display = 'flex';
      } else {
        spikeBanner.style.display = 'none';
      }

      renderCalendar();
      renderChart();
    } catch (e) {
      console.error('Forecast error:', e);
    }
  }

  // ── Fetch events ───────────────────────────────────────────────────────────
  async function loadEvents() {
    try {
      const res = await fetch('/api/events');
      eventsData = await res.json();
      renderEventsList();
      loadForecast();
    } catch (e) {
      console.error('Events error:', e);
    }
  }

  // ── Calendar render ────────────────────────────────────────────────────────
  function renderCalendar() {
    monthLabel.textContent = `${MONTHS[viewMonth]} ${viewYear}`;
    gridEl.innerHTML = '';

    const firstDay = new Date(viewYear, viewMonth, 1).getDay();
    const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
    const forecastMap = {};
    forecastData.forEach(f => { forecastMap[f.date] = f; });

    // Empty cells
    for (let i = 0; i < firstDay; i++) {
      const blank = document.createElement('div');
      blank.className = 'sc-day sc-day-blank';
      gridEl.appendChild(blank);
    }

    for (let d = 1; d <= daysInMonth; d++) {
      const dateStr = `${viewYear}-${String(viewMonth + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
      const forecast = forecastMap[dateStr];
      const isToday = dateStr === today.toISOString().slice(0, 10);

      const cell = document.createElement('div');
      cell.className = 'sc-day';
      if (isToday) cell.classList.add('sc-today');
      if (forecast) cell.classList.add(`sc-risk-${forecast.risk_level}`);

      // Event dots
      const dayEvents = eventsData.filter(ev => ev.event_date === dateStr);
      let dotsHtml = '';
      if (dayEvents.length > 0) {
        dotsHtml = '<div class="sc-dots">' +
          dayEvents.slice(0, 3).map(ev => `<span class="sc-dot" style="background:${TYPE_COLORS[ev.event_type] || '#aaa'}" title="${ev.title}"></span>`).join('') +
          '</div>';
      }

      cell.innerHTML = `<span class="sc-day-num">${d}</span>${dotsHtml}`;
      if (forecast && forecast.stress_score) {
        cell.title = `Stress: ${forecast.stress_score}/100`;
      }

      if (dayEvents.length > 0 || (forecast && forecast.events && forecast.events.length > 0)) {
        cell.style.cursor = 'pointer';
        cell.addEventListener('click', () => showDayDetail(dateStr, dayEvents, forecast));
      }

      gridEl.appendChild(cell);
    }
  }

  function showDayDetail(dateStr, dayEvents, forecast) {
    const d = new Date(dateStr);
    dayDetailTitle.textContent = d.toLocaleDateString('en-BD', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

    let html = '';
    if (forecast) {
      const color = forecast.risk_level === 'high' ? '#ff6b6b' : forecast.risk_level === 'medium' ? '#ffa94d' : '#69db7c';
      html += `<div class="sc-day-stress">
        <span>Predicted Stress</span>
        <span style="color:${color};font-weight:700">${forecast.stress_score}/100 (${forecast.risk_level})</span>
      </div>`;
    }
    if (dayEvents.length > 0) {
      html += '<div class="sc-day-events">';
      dayEvents.forEach(ev => {
        html += `<div class="sc-detail-event" style="border-left:3px solid ${TYPE_COLORS[ev.event_type] || '#aaa'}">
          <span class="sc-detail-icon">${TYPE_ICONS[ev.event_type] || '📌'}</span>
          <span class="sc-detail-title">${ev.title}</span>
          <span class="sc-detail-type">${ev.event_type}</span>
        </div>`;
      });
      html += '</div>';
    }
    if (!html) html = '<p style="color:var(--text-muted)">No events on this day.</p>';

    dayDetailBody.innerHTML = html;
    dayDetail.style.display = 'block';
  }

  prevBtn.addEventListener('click', () => {
    viewMonth--;
    if (viewMonth < 0) { viewMonth = 11; viewYear--; }
    renderCalendar();
  });

  nextBtn.addEventListener('click', () => {
    viewMonth++;
    if (viewMonth > 11) { viewMonth = 0; viewYear++; }
    renderCalendar();
  });

  // ── Chart ──────────────────────────────────────────────────────────────────
  function renderChart() {
    const ctx = document.getElementById('scForecastChart');
    if (!ctx || forecastData.length === 0) return;

    const labels = forecastData.map(f => f.day_label || f.date.slice(5));
    const scores = forecastData.map(f => f.stress_score);
    const colors = forecastData.map(f =>
      f.risk_level === 'high' ? 'rgba(255,107,107,0.8)' :
      f.risk_level === 'medium' ? 'rgba(255,169,77,0.8)' :
      'rgba(105,219,124,0.8)'
    );

    if (chart) chart.destroy();
    chart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Stress Score',
          data: scores,
          backgroundColor: colors,
          borderRadius: 4,
          borderSkipped: false,
        }],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: ctx => `Stress: ${ctx.raw}/100`,
              afterLabel: (ctx) => {
                const f = forecastData[ctx.dataIndex];
                if (f.events && f.events.length > 0) {
                  return f.events.map(e => `• ${e.title}`).join('\n');
                }
                return '';
              },
            },
          },
        },
        scales: {
          y: {
            min: 0, max: 100,
            ticks: { color: 'var(--text-muted)', font: { size: 10 } },
            grid: { color: 'rgba(255,255,255,0.05)' },
          },
          x: {
            ticks: {
              color: 'var(--text-muted)',
              font: { size: 9 },
              maxRotation: 45,
              autoSkip: true,
              maxTicksLimit: 15,
            },
            grid: { display: false },
          },
        },
      },
    });
  }

  // ── Events list ────────────────────────────────────────────────────────────
  function renderEventsList() {
    const upcoming = eventsData
      .filter(ev => ev.event_date >= today.toISOString().slice(0, 10))
      .sort((a, b) => a.event_date.localeCompare(b.event_date));

    if (upcoming.length === 0) {
      if (eventsEmpty) eventsEmpty.style.display = 'block';
      return;
    }
    if (eventsEmpty) eventsEmpty.style.display = 'none';

    // Clear non-empty items
    [...eventsList.querySelectorAll('.sc-event-item')].forEach(el => el.remove());

    upcoming.forEach(ev => appendEventItem(ev));
  }

  function appendEventItem(ev) {
    const div = document.createElement('div');
    div.className = 'sc-event-item';
    div.dataset.id = ev.id;
    const color = TYPE_COLORS[ev.event_type] || '#aaa';
    const icon = TYPE_ICONS[ev.event_type] || '📌';
    const d = new Date(ev.event_date + 'T00:00:00');
    const label = d.toLocaleDateString('en-BD', { month: 'short', day: 'numeric' });
    const daysUntil = Math.ceil((d - today) / 86400000);
    const urgency = daysUntil <= 3 ? 'urgent' : daysUntil <= 7 ? 'soon' : '';

    div.innerHTML = `
      <div class="sc-event-left" style="border-left:3px solid ${color}">
        <span class="sc-event-icon">${icon}</span>
        <div class="sc-event-info">
          <span class="sc-event-title">${ev.title}</span>
          <span class="sc-event-meta">${ev.event_type} · ${label}</span>
        </div>
      </div>
      <div class="sc-event-right">
        ${urgency === 'urgent' ? '<span class="sc-urgency-badge urgent">🔥 ' + daysUntil + 'd</span>' :
          urgency === 'soon' ? '<span class="sc-urgency-badge soon">⚡ ' + daysUntil + 'd</span>' :
          '<span class="sc-days-badge">' + daysUntil + 'd</span>'}
        <button class="sc-del-btn" data-id="${ev.id}" title="Remove">✕</button>
      </div>`;

    div.querySelector('.sc-del-btn').addEventListener('click', () => deleteEvent(ev.id));
    eventsList.appendChild(div);
  }

  // ── Add event ──────────────────────────────────────────────────────────────
  addBtn.addEventListener('click', async () => {
    const title = document.getElementById('scEventTitle').value.trim();
    const type = document.getElementById('scEventType').value;
    const date = document.getElementById('scEventDate').value;

    if (!title || !date) {
      addStatus.textContent = 'Please fill in all fields.';
      addStatus.style.color = '#ff6b6b';
      return;
    }

    addBtn.disabled = true;
    addBtn.textContent = 'Adding…';

    try {
      const res = await fetch('/api/events', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, event_type: type, event_date: date }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed');

      eventsData.push(data);
      if (eventsEmpty) eventsEmpty.style.display = 'none';
      appendEventItem(data);
      addStatus.textContent = 'Event added!';
      addStatus.style.color = '#69db7c';
      document.getElementById('scEventTitle').value = '';
      document.getElementById('scEventDate').value = '';
      loadForecast();
    } catch (e) {
      addStatus.textContent = e.message;
      addStatus.style.color = '#ff6b6b';
    } finally {
      addBtn.disabled = false;
      addBtn.textContent = 'Add Event';
      setTimeout(() => { addStatus.textContent = ''; }, 3000);
    }
  });

  async function deleteEvent(id) {
    if (!confirm('Remove this event?')) return;
    try {
      await fetch(`/api/events/${id}`, { method: 'DELETE' });
      eventsData = eventsData.filter(ev => ev.id !== id);
      const item = eventsList.querySelector(`[data-id="${id}"]`);
      if (item) item.remove();
      if (eventsList.querySelectorAll('.sc-event-item').length === 0 && eventsEmpty) {
        eventsEmpty.style.display = 'block';
      }
      loadForecast();
    } catch (e) {
      console.error('Delete error:', e);
    }
  }

  // ── Init ───────────────────────────────────────────────────────────────────
  loadEvents();
})();
