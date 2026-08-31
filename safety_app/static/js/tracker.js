/**
 * RESQ — Emergency & Rapid Response
 * Live Response Status Polling Engine & Real-Time Stepper
 */

const TrackerEngine = {
  incidentId: null,
  pollInterval: null,
  lastStatus: null,
  isPollingActive: true,

  init(incidentId) {
    this.incidentId = incidentId;
    if (!this.incidentId) return;

    this.bindSafeButton();
    this.startPolling();
  },

  startPolling() {
    this.pollStatus();
    this.pollInterval = setInterval(() => {
      if (this.isPollingActive) {
        this.pollStatus();
      }
    }, 2500);
  },

  pollStatus() {
    fetch(`/incidents/${this.incidentId}/status/`)
      .then(res => {
        if (!res.ok) throw new Error('Status poll failed');
        return res.json();
      })
      .then(data => {
        this.renderStatus(data);
      })
      .catch(err => {
        console.warn('Tracker polling warning:', err.message);
      });
  },

  renderStatus(data) {
    const statusBadge = document.getElementById('tracker-status-badge');
    const responderName = document.getElementById('responder-name');
    const responderNotes = document.getElementById('responder-notes');
    const responderEta = document.getElementById('responder-eta');
    const safeBanner = document.getElementById('safe-action-banner');
    const resolvedCard = document.getElementById('resolved-confirmation-card');

    if (statusBadge) {
      statusBadge.textContent = this.formatStatusDisplay(data.status);
      statusBadge.className = `badge badge-${this.getBadgeClass(data.status)}`;
    }

    // Play chime on status change
    if (this.lastStatus && this.lastStatus !== data.status) {
      if (data.status === 'RESOLVED') {
        SoundFX.playSafeChime();
        showToast('✅ Emergency Marked RESOLVED. All clear!', 'success');
      } else {
        SoundFX.playBeep(660, 0.2, 'triangle');
        showToast(`Response Update: ${this.formatStatusDisplay(data.status)}`, 'info');
      }
      Accessibility.speak(`Response status updated to ${this.formatStatusDisplay(data.status)}`);
    }
    this.lastStatus = data.status;

    if (responderName) responderName.textContent = data.response_team_name;
    if (responderNotes) responderNotes.textContent = data.responder_notes || 'Response dispatch is active. Keep your device on hand.';
    
    if (responderEta) {
      if (data.status === 'ARRIVED') {
        responderEta.innerHTML = '🟢 <strong style="color:var(--success-green);">Team Arrived On Scene</strong>';
      } else if (data.status === 'RESOLVED') {
        responderEta.innerHTML = '✅ <strong style="color:var(--success-green);">Emergency Resolved</strong>';
      } else if (data.eta_minutes !== null && data.eta_minutes !== undefined) {
        responderEta.textContent = `Estimated Arrival: ~${data.eta_minutes} mins`;
        responderEta.style.color = 'var(--nav-blue)';
      } else {
        responderEta.textContent = 'Coordinating dispatch...';
      }
    }

    // Update Progress Stepper Nodes
    this.updateStepper(data.status);

    // Show/Hide "I'm Safe" and Resolution confirmation cards
    if (data.status === 'RESOLVED') {
      if (safeBanner) safeBanner.style.display = 'none';
      if (resolvedCard) resolvedCard.style.display = 'block';
      this.isPollingActive = false; // Emergency closed, stop polling
    } else {
      if (safeBanner) safeBanner.style.display = 'block';
      if (resolvedCard) resolvedCard.style.display = 'none';
    }

    // Update Audit Logs list
    this.renderLogs(data.logs);
  },

  formatStatusDisplay(status) {
    switch (status) {
      case 'PENDING': return 'Waiting for response';
      case 'ACCEPTED': return 'Team accepted';
      case 'ON_THE_WAY': return 'Team on the way';
      case 'ARRIVED': return 'Team arrived';
      case 'RESOLVED': return 'Emergency resolved';
      default: return status;
    }
  },

  updateStepper(status) {
    const stepOrder = ['PENDING', 'ACCEPTED', 'ON_THE_WAY', 'ARRIVED', 'RESOLVED'];
    const currentIdx = stepOrder.indexOf(status);

    // Stepper mapping:
    // Step 0: SOS Submitted (Always completed if incident exists)
    // Step 1: Response Team Notified (Completed when PENDING or higher)
    // Step 2: Team Accepted (Completed when ACCEPTED or higher)
    // Step 3: Team On The Way (Completed when ON_THE_WAY or higher)
    // Step 4: Team Arrived (Completed when ARRIVED or higher)
    // Step 5: Resolved (Completed when RESOLVED)

    for (let i = 0; i <= 5; i++) {
      const stepElem = document.getElementById(`timeline-step-${i}`);
      const nodeElem = document.getElementById(`step-node-${i}`);
      if (!stepElem || !nodeElem) continue;

      let isCompleted = false;
      let isCurrent = false;

      if (i === 0) {
        isCompleted = true; // Always submitted
      } else if (i === 1) {
        isCompleted = currentIdx >= 0;
        isCurrent = currentIdx === 0;
      } else if (i === 2) {
        isCompleted = currentIdx >= 1;
        isCurrent = currentIdx === 1;
      } else if (i === 3) {
        isCompleted = currentIdx >= 2;
        isCurrent = currentIdx === 2;
      } else if (i === 4) {
        isCompleted = currentIdx >= 3;
        isCurrent = currentIdx === 3;
      } else if (i === 5) {
        isCompleted = currentIdx >= 4;
        isCurrent = currentIdx === 4;
      }

      stepElem.classList.remove('completed', 'current', 'pending');
      if (isCompleted && !isCurrent) {
        stepElem.classList.add('completed');
        nodeElem.innerHTML = '✓';
      } else if (isCurrent) {
        stepElem.classList.add('current');
        nodeElem.innerHTML = '●';
      } else {
        stepElem.classList.add('pending');
        nodeElem.innerHTML = '○';
      }
    }
  },

  renderLogs(logs) {
    const logsList = document.getElementById('incident-logs-list');
    if (!logsList || !logs) return;

    logsList.innerHTML = logs.map(log => `
      <div style="display:flex; justify-content:space-between; align-items:flex-start; padding:0.6rem 0; border-bottom:1px solid var(--border-subtle); font-size:0.85rem;">
        <div>
          <span style="font-weight:800; color:var(--text-primary);">${this.formatStatusDisplay(log.status)}</span>
          <span style="color:var(--text-muted); font-size:0.75rem;"> • ${log.updated_by}</span>
          <div style="color:var(--text-secondary); margin-top:2px;">${log.note}</div>
        </div>
        <span style="font-family:var(--font-mono); color:var(--text-muted); font-size:0.75rem; white-space:nowrap; margin-left:8px;">
          ${log.time}
        </span>
      </div>
    `).join('');
  },

  getBadgeClass(status) {
    switch (status) {
      case 'PENDING': return 'warning';
      case 'ACCEPTED': return 'info';
      case 'ON_THE_WAY': return 'high';
      case 'ARRIVED': return 'emergency';
      case 'RESOLVED': return 'success';
      default: return 'gray';
    }
  },

  bindSafeButton() {
    const safeBtn = document.getElementById('btn-im-safe-trigger');
    if (!safeBtn) return;

    safeBtn.addEventListener('click', () => {
      safeBtn.disabled = true;
      safeBtn.textContent = 'Updating status...';

      fetch(`/incidents/${this.incidentId}/safe/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken,
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({})
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          SoundFX.playSafeChime();
          showToast('✓ Glad you\'re safe! Emergency resolved.', 'success', 5000);
          this.pollStatus();
        }
      })
      .catch(err => {
        console.error('Error marking safe:', err);
        window.location.reload();
      });
    });
  }
};
