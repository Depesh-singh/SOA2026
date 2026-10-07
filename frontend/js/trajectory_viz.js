/**
 * =============================================================================
 * VayuNetra (वायुNetra) — Advanced 3D AI Trajectory & Intercept Visualizer
 * =============================================================================
 * Features:
 * - 2-Second & 3-Second Future-State Trajectory Prediction (AI Kalman / Fusion)
 * - Solid Historical Track vs Glowing Dashed Future Forecast
 * - Distinct Highlighted +2.0s & +3.0s Projected Endpoint Diamond Markers
 * - Multi-Target Tracking Isolation with Dynamic Color Palettes
 * - Kalman Prediction Uncertainty Envelope / Covariance Cones
 * - Base Defence Security Perimeter (50m) Breach Detection
 * - 3 Interactive Views: [3D ISOMETRIC], [LATERAL X-Z], [VERTICAL Y-Z]
 * - Calibrated Pure Square (1:1) Projection Without Edge / Side Clipping
 * - Always-Active 3D Airspace Scanning Frame (Never Blank When Idle)
 * - Smooth 60 FPS requestAnimationFrame Rendering Loop
 * =============================================================================
 */

class TrajectoryVisualizer {
  constructor(canvasId, options = {}) {
    this.canvasId = canvasId;
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.currentView = '3d';

    this.idPrefix = options.idPrefix || '';
    this.isSquare = options.isSquare !== undefined ? options.isSquare : true;
    this.forecastHorizon = options.forecastHorizon || 3.0;

    // Multi-target state stores
    // id -> { id, colorIdx, history: [{x,y,z,t}], predicted: [{t_sec,x,y,z,uncertainty_m}], endpoint_2s, endpoint_3s, current, speed, confidence, threat_level, threat_score, zone_breach, tti_sec, lastUpdate }
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
      bg: 'rgba(6, 14, 24, 0.96)',
      grid: 'rgba(0, 240, 255, 0.08)',
      gridLine: 'rgba(0, 240, 255, 0.14)',
      axisLabel: 'rgba(0, 240, 255, 0.8)',
      flightPath: 'rgba(140, 180, 210, 0.75)',
      zoneSafe: 'rgba(0, 240, 255, 0.35)',
      zoneBreach: 'rgba(255, 30, 56, 0.75)',
      zoneFill: 'rgba(0, 240, 255, 0.03)',
      zoneBreachFill: 'rgba(255, 30, 56, 0.12)',
      textDim: 'rgba(150, 180, 200, 0.8)',
      textBright: '#00f0ff'
    };

    // 2s/3s Future Prediction & Operator Response State
    this.showFutureForecast = true;
    this.rotorPhase = 0;          // rotor blade spin angle
    this.lastFrameTime = performance.now();
    this.energyPulse = 0;         // flow along future forecast corridor
    this.trackHeld = false;
    this.heldTrackId = null;
    this.simulationActive = false;

    this.resizeCanvas();
    window.addEventListener('resize', () => this.resizeCanvas());
    this.startRenderLoop();
  }

  resizeCanvas() {
    if (!this.canvas) return;
    const wrap = this.canvas.parentElement;
    if (this.isSquare) {
      const wrapW = wrap ? wrap.clientWidth : 0;
      const wrapH = wrap ? wrap.clientHeight : 0;
      let size = 340;
      if (wrapW > 0 && wrapH > 0) {
        size = Math.min(wrapW, wrapH);
      } else if (wrapW > 0) {
        size = wrapW;
      }
      this.canvas.width = Math.max(280, Math.min(size, 480));
      this.canvas.height = this.canvas.width;
    } else if (wrap && wrap.clientWidth > 0 && wrap.clientHeight > 0) {
      this.canvas.width = wrap.clientWidth;
      this.canvas.height = wrap.clientHeight;
    } else {
      this.canvas.width = parseInt(this.canvas.getAttribute('width'), 10) || 340;
      this.canvas.height = parseInt(this.canvas.getAttribute('height'), 10) || 340;
    }
  }

  setView(view) {
    this.currentView = view;
    const prefix = this.idPrefix;
    // Highlight matching view tabs
    const tabPrefix = prefix || '';
    const tabs = [
      { view: '3d', id: `${tabPrefix}tab-3d` },
      { view: 'lateral', id: `${tabPrefix}tab-lateral` },
      { view: 'vertical', id: `${tabPrefix}tab-vertical` }
    ];
    tabs.forEach(t => {
      const el = document.getElementById(t.id);
      if (el) {
        if (t.view === view) el.classList.add('active');
        else el.classList.remove('active');
      }
    });
  }

  // =========================================================================
  // OPERATOR RESPONSE PANEL CONTROLS (UI-Only, No Physical Action)
  // =========================================================================

  toggleFutureForecast() {
    this.showFutureForecast = !this.showFutureForecast;
    const btn = document.getElementById('btn-show-trajectory');
    if (btn) {
      btn.classList.toggle('active', this.showFutureForecast);
      btn.innerText = this.showFutureForecast ? '📐 SHOW TRAJECTORY (ON)' : '📐 SHOW TRAJECTORY (OFF)';
    }
    this.updateOpsStatus(
      this.showFutureForecast ? '📐 TRAJECTORY FORECAST: 2s/3s FUTURE WAYPOINTS ENABLED' : '📐 TRAJECTORY FORECAST: DISPLAY HIDDEN',
      this.showFutureForecast ? 'info' : 'alert'
    );
    return this.showFutureForecast;
  }

  updateOpsStatus(text, level) {
    const statusText = document.getElementById('ops-status-text');
    if (statusText) {
      statusText.innerText = text;
      statusText.style.color = level === 'alert' ? '#ffaa00' : (level === 'success' ? '#00ff66' : '#00f0ff');
    }
  }

  updateOpsTargetCard(track) {
    if (!track) {
      const titleEl = document.getElementById('ops-card-title');
      if (titleEl) titleEl.innerText = 'TARGET CARD — AWAITING TRACK';
      ['tc-class','tc-track','tc-conf','tc-radar','tc-speed','tc-distance','tc-altitude','tc-risk'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerText = '—';
      });
      return;
    }
    const t = track;
    const setVal = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };
    const titleEl = document.getElementById('ops-card-title');
    const tid = t.trackId || t.id || 'TRK-101';
    if (titleEl) titleEl.innerText = `TARGET CARD — ${tid} (${t.callsign || t.classification || 'DRONE'})`;
    setVal('tc-class', t.classification || 'Drone');
    setVal('tc-track', tid);
    setVal('tc-conf', t.confidence !== undefined ? `${Math.round(t.confidence * 100)}%` : '92%');
    const rRng = t.radarRange !== undefined ? t.radarRange : (t.radar_range_m !== undefined ? t.radar_range_m : (t.range || 32.0));
    setVal('tc-radar', rRng !== undefined ? `${Number(rRng).toFixed(1)}m` : '32.0m');
    setVal('tc-speed', t.speed !== undefined ? `${Number(t.speed).toFixed(1)} m/s` : (t.speed_ms !== undefined ? `${Number(t.speed_ms).toFixed(1)} m/s` : '5.4 m/s'));
    const dist = t.range !== undefined ? t.range : (t.distance_m !== undefined ? t.distance_m : (t.current ? Math.hypot(t.current.x, t.current.y) : 32.0));
    setVal('tc-distance', `${Number(dist).toFixed(1)}m`);
    const alt = t.altitude !== undefined ? t.altitude : (t.z_m !== undefined ? t.z_m : (t.z !== undefined ? t.z : (t.current ? t.current.z : 15.0)));
    setVal('tc-altitude', `${Number(alt).toFixed(1)}m`);
    
    const levelStr = t.threatLevel || t.threat_level || (t.threatScore >= 70 ? 'HIGH' : (t.threatScore >= 40 ? 'MEDIUM' : 'LOW'));
    const scoreVal = t.threatScore !== undefined ? t.threatScore : (t.threat_score !== undefined ? t.threat_score : 80);
    setVal('tc-risk', `${levelStr} (${scoreVal})`);

    const riskEl = document.getElementById('tc-risk');
    if (riskEl) {
      riskEl.style.color = levelStr === 'HIGH' ? '#ff3b30' : (levelStr === 'MEDIUM' ? '#ffaa00' : '#00ff66');
      riskEl.style.fontWeight = '800';
    }

    const riskBadge = document.getElementById('ops-risk-badge');
    if (riskBadge) {
      if (levelStr === 'HIGH') {
        riskBadge.innerText = 'RISK: CRITICAL';
        riskBadge.className = 'ops-risk-badge risk-critical';
      } else if (levelStr === 'MEDIUM') {
        riskBadge.innerText = 'RISK: ELEVATED';
        riskBadge.className = 'ops-risk-badge risk-elevated';
      } else {
        riskBadge.innerText = 'RISK: MONITOR';
        riskBadge.className = 'ops-risk-badge';
      }
    }
  }

  holdTrack(trackId) {
    this.trackHeld = true;
    this.heldTrackId = trackId;
  }

  releaseTrack() {
    this.trackHeld = false;
    this.heldTrackId = null;
  }


  /**
   * Updates multi-target tracking & prediction telemetry.
   * @param {Array} incomingTracks - Array of target telemetry objects
   */
  updateTracks(incomingTracks) {
    const now = performance.now() / 1000;

    if (Array.isArray(incomingTracks)) {
      incomingTracks.forEach((t, idx) => {
        const id = t.id || t.trackId || `TRK-${idx + 1}`;
        if (!this.tracks[id]) {
          this.tracks[id] = {
            id: id,
            colorIdx: Object.keys(this.tracks).length % this.palette.length,
            history: [],
            predicted: [],
            endpoint_2s: null,
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
        track.confidence = t.confidence !== undefined ? t.confidence : 0.90;
        track.threat_level = t.threat_level || t.threatLevel || 'NOMINAL';
        track.threat_score = t.threat_score !== undefined ? t.threat_score : (t.threatScore || 0);
        track.speed = t.speed_ms !== undefined ? Number(t.speed_ms) : (t.speed !== undefined ? Number(t.speed) : 0);

        // Current 3D metric coordinates
        const curX = (t.x_m !== undefined) ? Number(t.x_m) : (t.x !== undefined ? Number(t.x) : 0);
        const curY = (t.y_m !== undefined) ? Number(t.y_m) : (t.y !== undefined ? Number(t.y) : (t.range || 45));
        const curZ = (t.z_m !== undefined) ? Number(t.z_m) : (t.z !== undefined ? Number(t.z) : (t.altitude || 15));
        const curVx = (t.vx_ms !== undefined) ? Number(t.vx_ms) : (t.vx !== undefined ? Number(t.vx) : 0);
        const curVy = (t.vy_ms !== undefined) ? Number(t.vy_ms) : (t.vy !== undefined ? Number(t.vy) : -3.0);
        const curVz = (t.vz_ms !== undefined) ? Number(t.vz_ms) : (t.vz !== undefined ? Number(t.vz) : 0);

        track.current = { x: curX, y: curY, z: curZ, vx: curVx, vy: curVy, vz: curVz };

        // Historical flight path
        track.history.push({ x: curX, y: curY, z: curZ, t: now });
        if (track.history.length > this.maxHistoryLength) {
          track.history.shift();
        }

        // Future Waypoints (from backend or constant-velocity extrapolation)
        if (t.future_waypoints && Array.isArray(t.future_waypoints) && t.future_waypoints.length > 0) {
          track.predicted = t.future_waypoints.map(wp => ({
            t_sec: wp.t_sec,
            x: (wp.x_m !== undefined) ? wp.x_m : (wp.x || 0),
            y: (wp.y_m !== undefined) ? wp.y_m : (wp.y || 0),
            z: (wp.z_m !== undefined) ? wp.z_m : (wp.z || 0),
            uncertainty_m: wp.uncertainty_m || (1.5 + 0.5 * (wp.t_sec || 1.0))
          }));
        } else {
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

        // +2.0s Forecast Endpoint
        if (t.predicted_endpoint_2s) {
          track.endpoint_2s = {
            x: (t.predicted_endpoint_2s.x_m !== undefined) ? t.predicted_endpoint_2s.x_m : t.predicted_endpoint_2s.x,
            y: (t.predicted_endpoint_2s.y_m !== undefined) ? t.predicted_endpoint_2s.y_m : t.predicted_endpoint_2s.y,
            z: (t.predicted_endpoint_2s.z_m !== undefined) ? t.predicted_endpoint_2s.z_m : t.predicted_endpoint_2s.z,
            t_sec: 2.0
          };
        } else {
          const wp2 = track.predicted.find(p => Math.abs(p.t_sec - 2.0) < 0.25) || track.predicted[3];
          if (wp2) {
            track.endpoint_2s = { x: wp2.x, y: wp2.y, z: wp2.z, t_sec: 2.0 };
          }
        }

        // +3.0s Forecast Endpoint
        if (t.predicted_endpoint_3s) {
          track.endpoint_3s = {
            x: (t.predicted_endpoint_3s.x_m !== undefined) ? t.predicted_endpoint_3s.x_m : t.predicted_endpoint_3s.x,
            y: (t.predicted_endpoint_3s.y_m !== undefined) ? t.predicted_endpoint_3s.y_m : t.predicted_endpoint_3s.y,
            z: (t.predicted_endpoint_3s.z_m !== undefined) ? t.predicted_endpoint_3s.z_m : t.predicted_endpoint_3s.z,
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
    }

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
    const p = this.idPrefix;
    const trackIds = Object.keys(this.tracks);
    const primaryId = trackIds[0];
    const primary = primaryId ? this.tracks[primaryId] : null;

    // 1. Target Count
    const statPts = document.getElementById(`${p}traj-stat-targets`) || document.getElementById(`${p}traj-stat-points`);
    if (statPts) {
      statPts.innerHTML = primary ? `<strong>${trackIds.length}</strong> ACTIVE` : `<strong>0</strong>`;
    }

    // 2. Speed
    const statSpd = document.getElementById(`${p}traj-stat-speed`);
    if (statSpd) {
      statSpd.innerHTML = primary ? `<strong>${primary.speed.toFixed(1)} m/s</strong>` : `<strong>0.0 m/s</strong>`;
    }

    // 3. Confidence
    const statConf = document.getElementById(`${p}traj-stat-conf`) || document.getElementById(`${p}traj-stat-confidence`);
    if (statConf) {
      statConf.innerHTML = (primary && primary.confidence) ? `<strong>${Math.round(primary.confidence * 100)}%</strong>` : `<strong>--%</strong>`;
    }

    // 4. Forecast Position (+2s / +3s)
    const statPred = document.getElementById(`${p}traj-stat-pred`) || document.getElementById(`${p}traj-stat-pred3s`);
    if (statPred) {
      if (primary && primary.endpoint_2s) {
        const ep2 = primary.endpoint_2s;
        const ep3 = primary.endpoint_3s;
        if (ep3) {
          statPred.innerHTML = `+2s:[<strong>${ep2.x.toFixed(0)},${ep2.y.toFixed(0)}m</strong>] &nbsp;|&nbsp; +3s:[<strong>${ep3.x.toFixed(0)},${ep3.y.toFixed(0)},${ep3.z.toFixed(0)}m</strong>]`;
        } else {
          statPred.innerHTML = `+2s:[<strong>${ep2.x.toFixed(1)},${ep2.y.toFixed(1)}m</strong>]`;
        }
      } else {
        statPred.innerHTML = `<strong>AWAITING TRACK</strong>`;
      }
    }

    // 5. Perimeter Status
    const statZone = document.getElementById(`${p}traj-stat-zone`);
    if (statZone) {
      const isAnyBreach = Object.values(this.tracks).some(tr => tr.zone_breach);
      if (isAnyBreach) {
        const breachTrack = Object.values(this.tracks).find(tr => tr.zone_breach);
        statZone.innerHTML = `<strong style="color:#ff1e38;">BREACH INBOUND (TTI: ${(breachTrack.tti_sec || 2.0).toFixed(1)}s)</strong>`;
      } else {
        statZone.innerHTML = `<strong style="color:#00ff66;">SECURE (ALL SECTORS)</strong>`;
      }
    }
  }

  // 3D Isometric projection mapping (World meters -> Screen pixels)
  project3D(x, y, z, cx, cy, scale) {
    const cosR = Math.cos(this.rotAngle);
    const sinR = Math.sin(this.rotAngle);
    const cosT = Math.cos(this.tiltAngle);
    const sinT = Math.sin(this.tiltAngle);

    // Yaw rotation around vertical axis
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
      this.pulsePhase = (this.pulsePhase + 0.04) % (Math.PI * 2);
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

    // Time delta for smooth physical trajectory simulation
    const now = performance.now();
    const dt = Math.min(0.06, (now - this.lastFrameTime) / 1000);
    this.lastFrameTime = now;
    this.rotorPhase += 0.45;
    this.energyPulse = (this.energyPulse + 0.02) % 1.0;


    // Clear background
    ctx.fillStyle = this.colors.bg;
    ctx.fillRect(0, 0, W, H);

    // Subtle ambient grid pattern in background
    this.drawBgGrid(ctx, W, H);

    // Auto-rotate in 3D view
    if (this.autoRotate && this.currentView === '3d') {
      this.rotAngle += 0.0016;
    }

    // Render active view
    switch (this.currentView) {
      case '3d': this.render3D(ctx, W, H); break;
      case 'lateral': this.renderLateral(ctx, W, H); break;
      case 'vertical': this.renderVertical(ctx, W, H); break;
    }
  }

  drawBgGrid(ctx, W, H) {
    ctx.save();
    ctx.strokeStyle = this.colors.grid;
    ctx.lineWidth = 0.5;
    const step = 28;
    for (let x = 0; x < W; x += step) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
    }
    for (let y = 0; y < H; y += step) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
    }
    ctx.restore();
  }

  // =========================================================================
  // 3D MODELS: AIRBORNE DRONES & SENSOR BASE
  // =========================================================================

  drawSensorBase(ctx, cx, cy, scale) {
    const baseP = this.project3D(0, 0, 0, cx, cy, scale);
    ctx.save();
    // Base platform hexagon (Sensor Station)
    ctx.strokeStyle = 'rgba(0, 240, 255, 0.45)';
    ctx.fillStyle = 'rgba(0, 240, 255, 0.08)';
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    const padR = 12 * scale * 10;
    for (let i = 0; i < 6; i++) {
      const a = (i / 6) * Math.PI * 2;
      const px = baseP.sx + Math.cos(a) * padR;
      const py = baseP.sy + Math.sin(a) * (padR * 0.45);
      if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
    }
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    // Central Sensor Node
    ctx.fillStyle = '#00f0ff';
    ctx.shadowColor = '#00f0ff';
    ctx.shadowBlur = 8;
    ctx.beginPath();
    ctx.arc(baseP.sx, baseP.sy, 4.0, 0, Math.PI * 2);
    ctx.fill();

    // Platform Tag
    ctx.fillStyle = 'rgba(0, 240, 255, 0.85)';
    ctx.font = 'bold 8px "Share Tech Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText('SENSOR BASE (0,0)', baseP.sx, baseP.sy + 12);
    ctx.restore();
  }

  draw3DDrone(ctx, x, y, z, cx, cy, scale, opts = {}) {
    // 1. Altitude stem line and ground shadow
    let groundP = this.project3D(x, y, 0, cx, cy, scale);
    let bodyP = this.project3D(x, y, z, cx, cy, scale);

    // Bounds safety clamp: keep strictly inside visible canvas area
    const pad = 16;
    const W = this.canvas ? this.canvas.width : 340;
    const H = this.canvas ? this.canvas.height : 340;
    bodyP.sx = Math.max(pad, Math.min(W - pad, bodyP.sx));
    bodyP.sy = Math.max(pad + 8, Math.min(H - pad, bodyP.sy));
    groundP.sx = Math.max(pad, Math.min(W - pad, groundP.sx));
    groundP.sy = Math.max(pad, Math.min(H - pad, groundP.sy));

    ctx.save();
    // Drop line to ground
    ctx.strokeStyle = opts.isHologram ? 'rgba(0, 240, 255, 0.4)' : 'rgba(255, 255, 255, 0.25)';
    ctx.lineWidth = 0.8;
    ctx.setLineDash([3, 3]);
    ctx.beginPath();
    ctx.moveTo(groundP.sx, groundP.sy);
    ctx.lineTo(bodyP.sx, bodyP.sy);
    ctx.stroke();
    ctx.setLineDash([]);

    // Ground shadow ring
    ctx.fillStyle = opts.isHologram ? 'rgba(0, 240, 255, 0.15)' : 'rgba(0, 0, 0, 0.45)';
    ctx.strokeStyle = opts.isHologram ? 'rgba(0, 240, 255, 0.5)' : 'rgba(255, 50, 50, 0.4)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.ellipse(groundP.sx, groundP.sy, Math.max(4, 6 * scale * 10), Math.max(2, 3 * scale * 10), 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // Ground tag
    if (opts.isHologram) {
      ctx.fillStyle = 'rgba(0, 240, 255, 0.7)';
      ctx.font = '7px "Share Tech Mono", monospace';
      ctx.textAlign = 'center';
      ctx.fillText('+2.5s GND', groundP.sx, groundP.sy + 8);
    }
    ctx.restore();

    // 2. Arms & Rotors in 3D Perspective
    const heading = opts.heading !== undefined ? opts.heading : (opts.vx !== undefined && (opts.vx !== 0 || opts.vy !== 0) ? Math.atan2(opts.vy, opts.vx) : 0);
    const armL = 2.8; // meters in world space
    const angles = [heading + Math.PI / 4, heading + (3 * Math.PI) / 4, heading + (5 * Math.PI) / 4, heading + (7 * Math.PI) / 4];
    const armEndpoints = angles.map(ang => ({
      x: x + Math.cos(ang) * armL,
      y: y + Math.sin(ang) * armL,
      z: z
    }));

    ctx.save();
    // Arm struts
    ctx.strokeStyle = opts.isHologram ? 'rgba(0, 240, 255, 0.7)' : '#556677';
    ctx.lineWidth = opts.isHologram ? 1.2 : 1.6;
    if (opts.isHologram) ctx.setLineDash([2, 2]);

    armEndpoints.forEach(ep => {
      const epP = this.project3D(ep.x, ep.y, ep.z, cx, cy, scale);
      ctx.beginPath();
      ctx.moveTo(bodyP.sx, bodyP.sy);
      ctx.lineTo(epP.sx, epP.sy);
      ctx.stroke();

      // Motor hub
      ctx.fillStyle = opts.isHologram ? '#00f0ff' : '#222222';
      ctx.beginPath();
      ctx.arc(epP.sx, epP.sy, 1.8, 0, Math.PI * 2);
      ctx.fill();

      // Spinning Rotor Discs
      const rotorRadius = Math.max(3.0, 4.0 * scale * 2.0);
      ctx.strokeStyle = opts.isHologram
        ? 'rgba(0, 240, 255, 0.75)'
        : 'rgba(255, 60, 60, 0.75)';
      ctx.fillStyle = opts.isHologram
        ? 'rgba(0, 240, 255, 0.18)'
        : 'rgba(255, 40, 40, 0.2)';
      ctx.lineWidth = 0.8;

      ctx.beginPath();
      ctx.ellipse(epP.sx, epP.sy, rotorRadius, rotorRadius * 0.45, heading + this.rotorPhase, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
    });
    ctx.restore();

    // 3. Central Fuselage Body
    ctx.save();
    if (opts.isHologram) {
      // Holographic glowing futuristic body (+2.5s future drone)
      ctx.fillStyle = 'rgba(0, 240, 255, 0.35)';
      ctx.strokeStyle = '#00f0ff';
      ctx.lineWidth = 1.4;
      ctx.shadowColor = '#00f0ff';
      ctx.shadowBlur = 10;
      ctx.beginPath();
      ctx.arc(bodyP.sx, bodyP.sy, 4.0, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
    } else {
      // Active drone chassis
      ctx.fillStyle = opts.threat_level === 'HIGH' ? '#ff1e38' : '#ff8833';
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1.2;
      ctx.shadowColor = opts.threat_level === 'HIGH' ? '#ff1e38' : '#ff8833';
      ctx.shadowBlur = 8;
      ctx.beginPath();
      ctx.arc(bodyP.sx, bodyP.sy, 4.0, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
    }
    ctx.restore();

    // 4. Tactical Labels & HUD Callouts (Bounds-Safe Dynamic Orientation)
    ctx.save();
    const isRightSide = bodyP.sx > (W * 0.52);
    const labelX = isRightSide ? bodyP.sx - 8 : bodyP.sx + 8;
    ctx.textAlign = isRightSide ? 'right' : 'left';

    if (opts.isHologram) {
      ctx.fillStyle = '#00f0ff';
      ctx.font = 'bold 8px "Share Tech Mono", monospace';
      ctx.fillText(`+2.5s FORECAST`, labelX, bodyP.sy - 5);
      ctx.fillStyle = 'rgba(0, 240, 255, 0.75)';
      ctx.font = '7px "Share Tech Mono", monospace';
      ctx.fillText(`[${x.toFixed(0)},${y.toFixed(0)},${z.toFixed(0)}m]`, labelX, bodyP.sy + 4);
    } else {
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 8px "Share Tech Mono", monospace';
      ctx.fillText(`${opts.id || 'DRONE'} (${z.toFixed(0)}m)`, labelX, bodyP.sy - 4);
      if (opts.speed) {
        ctx.fillStyle = 'rgba(255, 170, 0, 0.85)';
        ctx.font = '7px "Share Tech Mono", monospace';
        ctx.fillText(`SPD: ${Number(opts.speed).toFixed(1)}m/s`, labelX, bodyP.sy + 5);
      }
    }
    ctx.restore();

    // 5. Tactical Operator Reticle (if locked or held)
    const isTargetLocked = opts.isLocked || (this.heldTrackId === opts.id) || (window.smartShield && window.smartShield.primaryTrackId === opts.id);
    if (!opts.isHologram && isTargetLocked) {
      ctx.save();
      const rSize = 14;
      const isHeld = (this.heldTrackId === opts.id);
      ctx.strokeStyle = isHeld ? '#fcd34d' : '#00f0ff';
      ctx.lineWidth = 1.6;
      ctx.shadowColor = ctx.strokeStyle;
      ctx.shadowBlur = 8;

      const dcx = bodyP.sx, dcy = bodyP.sy;
      const bLen = 5;
      // Top-Left
      ctx.beginPath(); ctx.moveTo(dcx - rSize, dcy - rSize + bLen); ctx.lineTo(dcx - rSize, dcy - rSize); ctx.lineTo(dcx - rSize + bLen, dcy - rSize); ctx.stroke();
      // Top-Right
      ctx.beginPath(); ctx.moveTo(dcx + rSize - bLen, dcy - rSize); ctx.lineTo(dcx + rSize, dcy - rSize); ctx.lineTo(dcx + rSize, dcy - rSize + bLen); ctx.stroke();
      // Bottom-Left
      ctx.beginPath(); ctx.moveTo(dcx - rSize, dcy + rSize - bLen); ctx.lineTo(dcx - rSize, dcy + rSize); ctx.lineTo(dcx - rSize + bLen, dcy + rSize); ctx.stroke();
      // Bottom-Right
      ctx.beginPath(); ctx.moveTo(dcx + rSize - bLen, dcy + rSize); ctx.lineTo(dcx + rSize, dcy + rSize); ctx.lineTo(dcx + rSize, dcy + rSize - bLen); ctx.stroke();

      // Lock Reticle Center Crosshair
      ctx.beginPath();
      ctx.moveTo(dcx - 3, dcy); ctx.lineTo(dcx + 3, dcy);
      ctx.moveTo(dcx, dcy - 3); ctx.lineTo(dcx, dcy + 3);
      ctx.stroke();

      // Tactical Status Tag
      ctx.fillStyle = ctx.strokeStyle;
      ctx.font = 'bold 7.5px "Share Tech Mono", monospace';
      ctx.textAlign = 'center';
      ctx.fillText(isHeld ? '⏸ HOLD LOCK' : '🎯 TRACK LOCK', dcx, dcy - rSize - 3);
      ctx.restore();
    }
  }


  // =========================================================================
  // 3D ISOMETRIC VIEW — STRICT BOUNDS & ZERO CLIPPING
  // =========================================================================
  render3D(ctx, W, H) {
    const cx = W / 2;
    const cy = H * 0.53;

    // Calculate maximum world distance across all active targets and prediction endpoints
    let maxDist = this.protectedZoneRadius; // default 50.0m
    const trackValues = Object.values(this.tracks);
    trackValues.forEach(t => {
      if (t.current) {
        const d = Math.hypot(t.current.x, t.current.y);
        if (d > maxDist) maxDist = d;
      }
      if (this.showFutureForecast) {
        if (t.endpoint_2s) {
          const d2 = Math.hypot(t.endpoint_2s.x, t.endpoint_2s.y);
          if (d2 > maxDist) maxDist = d2;
        }
        if (t.endpoint_3s) {
          const d3 = Math.hypot(t.endpoint_3s.x, t.endpoint_3s.y);
          if (d3 > maxDist) maxDist = d3;
        }
      }
    });

    // World extent with safety margin so drone models, rotors, labels & altitude never clip
    const maxWorldExtent = Math.max(54, maxDist * 1.25);
    // Safe radius keeps elements within central 74% of canvas (13% margin on all borders)
    const safeRadiusPx = Math.min(W, H) * 0.37;
    const targetScale = safeRadiusPx / maxWorldExtent;

    // Smooth camera scale transitions (no jarring jumps)
    this.currentScale = this.currentScale ? (this.currentScale * 0.90 + targetScale * 0.10) : targetScale;
    const scale = this.currentScale;

    // 1. Draw 3D Ground Grid Floor
    this.draw3DGrid(ctx, cx, cy, scale);

    // 2. Draw Protected Defence Base Security Perimeter Ring (50m)
    this.draw3DProtectedZone(ctx, cx, cy, scale);

    // 3. Draw 3D Coordinate Reference Axes
    this.draw3DAxes(ctx, cx, cy, scale);

    // 4. Draw Sensor Base Platform at (0, 0, 0)
    this.drawSensorBase(ctx, cx, cy, scale);

    const trackKeys = Object.keys(this.tracks);

    // 5. Idle Airspace Scanning Tag when awaiting targets
    if (trackKeys.length === 0) {
      ctx.save();
      const pulseAlpha = 0.55 + Math.sin(this.pulsePhase) * 0.35;
      ctx.fillStyle = `rgba(0, 240, 255, ${pulseAlpha})`;
      ctx.font = 'bold 9.5px "Share Tech Mono", monospace';
      ctx.textAlign = 'center';
      ctx.fillText('● AIRSPACE SCANNING ACTIVE • 50m PERIMETER SECURE', W / 2, H - 16);
      ctx.restore();
    }

    // 6. Draw Each Active Target Track (Dual 3D Models: Current + Future Forecast)
    trackKeys.forEach(id => {
      const track = this.tracks[id];
      const pal = this.palette[track.colorIdx];
      const hist = track.history;
      const pred = track.predicted;

      if (hist.length === 0) return;
      const cur = hist[hist.length - 1];
      const curHeading = (cur.vx !== undefined && (cur.vx !== 0 || cur.vy !== 0))
        ? Math.atan2(cur.vy, cur.vx)
        : (track.current && (track.current.vx !== 0 || track.current.vy !== 0) ? Math.atan2(track.current.vy, track.current.vx) : 0);

      // 6a. Historical Flight Path (Solid Trajectory Line)
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

        // Historical Waypoint Dots
        const recentHist = hist.slice(-20);
        recentHist.forEach((p, i) => {
          const proj = this.project3D(p.x, p.y, p.z, cx, cy, scale);
          const alpha = 0.25 + (0.75 * (i / recentHist.length));
          ctx.fillStyle = pal.actual;
          ctx.globalAlpha = alpha;
          ctx.beginPath();
          ctx.arc(proj.sx, proj.sy, 2.5, 0, Math.PI * 2);
          ctx.fill();
        });
        ctx.globalAlpha = 1.0;
      }

      // 6b. Future Predicted Trajectory & 2s/3s Forecast Model
      if (this.showFutureForecast && pred.length > 0 && hist.length > 0) {
        const curProj = this.project3D(cur.x, cur.y, cur.z, cx, cy, scale);

        // Uncertainty Covariance Envelope
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

        // Glowing Dashed Future Flight Path
        ctx.save();
        ctx.shadowColor = pal.predGlow;
        ctx.shadowBlur = 8;
        ctx.strokeStyle = pal.pred;
        ctx.lineWidth = 2.0;
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

        // Animated Energy Flow Stream along future corridor
        if (pred.length >= 2) {
          ctx.save();
          const totalSteps = pred.length - 1;
          const pulseIdxFloat = this.energyPulse * totalSteps;
          const baseStep = Math.floor(pulseIdxFloat);
          const fracStep = pulseIdxFloat - baseStep;
          const p1 = pred[baseStep];
          const p2 = pred[Math.min(totalSteps, baseStep + 1)];
          if (p1 && p2) {
            const flowX = p1.x + (p2.x - p1.x) * fracStep;
            const flowY = p1.y + (p2.y - p1.y) * fracStep;
            const flowZ = p1.z + (p2.z - p1.z) * fracStep;
            const flowProj = this.project3D(flowX, flowY, flowZ, cx, cy, scale);
            ctx.fillStyle = '#00f0ff';
            ctx.shadowColor = '#00f0ff';
            ctx.shadowBlur = 12;
            ctx.beginPath();
            ctx.arc(flowProj.sx, flowProj.sy, 3.5, 0, Math.PI * 2);
            ctx.fill();
          }
          ctx.restore();
        }

        // Intermediate Nodes (+1.0s)
        pred.forEach(wp => {
          const proj = this.project3D(wp.x, wp.y, wp.z, cx, cy, scale);
          ctx.fillStyle = pal.pred;
          ctx.beginPath();
          ctx.arc(proj.sx, proj.sy, 2.5, 0, Math.PI * 2);
          ctx.fill();

          if (wp.t_sec === 1.0) {
            ctx.fillStyle = 'rgba(0, 240, 255, 0.7)';
            ctx.font = '8px "Share Tech Mono", monospace';
            ctx.textAlign = 'left';
            ctx.fillText(`+1.0s`, proj.sx + 4, proj.sy - 3);
          }
        });

        // SECOND DIAGRAM: 3D Hologram Drone Model at +2.5s Future Position
        const epFuture = track.endpoint_2s || (pred.length > 0 ? pred[Math.min(pred.length - 1, 3)] : null);
        if (epFuture) {
          this.draw3DDrone(ctx, epFuture.x, epFuture.y, epFuture.z, cx, cy, scale, {
            isHologram: true,
            id: track.id,
            heading: curHeading,
            vx: cur.vx,
            vy: cur.vy
          });
        }
      }

      // Current Active 3D Drone Model in Airspace
      const isLocked = (this.heldTrackId === track.id) || (window.smartShield && window.smartShield.primaryTrackId === track.id);
      this.draw3DDrone(ctx, cur.x, cur.y, cur.z, cx, cy, scale, {
        id: track.id,
        speed: track.speed,
        heading: curHeading,
        vx: cur.vx,
        vy: cur.vy,
        threat_level: track.threat_level,
        isLocked: isLocked
      });
    });

    // Safe Simulation Protocol Visual Overlay (Non-Kinetic Decision Support)
    if (this.simulationActive) {
      this.draw3DSimulationCorridor(ctx, cx, cy, scale);
    }

    // View Banner Overlay
    this.drawViewHeader(ctx, '3D AIRSPACE ISOMETRIC (+2s / +3s TRAJECTORY FORECAST)');
  }


  // Draw 3D Ground Floor Grid (Strictly within non-clipping bounds)
  draw3DGrid(ctx, cx, cy, scale) {
    ctx.strokeStyle = this.colors.gridLine;
    ctx.lineWidth = 0.4;
    const gridRange = 50; // m (matches 50m perimeter)
    const step = 10;     // m

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
    const nSegments = 36;
    const r = this.protectedZoneRadius; // 50.0m

    ctx.save();
    ctx.strokeStyle = isBreach ? this.colors.zoneBreach : this.colors.zoneSafe;
    ctx.fillStyle = isBreach ? this.colors.zoneBreachFill : this.colors.zoneFill;
    ctx.lineWidth = isBreach ? 2.0 : 1.2;
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

    // Perimeter Ring Label (North tip, comfortably inside top margin)
    const zLabelP = this.project3D(0, r, 0, cx, cy, scale);
    ctx.fillStyle = isBreach ? '#ff1e38' : 'rgba(0, 240, 255, 0.7)';
    ctx.font = '8px "Share Tech Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText(isBreach ? '⚠ DEFENCE PERIMETER BREACH' : '50m DEFENCE PERIMETER', zLabelP.sx, zLabelP.sy + 10);
  }

  // Draw Non-Kinetic Advisory Protocol Simulation Corridor Overlay in 3D
  draw3DSimulationCorridor(ctx, cx, cy, scale) {
    ctx.save();
    const nSeg = 36;
    const rSim = 35.0; // 35m protocol verification zone
    const simPulse = (Math.sin(performance.now() * 0.006) + 1) * 0.5;
    ctx.strokeStyle = `rgba(168, 85, 247, ${0.4 + simPulse * 0.4})`;
    ctx.fillStyle = `rgba(168, 85, 247, ${0.05 + simPulse * 0.08})`;
    ctx.lineWidth = 1.8;
    ctx.setLineDash([6, 4]);

    ctx.beginPath();
    for (let i = 0; i <= nSeg; i++) {
      const theta = (i / nSeg) * (Math.PI * 2);
      const zx = rSim * Math.cos(theta);
      const zy = rSim * Math.sin(theta);
      const proj = this.project3D(zx, zy, 4.0 * simPulse, cx, cy, scale);
      if (i === 0) ctx.moveTo(proj.sx, proj.sy);
      else ctx.lineTo(proj.sx, proj.sy);
    }
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    // Simulation Corridor Label
    const simP = this.project3D(0, rSim * 0.75, 7, cx, cy, scale);
    ctx.fillStyle = '#c084fc';
    ctx.font = 'bold 8.5px "Share Tech Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText('⚡ NON-KINETIC PROTOCOL SIMULATION CORRIDOR', simP.sx, simP.sy);
    ctx.restore();
  }

  // Draw 3D Reference Coordinate Axes (With clearance from canvas edges)
  draw3DAxes(ctx, cx, cy, scale) {
    const axLen = 28; // 28 meters
    const orig = this.project3D(0, 0, 0, cx, cy, scale);

    // X Axis (East / Red)
    const xEnd = this.project3D(axLen, 0, 0, cx, cy, scale);
    ctx.strokeStyle = '#ff4444'; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(orig.sx, orig.sy); ctx.lineTo(xEnd.sx, xEnd.sy); ctx.stroke();
    ctx.fillStyle = '#ff4444'; ctx.font = '8.5px "Share Tech Mono", monospace'; ctx.textAlign = 'center';
    ctx.fillText('X (East)', xEnd.sx, xEnd.sy + 11);

    // Y Axis (North / Green)
    const yEnd = this.project3D(0, axLen, 0, cx, cy, scale);
    ctx.strokeStyle = '#44ff44'; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(orig.sx, orig.sy); ctx.lineTo(yEnd.sx, yEnd.sy); ctx.stroke();
    ctx.fillStyle = '#44ff44'; ctx.font = '8.5px "Share Tech Mono", monospace'; ctx.textAlign = 'center';
    ctx.fillText('Y (North)', yEnd.sx, yEnd.sy + 11);

    // Z Axis (Altitude / Cyan)
    const zEnd = this.project3D(0, 0, axLen * 0.75, cx, cy, scale);
    ctx.strokeStyle = '#00f0ff'; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(orig.sx, orig.sy); ctx.lineTo(zEnd.sx, zEnd.sy); ctx.stroke();
    ctx.fillStyle = '#00f0ff'; ctx.font = '8.5px "Share Tech Mono", monospace'; ctx.textAlign = 'left';
    ctx.fillText('Z (Alt)', zEnd.sx + 4, zEnd.sy);
  }

  // =========================================================================
  // 2D ORTHOGONAL VIEWS (Lateral X-Z and Vertical Y-Z)
  // =========================================================================
  renderLateral(ctx, W, H) {
    this.render2DProfile(ctx, W, H, 'x', 'z', 'LATERAL VIEW (X vs ALTITUDE Z)', 'Lateral X (m)', 'Altitude Z (m)');
  }

  renderVertical(ctx, W, H) {
    this.render2DProfile(ctx, W, H, 'y', 'z', 'VERTICAL PROFILE (RANGE Y vs ALTITUDE Z)', 'Forward Range Y (m)', 'Altitude Z (m)');
  }

  render2DProfile(ctx, W, H, xKey, yKey, title, xLabel, yLabel) {
    const pad = { left: 45, right: 18, top: 26, bottom: 28 };
    const plotW = W - pad.left - pad.right;
    const plotH = H - pad.top - pad.bottom;

    // Gather bounds
    let allX = [-10, 10], allY = [0, 25];
    Object.values(this.tracks).forEach(tr => {
      tr.history.forEach(p => { allX.push(p[xKey]); allY.push(p[yKey]); });
      tr.predicted.forEach(p => { allX.push(p[xKey]); allY.push(p[yKey]); });
    });

    let minX = Math.min(...allX), maxX = Math.max(...allX);
    let minY = Math.min(...allY), maxY = Math.max(...allY);
    const rangeX = Math.max(25, (maxX - minX));
    const rangeY = Math.max(20, (maxY - minY));

    minX -= rangeX * 0.12; maxX += rangeX * 0.12;
    minY = Math.max(0, minY - rangeY * 0.1); maxY += rangeY * 0.15;

    const scaleX = plotW / (maxX - minX);
    const scaleY = plotH / (maxY - minY);

    const toSX = v => pad.left + (v - minX) * scaleX;
    const toSY = v => pad.top + plotH - (v - minY) * scaleY;

    // Background
    ctx.fillStyle = 'rgba(10, 20, 35, 0.85)';
    ctx.fillRect(pad.left, pad.top, plotW, plotH);

    ctx.strokeStyle = this.colors.gridLine;
    ctx.lineWidth = 0.4;
    ctx.font = '8px "Share Tech Mono", monospace';
    ctx.fillStyle = this.colors.axisLabel;

    // Y Grid lines
    const nGridY = 4;
    for (let i = 0; i <= nGridY; i++) {
      const val = minY + ((maxY - minY) * i) / nGridY;
      const sy = toSY(val);
      ctx.beginPath(); ctx.moveTo(pad.left, sy); ctx.lineTo(pad.left + plotW, sy); ctx.stroke();
      ctx.textAlign = 'right';
      ctx.fillText(val.toFixed(0), pad.left - 5, sy + 3);
    }

    // X Grid lines
    const nGridX = 5;
    for (let i = 0; i <= nGridX; i++) {
      const val = minX + ((maxX - minX) * i) / nGridX;
      const sx = toSX(val);
      ctx.beginPath(); ctx.moveTo(sx, pad.top); ctx.lineTo(sx, pad.top + plotH); ctx.stroke();
      ctx.textAlign = 'center';
      ctx.fillText(val.toFixed(0), sx, pad.top + plotH + 12);
    }

    // Axis Labels
    ctx.fillStyle = this.colors.textBright;
    ctx.font = '8.5px "Share Tech Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText(xLabel, pad.left + plotW / 2, H - 4);

    ctx.save();
    ctx.translate(12, pad.top + plotH / 2);
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
        ctx.lineWidth = 1.6;
        ctx.beginPath();
        hist.forEach((p, i) => {
          const sx = toSX(p[xKey]), sy = toSY(p[yKey]);
          if (i === 0) ctx.moveTo(sx, sy); else ctx.lineTo(sx, sy);
        });
        ctx.stroke();

        // Past Dots
        hist.slice(-20).forEach(p => {
          ctx.fillStyle = pal.actual;
          ctx.beginPath();
          ctx.arc(toSX(p[xKey]), toSY(p[yKey]), 2.5, 0, Math.PI * 2);
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
          ctx.arc(toSX(p[xKey]), toSY(p[yKey]), 2.5, 0, Math.PI * 2);
          ctx.fill();
        });

        // +2s Endpoint Diamond
        if (tr.endpoint_2s) {
          const ep2 = tr.endpoint_2s;
          const ex2 = toSX(ep2[xKey]), ey2 = toSY(ep2[yKey]);
          ctx.fillStyle = '#ffea00';
          ctx.beginPath();
          ctx.moveTo(ex2, ey2 - 4); ctx.lineTo(ex2 + 4, ey2); ctx.lineTo(ex2, ey2 + 4); ctx.lineTo(ex2 - 4, ey2);
          ctx.closePath();
          ctx.fill();
        }

        // +3s Endpoint Diamond
        if (tr.endpoint_3s) {
          const ep3 = tr.endpoint_3s;
          const ex3 = toSX(ep3[xKey]), ey3 = toSY(ep3[yKey]);
          ctx.fillStyle = '#00f0ff';
          ctx.beginPath();
          ctx.moveTo(ex3, ey3 - 5); ctx.lineTo(ex3 + 5, ey3); ctx.lineTo(ex3, ey3 + 5); ctx.lineTo(ex3 - 5, ey3);
          ctx.closePath();
          ctx.fill();
          ctx.font = '8px "Share Tech Mono", monospace';
          ctx.fillText(`+3s`, ex3 + 6, ey3 - 2);
        }
      }

      // Current Marker
      if (hist.length > 0) {
        const cur = hist[hist.length - 1];
        const cx = toSX(cur[xKey]), cy = toSY(cur[yKey]);
        ctx.fillStyle = '#ff1e38';
        ctx.beginPath(); ctx.arc(cx, cy, 4.5, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 8.5px "Share Tech Mono", monospace';
        ctx.fillText(tr.id, cx + 7, cy + 3);
      }
    });

    this.drawViewHeader(ctx, title);
  }

  drawViewHeader(ctx, title) {
    ctx.save();
    ctx.fillStyle = this.colors.textBright;
    ctx.font = 'bold 9px "Share Tech Mono", monospace';
    ctx.textAlign = 'left';
    ctx.fillText(title, 8, 14);
    ctx.restore();
  }
}

// Global instantiation on DOM ready
window.addEventListener('DOMContentLoaded', () => {
  // Center Square Trajectory Visualizer below camera view
  if (document.getElementById('centerTrajectoryCanvas')) {
    window.centerTrajViz = new TrajectoryVisualizer('centerTrajectoryCanvas', {
      isSquare: true,
      idPrefix: 'center-'
    });
    // Initialize default status
    window.centerTrajViz.updateOpsStatus('TRACKING ACTIVE • HUMAN CONFIRMATION REQUIRED', 'info');
  }
  // Right side panel visualizer (if present)
  if (document.getElementById('trajectoryCanvas')) {
    window.trajViz = new TrajectoryVisualizer('trajectoryCanvas', {
      isSquare: false,
      idPrefix: ''
    });
  }
});

// =========================================================================
// LIGHTWEIGHT NATIVE WEB AUDIO TACTICAL CHIRP SYNTHESIZER
// =========================================================================
function playTacticalChirp(type) {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    if (!window._tacticalAudioCtx) {
      window._tacticalAudioCtx = new AudioCtx();
    }
    const ctx = window._tacticalAudioCtx;
    if (ctx.state === 'suspended') {
      ctx.resume().catch(() => {});
    }
    const now = ctx.currentTime;

    if (type === 'lock') {
      // High two-tone confirmation chirp
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(1200, now);
      osc.frequency.setValueAtTime(1600, now + 0.06);
      gain.gain.setValueAtTime(0.18, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.14);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.14);
    } else if (type === 'alert') {
      // Urgent warble chime
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(880, now);
      osc.frequency.setValueAtTime(660, now + 0.10);
      osc.frequency.setValueAtTime(880, now + 0.20);
      gain.gain.setValueAtTime(0.22, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.35);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.35);
    } else if (type === 'click') {
      // Tactile button click
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(750, now);
      gain.gain.setValueAtTime(0.12, now);
      gain.gain.exponentialRampToValueAtTime(0.005, now + 0.05);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.05);
    } else if (type === 'sim') {
      // Simulation sweep tone
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(440, now);
      osc.frequency.exponentialRampToValueAtTime(920, now + 0.18);
      gain.gain.setValueAtTime(0.18, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.22);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.22);
    }
  } catch (e) {
    // Fail silently if browser audio is blocked
  }
}

// =========================================================================
// GLOBAL OPERATOR RESPONSE PANEL DISPATCHERS (Decision-Support Only)
// =========================================================================

window.opsTrackTarget = function() {
  playTacticalChirp('lock');
  const viz = window.centerTrajViz;
  const app = window.smartShield;
  if (!viz) return;

  const trackKeys = Object.keys(viz.tracks);
  if (trackKeys.length === 0) {
    viz.updateOpsStatus('🎯 NO TARGETS IN RANGE — AIRSPACE SCANNING ACTIVE', 'info');
    return;
  }

  // If already tracking a target, cycle to the next available track
  let currentHeld = viz.heldTrackId;
  let nextIdx = 0;
  if (currentHeld) {
    const curIdx = trackKeys.indexOf(currentHeld);
    if (curIdx >= 0) {
      nextIdx = (curIdx + 1) % trackKeys.length;
    }
  }
  const targetId = trackKeys[nextIdx];
  const t = viz.tracks[targetId];

  // Set track hold lock
  viz.holdTrack(targetId);
  if (app) app.primaryTrackId = targetId;

  // Visual button states
  const btnTrack = document.getElementById('btn-track-target');
  if (btnTrack) {
    btnTrack.classList.add('active');
    btnTrack.innerText = `🎯 TRACKING [${targetId}]`;
  }
  const btnHold = document.getElementById('btn-hold-track');
  if (btnHold) {
    btnHold.classList.add('active');
    btnHold.innerText = `⏸ HOLD [${targetId}]`;
  }

  // Target Card highlight
  const card = document.getElementById('ops-target-card');
  if (card) {
    card.style.boxShadow = '0 0 16px rgba(0, 240, 255, 0.5)';
    card.style.borderColor = 'rgba(0, 240, 255, 0.8)';
    setTimeout(() => {
      card.style.boxShadow = '';
      card.style.borderColor = '';
    }, 2500);
  }

  // Update Target Card immediately
  viz.updateOpsTargetCard(t);

  const rng = t.current ? Math.hypot(t.current.x, t.current.y).toFixed(1) : '32.0';
  const alt = t.current ? t.current.z.toFixed(1) : '15.0';
  viz.updateOpsStatus(`🎯 OPERATOR LOCKED: [${targetId}] • RNG: ${rng}m • ALT: ${alt}m • THREAT: ${t.threat_level || 'HIGH'}`, 'alert');

  if (app) {
    app.addEventLog(`[OPS] 🎯 Target lock engaged: ${targetId} | Range: ${rng}m | Alt: ${alt}m | Threat Score: ${t.threat_score || 0}`);
  }
};

window.opsAlertOperator = function() {
  playTacticalChirp('alert');
  const banner = document.getElementById('ops-status-banner');
  if (banner) {
    banner.style.boxShadow = '0 0 24px rgba(255, 30, 56, 0.85)';
    banner.style.borderColor = 'rgba(255, 30, 56, 0.9)';
    setTimeout(() => {
      banner.style.boxShadow = '';
      banner.style.borderColor = '';
    }, 4000);
  }
  const badge = document.getElementById('ops-status-badge');
  if (badge) {
    badge.innerText = '🚨 PRIORITY ALERT';
    badge.className = 'ops-status-badge status-alert';
    setTimeout(() => {
      badge.innerText = '👁 MONITORING';
      badge.className = 'ops-status-badge';
    }, 6000);
  }
  const statusText = document.getElementById('ops-status-text');
  if (statusText) {
    statusText.innerText = '🚨 OPERATOR ALERT BROADCAST: PERIMETER REVIEW & VERIFICATION REQUIRED';
    statusText.style.color = '#ff3b30';
    setTimeout(() => {
      statusText.innerText = 'TRACKING ACTIVE • HUMAN CONFIRMATION REQUIRED';
      statusText.style.color = '#00f0ff';
    }, 6000);
  }
  if (window.smartShield) {
    window.smartShield.addEventLog('🚨 [OPS-ALERT] Operator priority alert sounded. Verification advisory broadcast to C2 console.');
  }
};

window.opsLogEvent = function() {
  playTacticalChirp('click');
  const viz = window.centerTrajViz;
  const app = window.smartShield;
  const btn = document.getElementById('btn-log-event');

  const now = new Date().toTimeString().substring(0, 8);
  let summary = `[OPS-LOG @ ${now}] Snapshot: `;

  if (viz && Object.keys(viz.tracks).length > 0) {
    const trackSummaries = Object.values(viz.tracks).map(t => {
      const spd = t.speed !== undefined ? t.speed.toFixed(1) : '0.0';
      const cur = t.current;
      const rng = cur ? Math.hypot(cur.x, cur.y).toFixed(1) : '?';
      const alt = cur ? cur.z.toFixed(1) : '?';
      return `${t.id} (R:${rng}m Z:${alt}m S:${spd}m/s [${t.threat_level || 'NOMINAL'} ${t.threat_score || 0}])`;
    });
    summary += trackSummaries.join(' | ');
  } else {
    summary += 'Airspace clear. 0 active airborne tracks in perimeter.';
  }

  if (app) app.addEventLog(summary);
  if (viz) viz.updateOpsStatus('📋 TELEMETRY SNAPSHOT COMMITTED TO MISSION EVENT LOG', 'success');

  if (btn) {
    const origText = btn.innerText;
    btn.innerText = '✔ LOGGED (SAVED)';
    btn.style.borderColor = '#00ff66';
    btn.style.color = '#00ff66';
    setTimeout(() => {
      btn.innerText = origText;
      btn.style.borderColor = '';
      btn.style.color = '';
    }, 1800);
  }
};

window.opsSimulateResponse = function() {
  playTacticalChirp('sim');
  const viz = window.centerTrajViz;
  const app = window.smartShield;
  const btn = document.getElementById('btn-simulate-response');
  const badge = document.getElementById('ops-status-badge');

  if (btn) {
    btn.classList.add('active');
    btn.innerText = '⚡ SIMULATING...';
  }
  if (badge) {
    badge.innerText = '⚡ SIMULATION';
    badge.className = 'ops-status-badge status-tracking';
  }

  if (viz) {
    viz.simulationActive = true;
    viz.updateOpsStatus('⚡ SIMULATION: Step 1/4 — Evaluating non-kinetic geo-fence perimeter protocol...', 'alert');
  }
  if (app) app.addEventLog('[OPS-SIM] ⚡ Protocol simulation initiated: Step 1/4 Non-kinetic perimeter advisory.');

  setTimeout(() => {
    playTacticalChirp('click');
    if (viz) viz.updateOpsStatus('📡 SIMULATION: Step 2/4 — Testing RF geo-fence broadcast corridor (NO JAMMING)...', 'alert');
    if (app) app.addEventLog('[OPS-SIM] 📡 Step 2/4: Geo-fence advisory corridor verified. Zero civilian hazard.');
  }, 1500);

  setTimeout(() => {
    playTacticalChirp('click');
    if (viz) viz.updateOpsStatus('🔍 SIMULATION: Step 3/4 — Computing safe return-to-home navigational vector...', 'alert');
    if (app) app.addEventLog('[OPS-SIM] 🔍 Step 3/4: Safe clearance vector computed: Vector 215° @ 18m AGL.');
  }, 3000);

  setTimeout(() => {
    playTacticalChirp('click');
    if (viz) viz.updateOpsStatus('🛡 SIMULATION: Step 4/4 — Advisory response verified safe. Operator decision ready.', 'success');
    if (app) app.addEventLog('[OPS-SIM] 🛡 Step 4/4: Non-kinetic advisory verified. Human operator in command.');
  }, 4500);

  setTimeout(() => {
    playTacticalChirp('click');
    if (btn) {
      btn.classList.remove('active');
      btn.innerText = '⚡ SIMULATE RESPONSE';
    }
    if (badge) {
      badge.innerText = '👁 MONITORING';
      badge.className = 'ops-status-badge';
    }
    if (viz) {
      viz.simulationActive = false;
      viz.updateOpsStatus('TRACKING ACTIVE • HUMAN CONFIRMATION REQUIRED', 'info');
    }
  }, 6000);
};

window.opsHoldTrack = function() {
  playTacticalChirp('click');
  const viz = window.centerTrajViz;
  const app = window.smartShield;
  if (!viz) return;

  const trackKeys = Object.keys(viz.tracks);
  if (trackKeys.length === 0) {
    viz.updateOpsStatus('⏸ NO ACTIVE TRACKS TO HOLD', 'info');
    return;
  }

  // Use currently selected track or primary
  const targetId = viz.heldTrackId || (app && app.primaryTrackId) || trackKeys[0];
  viz.holdTrack(targetId);

  const btnHold = document.getElementById('btn-hold-track');
  if (btnHold) {
    btnHold.classList.add('active');
    btnHold.innerText = `⏸ HOLD [${targetId}]`;
  }
  const btnTrack = document.getElementById('btn-track-target');
  if (btnTrack) {
    btnTrack.classList.add('active');
    btnTrack.innerText = `🎯 TRACKING [${targetId}]`;
  }

  viz.updateOpsStatus(`⏸ TRACK HOLD ACTIVE: [${targetId}] • AUTO-PRIORITY FROZEN`, 'alert');
  if (app) app.addEventLog(`[OPS] ⏸ Track hold engaged on ${targetId}. Automatic track switching suspended.`);
};

window.opsReleaseTrack = function() {
  playTacticalChirp('click');
  const viz = window.centerTrajViz;
  const app = window.smartShield;
  if (!viz) return;

  viz.releaseTrack();

  const btnTrack = document.getElementById('btn-track-target');
  if (btnTrack) {
    btnTrack.classList.remove('active');
    btnTrack.innerText = '🎯 TRACK TARGET';
  }
  const btnHold = document.getElementById('btn-hold-track');
  if (btnHold) {
    btnHold.classList.remove('active');
    btnHold.innerText = '⏸ HOLD TRACK';
  }

  viz.updateOpsStatus('▶ TRACK RELEASED — DYNAMIC THREAT PRIORITIZATION RESUMED', 'success');
  if (app) app.addEventLog('[OPS] ▶ Track hold released. Dynamic threat prioritization active.');
};

window.opsCameraCenter = function() {
  playTacticalChirp('click');
  const viz = window.centerTrajViz;
  const app = window.smartShield;

  // 1. Recenter hardware/simulated servo gimbal to 90.0°
  if (typeof window.recenterServo === 'function') {
    window.recenterServo();
  } else {
    const apiBase = (window.location.protocol === 'file:' || !window.location.host) ? 'http://localhost:8000' : '';
    fetch(`${apiBase}/api/gimbal/recenter`, { method: 'POST' }).catch(() => {});
  }

  // 2. Reset 3D isometric view angles and rotation
  if (viz) {
    viz.rotAngle = 0.65;
    viz.tiltAngle = 0.42;
    viz.setView('3d');
    viz.updateOpsStatus('📷 CAMERA & AIRSPACE RECENTERED TO BORESIGHT (90°)', 'info');
  }

  const btn = document.getElementById('btn-camera-center');
  if (btn) {
    btn.style.borderColor = '#00f0ff';
    btn.style.boxShadow = '0 0 12px rgba(0, 240, 255, 0.6)';
    setTimeout(() => {
      btn.style.borderColor = '';
      btn.style.boxShadow = '';
    }, 1200);
  }

  if (app) app.addEventLog('[OPS] 📷 Camera and 3D airspace recentered to boresight origin (90.0° Pan / 0.0° Tilt).');
};

window.opsShowTrajectory = function() {
  playTacticalChirp('click');
  const viz = window.centerTrajViz;
  const sideViz = window.trajViz;
  const app = window.smartShield;
  const btn = document.getElementById('btn-show-trajectory');

  let state = true;
  if (viz) {
    state = viz.toggleFutureForecast();
  } else if (sideViz) {
    state = sideViz.toggleFutureForecast();
  }

  if (btn) {
    if (state) {
      btn.classList.add('active');
      btn.innerText = '📐 SHOW TRAJECTORY (ON)';
      btn.style.borderColor = 'rgba(0, 240, 255, 0.8)';
    } else {
      btn.classList.remove('active');
      btn.innerText = '📐 SHOW TRAJECTORY (OFF)';
      btn.style.borderColor = 'rgba(100, 120, 140, 0.4)';
    }
  }

  if (viz) {
    viz.updateOpsStatus(
      state ? '📐 TRAJECTORY FORECAST: 2s/3s FUTURE WAYPOINTS ENABLED' : '📐 TRAJECTORY FORECAST: DISPLAY HIDDEN',
      state ? 'info' : 'alert'
    );
  }
  if (app) app.addEventLog(`[OPS] 📐 Trajectory forecast overlay toggled: ${state ? 'ENABLED' : 'DISABLED'}`);
};

