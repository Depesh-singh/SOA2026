/**
 * =============================================================================
 * VayuNetra (वायुNetra) — Advanced 3D AI Trajectory & Intercept Visualizer
 * =============================================================================
 * Features:
 * - 3-Second Future-State Trajectory Prediction from Kalman / Sensor Fusion
 * - Solid Historical Track vs Glowing Dashed Future Forecast
 * - Distinct Highlighted +3.0s Projected Endpoint Marker
 * - Multi-Target Tracking Isolation with Dynamic Color Palettes
 * - Kalman Prediction Uncertainty Envelope / Covariance Cones
 * - Base Defence Security Perimeter / Protected Zone Breach Detection
 * - 3 Interactive Views: [3D ISOMETRIC], [LATERAL X-Z], [VERTICAL Y-Z]
 * - Smooth 60 FPS requestAnimationFrame Rendering Loop
 * =============================================================================
 */

class TrajectoryVisualizer {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.currentView = '3d';

    // Multi-target state stores
    // id -> { id, callsign, history: [{x,y,z,t}], predicted: [{t_sec,x_m,y_m,z_m,uncertainty_m}], endpoint_3s, current, speed, confidence, threat_level, threat_score, zone_breach, lastUpdate }
    this.tracks = {};
    this.maxHistoryLength = 150;
    this.protectedZoneRadius = 50.0; // meters

    // 3D View Angles & Controls
    this.rotAngle = 0.65;
    this.tiltAngle = 0.42;
    this.autoRotate = true;
    this.pulsePhase = 0;

    // Palette per track
    this.palette = [
      { actual: '#ff8833', actualGlow: 'rgba(255, 136, 51, 0.4)', pred: '#00f0ff', predGlow: 'rgba(0, 240, 255, 0.5)', envelope: 'rgba(0, 240, 255, 0.12)' },
      { actual: '#ff33aa', actualGlow: 'rgba(255, 51, 170, 0.4)', pred: '#ffea00', predGlow: 'rgba(255, 234, 0, 0.5)', envelope: 'rgba(255, 234, 0, 0.12)' },
      { actual: '#39ff14', actualGlow: 'rgba(57, 255, 20, 0.4)', pred: '#ff0055', predGlow: 'rgba(255, 0, 85, 0.5)', envelope: 'rgba(255, 0, 85, 0.12)' },
      { actual: '#ffb703', actualGlow: 'rgba(255, 183, 3, 0.4)', pred: '#7000ff', predGlow: 'rgba(112, 0, 255, 0.5)', envelope: 'rgba(112, 0, 255, 0.12)' }
    ];

    // Theme Styles
    this.colors = {
      bg: 'rgba(6, 14, 24, 0.95)',
      grid: 'rgba(0, 240, 255, 0.08)',
      gridLine: 'rgba(0, 240, 255, 0.15)',
      axisLabel: 'rgba(0, 240, 255, 0.7)',
      flightPath: 'rgba(140, 180, 210, 0.7)',
      zoneSafe: 'rgba(0, 240, 255, 0.25)',
      zoneBreach: 'rgba(255, 30, 56, 0.65)',
      zoneFill: 'rgba(0, 240, 255, 0.03)',
      zoneBreachFill: 'rgba(255, 30, 56, 0.12)',
      textDim: 'rgba(150, 180, 200, 0.8)',
      textBright: '#00f0ff',
      noData: 'rgba(0, 240, 255, 0.35)'
    };

    this.resizeCanvas();
    window.addEventListener('resize', () => this.resizeCanvas());
    this.startRenderLoop();
  }

  resizeCanvas() {
    if (!this.canvas) return;
    const wrap = this.canvas.parentElement;
    if (wrap) {
      this.canvas.width = wrap.clientWidth || 480;
      this.canvas.height = wrap.clientHeight || 260;
    }
  }

  setView(view) {
    this.currentView = view;
    document.querySelectorAll('.traj-tab').forEach(t => t.classList.remove('active'));
    const tabId = view === '3d' ? 'tab-3d' : (view === 'lateral' ? 'tab-lateral' : 'tab-vertical');
    const tab = document.getElementById(tabId);
    if (tab) tab.classList.add('active');
  }

  /**
   * Updates multi-target tracking & prediction telemetry from WebSocket stream.
   * @param {Array} incomingTracks - Array of target telemetry objects
   */
  updateTracks(incomingTracks) {
    if (!Array.isArray(incomingTracks)) return;
    const now = performance.now() / 1000;

    incomingTracks.forEach((t, idx) => {
      const id = t.id || t.trackId || `TRK-${idx + 1}`;
      if (!this.tracks[id]) {
        this.tracks[id] = {
          id: id,
          colorIdx: Object.keys(this.tracks).length % this.palette.length,
          history: [],
          predicted: [],
          endpoint_3s: null,
          current: null,
          speed: 0,
          confidence: 0.9,
          threat_level: 'NOMINAL',
          threat_score: 0,
          zone_breach: false,
          tti_sec: null,
          lastUpdate: now
        };
      }

      const track = this.tracks[id];
      track.lastUpdate = now;
      track.confidence = t.confidence || 0.90;
      track.threat_level = t.threat_level || 'NOMINAL';
      track.threat_score = t.threat_score || 0;
      track.speed = t.speed_ms || (t.speed ? Number(t.speed) : 0);

      // Current 3D position
      const curX = (t.x_m !== undefined) ? Number(t.x_m) : (t.x || 0);
      const curY = (t.y_m !== undefined) ? Number(t.y_m) : (t.y || t.range || 50);
      const curZ = (t.z_m !== undefined) ? Number(t.z_m) : (t.z || t.altitude || 15);
      const curVx = (t.vx_ms !== undefined) ? Number(t.vx_ms) : (t.vx || 0);
      const curVy = (t.vy_ms !== undefined) ? Number(t.vy_ms) : (t.vy || -3.0);
      const curVz = (t.vz_ms !== undefined) ? Number(t.vz_ms) : (t.vz || 0);

      track.current = { x: curX, y: curY, z: curZ, vx: curVx, vy: curVy, vz: curVz };

      // Append to historical path
      track.history.push({ x: curX, y: curY, z: curZ, t: now });
      if (track.history.length > this.maxHistoryLength) {
        track.history.shift();
      }

      // Read backend-generated future waypoints (if provided), or calculate client-side EKF prediction
      if (t.future_waypoints && Array.isArray(t.future_waypoints) && t.future_waypoints.length > 0) {
        track.predicted = t.future_waypoints.map(wp => ({
          t_sec: wp.t_sec,
          x: wp.x_m,
          y: wp.y_m,
          z: wp.z_m,
          uncertainty_m: wp.uncertainty_m || (1.5 + 0.5 * wp.t_sec)
        }));
      } else {
        // Fallback: Constant Velocity EKF Extrapolation over 3.0s horizon
        track.predicted = [];
        for (let dt = 0.5; dt <= 3.0 + 0.01; dt += 0.5) {
          track.predicted.push({
            t_sec: Number(dt.toFixed(1)),
            x: curX + (curVx * dt),
            y: curY + (curVy * dt),
            z: Math.max(0, curZ + (curVz * dt)),
            uncertainty_m: 1.5 + (0.6 * dt)
          });
        }
      }

      // 3-Second Projected Endpoint
      if (t.predicted_endpoint_3s) {
        track.endpoint_3s = {
          x: t.predicted_endpoint_3s.x_m,
          y: t.predicted_endpoint_3s.y_m,
          z: t.predicted_endpoint_3s.z_m,
          t_sec: t.predicted_endpoint_3s.t_sec || 3.0
        };
      } else if (track.predicted.length > 0) {
        const lastWp = track.predicted[track.predicted.length - 1];
        track.endpoint_3s = { x: lastWp.x, y: lastWp.y, z: lastWp.z, t_sec: lastWp.t_sec };
      }

      // Protected Zone Approach Check
      if (t.protected_zone) {
        track.zone_breach = t.protected_zone.is_breaching;
        track.tti_sec = t.protected_zone.tti_sec;
      } else {
        // Compute against base perimeter
        let breach = false;
        let tti = null;
        for (const wp of track.predicted) {
          const gDist = Math.hypot(wp.x, wp.y);
          if (gDist <= this.protectedZoneRadius) {
            breach = true;
            tti = wp.t_sec;
            break;
          }
        }
        track.zone_breach = breach;
        track.tti_sec = tti;
      }
    });

    // Clean stale tracks (no telemetry in 5 seconds)
    const staleLimit = now - 5.0;
    Object.keys(this.tracks).forEach(id => {
      if (this.tracks[id].lastUpdate < staleLimit) {
        delete this.tracks[id];
      }
    });

    this.updateDomStats();
  }

  updateDomStats() {
    const trackIds = Object.keys(this.tracks);
    const primaryId = trackIds[0];
    const primary = primaryId ? this.tracks[primaryId] : null;

    // 1. Points / Target Count
    const statPts = document.getElementById('traj-stat-points');
    if (statPts) {
      const totalPoints = Object.values(this.tracks).reduce((s, tr) => s + tr.history.length, 0);
      statPts.innerHTML = `TARGETS: <strong>${trackIds.length}</strong> (PTS: ${totalPoints})`;
    }

    // 2. Horizon
    const statHz = document.getElementById('traj-stat-horizon');
    if (statHz) {
      statHz.innerHTML = `HORIZON: <strong>3.0s (CV-EKF)</strong>`;
    }

    // 3. 3s Predicted Position
    const statPred = document.getElementById('traj-stat-pred3s');
    if (statPred) {
      if (primary && primary.endpoint_3s) {
        const ep = primary.endpoint_3s;
        statPred.innerHTML = `+3s: <strong>X:${ep.x.toFixed(1)} Y:${ep.y.toFixed(1)} Z:${ep.z.toFixed(1)}m</strong>`;
      } else {
        statPred.innerHTML = `+3s: <strong>AWAITING TRACK</strong>`;
      }
    }

    // 4. Speed
    const statSpd = document.getElementById('traj-stat-speed');
    if (statSpd && primary) {
      statSpd.innerHTML = `SPD: <strong>${primary.speed.toFixed(1)} m/s</strong>`;
    }

    // 5. Confidence
    const statConf = document.getElementById('traj-stat-confidence');
    if (statConf) {
      if (primary && primary.confidence) {
        statConf.innerHTML = `CONF: <strong>${Math.round(primary.confidence * 100)}%</strong>`;
      } else {
        statConf.innerHTML = `CONF: <strong>N/A</strong>`;
      }
    }

    // 6. Perimeter Breach Status
    const statZone = document.getElementById('traj-stat-zone');
    if (statZone) {
      const isAnyBreach = Object.values(this.tracks).some(tr => tr.zone_breach);
      if (isAnyBreach) {
        const breachTrack = Object.values(this.tracks).find(tr => tr.zone_breach);
        statZone.innerHTML = `PERIMETER: <strong style="color:#ff1e38;">BREACH INBOUND (TTI: ${breachTrack.tti_sec || 2.5}s)</strong>`;
      } else {
        statZone.innerHTML = `PERIMETER: <strong style="color:#00ff66;">SECURE</strong>`;
      }
    }
  }

  // 3D Isometric projection mapping (World meters -> Screen pixels)
  project3D(x, y, z, cx, cy, scale) {
    const cosR = Math.cos(this.rotAngle);
    const sinR = Math.sin(this.rotAngle);
    const cosT = Math.cos(this.tiltAngle);
    const sinT = Math.sin(this.tiltAngle);

    // Yaw rotation
    const rx = x * cosR - y * sinR;
    const ry = x * sinR + y * cosR;
    const rz = z;

    // Pitch tilt
    const py = ry * cosT - rz * sinT;
    const pz = ry * sinT + rz * cosT;

    return {
      sx: cx + rx * scale,
      sy: cy - pz * scale,
      depth: py
    };
  }

  startRenderLoop() {
    const renderFrame = () => {
      this.pulsePhase = (this.pulsePhase + 0.05) % (Math.PI * 2);
      this.render();
      requestAnimationFrame(renderFrame);
    };
    requestAnimationFrame(renderFrame);
  }

  render() {
    if (!this.canvas || !this.ctx) return;
    const ctx = this.ctx;
    const W = this.canvas.width;
    const H = this.canvas.height;

    // Clear background
    ctx.fillStyle = this.colors.bg;
    ctx.fillRect(0, 0, W, H);

    // Auto-rotate in 3D view
    if (this.autoRotate && this.currentView === '3d') {
      this.rotAngle += 0.0018;
    }

    const hasData = Object.keys(this.tracks).length > 0;

    if (!hasData) {
      this.renderNoData(ctx, W, H);
      return;
    }

    switch (this.currentView) {
      case '3d': this.render3D(ctx, W, H); break;
      case 'lateral': this.renderLateral(ctx, W, H); break;
      case 'vertical': this.renderVertical(ctx, W, H); break;
    }
  }

  renderNoData(ctx, W, H) {
    this.drawGrid2D(ctx, W, H);

    ctx.fillStyle = this.colors.noData;
    ctx.font = '11px "Share Tech Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText('AWAITING DRONE ACQUISITION FOR 3D TRAJECTORY PREDICTION...', W / 2, H / 2 - 8);
    ctx.font = '9px "Share Tech Mono", monospace';
    ctx.fillStyle = 'rgba(0, 240, 255, 0.25)';
    ctx.fillText('Constant-Velocity EKF will forecast +3.0s flight path once targets appear', W / 2, H / 2 + 14);
  }

  drawGrid2D(ctx, W, H) {
    ctx.strokeStyle = this.colors.grid;
    ctx.lineWidth = 0.5;
    for (let x = 0; x < W; x += 30) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
    }
    for (let y = 0; y < H; y += 30) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
    }
  }

  // =========================================================================
  // 3D ISOMETRIC VIEW
  // =========================================================================
  render3D(ctx, W, H) {
    const cx = W / 2;
    const cy = H * 0.54;
    const scale = Math.min(W, H) * 0.019;

    // 1. Draw 3D Ground Grid Floor
    this.draw3DGrid(ctx, cx, cy, scale);

    // 2. Draw Protected Defence Base Security Perimeter Ring
    this.draw3DProtectedZone(ctx, cx, cy, scale);

    // 3. Draw 3D Coordinate Reference Axes
    this.draw3DAxes(ctx, cx, cy, scale);

    // 4. Draw Sensor Base Origin Marker at (0, 0, 0)
    const baseP = this.project3D(0, 0, 0, cx, cy, scale);
    ctx.fillStyle = '#00f0ff';
    ctx.beginPath(); ctx.arc(baseP.sx, baseP.sy, 4, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = 'rgba(0, 240, 255, 0.6)';
    ctx.font = '8px "Share Tech Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText('BASE (0,0)', baseP.sx, baseP.sy + 12);

    // 5. Draw Each Track Independently
    Object.keys(this.tracks).forEach(id => {
      const track = this.tracks[id];
      const pal = this.palette[track.colorIdx];
      const hist = track.history;
      const pred = track.predicted;

      if (hist.length === 0) return;

      // 5a. Historical Flight Path (Solid Line)
      if (hist.length >= 2) {
        ctx.save();
        ctx.strokeStyle = this.colors.flightPath;
        ctx.lineWidth = 1.6;
        ctx.beginPath();
        hist.forEach((p, i) => {
          const proj = this.project3D(p.x, p.y, p.z, cx, cy, scale);
          if (i === 0) ctx.moveTo(proj.sx, proj.sy);
          else ctx.lineTo(proj.sx, proj.sy);
        });
        ctx.stroke();
        ctx.restore();

        // Historical Waypoint Dots (Orange/Paletted)
        const recentHist = hist.slice(-25);
        recentHist.forEach((p, i) => {
          const proj = this.project3D(p.x, p.y, p.z, cx, cy, scale);
          const alpha = 0.2 + (0.8 * (i / recentHist.length));
          ctx.fillStyle = pal.actual;
          ctx.globalAlpha = alpha;
          ctx.beginPath();
          ctx.arc(proj.sx, proj.sy, 2.5, 0, Math.PI * 2);
          ctx.fill();
        });
        ctx.globalAlpha = 1.0;
      }

      // 5b. Future Predicted Trajectory (Glowing Dashed Line from 0s to 3s)
      if (pred.length > 0 && hist.length > 0) {
        const cur = hist[hist.length - 1];
        const curProj = this.project3D(cur.x, cur.y, cur.z, cx, cy, scale);

        // Uncertainty Envelope (Cone around prediction)
        ctx.save();
        ctx.fillStyle = pal.envelope;
        ctx.beginPath();
        pred.forEach((wp, i) => {
          const unc = wp.uncertainty_m || 2.0;
          const leftProj = this.project3D(wp.x - unc, wp.y, wp.z, cx, cy, scale);
          if (i === 0) ctx.moveTo(curProj.sx, curProj.sy);
          ctx.lineTo(leftProj.sx, leftProj.sy);
        });
        for (let i = pred.length - 1; i >= 0; i--) {
          const wp = pred[i];
          const unc = wp.uncertainty_m || 2.0;
          const rightProj = this.project3D(wp.x + unc, wp.y, wp.z, cx, cy, scale);
          ctx.lineTo(rightProj.sx, rightProj.sy);
        }
        ctx.closePath();
        ctx.fill();
        ctx.restore();

        // Glowing Dashed Prediction Path
        ctx.save();
        ctx.shadowColor = pal.predGlow;
        ctx.shadowBlur = 10;
        ctx.strokeStyle = pal.pred;
        ctx.lineWidth = 2.2;
        ctx.setLineDash([5, 4]);
        ctx.beginPath();
        ctx.moveTo(curProj.sx, curProj.sy);
        pred.forEach(wp => {
          const proj = this.project3D(wp.x, wp.y, wp.z, cx, cy, scale);
          ctx.lineTo(proj.sx, proj.sy);
        });
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.restore();

        // Intermediate Forecast Nodes (+1.0s, +2.0s)
        pred.forEach(wp => {
          const proj = this.project3D(wp.x, wp.y, wp.z, cx, cy, scale);
          ctx.fillStyle = pal.pred;
          ctx.beginPath();
          ctx.arc(proj.sx, proj.sy, 3.0, 0, Math.PI * 2);
          ctx.fill();

          if (wp.t_sec === 1.0 || wp.t_sec === 2.0) {
            ctx.fillStyle = 'rgba(0, 240, 255, 0.7)';
            ctx.font = '8px "Share Tech Mono", monospace';
            ctx.textAlign = 'left';
            ctx.fillText(`+${wp.t_sec}s`, proj.sx + 4, proj.sy - 3);
          }
        });

        // 5c. Distinct +3.0s Future Endpoint Marker
        const ep = pred[pred.length - 1];
        const epProj = this.project3D(ep.x, ep.y, ep.z, cx, cy, scale);

        // Glowing Diamond
        ctx.save();
        ctx.shadowColor = '#00f0ff';
        ctx.shadowBlur = 12;
        ctx.fillStyle = '#00f0ff';
        ctx.beginPath();
        const dSize = 6.0;
        ctx.moveTo(epProj.sx, epProj.sy - dSize);
        ctx.lineTo(epProj.sx + dSize, epProj.sy);
        ctx.lineTo(epProj.sx, epProj.sy + dSize);
        ctx.lineTo(epProj.sx - dSize, epProj.sy);
        ctx.closePath();
        ctx.fill();
        ctx.restore();

        // +3.0s Endpoint Label
        ctx.fillStyle = '#00f0ff';
        ctx.font = 'bold 9px "Share Tech Mono", monospace';
        ctx.textAlign = 'left';
        ctx.fillText(`+3.0s [${ep.x.toFixed(0)},${ep.y.toFixed(0)},${ep.z.toFixed(0)}]`, epProj.sx + 8, epProj.sy + 3);
      }

      // 5d. Current Drone Position Marker (Pulsing Center + Vector)
      const cur = hist[hist.length - 1];
      const curProj = this.project3D(cur.x, cur.y, cur.z, cx, cy, scale);

      // Pulsing Halo
      const pulseSize = 6 + Math.sin(this.pulsePhase) * 3;
      ctx.strokeStyle = track.threat_level === 'HIGH' ? 'rgba(255, 30, 56, 0.8)' : 'rgba(0, 240, 255, 0.8)';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(curProj.sx, curProj.sy, pulseSize, 0, Math.PI * 2);
      ctx.stroke();

      // Solid Core
      ctx.fillStyle = track.threat_level === 'HIGH' ? '#ff1e38' : '#00f0ff';
      ctx.beginPath();
      ctx.arc(curProj.sx, curProj.sy, 4.5, 0, Math.PI * 2);
      ctx.fill();

      // Track Label & Altitude
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 9px "Share Tech Mono", monospace';
      ctx.textAlign = 'left';
      ctx.fillText(`${track.id} (Alt: ${cur.z.toFixed(1)}m)`, curProj.sx + 8, curProj.sy - 6);
    });

    // View Banner Overlay
    this.drawViewHeader(ctx, '3D AIRSPACE ISOMETRIC VIEW (REAL-TIME + 3.0s FORECAST)');
  }

  // Draw 3D Ground Floor Grid
  draw3DGrid(ctx, cx, cy, scale) {
    ctx.strokeStyle = this.colors.gridLine;
    ctx.lineWidth = 0.4;
    const gridRange = 60;
    const step = 10;

    for (let i = -gridRange; i <= gridRange; i += step) {
      const a1 = this.project3D(i, -gridRange, 0, cx, cy, scale);
      const a2 = this.project3D(i, gridRange, 0, cx, cy, scale);
      ctx.beginPath(); ctx.moveTo(a1.sx, a1.sy); ctx.lineTo(a2.sx, a2.sy); ctx.stroke();

      const b1 = this.project3D(-gridRange, i, 0, cx, cy, scale);
      const b2 = this.project3D(gridRange, i, 0, cx, cy, scale);
      ctx.beginPath(); ctx.moveTo(b1.sx, b1.sy); ctx.lineTo(b2.sx, b2.sy); ctx.stroke();
    }
  }

  // Draw Protected Base Security Perimeter on 3D Ground
  draw3DProtectedZone(ctx, cx, cy, scale) {
    const isBreach = Object.values(this.tracks).some(t => t.zone_breach);
    const nSegments = 32;
    const r = this.protectedZoneRadius;

    ctx.save();
    ctx.strokeStyle = isBreach ? this.colors.zoneBreach : this.colors.zoneSafe;
    ctx.fillStyle = isBreach ? this.colors.zoneBreachFill : this.colors.zoneFill;
    ctx.lineWidth = isBreach ? 2.0 : 1.0;
    if (isBreach) ctx.setLineDash([4, 2]);

    ctx.beginPath();
    for (let i = 0; i <= nSegments; i++) {
      const theta = (i / nSegments) * (Math.PI * 2);
      const zx = r * Math.cos(theta);
      const zy = r * Math.sin(theta);
      const proj = this.project3D(zx, zy, 0, cx, cy, scale);
      if (i === 0) ctx.moveTo(proj.sx, proj.sy);
      else ctx.lineTo(proj.sx, proj.sy);
    }
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    ctx.restore();

    // Perimeter Ring Label
    const zLabelP = this.project3D(0, r, 0, cx, cy, scale);
    ctx.fillStyle = isBreach ? '#ff1e38' : 'rgba(0, 240, 255, 0.6)';
    ctx.font = '8px "Share Tech Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText(isBreach ? '⚠ PROTECTED ZONE BREACH' : '50m DEFENCE PERIMETER', zLabelP.sx, zLabelP.sy + 10);
  }

  // Draw 3D Reference Coordinate Axes
  draw3DAxes(ctx, cx, cy, scale) {
    const axLen = 30;
    const orig = this.project3D(0, 0, 0, cx, cy, scale);

    // X Axis (East / Red)
    const xEnd = this.project3D(axLen, 0, 0, cx, cy, scale);
    ctx.strokeStyle = '#ff4444'; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(orig.sx, orig.sy); ctx.lineTo(xEnd.sx, xEnd.sy); ctx.stroke();
    ctx.fillStyle = '#ff4444'; ctx.font = '9px "Share Tech Mono", monospace'; ctx.textAlign = 'center';
    ctx.fillText('X (East)', xEnd.sx, xEnd.sy + 12);

    // Y Axis (North / Green)
    const yEnd = this.project3D(0, axLen, 0, cx, cy, scale);
    ctx.strokeStyle = '#44ff44'; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(orig.sx, orig.sy); ctx.lineTo(yEnd.sx, yEnd.sy); ctx.stroke();
    ctx.fillStyle = '#44ff44'; ctx.font = '9px "Share Tech Mono", monospace'; ctx.textAlign = 'center';
    ctx.fillText('Y (North)', yEnd.sx, yEnd.sy + 12);

    // Z Axis (Altitude / Cyan)
    const zEnd = this.project3D(0, 0, axLen * 0.7, cx, cy, scale);
    ctx.strokeStyle = '#00f0ff'; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(orig.sx, orig.sy); ctx.lineTo(zEnd.sx, zEnd.sy); ctx.stroke();
    ctx.fillStyle = '#00f0ff'; ctx.font = '9px "Share Tech Mono", monospace'; ctx.textAlign = 'left';
    ctx.fillText('Z (Alt)', zEnd.sx + 4, zEnd.sy);
  }

  // =========================================================================
  // 2D ORTHOGONAL VIEWS (Lateral X-Z and Vertical Y-Z)
  // =========================================================================
  renderLateral(ctx, W, H) {
    this.render2DProfile(ctx, W, H, 'x', 'z', 'LATERAL VIEW (X vs ALTITUDE Z)', 'Lateral Displacement X (m)', 'Altitude Z (m)');
  }

  renderVertical(ctx, W, H) {
    this.render2DProfile(ctx, W, H, 'y', 'z', 'VERTICAL PROFILE (RANGE Y vs ALTITUDE Z)', 'Forward Range Y (m)', 'Altitude Z (m)');
  }

  render2DProfile(ctx, W, H, xKey, yKey, title, xLabel, yLabel) {
    const pad = { left: 55, right: 25, top: 32, bottom: 34 };
    const plotW = W - pad.left - pad.right;
    const plotH = H - pad.top - pad.bottom;

    // Gather bounds
    let allX = [0], allY = [0];
    Object.values(this.tracks).forEach(tr => {
      tr.history.forEach(p => { allX.push(p[xKey]); allY.push(p[yKey]); });
      tr.predicted.forEach(p => { allX.push(p[xKey]); allY.push(p[yKey]); });
    });

    let minX = Math.min(...allX), maxX = Math.max(...allX);
    let minY = Math.min(...allY), maxY = Math.max(...allY);
    const rangeX = Math.max(20, (maxX - minX));
    const rangeY = Math.max(15, (maxY - minY));

    minX -= rangeX * 0.12; maxX += rangeX * 0.12;
    minY = Math.max(0, minY - rangeY * 0.1); maxY += rangeY * 0.15;

    const scaleX = plotW / (maxX - minX);
    const scaleY = plotH / (maxY - minY);

    const toSX = v => pad.left + (v - minX) * scaleX;
    const toSY = v => pad.top + plotH - (v - minY) * scaleY;

    // Background & Grid
    ctx.fillStyle = 'rgba(10, 20, 35, 0.75)';
    ctx.fillRect(pad.left, pad.top, plotW, plotH);

    ctx.strokeStyle = this.colors.gridLine;
    ctx.lineWidth = 0.4;
    ctx.font = '8px "Share Tech Mono", monospace';
    ctx.fillStyle = this.colors.axisLabel;

    // Y Grid lines
    const nGridY = 5;
    for (let i = 0; i <= nGridY; i++) {
      const val = minY + ((maxY - minY) * i) / nGridY;
      const sy = toSY(val);
      ctx.beginPath(); ctx.moveTo(pad.left, sy); ctx.lineTo(pad.left + plotW, sy); ctx.stroke();
      ctx.textAlign = 'right';
      ctx.fillText(val.toFixed(0), pad.left - 6, sy + 3);
    }

    // X Grid lines
    const nGridX = 6;
    for (let i = 0; i <= nGridX; i++) {
      const val = minX + ((maxX - minX) * i) / nGridX;
      const sx = toSX(val);
      ctx.beginPath(); ctx.moveTo(sx, pad.top); ctx.lineTo(sx, pad.top + plotH); ctx.stroke();
      ctx.textAlign = 'center';
      ctx.fillText(val.toFixed(0), sx, pad.top + plotH + 14);
    }

    // Axis Labels
    ctx.fillStyle = this.colors.textBright;
    ctx.font = '9px "Share Tech Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText(xLabel, pad.left + plotW / 2, H - 6);

    ctx.save();
    ctx.translate(14, pad.top + plotH / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText(yLabel, 0, 0);
    ctx.restore();

    // Render Tracks
    Object.values(this.tracks).forEach(tr => {
      const pal = this.palette[tr.colorIdx];
      const hist = tr.history;
      const pred = tr.predicted;

      // Solid Historical Path
      if (hist.length >= 2) {
        ctx.strokeStyle = this.colors.flightPath;
        ctx.lineWidth = 1.8;
        ctx.beginPath();
        hist.forEach((p, i) => {
          const sx = toSX(p[xKey]), sy = toSY(p[yKey]);
          if (i === 0) ctx.moveTo(sx, sy); else ctx.lineTo(sx, sy);
        });
        ctx.stroke();

        // Past Dots
        hist.slice(-30).forEach(p => {
          ctx.fillStyle = pal.actual;
          ctx.beginPath();
          ctx.arc(toSX(p[xKey]), toSY(p[yKey]), 3, 0, Math.PI * 2);
          ctx.fill();
        });
      }

      // Future Dashed Path
      if (pred.length > 0 && hist.length > 0) {
        const last = hist[hist.length - 1];
        ctx.save();
        ctx.shadowColor = pal.predGlow;
        ctx.shadowBlur = 8;
        ctx.strokeStyle = pal.pred;
        ctx.lineWidth = 2.0;
        ctx.setLineDash([5, 4]);
        ctx.beginPath();
        ctx.moveTo(toSX(last[xKey]), toSY(last[yKey]));
        pred.forEach(p => ctx.lineTo(toSX(p[xKey]), toSY(p[yKey])));
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.restore();

        // Predicted dots
        pred.forEach(p => {
          ctx.fillStyle = pal.pred;
          ctx.beginPath();
          ctx.arc(toSX(p[xKey]), toSY(p[yKey]), 3, 0, Math.PI * 2);
          ctx.fill();
        });

        // +3s Endpoint Diamond
        const ep = pred[pred.length - 1];
        const ex = toSX(ep[xKey]), ey = toSY(ep[yKey]);
        ctx.fillStyle = '#00f0ff';
        ctx.beginPath();
        ctx.moveTo(ex, ey - 5); ctx.lineTo(ex + 5, ey); ctx.lineTo(ex, ey + 5); ctx.lineTo(ex - 5, ey);
        ctx.closePath();
        ctx.fill();
        ctx.fillText(`+3.0s (${ep[xKey].toFixed(0)},${ep[yKey].toFixed(0)})`, ex + 7, ey - 3);
      }

      // Current Marker
      if (hist.length > 0) {
        const cur = hist[hist.length - 1];
        const cx = toSX(cur[xKey]), cy = toSY(cur[yKey]);
        ctx.fillStyle = '#ff1e38';
        ctx.beginPath(); ctx.arc(cx, cy, 5, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 9px "Share Tech Mono", monospace';
        ctx.fillText(`${tr.id}`, cx + 7, cy + 3);
      }
    });

    this.drawViewHeader(ctx, title);
  }

  drawViewHeader(ctx, title) {
    ctx.fillStyle = this.colors.textBright;
    ctx.font = '10px "Share Tech Mono", monospace';
    ctx.textAlign = 'left';
    ctx.fillText(title, 10, 15);
  }
}

// Global instantiation on DOM ready
window.addEventListener('DOMContentLoaded', () => {
  window.trajViz = new TrajectoryVisualizer('trajectoryCanvas');
});
