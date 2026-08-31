/**
 * SafeCampus Emergency & Safety System
 * Location Services & Geolocation API Manager
 */

const LocationManager = {
  currentLocation: {
    lat: null,
    lng: null,
    accuracy: null,
    name: 'Main Campus Grounds',
    isManual: false,
    timestamp: null
  },

  campusLandmarks: [
    { name: 'Library - Learning Commons 1F', lat: 37.7749, lng: -122.4194 },
    { name: 'Science & Engineering Complex', lat: 37.7752, lng: -122.4188 },
    { name: 'West Dormitory Quad - Hall B', lat: 37.7741, lng: -122.4205 },
    { name: 'Student Union & Dining Hall', lat: 37.7760, lng: -122.4190 },
    { name: 'Athletic Center & Gym Arena', lat: 37.7758, lng: -122.4180 },
    { name: 'North Campus Parking Deck B', lat: 37.7768, lng: -122.4210 },
    { name: 'Arts & Humanities Building', lat: 37.7735, lng: -122.4175 },
    { name: 'Health & Wellness Center', lat: 37.7745, lng: -122.4168 },
  ],

  init() {
    this.requestLocation();
    this.bindManualModal();
  },

  requestLocation() {
    const statusText = document.getElementById('location-status-text');
    const locationName = document.getElementById('location-display-name');
    const locationCoords = document.getElementById('location-display-coords');

    if (!('geolocation' in navigator)) {
      this.setFallbackLocation('GPS Not Supported (Manual Active)');
      return;
    }

    if (statusText) statusText.textContent = 'Acquiring GPS...';

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        this.currentLocation.lat = pos.coords.latitude;
        this.currentLocation.lng = pos.coords.longitude;
        this.currentLocation.accuracy = Math.round(pos.coords.accuracy);
        this.currentLocation.isManual = false;
        this.currentLocation.timestamp = new Date();

        // Approximate closest campus zone or address
        this.currentLocation.name = this.findClosestLandmark(this.currentLocation.lat, this.currentLocation.lng);

        this.updateUI();
      },
      (err) => {
        console.warn('Geolocation denied or timeout:', err.message);
        this.setFallbackLocation('Campus Zone (Default GPS)');
      },
      {
        enableHighAccuracy: true,
        timeout: 8000,
        maximumAge: 10000
      }
    );

    // Watch position continuously for updates
    try {
      navigator.geolocation.watchPosition(
        (pos) => {
          if (!this.currentLocation.isManual) {
            this.currentLocation.lat = pos.coords.latitude;
            this.currentLocation.lng = pos.coords.longitude;
            this.currentLocation.accuracy = Math.round(pos.coords.accuracy);
            this.currentLocation.timestamp = new Date();
            this.updateUI();
          }
        },
        null,
        { enableHighAccuracy: true, maximumAge: 15000 }
      );
    } catch(e) {}
  },

  findClosestLandmark(lat, lng) {
    if (!lat || !lng) return 'Main Campus Grounds';
    
    let closest = this.campusLandmarks[0];
    let minDistance = Infinity;

    this.campusLandmarks.forEach(item => {
      const dLat = item.lat - lat;
      const dLng = item.lng - lng;
      const dist = Math.sqrt(dLat * dLat + dLng * dLng);
      if (dist < minDistance) {
        minDistance = dist;
        closest = item;
      }
    });

    return closest.name;
  },

  setFallbackLocation(label) {
    // Default campus coordinates
    this.currentLocation.lat = 37.7749;
    this.currentLocation.lng = -122.4194;
    this.currentLocation.accuracy = 25;
    this.currentLocation.name = label || 'Main Campus Grounds';
    this.updateUI();
  },

  setManualLocation(name, lat, lng) {
    this.currentLocation.name = name;
    this.currentLocation.lat = lat || 37.7749;
    this.currentLocation.lng = lng || -122.4194;
    this.currentLocation.isManual = true;
    this.updateUI();
    showToast(`Location set to: ${name}`, 'info');
  },

  updateUI() {
    const statusText = document.getElementById('location-status-text');
    const locationName = document.getElementById('location-display-name');
    const locationCoords = document.getElementById('location-display-coords');
    const hiddenLat = document.getElementById('id_latitude');
    const hiddenLng = document.getElementById('id_longitude');
    const formLocation = document.getElementById('location_name');

    if (locationName) {
      locationName.textContent = this.currentLocation.name;
    }
    if (locationCoords && this.currentLocation.lat && this.currentLocation.lng) {
      locationCoords.textContent = `${this.currentLocation.lat.toFixed(5)}, ${this.currentLocation.lng.toFixed(5)} (±${this.currentLocation.accuracy || 10}m)`;
    }
    if (statusText) {
      statusText.innerHTML = this.currentLocation.isManual ? 
        '<span class="pulse-dot" style="background:#3b82f6;"></span> Manual Override' : 
        '<span class="pulse-dot" style="background:#16a34a;"></span> Live GPS Locked';
    }

    if (hiddenLat) hiddenLat.value = this.currentLocation.lat || '';
    if (hiddenLng) hiddenLng.value = this.currentLocation.lng || '';
    if (formLocation && !formLocation.value) formLocation.value = this.currentLocation.name;
  },

  bindManualModal() {
    const editBtn = document.getElementById('btn-edit-location');
    const modal = document.getElementById('location-modal');
    if (!editBtn || !modal) return;

    editBtn.addEventListener('click', () => {
      modal.classList.add('active');
    });

    const landmarkBtns = document.querySelectorAll('.landmark-preset-btn');
    landmarkBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const name = btn.getAttribute('data-name');
        const lat = parseFloat(btn.getAttribute('data-lat'));
        const lng = parseFloat(btn.getAttribute('data-lng'));
        this.setManualLocation(name, lat, lng);
        modal.classList.remove('active');
      });
    });

    const saveManualBtn = document.getElementById('btn-save-manual-location');
    const manualInput = document.getElementById('manual-location-input');
    if (saveManualBtn && manualInput) {
      saveManualBtn.addEventListener('click', () => {
        if (manualInput.value.trim()) {
          this.setManualLocation(manualInput.value.trim());
          modal.classList.remove('active');
        }
      });
    }
  },

  shareLocation() {
    const lat = this.currentLocation.lat || 37.7749;
    const lng = this.currentLocation.lng || -122.4194;
    const name = this.currentLocation.name || 'SafeCampus';
    const mapsUrl = `https://maps.google.com/?q=${lat},${lng}`;
    const shareText = `[RESQ Emergency Beacon] I am at ${name} (${lat.toFixed(5)}, ${lng.toFixed(5)}). Maps link: ${mapsUrl}`;

    if (navigator.share) {
      navigator.share({
        title: 'RESQ Live Location Beacon',
        text: shareText,
        url: mapsUrl
      }).catch(() => {});
    } else if (navigator.clipboard) {
      navigator.clipboard.writeText(shareText).then(() => {
        showToast('Live location beacon copied to clipboard!', 'success');
      });
    } else {
      showToast(shareText, 'info', 6000);
    }
  }
};

document.addEventListener('DOMContentLoaded', () => {
  LocationManager.init();
});
