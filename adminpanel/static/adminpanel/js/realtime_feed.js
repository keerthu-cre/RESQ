/**
 * RESQ Real-time WebSocket Client for Admin Dashboard
 * Connects to /ws/admin/incidents/
 * Handles "incident.new" and "incident.status_changed" events
 */

(function () {
  let socket = null;
  let reconnectInterval = 3000;
  const statusIndicator = document.getElementById('ws-status-indicator');
  const statusText = document.getElementById('ws-status-text');
  const toastContainer = document.getElementById('toast-container');

  function getStatusBadge(status) {
    switch (status) {
      case 'pending':
        return '<span class="badge badge-pending"><i class="fa-solid fa-circle-exclamation me-1"></i>Pending</span>';
      case 'accepted':
        return '<span class="badge badge-accepted"><i class="fa-solid fa-check me-1"></i>Accepted</span>';
      case 'in-progress':
        return '<span class="badge badge-in-progress"><i class="fa-solid fa-spinner fa-spin me-1"></i>In Progress</span>';
      case 'resolved':
        return '<span class="badge badge-resolved"><i class="fa-solid fa-circle-check me-1"></i>Resolved</span>';
      case 'rejected':
        return '<span class="badge badge-rejected"><i class="fa-solid fa-ban me-1"></i>Rejected</span>';
      default:
        return `<span class="badge bg-secondary">${status}</span>`;
    }
  }

  function getTypeBadge(type) {
    const iconMap = {
      medical: 'fa-heart-pulse',
      fire: 'fa-fire-flame-curved',
      security: 'fa-shield-halved',
      harassment: 'fa-triangle-exclamation',
      other: 'fa-bell',
    };
    const icon = iconMap[type] || 'fa-bell';
    return `<span class="badge badge-type-${type}"><i class="fa-solid ${icon} me-1"></i>${type ? type.toUpperCase() : 'OTHER'}</span>`;
  }

  function showToast(title, message, isAlert = false) {
    if (!toastContainer) return;
    const toastId = 'toast-' + Date.now();
    const bgClass = isAlert ? 'bg-danger text-white' : 'bg-primary text-white';
    const toastHtml = `
      <div id="${toastId}" class="toast align-items-center ${bgClass} border-0 show shadow-lg mb-2" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="d-flex">
          <div class="toast-body">
            <strong>${title}</strong><br>${message}
          </div>
          <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
      </div>
    `;
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    setTimeout(() => {
      const el = document.getElementById(toastId);
      if (el) el.remove();
    }, 6000);
  }

  function playAlertSound() {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(880, ctx.currentTime); // A5 tone
      osc.frequency.exponentialRampToValueAtTime(440, ctx.currentTime + 0.3);
      gain.gain.setValueAtTime(0.2, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.3);
    } catch (e) {
      // Audio context might be restricted before user gesture
    }
  }

  function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/admin/incidents/`;

    console.log('[RESQ Realtime] Connecting to WebSocket:', wsUrl);
    socket = new WebSocket(wsUrl);

    socket.onopen = function () {
      console.log('[RESQ Realtime] Connected.');
      if (statusIndicator) {
        statusIndicator.className = 'live-pulse';
      }
      if (statusText) {
        statusText.textContent = 'Live Sync Active';
        statusText.className = 'text-success fw-semibold small';
      }
    };

    socket.onclose = function () {
      console.warn('[RESQ Realtime] Disconnected. Reconnecting in', reconnectInterval, 'ms...');
      if (statusIndicator) {
        statusIndicator.className = 'live-pulse-offline';
      }
      if (statusText) {
        statusText.textContent = 'Reconnecting...';
        statusText.className = 'text-danger fw-semibold small';
      }
      setTimeout(initWebSocket, reconnectInterval);
    };

    socket.onerror = function (err) {
      console.error('[RESQ Realtime] WebSocket Error:', err);
    };

    socket.onmessage = function (e) {
      try {
        const payload = JSON.parse(e.data);
        console.log('[RESQ Realtime] Event received:', payload);

        if (payload.event === 'incident.new') {
          handleNewIncident(payload.data);
        } else if (payload.event === 'incident.status_changed') {
          handleStatusChanged(payload.data);
        }
      } catch (err) {
        console.error('[RESQ Realtime] Message parse error:', err);
      }
    };
  }

  function handleNewIncident(incident) {
    playAlertSound();
    showToast('🚨 NEW SOS EMERGENCY RAISED', `Incident #${incident.id}: ${incident.incident_type.toUpperCase()} at ${incident.address}`, true);

    // Update pending counter metric card if present
    const pendingCounter = document.getElementById('metric-pending-count');
    if (pendingCounter) {
      let count = parseInt(pendingCounter.textContent.trim()) || 0;
      pendingCounter.textContent = count + 1;
    }

    const todayCounter = document.getElementById('metric-today-count');
    if (todayCounter) {
      let count = parseInt(todayCounter.textContent.trim()) || 0;
      todayCounter.textContent = count + 1;
    }

    // Insert into live feed table if present
    const tableBody = document.getElementById('live-incidents-body');
    if (tableBody) {
      const noDataDiv = document.getElementById('no-incidents-msg');
      if (noDataDiv) noDataDiv.remove();

      const reporterName = incident.reported_by ? (incident.reported_by.username || 'Student') : 'Unknown';
      const teamName = incident.assigned_team ? incident.assigned_team.name : '<span class="text-muted fst-italic">Unassigned</span>';
      
      const dateStr = new Date(incident.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

      const newRowHtml = `
        <tr id="incident-row-${incident.id}" class="highlight-row">
          <td class="fw-bold text-primary">#${incident.id}</td>
          <td>${getTypeBadge(incident.incident_type)}</td>
          <td>
            <div class="fw-semibold text-truncate" style="max-width: 260px;">${incident.address}</div>
            <small class="text-muted">${incident.description || ''}</small>
          </td>
          <td>${reporterName}</td>
          <td id="incident-team-${incident.id}">${teamName}</td>
          <td id="incident-status-${incident.id}">${getStatusBadge(incident.status)}</td>
          <td><small class="text-muted">${dateStr}</small></td>
          <td class="text-end">
            <a href="/admin-dashboard/incidents/${incident.id}/" class="btn btn-sm btn-outline-primary">
              <i class="fa-solid fa-arrow-up-right-from-square"></i> Inspect
            </a>
          </td>
        </tr>
      `;
      tableBody.insertAdjacentHTML('afterbegin', newRowHtml);
    }
  }

  function handleStatusChanged(incident) {
    showToast('🔄 Status Updated', `Incident #${incident.id} status changed to ${incident.status.toUpperCase()}`);

    // Update row status badge if exists
    const statusCell = document.getElementById(`incident-status-${incident.id}`);
    if (statusCell) {
      statusCell.innerHTML = getStatusBadge(incident.status);
    }

    const teamCell = document.getElementById(`incident-team-${incident.id}`);
    if (teamCell && incident.assigned_team) {
      teamCell.innerHTML = `<span class="fw-semibold text-dark">${incident.assigned_team.name}</span>`;
    }

    const row = document.getElementById(`incident-row-${incident.id}`);
    if (row) {
      row.classList.remove('highlight-row');
      void row.offsetWidth; // Trigger reflow
      row.classList.add('highlight-row');
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    initWebSocket();
  });
})();
