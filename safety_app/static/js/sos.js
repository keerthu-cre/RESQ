/**
 * RESQ — Emergency & Rapid Response
 * Complete SOS Workflow Engine (2-Second Press-and-Hold & Geolocation Dispatch)
 */

const SosEngine = {
  HOLD_DURATION_MS: 2000,
  CIRCUMFERENCE: 654, // 2 * Math.PI * 104
  
  isHolding: false,
  startTime: null,
  animFrameId: null,
  hasTriggered: false,

  init() {
    this.btn = document.getElementById('sos-command-button');
    this.ringProgress = document.getElementById('sos-ring-progress');
    this.statusTag = document.getElementById('sos-status-instruction');
    this.techOrbit = document.getElementById('sos-tech-orbit');
    this.overlay = document.getElementById('sos-activation-overlay');

    if (!this.btn) return;

    this.bindEvents();
  },

  bindEvents() {
    // Unified Pointer Events (Mouse, Touch, Pen)
    this.btn.addEventListener('pointerdown', (e) => {
      if (e.button === 0) { // Left click / touch
        this.btn.setPointerCapture(e.pointerId);
        this.startHold();
      }
    });

    this.btn.addEventListener('pointerup', (e) => {
      try { this.btn.releasePointerCapture(e.pointerId); } catch(err) {}
      this.cancelHold();
    });

    this.btn.addEventListener('pointercancel', (e) => {
      try { this.btn.releasePointerCapture(e.pointerId); } catch(err) {}
      this.cancelHold();
    });

    // Keyboard Access (Spacebar / Enter)
    this.btn.addEventListener('keydown', (e) => {
      if ((e.key === ' ' || e.key === 'Enter') && !this.isHolding) {
        e.preventDefault();
        this.startHold();
      }
    });

    this.btn.addEventListener('keyup', (e) => {
      if (e.key === ' ' || e.key === 'Enter') {
        this.cancelHold();
      }
    });

    this.btn.addEventListener('contextmenu', (e) => e.preventDefault());
  },

  startHold() {
    if (this.hasTriggered) return;
    this.isHolding = true;
    this.startTime = performance.now();
    this.btn.classList.add('holding');

    if (this.techOrbit) {
      this.techOrbit.style.animationDuration = '3s';
    }

    if ('vibrate' in navigator) {
      navigator.vibrate(60);
    }
    SoundFX.playBeep(340, 0.08, 'triangle');

    this.loop();
  },

  loop() {
    if (!this.isHolding) return;

    const elapsed = performance.now() - this.startTime;
    const progress = Math.min(elapsed / this.HOLD_DURATION_MS, 1);
    const holdSeconds = (elapsed / 1000).toFixed(1);

    // Update circular SVG progress stroke
    const offset = this.CIRCUMFERENCE * (1 - progress);
    if (this.ringProgress) {
      this.ringProgress.style.strokeDashoffset = offset;
    }

    // Real-time HUD status
    if (this.statusTag) {
      this.statusTag.innerHTML = `HOLD TO ACTIVATE — <span style="color:var(--emergency-red); font-weight:900;">${holdSeconds}s</span>`;
    }

    // Accelerating subtle haptics
    if (elapsed > 1000 && Math.floor(elapsed / 250) % 2 === 0) {
      if ('vibrate' in navigator) navigator.vibrate(25);
    }

    if (progress >= 1) {
      this.triggerSos();
    } else {
      this.animFrameId = requestAnimationFrame(() => this.loop());
    }
  },

  cancelHold() {
    if (!this.isHolding || this.hasTriggered) return;
    
    const elapsed = performance.now() - (this.startTime || performance.now());
    this.isHolding = false;
    if (this.animFrameId) cancelAnimationFrame(this.animFrameId);
    this.btn.classList.remove('holding');

    if (this.techOrbit) {
      this.techOrbit.style.animationDuration = '22s';
    }

    // Smooth spring back of circular ring
    if (this.ringProgress) {
      this.ringProgress.style.transition = 'stroke-dashoffset 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)';
      this.ringProgress.style.strokeDashoffset = this.CIRCUMFERENCE;
      setTimeout(() => {
        if (this.ringProgress) this.ringProgress.style.transition = 'none';
      }, 300);
    }

    if (this.statusTag) {
      this.statusTag.textContent = 'PRESS & HOLD FOR 2 SECONDS';
    }

    // Show cancel feedback only if the user had started holding (>200ms)
    if (elapsed > 200) {
      showToast('SOS activation cancelled', 'info', 2500);
    }
  },

  triggerSos() {
    this.isHolding = false;
    this.hasTriggered = true;
    if (this.animFrameId) cancelAnimationFrame(this.animFrameId);

    if ('vibrate' in navigator) {
      navigator.vibrate([200, 100, 200, 100, 400]);
    }
    SoundFX.playSosAlert();

    if (this.statusTag) {
      this.statusTag.innerHTML = '🚨 <strong style="color:var(--emergency-red);">SENDING SOS...</strong>';
    }

    // Attempt fresh location capture or fallback
    this.captureLocationAndSend();
  },

  captureLocationAndSend() {
    // Check if Geolocation is available
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          this.sendSosPayload({
            lat: pos.coords.latitude,
            lng: pos.coords.longitude,
            name: LocationManager.currentLocation.name || 'Campus Grounds'
          });
        },
        (err) => {
          console.warn('Geolocation unavailable during SOS:', err.message);
          // GPS failure must NOT prevent SOS!
          this.sendSosPayload({
            lat: null,
            lng: null,
            name: LocationManager.currentLocation.name || 'Location unavailable'
          });
        },
        { timeout: 2500, enableHighAccuracy: true }
      );
    } else {
      this.sendSosPayload({
        lat: null,
        lng: null,
        name: LocationManager.currentLocation.name || 'Location unavailable'
      });
    }
  },

  sendSosPayload(loc) {
    fetch('/api/sos/trigger/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken,
      },
      body: JSON.stringify({
        latitude: loc.lat,
        longitude: loc.lng,
        location_name: loc.name,
      })
    })
    .then(async (res) => {
      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`Server returned status ${res.status}: ${errText}`);
      }
      return res.json();
    })
    .then((data) => {
      if (data.success) {
        this.renderSuccessModal(data);
      } else if (data.already_active) {
        this.renderAlreadyActiveState(data);
      } else {
        throw new Error(data.message || 'Unknown error creating emergency incident');
      }
    })
    .catch((err) => {
      console.error('SOS Emergency Request Error:', err);
      this.renderErrorState(err);
    });
  },

  renderSuccessModal(data) {
    if (!this.overlay) return;

    this.overlay.innerHTML = `
      <div class="modal-content" style="text-align:center; border:2.5px solid var(--emergency-red); box-shadow: 0 0 60px rgba(255, 59, 48, 0.6);">
        <div style="font-size:3.2rem; margin-bottom:0.4rem;">🚨</div>
        <h2 style="font-size:1.8rem; font-weight:900; color:var(--emergency-red); letter-spacing:-0.02em; margin-bottom:0.25rem;">
          SOS SENT
        </h2>
        <div style="font-size:1rem; font-weight:800; color:var(--text-primary); margin-bottom:1.25rem;">
          Help is being arranged.
        </div>

        <div style="background:var(--bg-subtle); border:1.5px solid var(--border-color); border-radius:var(--radius-md); padding:1rem 1.25rem; text-align:left; margin-bottom:1.25rem; display:flex; flex-direction:column; gap:0.6rem;">
          <div style="display:flex; align-items:center; gap:0.6rem; font-weight:800; font-size:0.92rem; color:var(--text-primary);">
            <span style="color:var(--success-green); font-size:1.1rem;">✓</span> Emergency request sent
          </div>
          <div style="display:flex; align-items:center; gap:0.6rem; font-weight:800; font-size:0.92rem; color:var(--text-primary);">
            ${data.has_location ? 
              '<span style="color:var(--success-green); font-size:1.1rem;">✓</span> Location captured' : 
              '<span style="color:var(--warning-amber); font-size:1.1rem;">⚠️</span> Location unavailable'}
          </div>
          <div style="display:flex; align-items:center; gap:0.6rem; font-weight:800; font-size:0.92rem; color:var(--text-primary);">
            <span style="color:var(--success-green); font-size:1.1rem;">✓</span> Response team notified
          </div>
        </div>

        <div style="background:var(--bg-card-alt); border-radius:var(--radius-md); padding:0.85rem; margin-bottom:1.25rem; display:flex; justify-content:space-between; align-items:center;">
          <div style="text-align:left;">
            <div style="font-size:0.72rem; font-weight:800; text-transform:uppercase; color:var(--text-muted);">STATUS</div>
            <div style="font-size:0.92rem; font-weight:900; color:var(--warning-amber);">🟡 WAITING FOR RESPONSE</div>
          </div>
          <div style="text-align:right;">
            <div style="font-size:0.72rem; font-weight:800; text-transform:uppercase; color:var(--text-muted);">INCIDENT ID</div>
            <div style="font-family:var(--font-mono); font-weight:900; font-size:1rem; color:var(--text-primary);">#${data.incident_id}</div>
          </div>
        </div>

        <a href="${data.tracker_url || `/incidents/${data.incident_id}/`}" class="btn btn-emergency btn-block btn-lg" style="font-size:1rem;">
          TRACK RESPONSE NOW →
        </a>
      </div>
    `;

    this.overlay.classList.add('active');
  },

  renderAlreadyActiveState(data) {
    showToast(`🚨 ACTIVE EMERGENCY: ${data.message}`, 'warning', 6000);
    this.hasTriggered = false;
    this.cancelHold();

    if (this.overlay) {
      this.overlay.innerHTML = `
        <div class="modal-content" style="text-align:center; border:2px solid var(--warning-amber);">
          <div style="font-size:2.8rem; margin-bottom:0.5rem;">⚠️</div>
          <h2 style="font-size:1.5rem; font-weight:900; color:var(--warning-amber); margin-bottom:0.35rem;">
            ACTIVE EMERGENCY IN PROGRESS
          </h2>
          <p style="font-size:0.9rem; color:var(--text-secondary); margin-bottom:1.25rem;">
            You already have an active emergency request (#${data.incident_id}).
          </p>
          <div style="display:flex; gap:0.75rem;">
            <button type="button" class="btn btn-outline" style="flex:1;" onclick="closeModal('sos-activation-overlay')">Close</button>
            <a href="${data.tracker_url || `/incidents/${data.incident_id}/`}" class="btn btn-primary" style="flex:1;">
              Track Response →
            </a>
          </div>
        </div>
      `;
      this.overlay.classList.add('active');
    }
  },

  renderErrorState(err) {
    this.hasTriggered = false;
    this.cancelHold();

    showToast('⚠️ Unable to send emergency request. Please try again.', 'error', 6000);

    if (this.overlay) {
      this.overlay.innerHTML = `
        <div class="modal-content" style="text-align:center; border:2px solid var(--emergency-red);">
          <div style="font-size:2.8rem; margin-bottom:0.5rem;">⚠️</div>
          <h2 style="font-size:1.5rem; font-weight:900; color:var(--emergency-red); margin-bottom:0.35rem;">
            UNABLE TO SEND REQUEST
          </h2>
          <p style="font-size:0.9rem; color:var(--text-secondary); margin-bottom:1.25rem;">
            Unable to connect with emergency dispatch server. Please check connection and try again, or speed dial campus security hotline directly.
          </p>
          <div style="display:flex; gap:0.75rem;">
            <button type="button" class="btn btn-outline" style="flex:1;" onclick="closeModal('sos-activation-overlay')">Cancel</button>
            <button type="button" class="btn btn-emergency" style="flex:1;" onclick="closeModal('sos-activation-overlay'); SosEngine.triggerSos();">
              TRY AGAIN
            </button>
          </div>
          <div style="margin-top:1rem; padding-top:0.75rem; border-top:1px solid var(--border-color);">
            <a href="tel:911" class="btn btn-outline btn-block" style="color:var(--emergency-red);">
              📞 CALL 911 / POLICE DIRECTLY
            </a>
          </div>
        </div>
      `;
      this.overlay.classList.add('active');
    }
  }
};

document.addEventListener('DOMContentLoaded', () => {
  SosEngine.init();
});
