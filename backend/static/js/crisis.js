/* ============================================================
   Crisis Safety Net
   Triggered when the assistant flags HIGH distress. Shows a
   calming box-breathing exercise + verified emergency helplines.
   Exposes: window.CrisisSafetyNet.trigger()
   ============================================================ */
(function () {
  const overlay = document.getElementById('crisis-overlay');
  if (!overlay) return; // Only present for logged-in students

  const orb = document.getElementById('breathe-orb');
  const phaseText = document.getElementById('breathe-phase');
  const toggleBtn = document.getElementById('breathe-toggle');
  const closeBtn = document.getElementById('crisis-close');
  const helplineList = document.getElementById('helpline-list');

  // Box-breathing cycle: 4s inhale -> 4s hold -> 4s exhale -> 4s hold
  const PHASES = [
    { label: 'Breathe in…', cls: 'inhale', ms: 4000 },
    { label: 'Hold',        cls: 'hold',   ms: 4000 },
    { label: 'Breathe out…', cls: 'exhale', ms: 4000 },
    { label: 'Hold',        cls: 'hold',   ms: 4000 },
  ];

  let phaseIndex = 0;
  let timer = null;
  let running = false;
  let resourcesLoaded = false;

  function applyPhase(i) {
    const p = PHASES[i];
    orb.classList.remove('inhale', 'exhale', 'hold');
    orb.classList.add(p.cls);
    phaseText.textContent = p.label;
  }

  function step() {
    applyPhase(phaseIndex);
    timer = setTimeout(() => {
      phaseIndex = (phaseIndex + 1) % PHASES.length;
      step();
    }, PHASES[phaseIndex].ms);
  }

  function startBreathing() {
    if (running) return;
    running = true;
    toggleBtn.textContent = 'Pause';
    step();
  }

  function stopBreathing() {
    running = false;
    toggleBtn.textContent = 'Resume';
    if (timer) clearTimeout(timer);
    orb.classList.remove('inhale', 'exhale', 'hold');
  }

  const phoneIcon =
    '<svg viewBox="0 0 24 24"><path d="M6.62 10.79a15.05 15.05 0 0 0 6.59 6.59l2.2-2.2a1 1 0 0 1 1.02-.24 11.36 11.36 0 0 0 3.57.57 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.25.2 2.45.57 3.57a1 1 0 0 1-.25 1.02l-2.2 2.2z"/></svg>';

  function renderHelplines(resources) {
    helplineList.innerHTML = '';
    resources.forEach((r) => {
      const row = document.createElement('div');
      row.className = 'helpline' + (r.priority ? ' priority' : '');

      const info = document.createElement('div');
      info.className = 'helpline-info';
      info.innerHTML =
        '<div class="helpline-name"></div>' +
        '<div class="helpline-desc"></div>' +
        '<div class="helpline-hours"></div>';
      info.querySelector('.helpline-name').textContent = r.name;
      info.querySelector('.helpline-desc').textContent = r.desc || '';
      info.querySelector('.helpline-hours').textContent = r.hours || '';

      let action;
      if (r.tel) {
        action = document.createElement('a');
        action.href = 'tel:' + r.tel;
        action.className = 'helpline-call';
        action.innerHTML = phoneIcon + '<span></span>';
        action.querySelector('span').textContent = r.phone;
      } else {
        action = document.createElement('span');
        action.className = 'helpline-call no-tel';
        action.textContent = r.phone || 'Info';
      }

      row.appendChild(info);
      row.appendChild(action);
      helplineList.appendChild(row);
    });
  }

  // Fallback resources if the API call fails (keeps the safety net reliable offline)
  const FALLBACK = [
    { name: 'National Emergency Service', phone: '999', tel: '999', hours: '24/7 — every day', desc: 'Free national emergency line for immediate, life-threatening situations.', priority: true },
    { name: 'Kaan Pete Roi', phone: '09612-119911', tel: '09612119911', hours: 'Every day, 3:00 PM – 3:00 AM', desc: "Bangladesh's emotional-support & suicide-prevention helpline.", priority: true },
    { name: 'Moner Bondhu', phone: '01776-632344', tel: '01776632344', hours: 'Daytime support', desc: 'Mental-health support and counselling.', priority: false },
  ];

  async function loadResources() {
    if (resourcesLoaded) return;
    try {
      const res = await fetch('/crisis-resources', { headers: { Accept: 'application/json' } });
      const data = await res.json();
      renderHelplines(data.resources && data.resources.length ? data.resources : FALLBACK);
    } catch (e) {
      renderHelplines(FALLBACK);
    }
    resourcesLoaded = true;
  }

  function open() {
    loadResources();
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
    phaseIndex = 0;
    startBreathing();
  }

  function close() {
    overlay.classList.remove('active');
    document.body.style.overflow = '';
    stopBreathing();
  }

  // Wire up controls
  closeBtn.addEventListener('click', close);
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) close();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && overlay.classList.contains('active')) close();
  });
  toggleBtn.addEventListener('click', () => {
    running ? stopBreathing() : startBreathing();
  });

  // Public API
  window.CrisisSafetyNet = { trigger: open, close: close };
})();
