/* DIU WISE AI — Voice Assistant  (VAD live-conversation + manual mode)
 *
 * LIVE MODE state machine:
 *   idle → listening → recording → processing → speaking → listening → …
 *
 * MANUAL MODE:
 *   click mic → recording → processing → speaking → idle
 */
(function () {
  'use strict';

  /* ── DOM ──────────────────────────────────────────────────────────── */
  const micBtn      = document.getElementById('va-mic-btn');
  const micIcon     = document.getElementById('va-mic-icon');
  const stopIcon    = document.getElementById('va-stop-icon');
  const statusEl    = document.getElementById('va-status-text');
  const convo       = document.getElementById('va-convo');
  const thinkingEl  = document.getElementById('va-thinking');
  const thinkingLbl = document.getElementById('va-thinking-label');
  const canvas      = document.getElementById('va-canvas');
  const voiceSel    = document.getElementById('va-voice-select');
  const ring1       = document.getElementById('va-ring-1');
  const ring2       = document.getElementById('va-ring-2');
  const liveBtn     = document.getElementById('va-live-btn');
  const phaseBadge  = document.getElementById('va-phase-badge');
  const ctx2d       = canvas ? canvas.getContext('2d') : null;

  /* ── VAD constants ────────────────────────────────────────────────── */
  const VAD_SPEECH_THRESHOLD = 20;   // peak amplitude (0–128) → speech
  const VAD_SILENCE_MS       = 1400; // ms of silence after speech → auto-send
  const VAD_MIN_SPEECH_MS    = 350;  // ignore bursts shorter than this (noise)
  const VAD_POLL_MS          = 60;   // VAD check interval in ms

  /* ── State ────────────────────────────────────────────────────────── */
  let mode         = 'manual';  // 'manual' | 'live'
  let phase        = 'idle';    // 'idle'|'listening'|'recording'|'processing'|'speaking'
  let micStream    = null;
  let audioCtx     = null;
  let analyser     = null;
  let mediaRec     = null;
  let audioChunks  = [];
  let animFrame    = null;
  let vadTimer     = null;      // setInterval for VAD polling
  let silenceTimer = null;      // setTimeout to fire after VAD_SILENCE_MS
  let speechStart  = null;      // Date.now() when speech began
  let langMode     = 'both';
  let history      = [];        // [{user, ai}] rolling context
  let playingAudio = null;

  /* ── Language pills ───────────────────────────────────────────────── */
  document.querySelectorAll('.va-lang-pill').forEach(p => {
    p.addEventListener('click', () => {
      document.querySelectorAll('.va-lang-pill').forEach(q => q.classList.remove('va-active'));
      p.classList.add('va-active');
      langMode = p.dataset.mode;
    });
  });

  /* ── Phase badge labels ───────────────────────────────────────────── */
  const PHASE_LABELS = {
    idle:       { text: 'Idle',       cls: 'badge-idle'       },
    listening:  { text: 'Listening',  cls: 'badge-listening'  },
    recording:  { text: 'You speak',  cls: 'badge-recording'  },
    processing: { text: 'Thinking…',  cls: 'badge-processing' },
    speaking:   { text: 'AI speaks',  cls: 'badge-speaking'   },
  };

  function setPhase(p) {
    phase = p;
    if (!phaseBadge) return;
    const info = PHASE_LABELS[p] || { text: p, cls: '' };
    phaseBadge.textContent = info.text;
    phaseBadge.className   = 'va-phase-badge ' + info.cls;
  }

  /* ── Status text ──────────────────────────────────────────────────── */
  function setStatus(msg, cls) {
    statusEl.textContent = msg;
    statusEl.className   = 'va-status-text' + (cls ? ' va-' + cls : '');
  }

  function showThinking(label) {
    thinkingEl.classList.remove('va-hidden');
    thinkingLbl.textContent = label || 'Processing…';
  }
  function hideThinking() { thinkingEl.classList.add('va-hidden'); }

  /* ── Canvas waveform ──────────────────────────────────────────────── */
  function drawIdle() {
    if (!ctx2d) return;
    const W = canvas.width, H = canvas.height, mid = H / 2;
    ctx2d.clearRect(0, 0, W, H);
    ctx2d.strokeStyle = 'rgba(99,102,241,0.22)';
    ctx2d.lineWidth = 1.5;
    ctx2d.beginPath(); ctx2d.moveTo(0, mid); ctx2d.lineTo(W, mid); ctx2d.stroke();
  }

  function drawLive() {
    if (!ctx2d || !analyser) return;
    animFrame = requestAnimationFrame(drawLive);
    const W = canvas.width, H = canvas.height;
    const buf = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteTimeDomainData(buf);
    ctx2d.clearRect(0, 0, W, H);
    // Color changes by phase
    ctx2d.strokeStyle = phase === 'recording' ? '#ef4444'
                      : phase === 'speaking'  ? '#a855f7'
                      : '#6366f1';
    ctx2d.lineWidth = 2;
    ctx2d.beginPath();
    const sw = W / buf.length;
    for (let i = 0; i < buf.length; i++) {
      const y = (buf[i] / 128) * (H / 2);
      i === 0 ? ctx2d.moveTo(0, y) : ctx2d.lineTo(i * sw, y);
    }
    ctx2d.stroke();
  }

  /* ── Shared: open microphone ──────────────────────────────────────── */
  async function openMic() {
    micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioCtx  = new (window.AudioContext || window.webkitAudioContext)();
    analyser  = audioCtx.createAnalyser();
    analyser.fftSize = 512;
    audioCtx.createMediaStreamSource(micStream).connect(analyser);
  }

  function closeMic() {
    if (vadTimer)   { clearInterval(vadTimer);   vadTimer   = null; }
    if (silenceTimer){ clearTimeout(silenceTimer); silenceTimer = null; }
    if (animFrame)  { cancelAnimationFrame(animFrame); animFrame = null; }
    if (micStream)  { micStream.getTracks().forEach(t => t.stop()); micStream = null; }
    if (audioCtx)   { audioCtx.close(); audioCtx = null; analyser = null; }
    mediaRec   = null;
    audioChunks = [];
    speechStart = null;
  }

  /* ════════════════════════════════════════════════════════════════════
     LIVE MODE
     ════════════════════════════════════════════════════════════════════ */

  async function startLiveMode() {
    if (mode === 'live') { stopLiveMode(); return; }

    try { await openMic(); } catch {
      setStatus('Microphone access denied.', 'error');
      return;
    }

    mode = 'live';
    liveBtn.textContent  = '⏹ End Conversation';
    liveBtn.classList.add('va-live-active');
    micBtn.disabled = true;

    // Draw waveform continuously
    drawLive();

    // Start VAD loop
    enterListening();
  }

  function stopLiveMode() {
    stopCapture();
    closeMic();
    if (playingAudio) { playingAudio.pause(); playingAudio = null; }
    if (window.speechSynthesis) window.speechSynthesis.cancel();

    mode = 'manual';
    setPhase('idle');
    liveBtn.textContent = '▶ Start Live Conversation';
    liveBtn.classList.remove('va-live-active');
    micBtn.disabled = false;
    setStatus('Tap the mic or start a live conversation', '');
    drawIdle();
  }

  /* ── VAD: enter listening state ───────────────────────────────────── */
  function enterListening() {
    setPhase('listening');
    setStatus('Listening… speak anytime', 'listening');
    ring1.classList.add('va-pulse');
    ring2.classList.add('va-pulse-slow');

    clearInterval(vadTimer);
    vadTimer = setInterval(vadTick, VAD_POLL_MS);
  }

  /* ── VAD: one poll tick ───────────────────────────────────────────── */
  function vadTick() {
    if (!analyser) return;
    const buf = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteTimeDomainData(buf);
    // Peak deviation from silence (128)
    const peak = buf.reduce((m, v) => Math.max(m, Math.abs(v - 128)), 0);

    if (phase === 'listening') {
      if (peak > VAD_SPEECH_THRESHOLD) {
        // Speech detected — transition to recording. Keep vadTimer running
        // so the recording block below can detect silence on the next ticks.
        speechStart = Date.now();
        setPhase('recording');
        setStatus('Recording…', 'listening');
        ring1.classList.remove('va-pulse');
        ring2.classList.remove('va-pulse-slow');
        startCapture();
      }
    } else if (phase === 'recording') {
      if (peak < VAD_SPEECH_THRESHOLD) {
        // Potential silence
        if (!silenceTimer) {
          silenceTimer = setTimeout(() => {
            silenceTimer = null;
            const speechLen = Date.now() - (speechStart || 0);
            if (speechLen > VAD_MIN_SPEECH_MS) {
              // Valid utterance — send it
              stopCapture();         // triggers onRecordingStop → processAudio
            } else {
              // Too short (noise) — reset to listening
              stopCapture(true);     // discard
              enterListening();
            }
          }, VAD_SILENCE_MS);
        }
      } else {
        // Still speaking — cancel pending silence timer
        if (silenceTimer) { clearTimeout(silenceTimer); silenceTimer = null; }
      }
    }
  }

  /* ── Capture helpers ──────────────────────────────────────────────── */
  function startCapture() {
    if (!micStream) return;
    audioChunks = [];
    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus' : 'audio/webm';
    mediaRec = new MediaRecorder(micStream, { mimeType });
    mediaRec.ondataavailable = e => { if (e.data.size > 0) audioChunks.push(e.data); };
    mediaRec.onstop = () => {
      if (phase !== 'idle') onRecordingStop();
    };
    mediaRec.start(200);
  }

  function stopCapture(discard) {
    if (mediaRec && mediaRec.state !== 'inactive') {
      if (discard) {
        mediaRec.ondataavailable = null;
        mediaRec.onstop = null;
      }
      mediaRec.stop();
    }
    if (discard) audioChunks = [];
  }

  /* ════════════════════════════════════════════════════════════════════
     MANUAL MODE
     ════════════════════════════════════════════════════════════════════ */

  micBtn.addEventListener('click', async () => {
    if (mode === 'live') return;  // ignore in live mode

    if (phase === 'recording') {
      // Manual stop
      stopCapture();
      setPhase('idle');
      micIcon.classList.remove('va-hidden');
      stopIcon.classList.add('va-hidden');
      micBtn.classList.remove('va-recording');
      ring1.classList.remove('va-pulse');
      ring2.classList.remove('va-pulse-slow');
      if (animFrame) { cancelAnimationFrame(animFrame); animFrame = null; }
      drawIdle();
      return;
    }

    if (phase !== 'idle') return;

    // Start manual recording
    try { await openMic(); } catch {
      setStatus('Microphone access denied.', 'error');
      return;
    }

    if (playingAudio) { playingAudio.pause(); playingAudio = null; }
    if (window.speechSynthesis) window.speechSynthesis.cancel();

    setPhase('recording');
    micIcon.classList.add('va-hidden');
    stopIcon.classList.remove('va-hidden');
    micBtn.classList.add('va-recording');
    ring1.classList.add('va-pulse');
    ring2.classList.add('va-pulse-slow');
    setStatus('Recording… tap again to stop', 'listening');
    drawLive();
    startCapture();
  });

  /* ════════════════════════════════════════════════════════════════════
     SHARED: process captured audio
     ════════════════════════════════════════════════════════════════════ */

  async function onRecordingStop() {
    if (!audioChunks.length) {
      if (mode === 'live') enterListening();
      else {
        setStatus('No audio captured.', 'error');
        setPhase('idle');
        closeMic();
        drawIdle();
      }
      return;
    }

    // Manual mode: clean up mic controls
    if (mode === 'manual') {
      micIcon.classList.remove('va-hidden');
      stopIcon.classList.add('va-hidden');
      micBtn.classList.remove('va-recording');
    }
    ring1.classList.remove('va-pulse');
    ring2.classList.remove('va-pulse-slow');

    setPhase('processing');
    showThinking('Transcribing…');
    setStatus('Processing…');

    const blob = new Blob(audioChunks, { type: 'audio/webm' });
    audioChunks = [];
    const form  = new FormData();
    form.append('audio',     blob, 'va_input.webm');
    form.append('lang_mode', langMode);
    form.append('history',   JSON.stringify(history.slice(-6)));

    let data;
    try {
      const res = await fetch('/voice-assistant/chat', { method: 'POST', body: form });
      data = await res.json();
    } catch (err) {
      hideThinking();
      setStatus('Network error.', 'error');
      console.error('[VA]', err);
      afterTurn(false);
      return;
    }

    hideThinking();

    if (data.error) {
      setStatus(data.error, 'error');
      appendBubble('ai', data.error, '', '', 'low');
      afterTurn(false);
      return;
    }

    const s = data.structured_response || {};
    appendBubble('user', data.transcript, data.detected_lang);

    const enLines = [s.summary, ...(s.advice || []).slice(0, 2)].filter(Boolean);
    const bnLines = [s.summary_bn, ...(s.advice_bn || []).slice(0, 2)].filter(Boolean);
    appendBubble('ai', enLines.join(' '), 'en', bnLines.join(' '), s.risk_level || 'low');

    history.push({ user: data.transcript, ai: s.summary || '' });
    if (history.length > 10) history.shift();

    setPhase('speaking');
    setStatus('AI is speaking…', 'speaking');
    // English via OpenAI TTS, Bangla via SpeechSynthesis — never mix them
    await speakBilingual(data.tts_en || '', data.tts_bn || '');

    afterTurn(true);
  }

  /* Called after TTS ends — resume listening in live mode or go idle */
  function afterTurn(success) {
    if (mode === 'live') {
      // Resume listening automatically
      enterListening();
    } else {
      // Manual mode: close mic and go idle
      if (animFrame) { cancelAnimationFrame(animFrame); animFrame = null; }
      closeMic();
      setPhase('idle');
      drawIdle();
      setStatus('Tap the mic to speak');
    }
  }

  /* ════════════════════════════════════════════════════════════════════
     TTS: bilingual sequential pipeline
     English  → OpenAI TTS (/voice-assistant/speak) — high quality
     Bangla   → browser SpeechSynthesis bn-BD       — only correct option
     ════════════════════════════════════════════════════════════════════ */

  let bnVoice = null;   // cached Bengali SpeechSynthesis voice

  function findBengaliVoice() {
    if (!window.speechSynthesis) return null;
    const voices = window.speechSynthesis.getVoices();
    // Prefer bn-BD, then bn-IN, then any Bengali voice
    return voices.find(v => v.lang === 'bn-BD')
        || voices.find(v => v.lang === 'bn-IN')
        || voices.find(v => v.lang.startsWith('bn'))
        || null;
  }

  function initBengaliVoice() {
    bnVoice = findBengaliVoice();
    if (!bnVoice && phaseBadge) {
      // Soft warning — doesn't block usage
      console.info('[VA] No Bengali TTS voice found. Bangla will be displayed but not spoken.');
    }
  }

  async function speakBilingual(enText, bnText) {
    // 1. English → OpenAI TTS (clean, never send Bangla here)
    if (enText && enText.trim()) {
      await speakEnglish(enText.trim());
    }
    // 2. Bangla → browser SpeechSynthesis with bn-BD voice
    if (bnText && bnText.trim()) {
      await speakBangla(bnText.trim());
    }
  }

  async function speakEnglish(text) {
    const voice = voiceSel ? voiceSel.value : 'nova';
    try {
      const res = await fetch('/voice-assistant/speak', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ text, voice }),
      });
      const ct = res.headers.get('Content-Type') || '';
      if (ct.includes('audio')) {
        const blob = await res.blob();
        const url  = URL.createObjectURL(blob);
        playingAudio = new Audio(url);
        await new Promise(resolve => {
          playingAudio.onended = resolve;
          playingAudio.onerror = resolve;
          playingAudio.play().catch(resolve);
        });
        URL.revokeObjectURL(url);
        playingAudio = null;
        return;
      }
      // Fallback: browser English voice
      await browserSpeakLang(text, 'en-US');
    } catch (err) {
      console.warn('[VA] English TTS error:', err);
      await browserSpeakLang(text, 'en-US');
    }
  }

  function speakBangla(text) {
    if (!bnVoice) {
      // No Bengali voice installed — skip audio, text is visible in the bubble
      return Promise.resolve();
    }
    return browserSpeakLang(text, 'bn-BD', bnVoice);
  }

  function browserSpeakLang(text, lang, forceVoice) {
    return new Promise(resolve => {
      if (!window.speechSynthesis || !text) { resolve(); return; }
      window.speechSynthesis.cancel();
      const utt  = new SpeechSynthesisUtterance(text);
      utt.lang   = lang;
      utt.rate   = lang.startsWith('bn') ? 0.88 : 0.95;  // slightly slower for Bangla
      utt.pitch  = 1.0;
      if (forceVoice) {
        utt.voice = forceVoice;
      } else {
        const vs    = window.speechSynthesis.getVoices();
        const match = vs.find(v => v.lang.startsWith(lang.split('-')[0]));
        if (match) utt.voice = match;
      }
      utt.onend   = resolve;
      utt.onerror = resolve;
      window.speechSynthesis.speak(utt);
    });
  }

  /* ════════════════════════════════════════════════════════════════════
     Bubble renderer
     ════════════════════════════════════════════════════════════════════ */

  function appendBubble(role, enText, lang, bnText, riskLevel) {
    document.getElementById('va-welcome')?.remove();

    const wrap = document.createElement('div');
    wrap.className = `va-bubble va-bubble-${role}`;

    if (role === 'user') {
      wrap.innerHTML = `
        <div class="va-bubble-meta">
          <span class="va-lang-tag">${esc(lang || 'voice')}</span>
        </div>
        <div class="va-bubble-text">${esc(enText)}</div>`;
    } else {
      const badge = (riskLevel === 'high' || riskLevel === 'medium')
        ? `<span class="va-risk-badge va-risk-${riskLevel}">${riskLevel === 'high' ? '⚠ High' : '· Medium'}</span>`
        : '';
      wrap.innerHTML = `
        <div class="va-bubble-meta">
          <img src="/static/images/wellness_bot.png" class="va-bot-avatar" alt="AI">
          <span>WISE AI</span>${badge}
        </div>
        <div class="va-bubble-text">${esc(enText)}</div>
        ${bnText ? `<div class="va-bubble-text va-bubble-bn">${esc(bnText)}</div>` : ''}`;
    }
    convo.appendChild(wrap);
    convo.scrollTop = convo.scrollHeight;
  }

  function esc(s) {
    return (s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  /* ── Live button ──────────────────────────────────────────────────── */
  if (liveBtn) liveBtn.addEventListener('click', startLiveMode);

  /* ── Init ─────────────────────────────────────────────────────────── */
  hideThinking();
  setPhase('idle');
  drawIdle();

  if (window.speechSynthesis) {
    // Voices load async in Chrome — initialise once list is ready
    if (window.speechSynthesis.getVoices().length > 0) {
      initBengaliVoice();
    }
    window.speechSynthesis.onvoiceschanged = () => {
      initBengaliVoice();
      updateBnVoiceHint();
    };
    // Trigger early for Firefox/Safari which don't fire onvoiceschanged
    setTimeout(() => { initBengaliVoice(); updateBnVoiceHint(); }, 800);
  }

  function updateBnVoiceHint() {
    const hint = document.getElementById('va-bn-voice-hint');
    if (!hint) return;
    if (bnVoice) {
      hint.textContent = `Bengali voice: ${bnVoice.name}`;
      hint.className = 'va-bn-hint va-bn-ok';
    } else {
      hint.textContent = 'No Bengali voice installed — Bangla shown as text only';
      hint.className = 'va-bn-hint va-bn-warn';
    }
  }

  if (!navigator.mediaDevices || !window.MediaRecorder) {
    if (micBtn) micBtn.disabled = true;
    if (liveBtn) liveBtn.disabled = true;
    setStatus('Recording not supported — please use Chrome or Edge.', 'error');
  }
})();
