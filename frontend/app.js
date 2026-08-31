/**
 * SMART SHIELD — Clean Tactical Airspace Defence C2 Coordinator
 * WebSocket Client & Real-Time Telemetry Data Binder
 */

class SmartShieldC2 {
  constructor() {
    this.tracks = [];
    this.primaryTrackId = null;
    this.gimbalPan = 0.0;
    this.gimbalTilt = 0.0;
    this.metSeconds = 0;
    this.isBackendConnected = false;
    this.ws = null;
    this.visionMode = 'LIVE_STREAM';
    this.zoomLevel = 4;

    this.initClocks();
    this.initWebSocket();
  }

  initWebSocket() {
    const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || !window.location.host;
    
    let wsUrl;
    if (isLocal) {
      wsUrl = 'ws://localhost:8000/ws/telemetry';
    } else {
      const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      wsUrl = `${proto}//${window.location.host}/ws/telemetry`;
    }

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.isBackendConnected = true;
        if (this.simInterval) {
          clearInterval(this.simInterval);
          this.simInterval = null;
        }
        console.log("SMART SHIELD C2 WebSocket Connected.");
        this.updateConnectionBadge(true);
        this.addEventLog("[SYSTEM] Connected to C2 Live Telemetry Stream at 30 FPS.");
        
        // Refresh live camera feed
        const mjpegImg = document.getElementById('mjpegVideoFeed');
        if (mjpegImg && this.visionMode === 'LIVE_STREAM') {
          mjpegImg.src = `/api/video_feed?t=${Date.now()}`;
          mjpegImg.style.display = 'block';
        }
      };

      this.ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          this.handleBackendTelemetry(payload);
        } catch (e) {
          console.error("Telemetry parse error:", e);
        }
      };

      this.ws.onclose = () => {
        this.isBackendConnected = false;
        this.updateConnectionBadge(false);
        this.startFallbackSimulation();
        setTimeout(() => this.initWebSocket(), 5000);
      };

      this.ws.onerror = () => {
        this.isBackendConnected = false;
        this.updateConnectionBadge(false);
        this.startFallbackSimulation();
      };
    } catch (e) {
      this.isBackendConnected = false;
      this.updateConnectionBadge(false);
      this.startFallbackSimulation();
    }
  }

  startFallbackSimulation() {
    if (this.simInterval) return;
    let simAngle = 0;
    this.simInterval = setInterval(() => {
      if (this.isBackendConnected) {
        clearInterval(this.simInterval);
        this.simInterval = null;
        return;
      }
      simAngle += 0.04;
      const r1 = 38.0 + Math.sin(simAngle * 0.7) * 8.0;
      const b1 = (simAngle * 25) % 360;
      const x1 = r1 * Math.cos((b1 * Math.PI) / 180);
      const y1 = r1 * Math.sin((b1 * Math.PI) / 180);
      const z1 = 18.0 + Math.sin(simAngle * 1.2) * 4.0;

      const r2 = 62.0 + Math.cos(simAngle * 0.5) * 12.0;
      const b2 = (180 + simAngle * 18) % 360;
      const x2 = r2 * Math.cos((b2 * Math.PI) / 180);
      const y2 = r2 * Math.sin((b2 * Math.PI) / 180);
      const z2 = 25.0 + Math.cos(simAngle * 0.8) * 6.0;

      const simPayload = {
        system_status: {
          fps: 30,
          camera_connected: false,
          radar_connected: false,
          simulation_mode: true
        },
        targets: [
          {
            id: 'TRK-101',
            track_id: 1,
            callsign: 'DRONE-ALPHA (DJI M300)',
            classification: 'Quadcopter',
            confidence: 0.94,
            distance_m: r1,
            azimuth_deg: b1,
            x_m: x1,
            y_m: y1,
            z_m: z1,
            vx_ms: -3.2 * Math.sin((b1 * Math.PI) / 180),
            vy_ms: -4.5,
            speed_ms: 5.5,
            closure_rate_ms: -4.5,
            threat_score: 82,
            threat_level: 'HIGH',
            threat_reasons: ['HIGH CLOSURE RATE (-4.5m/s)', 'AIRSPACE RESTRICTED ZONE INTRUSION'],
            is_highest_priority: true
          },
          {
            id: 'TRK-102',
            track_id: 2,
            callsign: 'DRONE-BRAVO (FIXED-WING)',
            classification: 'Fixed-Wing',
            confidence: 0.88,
            distance_m: r2,
            azimuth_deg: b2,
            x_m: x2,
            y_m: y2,
            z_m: z2,
            vx_ms: 2.1,
            vy_ms: -1.8,
            speed_ms: 12.4,
            closure_rate_ms: -1.8,
            threat_score: 54,
            threat_level: 'MEDIUM',
            threat_reasons: ['PERIMETER PATROL APPROACH'],
            is_highest_priority: false
          }
        ],
        primary_target: { id: 'TRK-101' },
        gimbal: {
          pan_deg: b1,
          tilt_deg: (Math.atan2(z1, r1) * 180) / Math.PI
        }
      };
      this.handleBackendTelemetry(simPayload);
    }, 100);
  }

  updateConnectionBadge(connected, sysStatus) {
    const fpsText = document.getElementById('c2-fps-text');
    const camText = document.getElementById('cam-status-text');
    const radarText = document.getElementById('radar-status-text');
    const camFpsVal = document.getElementById('cam-fps-val');

    if (fpsText) {
      if (connected) {
        const fps = sysStatus && sysStatus.fps ? sysStatus.fps : 30;
        fpsText.innerText = `ONLINE (${fps} FPS)`;
        if (camFpsVal) camFpsVal.innerText = `${fps}`;
      } else {
        fpsText.innerText = 'SIMULATED C2 (STANDBY)';
      }
    }

    if (camText) {
      if (sysStatus && sysStatus.camera_connected) {
        camText.innerText = 'USB WEBCAM (LIVE)';
      } else {
        camText.innerText = 'SYNTHETIC EO/IR HUD';
      }
    }

    if (radarText) {
      if (sysStatus && sysStatus.radar_connected) {
        radarText.innerText = 'CONNECTED (COM5)';
      } else {
        radarText.innerText = 'ACTIVE (SWEEP)';
      }
    }
  }

  handleBackendTelemetry(payload) {
    if (!payload) return;

    if (payload.system_status) {
      this.updateConnectionBadge(true, payload.system_status);
    }

    // 1. Process Targets
    if (payload.targets && Array.isArray(payload.targets)) {
      this.tracks = payload.targets.map((t, idx) => {
        const tid = t.id || `TRK-10${idx + 1}`;
        const score = Math.round(t.threat_score || 0);
        const level = t.threat_level || (score >= 70 ? 'HIGH' : (score >= 40 ? 'MEDIUM' : 'LOW'));
        const category = level === 'HIGH' ? 'CRITICAL' : (level === 'MEDIUM' ? 'ELEVATED' : 'NOMINAL');

        return {
          trackId: tid,
          idNum: t.track_id || (idx + 1),
          callsign: t.callsign || `DRONE (${tid})`,
          classification: t.classification || 'Drone',
          confidence: t.confidence !== undefined ? t.confidence : 0.92,
          x: t.x_m !== undefined ? t.x_m : 0.0,
          y: t.y_m !== undefined ? t.y_m : 50.0,
          z: t.z_m !== undefined ? t.z_m : 15.0,
          vx: t.vx_ms !== undefined ? t.vx_ms : 0.0,
          vy: t.vy_ms !== undefined ? t.vy_ms : 0.0,
          range: t.distance_m !== undefined ? t.distance_m : Math.hypot(t.x_m || 0, t.y_m || 50),
          bearing: t.azimuth_deg !== undefined ? t.azimuth_deg : 0.0,
          altitude: t.z_m !== undefined ? t.z_m : 15.0,
          speed: t.speed_ms !== undefined ? t.speed_ms : 0.0,
          closureRate: t.closure_rate_ms !== undefined ? t.closure_rate_ms : (t.vy_ms || 0.0),
          cameraSpeed: t.camera_speed_px_s,
          radarSpeed: t.radar_speed_mps,
          radarRange: t.radar_range_m,
          threatScore: score,
          threatCategory: category,
          threatLevel: level,
          threatReasons: t.threat_reasons || [],
          isPrimary: t.is_highest_priority || (idx === 0)
        };
      });
    }

    // 2. Primary Target Lock & Gimbal
    if (payload.primary_target) {
      this.primaryTrackId = payload.primary_target.id;
    } else if (this.tracks.length > 0) {
      this.primaryTrackId = this.tracks[0].trackId;
    } else {
      this.primaryTrackId = null;
    }

    if (payload.gimbal) {
      this.gimbalPan = payload.gimbal.pan_deg || this.gimbalPan;
      this.gimbalTilt = payload.gimbal.tilt_deg || this.gimbalTilt;

      // Update ESP32 Servo Tracking Badges (Top Toolbar & Bottom Bar)
      const badges = [
        document.getElementById('servo-status-badge'),
        document.getElementById('servo-status-badge-top')
      ];
      if (payload.gimbal.servo_connected !== undefined) {
        const servoPan = (payload.gimbal.servo_pan || 90.0).toFixed(1);
        const trackingStatus = payload.gimbal.tracking_status || 'IDLE';
        const isLocked = trackingStatus === 'LOCKED' && payload.primary_target;
        const isCoasting = trackingStatus === 'COASTING';

        badges.forEach(b => {
          if (!b) return;
          if (payload.gimbal.servo_connected) {
            if (isLocked) {
              b.innerText = `🔒 LOCKED [TRK-${payload.primary_target.track_id || 1}] ${servoPan}°`;
              b.style.background = '#7f1d1d';
              b.style.color = '#fca5a5';
              b.style.borderColor = '#ef4444';
            } else if (isCoasting) {
              b.innerText = `⏳ COASTING ${servoPan}°`;
              b.style.background = '#78350f';
              b.style.color = '#fde047';
              b.style.borderColor = '#eab308';
            } else {
              b.innerText = `🎯 SERVO: IDLE ${servoPan}°`;
              b.style.background = '#14532d';
              b.style.color = '#4ade80';
              b.style.borderColor = '#22c55e';
            }
          } else {
            b.innerText = '🎯 SERVO: OFFLINE';
            b.style.background = '#2a2a2a';
            b.style.color = '#666';
            b.style.borderColor = '#44444455';
          }
        });

        // Update FLIR Target Designation Banner
        const desTitle = document.getElementById('designation-title');
        const desDesc = document.getElementById('designation-text');
        if (desTitle && desDesc) {
          if (isLocked) {
            desTitle.innerText = `🔒 TARGET LOCKED: ${payload.primary_target.id || 'DRONE-01'} [ACTIVE AUTO-CENTER]`;
            desTitle.className = 'designator-title text-red';
            desDesc.innerText = `AZIMUTH: ${servoPan}° • VISUAL SERVOING LOCKED • CONTINUOUS STEP-BY-STEP RECONNAISSANCE`;
          } else if (isCoasting) {
            desTitle.innerText = `⏳ MEMORY COASTING: EXTRAPOLATING TRAJECTORY`;
            desTitle.className = 'designator-title text-amber';
            desDesc.innerText = `TARGET OCCLUSION DETECTED • MAINTAINING GIMBAL SLEW IN VECTOR DIRECTION`;
          }
        }
      }
    }

    this.render();
  }

  initClocks() {
    setInterval(() => {
      const now = new Date();
      const zulu = now.toISOString().substring(11, 19) + ' Z';
      const istOptions = { timeZone: 'Asia/Kolkata', hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' };
      const ist = now.toLocaleTimeString('en-GB', istOptions) + ' IST';

      this.metSeconds++;
      const metH = String(Math.floor(this.metSeconds / 3600)).padStart(2, '0');
      const metM = String(Math.floor((this.metSeconds % 3600) / 60)).padStart(2, '0');
      const metS = String(this.metSeconds % 60).padStart(2, '0');
      const met = `+${metH}:${metM}:${metS}`;

      const zuluEl = document.getElementById('clock-zulu');
      const istEl = document.getElementById('clock-ist');
      const metEl = document.getElementById('clock-met');

      if (zuluEl) zuluEl.innerText = zulu;
      if (istEl) istEl.innerText = ist;
      if (metEl) metEl.innerText = met;
    }, 1000);
  }

  render() {
    if (window.cinematicRadar) {
      window.cinematicRadar.updateAndDraw(this.tracks, this.primaryTrackId);
    }

    if (window.cinematicOpticalFLIR && this.visionMode !== 'LIVE_STREAM') {
      window.cinematicOpticalFLIR.updateAndDraw(this.tracks, this.primaryTrackId, this.gimbalPan, this.gimbalTilt);
    }

    // Feed trajectory prediction visualizer
    if (window.trajViz && this.tracks.length > 0) {
      window.trajViz.updateTracks(this.tracks);
    }

    this.updateTelemetryDom();
    this.updateThreatAnalyticsDom();
    this.updateTewaTableDom();
  }

  updateTelemetryDom() {
    const trackCountEl = document.getElementById('track-count-val');
    const closestRangeEl = document.getElementById('closest-range-val');
    const maxClosureEl = document.getElementById('max-closure-val');
    const ttiEl = document.getElementById('tti-val');
    const threatLevelEl = document.getElementById('air-threat-level');

    const fcrAzEl = document.getElementById('fcr-az-val');
    const fcrElEl = document.getElementById('fcr-el-val');
    const lrfStatus = document.getElementById('lrf-status');

    if (trackCountEl) {
      trackCountEl.innerText = this.tracks.length < 10 ? `0${this.tracks.length}` : `${this.tracks.length}`;
    }

    if (this.tracks.length > 0) {
      const primary = this.tracks[0];
      if (closestRangeEl) closestRangeEl.innerText = `${primary.range.toFixed(1)} m`;
      if (maxClosureEl) {
        maxClosureEl.innerText = `${primary.closureRate.toFixed(1)} m/s`;
        maxClosureEl.className = `sc-val ${primary.closureRate < 0 ? 'text-red' : 'text-green'}`;
      }

      const tti = Math.max(0.5, (primary.range / Math.max(Math.abs(primary.closureRate), 3.0))).toFixed(1);
      if (ttiEl) ttiEl.innerText = `${tti} SEC`;

      if (threatLevelEl) {
        threatLevelEl.innerText = primary.threatCategory;
        threatLevelEl.className = `sc-val ${primary.threatLevel === 'HIGH' ? 'text-red' : (primary.threatLevel === 'MEDIUM' ? 'text-amber' : 'text-green')}`;
      }

      if (fcrAzEl) fcrAzEl.innerText = `${primary.bearing.toFixed(1)}°`;
      if (fcrElEl) fcrElEl.innerText = `+${Math.abs(this.gimbalTilt).toFixed(1)}°`;
      if (lrfStatus) lrfStatus.innerText = `${primary.range.toFixed(1)}m [LOCK]`;

      const desTitle = document.getElementById('designation-title');
      const desText = document.getElementById('designation-text');
      if (desTitle) {
        desTitle.innerText = `⚡ TARGET LOCK: ${primary.trackId} (${primary.classification})`;
        desTitle.style.color = primary.threatLevel === 'HIGH' ? 'var(--neon-red)' : 'var(--neon-cyan)';
      }
      if (desText) {
        desText.innerText = `BEARING: ${primary.bearing.toFixed(1)}° • RANGE: ${primary.range.toFixed(1)}m • SPEED: ${primary.speed.toFixed(1)} m/s • THREAT: ${primary.threatScore}/100`;
      }
    } else {
      if (closestRangeEl) closestRangeEl.innerText = '--- m';
      if (maxClosureEl) maxClosureEl.innerText = '--- m/s';
      if (ttiEl) ttiEl.innerText = '--- SEC';
      if (threatLevelEl) {
        threatLevelEl.innerText = 'NOMINAL';
        threatLevelEl.className = 'sc-val text-green';
      }
      if (lrfStatus) lrfStatus.innerText = '---';

      const desTitle = document.getElementById('designation-title');
      const desText = document.getElementById('designation-text');
      if (desTitle) {
        desTitle.innerText = '⚡ TARGET STATUS: SCANNING AIRSPACE';
        desTitle.style.color = 'var(--neon-cyan)';
      }
      if (desText) {
        desText.innerText = 'NO ACTIVE CONTACT IN PERIMETER • CONTINUOUS REAL-TIME INGESTION ACTIVE';
      }
    }
  }

  updateThreatAnalyticsDom() {
    const scoreValEl = document.getElementById('main-threat-score-val');
    const badgeEl = document.getElementById('main-threat-badge');
    const barEl = document.getElementById('main-threat-progress-bar');

    const fProx = document.getElementById('factor-prox');
    const fProxVal = document.getElementById('factor-prox-val');
    const fSpd = document.getElementById('factor-spd');
    const fSpdVal = document.getElementById('factor-spd-val');
    const fHdg = document.getElementById('factor-hdg');
    const fHdgVal = document.getElementById('factor-hdg-val');
    const fConf = document.getElementById('factor-conf');
    const fConfVal = document.getElementById('factor-conf-val');

    const mCam = document.getElementById('metric-cam-spd');
    const mRad = document.getElementById('metric-rad-spd');
    const mFused = document.getElementById('metric-fused-spd');

    if (this.tracks.length > 0) {
      const top = this.tracks[0];
      const score = top.threatScore;

      if (scoreValEl) scoreValEl.innerHTML = `${score}<span class="score-max">/100</span>`;
      if (barEl) barEl.style.width = `${score}%`;

      if (badgeEl) {
        badgeEl.innerText = top.threatCategory;
        badgeEl.className = `threat-level-badge ${top.threatLevel === 'HIGH' ? 'level-critical' : (top.threatLevel === 'MEDIUM' ? 'level-elevated' : 'level-nominal')}`;
      }

      // Breakdown factors
      const proxPct = Math.round(Math.max(0, 1 - (top.range / 200.0)) * 100);
      const spdPct = Math.round(Math.min(100, (top.speed / 25.0) * 100));
      const hdgPct = Math.round(top.closureRate < 0 ? Math.min(100, (Math.abs(top.closureRate) / 20.0) * 100) : 10);
      const confPct = Math.round(top.confidence * 100);

      if (fProx) fProx.style.width = `${proxPct}%`;
      if (fProxVal) fProxVal.innerText = `${proxPct}%`;

      if (fSpd) fSpd.style.width = `${spdPct}%`;
      if (fSpdVal) fSpdVal.innerText = `${spdPct}%`;

      if (fHdg) fHdg.style.width = `${hdgPct}%`;
      if (fHdgVal) fHdgVal.innerText = `${hdgPct}%`;

      if (fConf) fConf.style.width = `${confPct}%`;
      if (fConfVal) fConfVal.innerText = `${confPct}%`;

      if (mCam) mCam.innerText = `${top.speed.toFixed(1)} m/s`;
      if (mRad) mRad.innerText = top.radarSpeed !== null && top.radarSpeed !== undefined ? `${top.radarSpeed.toFixed(1)} m/s` : '--- m/s';
      if (mFused) mFused.innerText = `${top.speed.toFixed(1)} m/s`;

    } else {
      if (scoreValEl) scoreValEl.innerHTML = `00<span class="score-max">/100</span>`;
      if (barEl) barEl.style.width = `0%`;
      if (badgeEl) {
        badgeEl.innerText = 'NOMINAL';
        badgeEl.className = 'threat-level-badge level-nominal';
      }
      if (fProx) fProx.style.width = '0%';
      if (fProxVal) fProxVal.innerText = '0%';
      if (fSpd) fSpd.style.width = '0%';
      if (fSpdVal) fSpdVal.innerText = '0%';
      if (fHdg) fHdg.style.width = '0%';
      if (fHdgVal) fHdgVal.innerText = '0%';
      if (fConf) fConf.style.width = '0%';
      if (fConfVal) fConfVal.innerText = '0%';

      if (mCam) mCam.innerText = '0.0 m/s';
      if (mRad) mRad.innerText = '--- m/s';
      if (mFused) mFused.innerText = '0.0 m/s';
    }
  }

  updateTewaTableDom() {
    const tbody = document.getElementById('tewa-table-body');
    if (!tbody) return;

    if (this.tracks.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="12" style="text-align: center; color: var(--text-dim); padding: 16px;">
            NO AIRBORNE TARGETS DETECTED IN PERIMETER • SYSTEM SCANNING
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = this.tracks.map(t => {
      const isPri = (t.trackId === this.primaryTrackId);
      const rowClass = isPri ? 'row-hostile-priority' : '';
      const badgeClass = t.threatCategory === 'CRITICAL' ? 'tewa-critical' : (t.threatCategory === 'ELEVATED' ? 'tewa-elevated' : 'tewa-nominal');
      const tti = Math.max(0.5, (t.range / Math.max(Math.abs(t.closureRate), 3.0))).toFixed(1);

      return `
        <tr class="${rowClass}">
          <td><strong>${t.trackId}</strong></td>
          <td>${t.classification}</td>
          <td>${(t.confidence * 100).toFixed(0)}%</td>
          <td>${t.range.toFixed(1)} m</td>
          <td>${t.bearing.toFixed(1)}°</td>
          <td>${t.altitude.toFixed(0)} m</td>
          <td>${t.speed.toFixed(1)} m/s</td>
          <td><strong class="${t.closureRate < 0 ? 'text-red' : 'text-green'}">${t.closureRate.toFixed(1)} m/s</strong></td>
          <td>${tti}s</td>
          <td><strong>${t.threatScore}/100</strong></td>
          <td><span class="tewa-badge ${badgeClass}">${t.threatCategory}</span></td>
          <td><span class="text-green">${isPri ? '● PRIMARY LOCK' : 'TRACKING'}</span></td>
        </tr>
      `;
    }).join('');
  }

  addEventLog(msg) {
    const logBox = document.getElementById('event-log-container');
    if (!logBox) return;
    const now = new Date().toTimeString().substring(0, 8);
    const item = document.createElement('div');
    item.className = 'log-item';
    item.innerText = `[${now}] ${msg}`;
    logBox.insertBefore(item, logBox.firstChild);
    if (logBox.children.length > 20) {
      logBox.removeChild(logBox.lastChild);
    }
  }
}

window.smartShield = new SmartShieldC2();

// USER ACTION HANDLERS

window.setVisionMode = function(mode) {
  if (window.smartShield) {
    window.smartShield.visionMode = mode;
  }
  const mjpegImg = document.getElementById('mjpegVideoFeed');

  if (mode === 'LIVE_STREAM') {
    if (mjpegImg) {
      mjpegImg.src = `/api/video_feed?t=${Date.now()}`;
      mjpegImg.style.display = 'block';
    }
  } else {
    if (mjpegImg) mjpegImg.style.display = 'none';
    if (window.cinematicOpticalFLIR) {
      window.cinematicOpticalFLIR.setVisionMode(mode);
    }
  }

  document.querySelectorAll('.btn-vision-mode').forEach(btn => btn.classList.remove('active'));
  const btnMap = {
    'LIVE_STREAM': 'mode-live-stream',
    'WHITE_HOT': 'mode-flir-white',
    'NVG_GREEN': 'mode-nvg',
    'DAY_OPTICAL': 'mode-optical'
  };
  const activeBtn = document.getElementById(btnMap[mode]);
  if (activeBtn) activeBtn.classList.add('active');
};

window.setZoomLevel = function(zoom) {
  if (window.smartShield) {
    window.smartShield.zoomLevel = zoom;
  }
  if (window.cinematicOpticalFLIR) {
    window.cinematicOpticalFLIR.setZoomLevel(zoom);
  }
  const zoomText = document.getElementById('zoom-text');
  if (zoomText) zoomText.innerText = `${zoom}.0X OPTICAL`;

  document.querySelectorAll('.btn-zoom').forEach(btn => {
    btn.classList.toggle('active', btn.innerText === `${zoom}X`);
  });
};

window.exportMissionReportCsv = function() {
  const apiBase = (window.location.protocol === 'file:' || !window.location.host) ? 'http://localhost:8000' : '';
  window.open(`${apiBase}/api/logs/export/csv`, '_blank');
};

window.handleVideoUpload = async function(event) {
  const file = event.target.files[0];
  if (!file) return;

  const statusBar = document.getElementById('video-upload-status-bar');
  const statusText = document.getElementById('upload-status-text');
  const badge = document.getElementById('current-stream-source-badge');

  if (statusBar && statusText) {
    statusBar.style.display = 'flex';
    statusText.innerText = `⏳ Uploading and initializing drone flight video "${file.name}"...`;
  }

  const formData = new FormData();
  formData.append('file', file);

  try {
    const apiBase = (window.location.protocol === 'file:' || !window.location.host) ? 'http://localhost:8000' : '';
    const res = await fetch(`${apiBase}/api/video/upload`, {
      method: 'POST',
      body: formData
    });
    const data = await res.json();

    if (data.status === 'SUCCESS') {
      if (statusText) {
        statusText.innerHTML = `✅ <strong>Video Active:</strong> "${file.name}" — AI Trajectory Prediction, Velocity & TEWA Tracking Running!`;
      }
      if (badge) {
        badge.innerText = `FEED: ${file.name.substring(0, 18)}...`;
        badge.className = 'pill-mil pill-active';
      }
      if (window.smartShield) {
        window.smartShield.addEventLog(`[VIDEO INGEST] Loaded drone video: ${file.name}`);
      }
      const mjpegImg = document.getElementById('mjpegVideoFeed');
      if (mjpegImg) {
        mjpegImg.src = `${apiBase}/api/video_feed?t=${Date.now()}`;
      }
    } else {
      if (statusText) statusText.innerText = `❌ Upload failed: ${data.message}`;
    }
  } catch (err) {
    if (statusText) statusText.innerText = `❌ Error connecting to server: ${err.message}`;
  }
};

window.switchVideoSource = async function(sourceType) {
  const statusBar = document.getElementById('video-upload-status-bar');
  const statusText = document.getElementById('upload-status-text');
  const badge = document.getElementById('current-stream-source-badge');

  try {
    const apiBase = (window.location.protocol === 'file:' || !window.location.host) ? 'http://localhost:8000' : '';
    const res = await fetch(`${apiBase}/api/video/switch_source`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source: sourceType })
    });
    const data = await res.json();

    if (data.status === 'SUCCESS') {
      const srcName = data.source_name || 'USB Camera';
      if (statusBar && statusText) {
        statusBar.style.display = 'flex';
        statusText.innerHTML = `📷 <strong>Active Input:</strong> Switched to ${srcName}.`;
        setTimeout(() => { statusBar.style.display = 'none'; }, 4000);
      }
      if (badge) {
        badge.innerText = `FEED: ${srcName.toUpperCase()}`;
        badge.className = 'pill-mil pill-online';
      }
      if (window.smartShield) {
        window.smartShield.addEventLog(`[HARDWARE] Switched stream to ${srcName}`);
      }
      const mjpegImg = document.getElementById('mjpegVideoFeed');
      if (mjpegImg) {
        mjpegImg.src = `${apiBase}/api/video_feed?t=${Date.now()}`;
      }
    }
  } catch (err) {
    console.error("Failed to switch source:", err);
  }
};

// RF JAMMING & ELECTRONIC WARFARE ACTION HANDLERS
window.executeSoftKill = function() {
  const directiveEl = document.getElementById('directive-text');
  const rfBadge = document.getElementById('rf-control-status-badge');
  const desTitle = document.getElementById('designation-title');
  const desText = document.getElementById('designation-text');

  if (directiveEl) {
    directiveEl.innerText = '⚡ DIRECTED RF DENIAL BEAM ENGAGED — INTRUDER C2 LINK SEVERED (FAILSAFE GROUNDING ACTIVATED)';
    directiveEl.className = 'text-cyan';
  }
  if (rfBadge) {
    rfBadge.innerText = '⚡ JAMMING BEAM ACTIVE';
    rfBadge.className = 'rf-status-badge tag-active';
  }
  if (desTitle) desTitle.innerText = '⚡ RF DENIAL BEAM ENGAGED';
  if (desText) desText.innerText = 'High-gain directional RF disruption beam transmitting on 2.4GHz / 5.8GHz channels.';

  if (window.smartShield) {
    window.smartShield.addEventLog('⚡ Soft-Kill Directed RF Jamming Beam engaged on active target!');
  }
};

window.toggleHostileJamming = function() {
  const apiBase = (window.location.protocol === 'file:' || !window.location.host) ? 'http://localhost:8000' : '';
  fetch(`${apiBase}/api/cyber/toggle_jamming`, { method: 'POST' }).catch(() => {});

  const directiveEl = document.getElementById('directive-text');
  const rfBadge = document.getElementById('rf-control-status-badge');
  const btnJam = document.getElementById('btn-jam-sim-cam');

  let isJamming = false;
  if (window.smartShield) {
    window.smartShield.isJammingActive = !window.smartShield.isJammingActive;
    isJamming = window.smartShield.isJammingActive;
  }

  if (isJamming) {
    if (directiveEl) {
      directiveEl.innerText = '⚠️ HOSTILE RF JAMMING ATTACK DETECTED — SPECTRUM DEGRADED BY +32dB';
      directiveEl.className = 'text-red';
    }
    if (rfBadge) {
      rfBadge.innerText = '⚠️ JAMMING ATTACK DETECTED';
      rfBadge.className = 'rf-status-badge tag-critical';
    }
    if (btnJam) btnJam.innerText = '🛑 STOP JAMMING ATTACK';
    if (window.smartShield) {
      window.smartShield.addEventLog('⚠️ WARNING: Hostile RF barrage jamming attack detected across channels 4-8!');
    }
  } else {
    if (directiveEl) {
      directiveEl.innerText = 'DEFENSIVE MONITORING ACTIVE — ALL PERIMETER SECTORS SECURE';
      directiveEl.className = 'text-green';
    }
    if (rfBadge) {
      rfBadge.innerText = 'RF LINK SECURE (CH-6)';
      rfBadge.className = 'rf-status-badge tag-secure';
    }
    if (btnJam) btnJam.innerText = '⚠️ SIMULATE HOSTILE JAMMING';
    if (window.smartShield) {
      window.smartShield.addEventLog('RF Spectrum restored to nominal baseline.');
    }
  }
};

window.executeEccmFrequencyHop = function() {
  const apiBase = (window.location.protocol === 'file:' || !window.location.host) ? 'http://localhost:8000' : '';
  fetch(`${apiBase}/api/cyber/frequency_hop`, { method: 'POST' }).catch(() => {});

  const channels = [11, 24, 38, 14, 28];
  const nextCh = channels[Math.floor(Math.random() * channels.length)];

  if (window.smartShield) {
    window.smartShield.isJammingActive = false;
    window.smartShield.activeChannel = nextCh;
  }

  const directiveEl = document.getElementById('directive-text');
  const rfBadge = document.getElementById('rf-control-status-badge');
  const btnJam = document.getElementById('btn-jam-sim-cam');

  if (directiveEl) {
    directiveEl.innerText = `🔄 ECCM FREQUENCY HOP EXECUTED — C2 LINK SECURED ON AGILITY CH-${nextCh}`;
    directiveEl.className = 'text-green';
  }
  if (rfBadge) {
    rfBadge.innerText = `🔄 ECCM SECURED (CH-${nextCh})`;
    rfBadge.className = 'rf-status-badge tag-secure';
  }
  if (btnJam) btnJam.innerText = '⚠️ SIMULATE HOSTILE JAMMING';

  if (window.smartShield) {
    window.smartShield.addEventLog(`🔄 ECCM Frequency Hopping executed -> Switched to CH-${nextCh}`);
  }
};

window.recenterServo = function() {
  const apiBase = (window.location.protocol === 'file:' || !window.location.host) ? 'http://localhost:8000' : '';
  fetch(`${apiBase}/api/gimbal/recenter`, { method: 'POST' })
    .then(r => r.json())
    .then(d => {
      if (window.smartShield) {
        window.smartShield.addEventLog('🎯 Servo recentered to 90.0° (Center position)');
      }
    })
    .catch(() => {});
};

window.toggleInvertServo = function() {
  const apiBase = (window.location.protocol === 'file:' || !window.location.host) ? 'http://localhost:8000' : '';
  fetch(`${apiBase}/api/gimbal/toggle_invert`, { method: 'POST' })
    .then(r => r.json())
    .then(d => {
      const mode = d.invert_pan ? 'REVERSED' : 'NORMAL';
      const btns = [
        document.getElementById('btn-invert-top'),
        document.getElementById('btn-invert-bottom')
      ];
      btns.forEach(b => {
        if (b) b.innerText = `🔄 INVERT (${mode})`;
      });
      if (window.smartShield) {
        window.smartShield.addEventLog(`🔄 Servo pan direction toggled: ${mode}`);
      }
    })
    .catch(() => {});
};

window.toggleGimbalMode = function() {
  const apiBase = (window.location.protocol === 'file:' || !window.location.host) ? 'http://localhost:8000' : '';
  fetch(`${apiBase}/api/gimbal/toggle_mode`, { method: 'POST' })
    .then(r => r.json())
    .then(d => {
      const btn = document.getElementById('btn-mode-top');
      if (btn) {
        const isCam = d.mode === 'CAMERA_MOUNTED';
        btn.innerText = isCam ? '🔭 MODE: AUTO-LOCK (CAM)' : '🎯 MODE: POINTER (FIXED)';
        btn.style.background = isCam ? '#065f46' : '#854d0e';
        btn.style.borderColor = isCam ? '#34d399' : '#facc15';
      }
      if (window.smartShield) {
        window.smartShield.addEventLog(`🔭 Gimbal tracking mode set to: ${d.mode}`);
      }
    })
    .catch(() => {});
};

