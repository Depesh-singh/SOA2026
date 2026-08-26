/**
 * CINEMATIC AIR FORCE STRATEGIC COMMAND & CONTROL WAR ROOM
 * Display Array 1: 3D Geospatial Airspace Vector Grid & Tactical RASP ("The Big Board")
 * Features SAM Threat Bubbles, Dynamic Intercept Curves & MIL-STD-2525D Symbology
 */

class CinematicRadarBigBoard {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.width = this.canvas.width;
    this.height = this.canvas.height;
    this.centerX = this.width / 2;
    this.centerY = this.height / 2;
    this.maxRadius = (this.width / 2) - 25;
    this.sweepAngle = 0;
    this.sweepSpeed = 0.04; // 30 RPM
    this.maxRangeMeters = 200.0;

    // SAM Threat Bubble Radii
    this.dewRadiusMeters = 50.0;
    this.akashSamRadiusMeters = 120.0;
  }

  updateAndDraw(tracks, primaryTrackId) {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.width, this.height);

    // 1. Perspective 3D Vector Grid
    this.drawTacticalVectorGrid(ctx);

    // 2. Concentric Range Rings
    this.drawRangeRings(ctx);

    // 3. Surface-to-Air Missile (SAM) Threat Engagement Bubbles
    this.drawSamThreatBubbles(ctx);

    // 4. Azimuth Crosshairs & Compass Rose
    this.drawCompassRose(ctx);

    // 5. Phosphor Radar Sweep
    this.drawSweepBeam(ctx);

    // 6. Dynamic Intercept Splines & Predicted Trajectories
    this.drawInterceptTrajectories(ctx, tracks, primaryTrackId);

    // 7. Tactical Air Tracks (MIL-STD-2525D Symbology)
    this.drawAirTracks(ctx, tracks, primaryTrackId);

    // Advance sweep angle
    this.sweepAngle += this.sweepSpeed;
    if (this.sweepAngle >= Math.PI * 2) {
      this.sweepAngle -= Math.PI * 2;
    }
  }

  drawTacticalVectorGrid(ctx) {
    ctx.save();
    ctx.strokeStyle = 'rgba(0, 240, 255, 0.06)';
    ctx.lineWidth = 1;

    // Isometric grid lines across the scope
    const step = 40;
    for (let x = 0; x <= this.width; x += step) {
      ctx.beginPath();
      ctx.moveTo(x, 0); ctx.lineTo(x, this.height);
      ctx.stroke();
    }
    for (let y = 0; y <= this.height; y += step) {
      ctx.beginPath();
      ctx.moveTo(0, y); ctx.lineTo(this.width, y);
      ctx.stroke();
    }
    ctx.restore();
  }

  drawRangeRings(ctx) {
    const rings = [50, 100, 150, 200];
    ctx.save();

    rings.forEach(rng => {
      const r = (rng / this.maxRangeMeters) * this.maxRadius;
      ctx.beginPath();
      ctx.arc(this.centerX, this.centerY, r, 0, Math.PI * 2);
      ctx.strokeStyle = 'rgba(0, 255, 102, 0.2)';
      ctx.lineWidth = 1;
      ctx.stroke();

      // Range Label
      ctx.fillStyle = 'rgba(0, 255, 102, 0.7)';
      ctx.font = '9px "Share Tech Mono"';
      ctx.fillText(`${rng}m`, this.centerX + 5, this.centerY - r + 11);
    });
    ctx.restore();
  }

  drawSamThreatBubbles(ctx) {
    ctx.save();
    // 1. Akash SAM Engagement Zone (120m)
    const rAkash = (this.akashSamRadiusMeters / this.maxRangeMeters) * this.maxRadius;
    ctx.beginPath();
    ctx.setLineDash([6, 6]);
    ctx.arc(this.centerX, this.centerY, rAkash, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(255, 170, 0, 0.45)';
    ctx.lineWidth = 1.2;
    ctx.stroke();
    ctx.fillStyle = 'rgba(255, 170, 0, 0.03)';
    ctx.fill();

    // 2. DEW Laser Close-In Kill Zone (50m)
    const rDew = (this.dewRadiusMeters / this.maxRangeMeters) * this.maxRadius;
    ctx.beginPath();
    ctx.setLineDash([4, 4]);
    ctx.arc(this.centerX, this.centerY, rDew, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(255, 30, 56, 0.6)';
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.fillStyle = 'rgba(255, 30, 56, 0.05)';
    ctx.fill();

    ctx.restore();
  }

  drawCompassRose(ctx) {
    ctx.save();
    ctx.strokeStyle = 'rgba(0, 240, 255, 0.2)';
    ctx.lineWidth = 1;

    // Major Axis
    ctx.beginPath();
    ctx.moveTo(this.centerX, this.centerY - this.maxRadius);
    ctx.lineTo(this.centerX, this.centerY + this.maxRadius);
    ctx.moveTo(this.centerX - this.maxRadius, this.centerY);
    ctx.lineTo(this.centerX + this.maxRadius, this.centerY);
    ctx.stroke();

    // Minor Angle Ticks (every 30 degrees)
    for (let deg = 0; deg < 360; deg += 30) {
      const rad = (deg * Math.PI) / 180;
      const x1 = this.centerX + Math.cos(rad) * (this.maxRadius - 6);
      const y1 = this.centerY + Math.sin(rad) * (this.maxRadius - 6);
      const x2 = this.centerX + Math.cos(rad) * this.maxRadius;
      const y2 = this.centerY + Math.sin(rad) * this.maxRadius;

      ctx.beginPath();
      ctx.moveTo(x1, y1); ctx.lineTo(x2, y2);
      ctx.stroke();
    }
    ctx.restore();
  }

  drawSweepBeam(ctx) {
    ctx.save();
    const grad = ctx.createRadialGradient(
      this.centerX, this.centerY, 5,
      this.centerX, this.centerY, this.maxRadius
    );
    grad.addColorStop(0, 'rgba(0, 255, 102, 0.45)');
    grad.addColorStop(0.8, 'rgba(0, 255, 102, 0.08)');
    grad.addColorStop(1, 'rgba(0, 255, 102, 0.0)');

    ctx.beginPath();
    ctx.moveTo(this.centerX, this.centerY);
    ctx.arc(this.centerX, this.centerY, this.maxRadius, this.sweepAngle - 0.32, this.sweepAngle, false);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    // High intensity leading edge
    ctx.beginPath();
    ctx.moveTo(this.centerX, this.centerY);
    ctx.lineTo(
      this.centerX + Math.cos(this.sweepAngle) * this.maxRadius,
      this.centerY + Math.sin(this.sweepAngle) * this.maxRadius
    );
    ctx.strokeStyle = 'rgba(0, 255, 102, 0.95)';
    ctx.lineWidth = 1.8;
    ctx.shadowColor = 'rgba(0, 255, 102, 0.8)';
    ctx.shadowBlur = 8;
    ctx.stroke();
    ctx.restore();
  }

  drawInterceptTrajectories(ctx, tracks, primaryTrackId) {
    if (!tracks || !tracks.length) return;

    ctx.save();
    const scale = this.maxRadius / this.maxRangeMeters;

    tracks.forEach(track => {
      const px = this.centerX + (track.x * scale);
      const py = this.centerY - (track.y * scale);

      // Parabolic predictive trajectory (next 3 seconds)
      if (track.vx !== undefined && track.vy !== undefined) {
        ctx.beginPath();
        ctx.setLineDash([3, 3]);
        ctx.moveTo(px, py);

        for (let t = 0.5; t <= 3.0; t += 0.5) {
          const futureX = px + (track.vx * scale * t);
          const futureY = py - (track.vy * scale * t);
          ctx.lineTo(futureX, futureY);
        }

        ctx.strokeStyle = (track.classification === 'HOSTILE') ? 'rgba(255, 30, 56, 0.65)' : 'rgba(0, 240, 255, 0.5)';
        ctx.lineWidth = 1;
        ctx.stroke();
      }
    });
    ctx.restore();
  }

  drawAirTracks(ctx, tracks, primaryTrackId) {
    if (!tracks || !tracks.length) return;

    const scale = this.maxRadius / this.maxRangeMeters;

    tracks.forEach(track => {
      const px = this.centerX + (track.x * scale);
      const py = this.centerY - (track.y * scale);

      const isPrimary = (track.trackId === primaryTrackId);
      const isHostile = track.classification === 'HOSTILE' || track.threatScore >= 75;
      const isSuspect = track.classification === 'SUSPECT' || (track.threatScore >= 40 && track.threatScore < 75);
      const isFriendly = track.classification === 'FRIENDLY';

      ctx.save();

      // Velocity Tail Vector
      if (track.vx !== undefined && track.vy !== undefined) {
        ctx.beginPath();
        ctx.moveTo(px, py);
        ctx.lineTo(px + (track.vx * 1.8), py - (track.vy * 1.8));
        ctx.strokeStyle = isHostile ? '#ff1e38' : (isFriendly ? '#00ff66' : '#ffaa00');
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      // MIL-STD-2525D Symbology
      if (isHostile) {
        // Red Diamond (HOSTILE BANDIT)
        ctx.strokeStyle = '#ff1e38';
        ctx.fillStyle = 'rgba(255, 30, 56, 0.4)';
        ctx.lineWidth = isPrimary ? 2.5 : 1.5;

        const s = isPrimary ? 10 : 8;
        ctx.beginPath();
        ctx.moveTo(px, py - s);
        ctx.lineTo(px + s, py);
        ctx.lineTo(px, py + s);
        ctx.lineTo(px - s, py);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();

        // Primary Target: Animated Targeting Ring
        if (isPrimary) {
          ctx.beginPath();
          ctx.arc(px, py, 16, 0, Math.PI * 2);
          ctx.strokeStyle = 'rgba(255, 30, 56, 0.9)';
          ctx.setLineDash([3, 3]);
          ctx.stroke();
        }
      } else if (isSuspect) {
        // Amber Square (SUSPECT BOGIE)
        ctx.strokeStyle = '#ffaa00';
        ctx.fillStyle = 'rgba(255, 170, 0, 0.35)';
        ctx.lineWidth = 1.5;

        const s = 6;
        ctx.beginPath();
        ctx.rect(px - s, py - s, s * 2, s * 2);
        ctx.fill();
        ctx.stroke();
      } else {
        // Green Circle (FRIENDLY INTERCEPTOR)
        ctx.strokeStyle = '#00ff66';
        ctx.fillStyle = 'rgba(0, 255, 102, 0.4)';
        ctx.lineWidth = 1.8;

        ctx.beginPath();
        ctx.arc(px, py, 6, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
      }

      // Track Data Block (Top Gun Callout Style)
      ctx.font = 'bold 9px "Share Tech Mono"';
      ctx.fillStyle = isHostile ? '#ff1e38' : (isFriendly ? '#00ff66' : '#ffaa00');
      ctx.fillText(`${track.trackId}`, px + 12, py - 6);

      ctx.font = '8px "Share Tech Mono"';
      ctx.fillStyle = '#7e94b0';
      const mach = (track.speed / 340.0).toFixed(2);
      ctx.fillText(`FL ${(track.altitude * 3.28).toFixed(0)} | M ${mach}`, px + 12, py + 4);
      ctx.fillText(`${Math.round(track.range)}m`, px + 12, py + 14);

      ctx.restore();
    });
  }
}

window.cinematicRadar = new CinematicRadarBigBoard('radarCanvas');
