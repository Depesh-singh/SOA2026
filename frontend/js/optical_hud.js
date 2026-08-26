/**
 * CINEMATIC AIR FORCE STRATEGIC COMMAND & CONTROL WAR ROOM
 * Display Array 2: Multi-Mode EO/IR FLIR Target Reconnaissance Pod
 * Multi-Spectral Vision Modes (White-Hot, Black-Hot, NVG Green, Day Optical) + Digital Zoom
 */

class CinematicOpticalFLIR {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.width = this.canvas.width;
    this.height = this.canvas.height;
    this.visionMode = 'WHITE_HOT'; // 'WHITE_HOT', 'BLACK_HOT', 'NVG_GREEN', 'DAY_OPTICAL'
    this.zoomLevel = 4; // 1, 4, 8, 16
  }

  setVisionMode(mode) {
    this.visionMode = mode;
  }

  setZoomLevel(zoom) {
    this.zoomLevel = zoom;
  }

  updateAndDraw(tracks, primaryTrackId, gimbalPan, gimbalTilt) {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.width, this.height);

    // 1. Render Thermal/Optical Background based on Vision Mode
    this.drawVisionBackground(ctx, gimbalTilt);

    // 2. Tactical Pitch Ladder & Bank Horizon
    this.drawPitchLadder(ctx, gimbalTilt);

    // 3. Boresight Crosshair & Laser Rangefinder
    this.drawBoresight(ctx);

    // 4. Optical Target Bounding Brackets with Zoom Scaling
    this.drawTargetBrackets(ctx, tracks, primaryTrackId);

    // 5. Thermal Sensor Noise Grain
    this.drawSensorNoise(ctx);
  }

  drawVisionBackground(ctx, tilt) {
    const horizonY = (this.height / 2) + (tilt * 2.2);

    if (this.visionMode === 'WHITE_HOT') {
      // White-Hot FLIR: Dark cold sky, slightly lighter terrain
      const sky = ctx.createLinearGradient(0, 0, 0, horizonY);
      sky.addColorStop(0, '#060a10');
      sky.addColorStop(1, '#121a24');
      ctx.fillStyle = sky;
      ctx.fillRect(0, 0, this.width, horizonY);

      const ground = ctx.createLinearGradient(0, horizonY, 0, this.height);
      ground.addColorStop(0, '#10161f');
      ground.addColorStop(1, '#080c14');
      ctx.fillStyle = ground;
      ctx.fillRect(0, horizonY, this.width, this.height - horizonY);

    } else if (this.visionMode === 'BLACK_HOT') {
      // Black-Hot FLIR: Light hot background
      const sky = ctx.createLinearGradient(0, 0, 0, horizonY);
      sky.addColorStop(0, '#75808d');
      sky.addColorStop(1, '#8c98a6');
      ctx.fillStyle = sky;
      ctx.fillRect(0, 0, this.width, horizonY);

      const ground = ctx.createLinearGradient(0, horizonY, 0, this.height);
      ground.addColorStop(0, '#66727f');
      ground.addColorStop(1, '#505963');
      ctx.fillStyle = ground;
      ctx.fillRect(0, horizonY, this.width, this.height - horizonY);

    } else if (this.visionMode === 'NVG_GREEN') {
      // NVG Night-Vision Phosphor Green
      const sky = ctx.createLinearGradient(0, 0, 0, horizonY);
      sky.addColorStop(0, '#031408');
      sky.addColorStop(1, '#062810');
      ctx.fillStyle = sky;
      ctx.fillRect(0, 0, this.width, horizonY);

      const ground = ctx.createLinearGradient(0, horizonY, 0, this.height);
      ground.addColorStop(0, '#05220d');
      ground.addColorStop(1, '#021106');
      ctx.fillStyle = ground;
      ctx.fillRect(0, horizonY, this.width, this.height - horizonY);

    } else {
      // Day Optical: Natural daylight sky/ground
      const sky = ctx.createLinearGradient(0, 0, 0, horizonY);
      sky.addColorStop(0, '#132840');
      sky.addColorStop(1, '#234568');
      ctx.fillStyle = sky;
      ctx.fillRect(0, 0, this.width, horizonY);

      const ground = ctx.createLinearGradient(0, horizonY, 0, this.height);
      ground.addColorStop(0, '#182b20');
      ground.addColorStop(1, '#0f1a14');
      ctx.fillStyle = ground;
      ctx.fillRect(0, horizonY, this.width, this.height - horizonY);
    }

    // Horizon line
    ctx.beginPath();
    ctx.moveTo(0, horizonY);
    ctx.lineTo(this.width, horizonY);
    ctx.strokeStyle = (this.visionMode === 'NVG_GREEN') ? 'rgba(0, 255, 102, 0.4)' : 'rgba(0, 240, 255, 0.35)';
    ctx.lineWidth = 1;
    ctx.stroke();
  }

  drawPitchLadder(ctx, tilt) {
    const cx = this.width / 2;
    const cy = this.height / 2;
    const horizonY = cy + (tilt * 2.2);

    ctx.save();
    const hudColor = (this.visionMode === 'NVG_GREEN') ? 'rgba(0, 255, 102, 0.7)' : (this.visionMode === 'BLACK_HOT' ? '#000000' : 'rgba(0, 240, 255, 0.7)');
    ctx.strokeStyle = hudColor;
    ctx.fillStyle = hudColor;
    ctx.lineWidth = 1;
    ctx.font = '9px "Share Tech Mono"';

    [-15, -10, -5, 5, 10, 15].forEach(deg => {
      const y = horizonY - (deg * 6.5);
      if (y > 35 && y < this.height - 35) {
        ctx.beginPath();
        ctx.moveTo(cx - 80, y); ctx.lineTo(cx - 35, y); ctx.lineTo(cx - 35, y + (deg > 0 ? 4 : -4));
        ctx.moveTo(cx + 35, y); ctx.lineTo(cx + 80, y); ctx.lineTo(cx + 35, y + (deg > 0 ? 4 : -4));
        ctx.stroke();

        ctx.fillText(`${deg > 0 ? '+' : ''}${deg}`, cx - 100, y + 3);
        ctx.fillText(`${deg > 0 ? '+' : ''}${deg}`, cx + 85, y + 3);
      }
    });
    ctx.restore();
  }

  drawBoresight(ctx) {
    const cx = this.width / 2;
    const cy = this.height / 2;

    ctx.save();
    const hudColor = (this.visionMode === 'NVG_GREEN') ? '#00ff66' : (this.visionMode === 'BLACK_HOT' ? '#000000' : '#00f0ff');
    ctx.strokeStyle = hudColor;
    ctx.lineWidth = 1.2;

    // Crosshair
    ctx.beginPath();
    ctx.moveTo(cx - 35, cy); ctx.lineTo(cx - 10, cy);
    ctx.moveTo(cx + 10, cy); ctx.lineTo(cx + 35, cy);
    ctx.moveTo(cx, cy - 35); ctx.lineTo(cx, cy - 10);
    ctx.moveTo(cx, cy + 10); ctx.lineTo(cx, cy + 35);
    ctx.stroke();

    // Center dot
    ctx.beginPath();
    ctx.arc(cx, cy, 1.5, 0, Math.PI * 2);
    ctx.fillStyle = hudColor;
    ctx.fill();
    ctx.restore();
  }

  drawTargetBrackets(ctx, tracks, primaryTrackId) {
    if (!tracks || !tracks.length) return;

    const fovRad = (60 * Math.PI) / 180;
    const zoomFactor = this.zoomLevel / 4.0; // Normalized to 4X default

    tracks.forEach(track => {
      const angleAz = Math.atan2(track.x, track.y);
      const angleEl = Math.atan2(track.z, Math.hypot(track.x, track.y));

      const screenX = (this.width / 2) + (Math.tan(angleAz) / Math.tan(fovRad / 2)) * (this.width / 2) * zoomFactor;
      const screenY = (this.height / 2) - (Math.tan(angleEl) / Math.tan(fovRad / 2)) * (this.height / 2) * zoomFactor;

      const dist = Math.max(track.range, 15);
      const baseBoxSize = Math.max(Math.min(2400 / dist, 120), 28);
      const boxSize = baseBoxSize * Math.sqrt(zoomFactor);

      const isPrimary = (track.trackId === primaryTrackId);
      const isHostile = track.classification === 'HOSTILE' || track.threatScore >= 75;

      ctx.save();

      // Render thermal heat silhouette if White-Hot or Black-Hot
      if (this.visionMode === 'WHITE_HOT') {
        ctx.fillStyle = isHostile ? 'rgba(255, 255, 255, 0.95)' : 'rgba(230, 240, 255, 0.7)';
        ctx.beginPath();
        ctx.arc(screenX, screenY, boxSize * 0.3, 0, Math.PI * 2);
        ctx.fill();
      } else if (this.visionMode === 'BLACK_HOT') {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.9)';
        ctx.beginPath();
        ctx.arc(screenX, screenY, boxSize * 0.3, 0, Math.PI * 2);
        ctx.fill();
      }

      // Targeting Corner Brackets
      const color = isHostile ? '#ff1e38' : (this.visionMode === 'NVG_GREEN' ? '#00ff66' : '#ffaa00');
      ctx.strokeStyle = color;
      ctx.lineWidth = isPrimary ? 2.2 : 1.2;

      const half = boxSize / 2;
      const arm = Math.max(boxSize * 0.28, 6);

      const left = screenX - half;
      const right = screenX + half;
      const top = screenY - half;
      const bottom = screenY + half;

      ctx.beginPath(); ctx.moveTo(left, top + arm); ctx.lineTo(left, top); ctx.lineTo(left + arm, top); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(right - arm, top); ctx.lineTo(right, top); ctx.lineTo(right, top + arm); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(left, bottom - arm); ctx.lineTo(left, bottom); ctx.lineTo(left + arm, bottom); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(right - arm, bottom); ctx.lineTo(right, bottom); ctx.lineTo(right, bottom - arm); ctx.stroke();

      if (isPrimary) {
        // Rotating Lock Ring
        ctx.beginPath();
        ctx.arc(screenX, screenY, half + 14, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(255, 30, 56, 0.85)';
        ctx.setLineDash([4, 4]);
        ctx.stroke();

        ctx.fillStyle = '#ff1e38';
        ctx.font = 'bold 9px "Share Tech Mono"';
        ctx.fillText(`FCR LOCK: ${track.trackId}`, left, top - 8);
        ctx.fillText(`TTI: ${(track.range / Math.max(track.speed, 5)).toFixed(1)}s`, left, bottom + 14);
      } else {
        ctx.fillStyle = color;
        ctx.font = '9px "Share Tech Mono"';
        ctx.fillText(`${track.trackId}`, left, top - 4);
      }

      ctx.restore();
    });
  }

  drawSensorNoise(ctx) {
    // Subtle realistic thermal camera grain noise
    ctx.save();
    ctx.fillStyle = (this.visionMode === 'NVG_GREEN') ? 'rgba(0, 255, 102, 0.04)' : 'rgba(255, 255, 255, 0.03)';
    for (let i = 0; i < 120; i++) {
      const rx = Math.random() * this.width;
      const ry = Math.random() * this.height;
      ctx.fillRect(rx, ry, 2, 2);
    }
    ctx.restore();
  }
}

window.cinematicOpticalFLIR = new CinematicOpticalFLIR('opticalCanvas');
