document.addEventListener('DOMContentLoaded', async () => {
  let wellnessTrendChartInstance = null;
  let burnoutPieChartInstance = null;
  let clusteringChartInstance = null;
  let dashboardData = null;

  // Fetch Dashboard Data
  try {
    const res = await fetch('/dashboard-data');
    if (res.status === 401) {
      window.location.href = '/login';
      return;
    }
    dashboardData = await res.json();
    
    renderStatsCards(dashboardData);
    renderWellnessTrend(dashboardData.wellness_trends);
    renderBurnoutPie(dashboardData.burnout_summary);
    renderRiskTable(dashboardData.at_risk_students);
    if(dashboardData.cohort_clusters) renderClusteringChart(dashboardData.cohort_clusters);
    if(dashboardData.sentiment_pulse) renderSentimentPulse(dashboardData.sentiment_pulse);
  } catch (err) {
    console.error("Failed to load admin data", err);
  }

  // Fetch Users for Management
  try {
    const uRes = await fetch('/admin/users');
    if (uRes.ok) {
      const uData = await uRes.json();
      renderUserTable(uData.users);
    }
  } catch (err) {
    console.error("Failed to load users", err);
  }

  function renderStatsCards(data) {
    const container = document.getElementById('stats-cards');
    if (!container) return;
    
    const totalRisk = data.burnout_summary['High'] || 0;
    
    container.innerHTML = `
      <div class="stat-card">
        <h3>Total Students Monitored</h3>
        <div class="value" style="color: var(--accent-primary)">${data.total_students}</div>
      </div>
      <div class="stat-card">
        <h3>High Burnout Risk</h3>
        <div class="value" style="color: var(--danger)">${totalRisk}</div>
      </div>
      <div class="stat-card">
        <h3>At-Risk Interventions Needed</h3>
        <div class="value" style="color: var(--warning)">${data.at_risk_students.length}</div>
      </div>
      <div class="stat-card">
        <h3>Platform Status</h3>
        <div class="value" style="color: var(--success)">Active</div>
      </div>
    `;
  }

  function renderWellnessTrend(trends) {
    const ctx = document.getElementById('wellnessTrendChart');
    if (!ctx) return;

    if (wellnessTrendChartInstance) wellnessTrendChartInstance.destroy();

    const isLight = document.documentElement.getAttribute('data-theme') === 'light';
    const textSec = isLight ? '#475569' : '#a0aec0';
    const gridColor = isLight ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.05)';

    wellnessTrendChartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: trends.map(t => t.period),
        datasets: [{
          label: 'Campus Stress Index',
          data: trends.map(t => t.stress_index),
          backgroundColor: 'rgba(139, 92, 246, 0.7)',
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        scales: {
          y: {
            grid: { color: gridColor },
            ticks: { color: textSec }
          },
          x: {
            grid: { display: false },
            ticks: { color: textSec }
          }
        }
      }
    });
  }

  function renderBurnoutPie(summary) {
    const ctx = document.getElementById('burnoutPieChart');
    if (!ctx) return;

    if (burnoutPieChartInstance) burnoutPieChartInstance.destroy();

    const isLight = document.documentElement.getAttribute('data-theme') === 'light';
    const textPri = isLight ? '#0f172a' : '#ffffff';

    burnoutPieChartInstance = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Low Risk', 'Medium Risk', 'High Risk'],
        datasets: [{
          data: [summary['Low']||0, summary['Medium']||0, summary['High']||0],
          backgroundColor: [
            'rgba(16, 185, 129, 0.8)', // Success
            'rgba(245, 158, 11, 0.8)', // Warning
            'rgba(239, 68, 68, 0.8)'   // Danger
          ],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        cutout: '70%',
        plugins: {
          legend: { position: 'bottom', labels: { color: textPri } }
        }
      }
    });
  }

  function renderClusteringChart(clustersData) {
    const ctx = document.getElementById('clusteringChart');
    if (!ctx || !clustersData || clustersData.length === 0) return;

    if (clusteringChartInstance) clusteringChartInstance.destroy();

    const isLight = document.documentElement.getAttribute('data-theme') === 'light';
    const textSec = isLight ? '#475569' : '#a0aec0';
    const textPri = isLight ? '#0f172a' : '#ffffff';
    const gridColor = isLight ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.05)';

    // Separate data by cluster
    const datasets = [
      { label: 'Cluster 1 (Engaged)', data: clustersData.filter(d => d.cluster === 0), backgroundColor: 'rgba(16, 185, 129, 0.6)', borderColor: 'var(--success)' },
      { label: 'Cluster 2 (At Risk)', data: clustersData.filter(d => d.cluster === 1), backgroundColor: 'rgba(239, 68, 68, 0.6)', borderColor: 'var(--danger)' },
      { label: 'Cluster 3 (Disengaged)', data: clustersData.filter(d => d.cluster === 2), backgroundColor: 'rgba(245, 158, 11, 0.6)', borderColor: 'var(--warning)' }
    ];

    clusteringChartInstance = new Chart(ctx, {
      type: 'bubble',
      data: { datasets },
      options: {
        responsive: true,
        scales: {
          x: { title: { display: true, text: 'Attendance Rate', color: textSec }, grid: { color: gridColor }, ticks: { color: textSec } },
          y: { title: { display: true, text: 'Activity Score', color: textSec }, grid: { color: gridColor }, ticks: { color: textSec } }
        },
        plugins: { legend: { labels: { color: textPri } } }
      }
    });
  }

  function renderSentimentPulse(sentimentData) {
    const container = document.getElementById('sentiment-pulse-container');
    if (!container || !sentimentData) return;
    
    container.innerHTML = '';
    sentimentData.forEach(item => {
      const span = document.createElement('span');
      span.innerText = item.text;
      
      // Calculate font size based on weight (10 to 50 weight map to 0.8rem to 2rem)
      const fontSize = Math.max(0.8, item.weight / 20) + 'rem';
      span.style.fontSize = fontSize;
      span.style.fontWeight = 'bold';
      span.style.padding = '4px 8px';
      span.style.borderRadius = '4px';
      span.style.transition = 'all 0.3s ease';
      
      // Color based on emotion
      let color = 'white';
      if (item.emotion === 'stress' || item.emotion === 'burnout') color = 'var(--danger)';
      if (item.emotion === 'anxiety') color = 'var(--warning)';
      if (item.emotion === 'positive') color = 'var(--success)';
      
      span.style.color = color;
      span.style.textShadow = '0 2px 4px rgba(0,0,0,0.5)';
      
      // Add hover effect
      span.addEventListener('mouseenter', () => span.style.transform = 'scale(1.1)');
      span.addEventListener('mouseleave', () => span.style.transform = 'scale(1)');

      container.appendChild(span);
    });
  }

  function renderRiskTable(students) {
    const tbody = document.getElementById('risk-table-body');
    if (!tbody) return;

    tbody.innerHTML = '';
    students.forEach(st => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${st.student_id}</strong></td>
        <td><span class="badge badge-${st.burnout_risk === 'High' ? 'danger' : 'warning'}">${st.burnout_risk}</span></td>
        <td>${st.distress_level}</td>
        <td>${st.stress_label}</td>
        <td><button class="btn btn-sm btn-primary">Intervene</button></td>
      `;
      tbody.appendChild(tr);
    });
  }

  function renderUserTable(users) {
    const tbody = document.getElementById('admin-user-table');
    if (!tbody) return;

    tbody.innerHTML = '';
    users.forEach(u => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${u.id}</td>
        <td>${u.full_name}</td>
        <td>${u.email}</td>
        <td><span class="badge badge-info">${u.role}</span></td>
        <td><span class="badge badge-${u.is_active_account ? 'success' : 'danger'}">${u.is_active_account ? 'Active' : 'Disabled'}</span></td>
        <td><button class="btn btn-sm btn-outline">Edit</button></td>
      `;
      tbody.appendChild(tr);
    });
  }

  // Re-render charts when theme changes
  window.addEventListener('themechanged', () => {
    if (dashboardData) {
      renderWellnessTrend(dashboardData.wellness_trends);
      renderBurnoutPie(dashboardData.burnout_summary);
      if (dashboardData.cohort_clusters) renderClusteringChart(dashboardData.cohort_clusters);
    }
  });
});
