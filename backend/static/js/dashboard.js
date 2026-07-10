document.addEventListener('DOMContentLoaded', () => {
  // --- UI Utilities ---
  
  const descElements = {
    'mood': 'mood-desc-detail',
    'stress-level': 'stress-desc-detail',
    'sleep-quality': 'sleep-desc-detail',
    'screen-time': 'screen-desc-detail',
    'social-interaction': 'social-desc-detail',
    'break-frequency': 'break-desc-detail'
  };

  function updateMetricDescription(id, val) {
    const descEl = document.getElementById(descElements[id]);
    if (!descEl) return;
    
    let descText = '';
    const numericVal = parseFloat(val);
    
    if (id === 'mood') {
      const moodMap = {
        1: "😞 Very Low (e.g. persistent sadness, exhaustion; maps to high emotional distress)",
        2: "😟 Low / Anxious (e.g. worry, frustration; indicates mild-to-moderate anxiety)",
        3: "😐 Neutral / Okay (e.g. stable mood baseline, standard everyday functioning)",
        4: "🙂 Good / Content (e.g. positive mindset, optimistic emotional state)",
        5: "😄 Excellent / Happy (e.g. high energy, enthusiasm, and joy)"
      };
      descText = moodMap[numericVal] || '';
    } else if (id === 'stress-level') {
      if (numericVal <= 2) descText = "Calm / Relaxed (Minimal stress indicators)";
      else if (numericVal <= 4) descText = "Mild / Manageable (Typical daily pressures)";
      else if (numericVal <= 6) descText = "Moderate (Elevated tension; consider taking a brief break)";
      else if (numericVal <= 8) descText = "High Stress (Significant fatigue; recommended relaxation exercises)";
      else descText = "Severe / Overwhelmed (Urgent rest needed; support pathways advised)";
    } else if (id === 'sleep-quality') {
      if (numericVal <= 2) descText = "Very Poor (Severe disruption/insomnia)";
      else if (numericVal <= 4) descText = "Restless (Frequent wakeups, unrefreshing sleep)";
      else if (numericVal <= 6) descText = "Fair / Average (Slightly disrupted but sufficient)";
      else if (numericVal <= 8) descText = "Good / Restful (Solid rest, normal sleep latency)";
      else descText = "Excellent (Deep, completely rejuvenating sleep)";
    } else if (id === 'screen-time') {
      if (numericVal <= 3) descText = "Very Low (Minimal digital eye strain)";
      else if (numericVal <= 6) descText = "Low / Balanced (Standard digital study allocation)";
      else if (numericVal <= 9) descText = "Moderate (Extended exposure; take screen breaks)";
      else if (numericVal <= 12) descText = "High (Increased risk of fatigue and eye strain)";
      else descText = "Extreme (WHO warning: high risk of study burnout)";
    } else if (id === 'social-interaction') {
      if (numericVal <= 2) descText = "Highly Isolated (Lack of supportive peer contact)";
      else if (numericVal <= 4) descText = "Low Socialization (Limited peer interaction today)";
      else if (numericVal <= 6) descText = "Moderate (Standard connection with friends/family)";
      else if (numericVal <= 8) descText = "Active Connection (Strong supportive conversations)";
      else descText = "Excellent Support (Strong, meaningful social engagement)";
    } else if (id === 'break-frequency') {
      if (numericVal <= 3) descText = "Infrequent / Continuous Study (High risk of cognitive overload)";
      else if (numericVal <= 7) descText = "Optimal / Periodic Breaks (Maintains healthy focus levels)";
      else descText = "Highly Frequent / Restorative (Helps recover from high fatigue)";
    }
    descEl.innerText = descText;
  }

  // Slider Value Sync
  const sliders = {
    'stress-level': 'stress-val',
    'sleep-quality': 'sleep-val',
    'screen-time': 'screen-val',
    'social-interaction': 'social-val',
    'break-frequency': 'break-val'
  };

  Object.entries(sliders).forEach(([id, valId]) => {
    const slider = document.getElementById(id);
    const display = document.getElementById(valId);
    if (slider && display) {
      slider.addEventListener('input', (e) => {
        let suffix = '';
        if (id === 'screen-time') suffix = 'h';
        else if (id.includes('level') || id.includes('quality') || id.includes('interaction')) suffix = '/10';
        
        let val = e.target.value;
        if (id === 'break-frequency') {
          val = val > 7 ? 'High' : val > 3 ? 'Medium' : 'Low';
        }
        display.innerText = `${val}${suffix}`;
        updateMetricDescription(id, e.target.value);
      });
    }
  });

  // Mood Picker
  const moodEmojis = document.querySelectorAll('.mood-emoji');
  const moodValDisplay = document.getElementById('mood-val');
  let selectedMood = 3;
  
  const moodTextMap = {
    1: "Very Low",
    2: "Low / Anxious",
    3: "Okay",
    4: "Good / Content",
    5: "Excellent"
  };

  moodEmojis.forEach(emoji => {
    emoji.addEventListener('click', () => {
      moodEmojis.forEach(e => e.classList.remove('active'));
      emoji.classList.add('active');
      selectedMood = parseInt(emoji.dataset.mood);
      if (moodValDisplay) {
        moodValDisplay.innerText = moodTextMap[selectedMood] || '';
      }
      updateMetricDescription('mood', selectedMood);
    });
  });

  // Initialize descriptions and initial displays
  updateMetricDescription('mood', selectedMood);
  if (moodValDisplay) {
    moodValDisplay.innerText = moodTextMap[selectedMood] || '';
  }
  Object.keys(sliders).forEach(id => {
    const slider = document.getElementById(id);
    if (slider) {
      updateMetricDescription(id, slider.value);
    }
  });

  // Wire up the aura CTA button to scroll to the insights form
  const auraStartBtn = document.getElementById('aura-start-btn');
  if (auraStartBtn) {
    auraStartBtn.addEventListener('click', () => {
      const insightsPanel = document.getElementById('predict-send');
      if (insightsPanel) insightsPanel.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });
  }

  // --- Core API Interaction ---

  const predictSend = document.getElementById('predict-send');
  let forecastChartInstance = null;

  if (predictSend) {
    predictSend.addEventListener('click', async () => {
      const payload = {
        stress_level: document.getElementById('stress-level').value,
        sleep_quality: document.getElementById('sleep-quality').value,
        screen_time: document.getElementById('screen-time').value,
        social_interaction: document.getElementById('social-interaction').value,
        break_frequency: document.getElementById('break-frequency').value,
        mood_score: selectedMood,
        journal_text: document.getElementById('journal-prompt').value,
        // Mock academic data if not present
        attendance_rate: 85,
        submission_delay: 1,
        grades: 78,
        activity_score: 60
      };

      predictSend.disabled = true;
      predictSend.innerText = 'Analyzing Wellbeing...';

      try {
        const res = await fetch('/predict', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        
        const container = document.getElementById('predict-result-container');
        container.style.display = 'flex';

        if (data.wellbeing) {
          const status = data.wellbeing.status;
          const statusElem = document.getElementById('current-risk-value');
          const confidenceElem = document.getElementById('confidence-val');
          const descElem = document.getElementById('status-desc');
          
          statusElem.innerText = status;
          confidenceElem.innerText = `${data.wellbeing.confidence}% Confidence`;
          
          // Color coding & Aura
          if (status === 'Doing Well') {
            statusElem.style.color = 'var(--success)';
            updateAura('low-risk', 'Your wellness state is stable. Keep up the good work!');
          } else if (status === 'Balanced') {
            statusElem.style.color = 'var(--warning)';
            updateAura('medium-risk', 'You are managing things well, but consider a small break.');
          } else {
            statusElem.style.color = 'var(--danger)';
            updateAura('high-risk', 'We noticed some stress indicators. We are here to support you.');
            // Show intervention panel
            const intervention = document.getElementById('intervention-panel');
            if (intervention) intervention.style.display = 'block';
          }

          // Dynamic Guidance
          const guidanceList = document.getElementById('guidance-list');
          guidanceList.innerHTML = '';
          if (data.triage && data.triage.actions) {
            data.triage.actions.forEach(action => {
              const item = document.createElement('div');
              item.className = 'guidance-item';
              item.innerHTML = `<i class="icon">✨</i> ${action}`;
              guidanceList.appendChild(item);
            });
            descElem.innerText = data.triage.message;
          }

          // Forecast
          renderForecastChart(status, data.wellbeing.forecast);
          updateForecastLabels(data.wellbeing.forecast);
          
          container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
          
          // Smart Alert check
          if (payload.screen_time > 10) {
             showSmartAlert('You\'ve had high screen time today. Consider a quick eye-rest routine?');
          }
        }
      } catch (err) {
        console.error('Wellbeing assessment failed:', err);
      } finally {
        predictSend.disabled = false;
        predictSend.innerText = '✨ Update My Wellbeing Insights';
      }
    });
  }

  // Wellbeing Plan Generator
  const planBtn = document.getElementById('generate-plan-btn');
  if (planBtn) {
    planBtn.addEventListener('click', async () => {
      planBtn.disabled = true;
      planBtn.innerText = 'Generating Plan...';
      
      const payload = {
        stress_level: document.getElementById('stress-level').value,
        sleep_quality: document.getElementById('sleep-quality').value,
        mood_score: selectedMood,
        social_interaction: document.getElementById('social-interaction').value
      };

      try {
        const res = await fetch('/generate-plan', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        
        // Display plan in a new section or modal
        let planContainer = document.getElementById('wellbeing-plan-container');
        if (!planContainer) {
          planContainer = document.createElement('div');
          planContainer.id = 'wellbeing-plan-container';
          planContainer.className = 'wellbeing-plan-result';
          document.querySelector('.wellbeing-status-panel').appendChild(planContainer);
        }
        
        planContainer.innerHTML = `
          <div class="wellbeing-plan-title">📜 Your Personalized Wellbeing Plan</div>
          <div class="wellbeing-plan-text">${data.plan}</div>
        `;
        planContainer.scrollIntoView({ behavior: 'smooth' });
      } catch (err) {
        console.error('Plan generation failed:', err);
      } finally {
        planBtn.disabled = false;
        planBtn.innerHTML = '<i class="icon">📜</i> Generate My Plan';
      }
    });
  }

  function showSmartAlert(message) {
    // Simple non-intrusive alert logic
    const alertBox = document.createElement('div');
    alertBox.className = 'panel glass-panel smart-alert';
    alertBox.style.position = 'fixed';
    alertBox.style.top = '20px';
    alertBox.style.right = '20px';
    alertBox.style.zIndex = '2000';
    alertBox.style.padding = '16px';
    alertBox.style.borderLeft = '4px solid var(--accent-primary)';
    alertBox.innerHTML = `<strong>Smart Tip:</strong> ${message} <button class="btn-sm btn-secondary ml-4" onclick="this.parentElement.remove()">Dismiss</button>`;
    document.body.appendChild(alertBox);
    setTimeout(() => alertBox.remove(), 8000);
  }

  function updateForecastLabels(forecast) {
    const labelsGrid = document.getElementById('forecast-labels');
    if (!labelsGrid) return;
    
    labelsGrid.innerHTML = `
      <div class="forecast-label-item">7 Days: <span class="badge ${getBadgeClass(forecast['7_days'].status)}">${forecast['7_days'].status}</span></div>
      <div class="forecast-label-item">14 Days: <span class="badge ${getBadgeClass(forecast['14_days'].status)}">${forecast['14_days'].status}</span></div>
      <div class="forecast-label-item">30 Days: <span class="badge ${getBadgeClass(forecast['30_days'].status)}">${forecast['30_days'].status}</span></div>
    `;
  }

  function getBadgeClass(status) {
    if (status === 'Doing Well') return 'badge-success';
    if (status === 'Balanced') return 'badge-info';
    return 'badge-danger';
  }

  function renderForecastChart(currentStatus, forecast) {
    const ctx = document.getElementById('forecastChart');
    if (!ctx) return;

    if (forecastChartInstance) forecastChartInstance.destroy();

    const statusMap = { 'Doing Well': 1, 'Balanced': 2, 'Needs Support': 3 };
    const dataPoints = [
      statusMap[currentStatus],
      statusMap[forecast['7_days'].status],
      statusMap[forecast['14_days'].status],
      statusMap[forecast['30_days'].status]
    ];

    const isLight = document.documentElement.getAttribute('data-theme') === 'light';
    const tickColor = isLight ? '#475569' : 'rgba(255,255,255,0.5)';

    forecastChartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: ['Today', '7d', '14d', '30d'],
        datasets: [{
          data: dataPoints,
          borderColor: '#6366f1',
          backgroundColor: 'rgba(99, 102, 241, 0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            min: 0.5, max: 3.5,
            ticks: {
              stepSize: 1,
              callback: v => v === 1 ? 'Well' : v === 2 ? 'Bal' : v === 3 ? 'Help' : '',
              color: tickColor,
              font: { size: 9 }
            },
            grid: { display: false }
          },
          x: { ticks: { color: tickColor, font: { size: 9 } }, grid: { display: false } }
        },
        plugins: { legend: { display: false } }
      }
    });
  }

  // Handle theme changed event to update forecast chart
  window.addEventListener('themechanged', (e) => {
    if (forecastChartInstance) {
      const isLight = e.detail.theme === 'light';
      const tickColor = isLight ? '#475569' : 'rgba(255, 255, 255, 0.5)';
      forecastChartInstance.options.scales.y.ticks.color = tickColor;
      forecastChartInstance.options.scales.x.ticks.color = tickColor;
      forecastChartInstance.update();
    }
  });

  function updateAura(riskClass, message) {
    const aura = document.getElementById('wellness-aura');
    const text = document.getElementById('aura-status-text');
    if (aura && text) {
      aura.className = `wellness-aura ${riskClass}`;
      text.innerText = message;
    }
  }

  // --- Other Logic (Logout, etc.) ---
  const chatWidget = document.getElementById('chat-widget');
  const chatBubble = document.getElementById('chat-bubble');
  const chatAiBtn = document.getElementById('chat-ai-btn');
  const counselorBtn = document.getElementById('book-counselor-btn');

  if (chatAiBtn && chatWidget && chatBubble) {
    chatAiBtn.addEventListener('click', () => {
      chatWidget.classList.remove('minimized');
      chatWidget.classList.add('active');
      chatBubble.style.display = 'none';
    });
  }

  if (counselorBtn) {
    counselorBtn.addEventListener('click', () => {
      showSmartAlert('Connecting to the next available counselor... Please wait.');
      // Simulate booking process
      setTimeout(() => {
        showSmartAlert('Booking confirmed! You will receive an email with the link shortly.');
      }, 3000);
    });
  }

  const emergencyBtn = document.getElementById('emergency-btn');
  if (emergencyBtn && window.CrisisSafetyNet) {
    emergencyBtn.addEventListener('click', () => {
      window.CrisisSafetyNet.trigger();
    });
  }



  // Placeholder Links
  document.querySelectorAll('.nav-link[href="#"]').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      showSmartAlert(`The ${link.innerText.trim()} feature is coming soon!`);
    });
  });

  // Privacy Controls
  const trackingToggle = document.getElementById('tracking-toggle');
  const deleteBtn = document.getElementById('delete-data-btn');

  if (trackingToggle) {
    trackingToggle.addEventListener('change', (e) => {
      const enabled = e.target.checked;
      showSmartAlert(enabled ? 
        'Wellbeing tracking enabled. Your insights will be more accurate over time.' : 
        'Wellbeing tracking paused. Your recent activity won\'t be used for forecasts.');
    });
  }

  if (deleteBtn) {
    deleteBtn.addEventListener('click', () => {
      if (confirm('Are you sure you want to delete all your wellbeing insights data? This action cannot be undone.')) {
        deleteBtn.innerText = 'Deleting...';
        setTimeout(() => {
          showSmartAlert('Your wellbeing data has been successfully deleted from our records.');
          deleteBtn.innerText = 'Delete My Insights Data';
          document.getElementById('predict-result-container').style.display = 'none';
        }, 2000);
      }
    });
  }
});
