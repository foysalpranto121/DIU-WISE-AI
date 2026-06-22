/* Voice Journal — Web Speech API (primary) + Whisper backend (fallback) */
(function () {
  /* ── DOM refs ─────────────────────────────────────────────────────── */
  const recordBtn      = document.getElementById('vjRecordBtn');
  const recIcon        = document.getElementById('vjRecIcon');
  const recLabel       = document.getElementById('vjRecLabel');
  const timerEl        = document.getElementById('vjTimer');
  const canvas         = document.getElementById('vjCanvas');
  const saveBar        = document.getElementById('vjSaveBar');
  const saveBtn        = document.getElementById('vjSaveBtn');
  const clearBtn       = document.getElementById('vjClearBtn');
  const resultPanel    = document.getElementById('vjResultPanel');
  const resultEmotion  = document.getElementById('vjResultEmotion');
  const statusEl       = document.getElementById('vjStatus');
  const newBtn         = document.getElementById('vjNewBtn');
  const transcriptBox  = document.getElementById('vjTranscriptArea');
  const transcriptWrap = document.getElementById('vjTranscriptWrap');
  const loadingEl      = document.getElementById('vjLoading');
  const entriesEl      = document.getElementById('vjEntries');
  const entryCountEl   = document.getElementById('vjEntryCount');
  const emptyHistory   = document.getElementById('vjEmptyHistory');
  const sendChatBtn    = document.getElementById('vjSendChatBtn');
  const chatAfterSave  = document.getElementById('vjChatAfterSave');

  /* ── Helpers ──────────────────────────────────────────────────────── */
  function show(el, displayVal) {
    if (!el) return;
    el.classList.remove('hidden');
    if (displayVal) el.style.display = displayVal;
  }
  function hide(el) {
    if (!el) return;
    el.classList.add('hidden');
    el.style.display = '';
  }
  function showStatus(msg, type = 'info') {
    statusEl.textContent = msg;
    statusEl.className = `vj-status vj-status-${type}`;
  }
  function clearStatus() { statusEl.textContent = ''; statusEl.className = 'vj-status'; }

  /* ── State ────────────────────────────────────────────────────────── */
  let isRecording    = false;
  let timerInterval  = null;
  let seconds        = 0;
  let detectedLang   = 'unknown';
  let lastTranscript = '';

  // Web Speech API state
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  let recognition        = null;
  let finalTranscript    = '';
  let interimTranscript  = '';
  let useWebSpeech       = !!SpeechRecognition;

  // MediaRecorder state (Whisper fallback)
  let mediaRecorder = null;
  let audioChunks   = [];
  let audioCtx      = null;
  let analyser      = null;
  let animFrame     = null;
  let stream        = null;

  /* ── Canvas waveform ──────────────────────────────────────────────── */
  const ctx = canvas ? canvas.getContext('2d') : null;

  function drawIdle() {
    if (!ctx) return;
    const W = canvas.width, H = canvas.height, mid = H / 2;
    ctx.clearRect(0, 0, W, H);
    ctx.strokeStyle = 'rgba(99,102,241,0.3)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(0, mid); ctx.lineTo(W, mid);
    ctx.stroke();
  }

  function drawWave() {
    if (!ctx || !analyser) return;
    animFrame = requestAnimationFrame(drawWave);
    const W = canvas.width, H = canvas.height;
    const bufLen = analyser.frequencyBinCount;
    const data = new Uint8Array(bufLen);
    analyser.getByteTimeDomainData(data);
    ctx.clearRect(0, 0, W, H);
    ctx.strokeStyle = '#6366f1';
    ctx.lineWidth = 2;
    ctx.beginPath();
    const sliceW = W / bufLen;
    let x = 0;
    for (let i = 0; i < bufLen; i++) {
      const v = data[i] / 128.0;
      const y = (v * H) / 2;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      x += sliceW;
    }
    ctx.stroke();
  }

  /* ── Timer ─────────────────────────────────────────────────────────── */
  function startTimer() {
    seconds = 0;
    timerInterval = setInterval(() => {
      seconds++;
      timerEl.textContent =
        String(Math.floor(seconds / 60)).padStart(2, '0') + ':' +
        String(seconds % 60).padStart(2, '0');
    }, 1000);
  }
  function stopTimer() { clearInterval(timerInterval); }

  /* ── UI: recording started ─────────────────────────────────────────── */
  function setRecordingUI() {
    isRecording = true;
    recordBtn.classList.add('recording');
    recIcon.innerHTML = '<svg viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor"/></svg>';
    recLabel.textContent = 'Stop Recording';
    hide(saveBar); hide(resultPanel); hide(loadingEl);
    show(transcriptWrap);
    transcriptBox.value = '';
    finalTranscript = ''; interimTranscript = '';
    startTimer();
  }

  /* ── UI: recording stopped ─────────────────────────────────────────── */
  function setStoppedUI() {
    isRecording = false;
    recordBtn.classList.remove('recording');
    recIcon.innerHTML = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="6" fill="currentColor"/></svg>';
    recLabel.textContent = 'Start Recording';
    stopTimer();
    drawIdle();
    if (audioCtx) { audioCtx.close(); audioCtx = null; analyser = null; }
    if (animFrame) { cancelAnimationFrame(animFrame); animFrame = null; }
    if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
  }

  /* ════════════════════════════════════════════════════════════════════
     PRIMARY: Web Speech API — real-time, instant, no server call
     ════════════════════════════════════════════════════════════════════ */
  function startWebSpeech() {
    const langEl = document.querySelector('.vj-lang-pill.active');
    const lang   = langEl ? langEl.dataset.lang : 'en-US';
    detectedLang = lang;

    recognition = new SpeechRecognition();
    recognition.continuous      = true;
    recognition.interimResults  = true;
    recognition.maxAlternatives = 1;
    recognition.lang            = lang;

    recognition.onstart = () => {
      setRecordingUI();
      showStatus('Listening… speak now', 'info');
      // Start visualizer via MediaStream
      navigator.mediaDevices.getUserMedia({ audio: true }).then(s => {
        stream = s;
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioCtx.createAnalyser();
        analyser.fftSize = 512;
        audioCtx.createMediaStreamSource(stream).connect(analyser);
        drawWave();
      }).catch(() => {});
    };

    recognition.onresult = (event) => {
      interimTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const t = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += t + ' ';
        } else {
          interimTranscript += t;
        }
      }
      // Show combined in textarea in real-time
      transcriptBox.value = finalTranscript + interimTranscript;
      lastTranscript = transcriptBox.value;
    };

    recognition.onerror = (event) => {
      if (event.error === 'not-allowed') {
        showStatus('Microphone access denied. Please allow microphone permission.', 'error');
      } else if (event.error === 'network') {
        showStatus('Network error — switching to Whisper AI...', 'info');
        useWebSpeech = false;
        stopWebSpeech();
        startWhisper();
        return;
      } else if (event.error !== 'aborted') {
        showStatus(`Speech error: ${event.error}`, 'error');
      }
    };

    recognition.onend = () => {
      if (!isRecording) return; // already stopped by user
      // Auto-restart if still recording (recognition stops after silence)
      if (isRecording) recognition.start();
    };

    recognition.start();
  }

  function stopWebSpeech() {
    if (recognition) {
      recognition.onend = null; // prevent auto-restart
      recognition.stop();
      recognition = null;
    }
    setStoppedUI();
    const text = (finalTranscript + interimTranscript).trim();
    if (text) {
      lastTranscript = text;
      transcriptBox.value = text;
      show(transcriptWrap);
      show(saveBar);
      const langLabel = document.getElementById('vjLangDetected');
      if (langLabel) langLabel.textContent = `Detected: ${detectedLang}`;
      clearStatus();
    } else {
      showStatus('Nothing captured. Try speaking louder or check your microphone.', 'error');
    }
  }

  /* ════════════════════════════════════════════════════════════════════
     FALLBACK: MediaRecorder + Whisper backend
     ════════════════════════════════════════════════════════════════════ */
  async function startWhisper() {
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (e) {
      showStatus('Microphone access denied.', 'error');
      return;
    }

    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 512;
    audioCtx.createMediaStreamSource(stream).connect(analyser);

    audioChunks = [];
    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : '';

    mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : {});
    mediaRecorder.ondataavailable = e => { if (e.data.size > 0) audioChunks.push(e.data); };
    mediaRecorder.onstop = handleWhisperStop;
    mediaRecorder.start(200);

    setRecordingUI();
    drawWave();
    showStatus('Recording… (Whisper mode)', 'info');
  }

  function stopWhisper() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') mediaRecorder.stop();
    setStoppedUI();
  }

  async function handleWhisperStop() {
    if (audioChunks.length === 0) {
      showStatus('No audio captured.', 'error');
      return;
    }

    const blob = new Blob(audioChunks, { type: 'audio/webm' });
    show(loadingEl);
    showStatus('Transcribing with Whisper AI…', 'info');
    const progressTimer = setTimeout(() => showStatus('Still transcribing… almost done', 'info'), 10000);

    const formData = new FormData();
    formData.append('audio', blob, 'recording.webm');
    const controller = new AbortController();
    const timeoutId  = setTimeout(() => controller.abort(), 28000);

    try {
      const res  = await fetch('/voice-journal/transcribe', { method: 'POST', body: formData, signal: controller.signal });
      clearTimeout(timeoutId); clearTimeout(progressTimer);
      const data = await res.json();
      hide(loadingEl);

      if (data.error || data.fallback) {
        showManualInput('');
        showStatus(`Transcription failed: ${data.error || 'Whisper unavailable'}. Type below.`, 'error');
      } else {
        detectedLang = data.language || 'unknown';
        showManualInput(data.transcript, data.language);
        clearStatus();
      }
    } catch (err) {
      clearTimeout(timeoutId); clearTimeout(progressTimer);
      hide(loadingEl);
      showManualInput('');
      showStatus(err.name === 'AbortError'
        ? 'Timed out. Type your entry below.'
        : `Error: ${err.message}`, 'error');
    }
  }

  function showManualInput(text, lang) {
    lastTranscript = text || '';
    transcriptBox.value = lastTranscript;
    const langLabel = document.getElementById('vjLangDetected');
    if (langLabel) langLabel.textContent = lang ? `Detected: ${lang}` : '';
    show(transcriptWrap);
    show(saveBar);
    transcriptBox.focus();
  }

  /* ── Record button ─────────────────────────────────────────────────── */
  recordBtn.addEventListener('click', () => {
    if (isRecording) {
      useWebSpeech ? stopWebSpeech() : stopWhisper();
    } else {
      hide(resultPanel);
      transcriptBox.value = '';
      finalTranscript = ''; interimTranscript = '';
      clearStatus();
      if (useWebSpeech) startWebSpeech();
      else startWhisper();
    }
  });

  /* ── Language pills ────────────────────────────────────────────────── */
  document.querySelectorAll('.vj-lang-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      document.querySelectorAll('.vj-lang-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      if (isRecording && recognition) {
        // Restart recognition with new language
        recognition.onend = null;
        recognition.stop();
        finalTranscript = transcriptBox.value;
        setTimeout(() => { if (isRecording) startWebSpeech(); }, 200);
      }
    });
  });

  /* ── Send to AI Chat ───────────────────────────────────────────────── */
  function sendToAIChat() {
    const text = (transcriptBox ? transcriptBox.value.trim() : '') || lastTranscript.trim();
    if (!text) return;

    const chatWidget = document.getElementById('chat-widget');
    const chatBubble = document.getElementById('chat-bubble');
    const chatInput  = document.getElementById('chat-input');
    const chatSend   = document.getElementById('chat-send');
    if (!chatInput || !chatSend) return;

    if (chatWidget) { chatWidget.classList.remove('minimized'); chatWidget.classList.add('active'); }
    if (chatBubble) chatBubble.style.display = 'none';

    chatInput.value = `I just recorded a voice journal entry. Here's what I said:\n\n"${text}"\n\nBased on this, can you give me some mental wellness suggestions or support?`;
    chatInput.focus();
    setTimeout(() => chatSend.click(), 150);
  }

  if (sendChatBtn)  sendChatBtn.addEventListener('click', sendToAIChat);
  if (chatAfterSave) chatAfterSave.addEventListener('click', sendToAIChat);
  if (transcriptBox) transcriptBox.addEventListener('input', () => { lastTranscript = transcriptBox.value; });

  /* ── Save ──────────────────────────────────────────────────────────── */
  saveBtn.addEventListener('click', async () => {
    const text = (transcriptBox.value || '').trim();
    if (!text) { showStatus('Please record or type something first.', 'error'); return; }

    saveBtn.disabled = true;
    saveBtn.textContent = 'Analyzing…';
    try {
      const res  = await fetch('/voice-journal/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcript: text, language: detectedLang, duration: seconds }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Save failed');

      hide(saveBar); hide(transcriptWrap); show(resultPanel);
      const COLORS = { stress:'#ff6b6b', anxiety:'#ffa94d', burnout:'#cc5de8', confusion:'#74c0fc', neutral:'#69db7c' };
      const em = data.emotion || 'neutral';
      resultEmotion.innerHTML = `
        <div class="vj-emotion-result" style="border-left:4px solid ${COLORS[em]||'#69db7c'}">
          <span class="vj-emotion-label">Detected Emotion</span>
          <span class="vj-emotion-value" style="color:${COLORS[em]||'#69db7c'}">${em[0].toUpperCase()+em.slice(1)}</span>
        </div>`;
      prependEntry(data, text);
      timerEl.textContent = '00:00';
      clearStatus();
    } catch (err) {
      showStatus(err.message, 'error');
    } finally {
      saveBtn.disabled = false;
      saveBtn.textContent = 'Save & Analyze Emotion';
    }
  });

  clearBtn.addEventListener('click', () => {
    transcriptBox.value = ''; hide(transcriptWrap); hide(saveBar);
    timerEl.textContent = '00:00'; clearStatus();
  });

  newBtn.addEventListener('click', () => {
    hide(resultPanel); transcriptBox.value = '';
    hide(transcriptWrap); hide(saveBar);
    timerEl.textContent = '00:00'; seconds = 0; clearStatus();
  });

  /* ── History helpers ───────────────────────────────────────────────── */
  function prependEntry(data, text) {
    if (emptyHistory) hide(emptyHistory);
    const div = document.createElement('div');
    div.className = 'vj-entry-item';
    div.dataset.id = data.entry_id;
    div.innerHTML = `
      <div class="vj-entry-top">
        <span class="vj-emotion-badge vj-emotion-${data.emotion}">${(data.emotion||'neutral').replace(/^\w/,c=>c.toUpperCase())}</span>
        <span class="vj-entry-lang">${data.language||'—'}</span>
        <span class="vj-entry-time">just now</span>
        <button type="button" class="vj-delete-btn" data-id="${data.entry_id}" title="Delete">✕</button>
      </div>
      <p class="vj-entry-text">${text}</p>`;
    entriesEl.prepend(div);
    const cur = parseInt(entryCountEl.textContent) || 0;
    entryCountEl.textContent = `${cur + 1} entries`;
    bindDelete(div.querySelector('.vj-delete-btn'));
  }

  function bindDelete(btn) {
    btn.addEventListener('click', async () => {
      if (!confirm('Delete this entry?')) return;
      const res = await fetch(`/voice-journal/entries/${btn.dataset.id}`, { method: 'DELETE' });
      if (res.ok) {
        btn.closest('.vj-entry-item').remove();
        const cur = parseInt(entryCountEl.textContent) || 1;
        entryCountEl.textContent = `${cur - 1} entries`;
        if (!entriesEl.querySelector('.vj-entry-item') && emptyHistory) show(emptyHistory);
      }
    });
  }

  document.querySelectorAll('.vj-delete-btn').forEach(bindDelete);

  /* ── Init ──────────────────────────────────────────────────────────── */
  if (useWebSpeech) {
    showStatus('Ready — Web Speech mode (real-time)', 'info');
    setTimeout(clearStatus, 2500);
  } else if (!navigator.mediaDevices || !window.MediaRecorder) {
    recordBtn.disabled = true;
    showStatus('Recording not supported. Use Chrome or Edge.', 'error');
  }
  drawIdle();
})();
