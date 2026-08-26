/**
 * VayuNetra — 3D Trajectory Prediction Visualization
 * Renders actual flight path + predicted trajectory on a canvas
 * with 3D perspective, lateral (X-Z), and vertical (Y-Z) views.
 * Inspired by research-grade trajectory prediction plots.
 */

class TrajectoryVisualizer {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.currentView = '3d';

    // Track history: stores {x, y, z, t} for each track
    this.trackHistories = {};      // trackId -> [{x,y,z,t}, ...]
    this.predictedPaths = {};      // trackId -> [{x,y,z,t}, ...]
    this.maxHistoryLength = 200;

    // 3D rotation angle (auto-rotates slowly)
    this.rotAngle = 0.6;
    this.tiltAngle = 0.45;
    this.autoRotate = true;

    // Colors
    this.colors = {
      grid: 'rgba(0, 240, 255, 0.08)',
      gridLine: 'rgba(0, 240, 255, 0.15)',
      axisLabel: 'rgba(0, 240, 255, 0.6)',
      flightPath: 'rgba(120, 160, 180, 0.7)',
      actual: '#e59344',
      predicted: '#4a9eff',
      predictedGlow: 'rgba(74, 158, 255, 0.4)',
      actualGlow: 'rgba(229, 147, 68, 0.4)',
      bg: 'rgba(6, 14, 24, 0.95)',
      text: 'rgba(0, 240, 255, 0.8)',
      noData: 'rgba(0, 240, 255, 0.3)'
    };

    this.resizeCanvas();
    window.addEventListener('resize', () => this.resizeCanvas());
    this.startRenderLoop();
  }

  resizeCanvas() {
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
   * Feed new track data from the telemetry system.
   * tracks: array of {trackId, x, y, z, vx, vy, speed, ...}
   */
  updateTracks(tracks) {
    const now = performance.now() / 1000;

    tracks.forEach(t => {
      const id = t.trackId;
      if (!this.trackHistories[id]) {
        this.trackHistories[id] = [];
        this.predictedPaths[id] = [];
      }

      // Add actual position
      this.trackHistories[id].push({
        x: t.x || 0,
        y: t.y || (t.range || 50),
        z: t.z || (t.altitude || 15),
        t: now
      });

      // Trim history
      if (this.trackHistories[id].length > this.maxHistoryLength) {
        this.trackHistories[id].shift();
      }

      // Generate predicted trajectory (constant-velocity model, 3s horizon, 0.2s step)
      const vx = t.vx || (t.speed || 2) * Math.cos((t.bearing || 0) * Math.PI / 180);
      const vy = t.vy || (t.speed || 2) * Math.sin((t.bearing || 0) * Math.PI / 180);
      const vz = (t.altitude && this.trackHistories[id].length > 2)
        ? (t.z - this.trackHistories[id][this.trackHistories[id].length - 2].z) * 2
        : 0;

      const predicted = [];
      for (let dt = 0.2; dt <= 3.0 + 0.001; dt += 0.2) {
        predicted.push({
          x: (t.x || 0) + vx * dt,
          y: (t.y || t.range || 50) + vy * dt,
          z: (t.z || t.altitude || 15) + vz * dt,
          t: now + dt
        });
      }
      this.predictedPaths[id] = predicted;
    });

    // Clean up stale tracks (no update in 5s)
    const staleThreshold = now - 5;
    Object.keys(this.trackHistories).forEach(id => {
      const hist = this.trackHistories[id];
      if (hist.length > 0 && hist[hist.length - 1].t < staleThreshold) {
        delete this.trackHistories[id];
        delete this.predictedPaths[id];
      }
    });

    // Update stats
    const totalPoints = Object.values(this.trackHistories).reduce((sum, h) => sum + h.length, 0);
    const statPts = document.getElementById('traj-stat-points');
    if (statPts) statPts.innerHTML = `POINTS: <strong>${totalPoints}</strong>`;
  }

  // 3D projection: rotate XYZ into 2D screen coords with isometric-style perspective
  project3D(x, y, z, cx, cy, scale) {
    const cosR = Math.cos(this.rotAngle);
    const sinR = Math.sin(this.rotAngle);
    const cosT = Math.cos(this.tiltAngle);
    const sinT = Math.sin(this.tiltAngle);

    // Rotate around Y axis (yaw)
    const rx = x * cosR - y * sinR;
    const ry = x * sinR + y * cosR;
    const rz = z;

    // Tilt (pitch)
    const py = ry * cosT - rz * sinT;
    const pz = ry * sinT + rz * cosT;

    return {
      sx: cx + rx * scale,
      sy: cy - pz * scale,
      depth: py
    };
  }

  startRenderLoop() {
    const draw = () => {
      this.render();
      requestAnimationFrame(draw);
    };
    requestAnimationFrame(draw);
  }

  render() {
    const ctx = this.ctx;
    const W = this.canvas.width;
    const H = this.canvas.height;

    // Clear
    ctx.fillStyle = this.colors.bg;
    ctx.fillRect(0, 0, W, H);

    // Auto-rotate in 3D view
    if (this.autoRotate && this.currentView === '3d') {
      this.rotAngle += 0.002;
    }

    const hasData = Object.keys(this.trackHistories).length > 0;

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
    // Draw subtle grid
    this.drawGrid2D(ctx, W, H);

    ctx.fillStyle = this.colors.noData;
    ctx.font = '11px "Share Tech Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText('AWAITING TARGET ACQUISITION FOR TRAJECTORY PLOT...', W / 2, H / 2 - 8);
    ctx.font = '9px "Share Tech Mono", monospace';
    ctx.fillStyle = 'rgba(0, 240, 255, 0.2)';
    ctx.fillText('Trajectory prediction will activate when drone targets are tracked', W / 2, H / 2 + 12);
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

  render3D(ctx, W, H) {
    const cx = W / 2;
    const cy = H * 0.55;
    const scale = Math.min(W, H) * 0.022;

    // Draw 3D grid floor
    this.draw3DGrid(ctx, cx, cy, scale);

    // Draw axis labels
    this.draw3DAxes(ctx, cx, cy, scale);

    // For each track: draw flight path, actual points, predicted points
    const trackIds = Object.keys(this.trackHistories);
    trackIds.forEach(id => {
      const hist = this.trackHistories[id];
      const pred = this.predictedPaths[id] || [];

      if (hist.length < 2) return;

      // Normalize positions relative to first point
      const origin = hist[0];

      // Draw flight path (grey line)
      ctx.strokeStyle = this.colors.flightPath;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      let first = true;
      hist.forEach(p => {
        const proj = this.project3D(p.x - origin.x, p.y - origin.y, p.z - origin.z, cx, cy, scale);
        if (first) { ctx.moveTo(proj.sx, proj.sy); first = false; }
        else ctx.lineTo(proj.sx, proj.sy);
      });
      ctx.stroke();

      // Draw predicted trajectory (blue line with glow)
      if (pred.length > 0) {
        // Glow
        ctx.save();
        ctx.shadowColor = this.colors.predictedGlow;
        ctx.shadowBlur = 8;
        ctx.strokeStyle = this.colors.predicted;
        ctx.lineWidth = 2;
        ctx.setLineDash([4, 3]);
        ctx.beginPath();
        const lastActual = hist[hist.length - 1];
        const startProj = this.project3D(lastActual.x - origin.x, lastActual.y - origin.y, lastActual.z - origin.z, cx, cy, scale);
        ctx.moveTo(startProj.sx, startProj.sy);
        pred.forEach(p => {
          const proj = this.project3D(p.x - origin.x, p.y - origin.y, p.z - origin.z, cx, cy, scale);
          ctx.lineTo(proj.sx, proj.sy);
        });
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.restore();

        // Predicted position dots (blue)
        pred.forEach(p => {
          const proj = this.project3D(p.x - origin.x, p.y - origin.y, p.z - origin.z, cx, cy, scale);
          ctx.fillStyle = this.colors.predicted;
          ctx.beginPath();
          ctx.arc(proj.sx, proj.sy, 3, 0, Math.PI * 2);
          ctx.fill();
        });
      }

      // Draw actual position dots (orange) — last N points
      const actualDots = hist.slice(-30);
      actualDots.forEach(p => {
        const proj = this.project3D(p.x - origin.x, p.y - origin.y, p.z - origin.z, cx, cy, scale);
        ctx.fillStyle = this.colors.actual;
        ctx.beginPath();
        ctx.arc(proj.sx, proj.sy, 3.5, 0, Math.PI * 2);
        ctx.fill();
      });

      // Draw starting point marker
      if (hist.length > 0) {
        const sp = this.project3D(0, 0, 0, cx, cy, scale);
        ctx.fillStyle = '#00ff66';
        ctx.beginPath(); ctx.arc(sp.sx, sp.sy, 5, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = 'rgba(0,255,102,0.7)';
        ctx.font = '8px "Share Tech Mono", monospace';
        ctx.textAlign = 'left';
        ctx.fillText('START', sp.sx + 7, sp.sy + 3);
      }

      // Draw current position marker
      const lastP = hist[hist.length - 1];
      const lp = this.project3D(lastP.x - origin.x, lastP.y - origin.y, lastP.z - origin.z, cx, cy, scale);
      ctx.fillStyle = '#ff1e38';
      ctx.beginPath(); ctx.arc(lp.sx, lp.sy, 5, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = 'rgba(255,30,56,0.8)';
      ctx.font = '8px "Share Tech Mono", monospace';
      ctx.textAlign = 'left';
      ctx.fillText(`${id}`, lp.sx + 7, lp.sy + 3);
    });

    // View label
    ctx.fillStyle = this.colors.text;
    ctx.font = '10px "Share Tech Mono", monospace';
    ctx.textAlign = 'left';
    ctx.fillText('THREE-DIMENSIONAL VIEW', 8, 14);
  }

  draw3DGrid(ctx, cx, cy, scale) {
    ctx.strokeStyle = this.colors.gridLine;
    ctx.lineWidth = 0.4;
    const gridRange = 10;
    const step = 2;

    for (let i = -gridRange; i <= gridRange; i += step) {
      // Lines along X
      const a1 = this.project3D(i, -gridRange, 0, cx, cy, scale);
      const a2 = this.project3D(i, gridRange, 0, cx, cy, scale);
      ctx.beginPath(); ctx.moveTo(a1.sx, a1.sy); ctx.lineTo(a2.sx, a2.sy); ctx.stroke();
      // Lines along Y
      const b1 = this.project3D(-gridRange, i, 0, cx, cy, scale);
      const b2 = this.project3D(gridRange, i, 0, cx, cy, scale);
      ctx.beginPath(); ctx.moveTo(b1.sx, b1.sy); ctx.lineTo(b2.sx, b2.sy); ctx.stroke();
    }
  }

  draw3DAxes(ctx, cx, cy, scale) {
    const axLen = 12;
    ctx.lineWidth = 1.2;
    ctx.font = '9px "Share Tech Mono", monospace';

    // X axis (red)
    const xEnd = this.project3D(axLen, 0, 0, cx, cy, scale);
    const orig = this.project3D(0, 0, 0, cx, cy, scale);
    ctx.strokeStyle = '#ff4444';
    ctx.beginPath(); ctx.moveTo(orig.sx, orig.sy); ctx.lineTo(xEnd.sx, xEnd.sy); ctx.stroke();
    ctx.fillStyle = '#ff4444';
    ctx.textAlign = 'center';
    ctx.fillText('X (m)', xEnd.sx, xEnd.sy + 12);

    // Y axis (green)
    const yEnd = this.project3D(0, axLen, 0, cx, cy, scale);
    ctx.strokeStyle = '#44ff44';
    ctx.beginPath(); ctx.moveTo(orig.sx, orig.sy); ctx.lineTo(yEnd.sx, yEnd.sy); ctx.stroke();
    ctx.fillStyle = '#44ff44';
    ctx.textAlign = 'center';
    ctx.fillText('Y (m)', yEnd.sx, yEnd.sy + 12);

    // Z axis (blue/cyan - up)
    const zEnd = this.project3D(0, 0, axLen, cx, cy, scale);
    ctx.strokeStyle = '#00f0ff';
    ctx.beginPath(); ctx.moveTo(orig.sx, orig.sy); ctx.lineTo(zEnd.sx, zEnd.sy); ctx.stroke();
    ctx.fillStyle = '#00f0ff';
    ctx.textAlign = 'left';
    ctx.fillText('Z (m)', zEnd.sx + 4, zEnd.sy);
  }

  renderLateral(ctx, W, H) {
    // Lateral view: X vs Z (altitude) — like a side view
    this.render2DView(ctx, W, H, 'x', 'z', 'LATERAL VIEW', 'X (m)', 'Altitude Z (m)');
  }

  renderVertical(ctx, W, H) {
    // Vertical view: Y vs Z — top-down with altitude
    this.render2DView(ctx, W, H, 'y', 'z', 'VERTICAL VIEW', 'Y (m)', 'Altitude Z (m)');
  }

  render2DView(ctx, W, H, xKey, yKey, title, xLabel, yLabel) {
    const pad = { left: 55, right: 20, top: 28, bottom: 32 };
    const plotW = W - pad.left - pad.right;
    const plotH = H - pad.top - pad.bottom;

    // Collect all points to find bounds
    let allX = [], allY = [];
    const trackIds = Object.keys(this.trackHistories);
    trackIds.forEach(id => {
      const hist = this.trackHistories[id];
      const pred = this.predictedPaths[id] || [];
      hist.forEach(p => { allX.push(p[xKey]); allY.push(p[yKey]); });
      pred.forEach(p => { allX.push(p[xKey]); allY.push(p[yKey]); });
    });

    if (allX.length === 0) { this.renderNoData(ctx, W, H); return; }

    let minX = Math.min(...allX), maxX = Math.max(...allX);
    let minY = Math.min(...allY), maxY = Math.max(...allY);
    // Add padding to range
    const rangeX = (maxX - minX) || 10;
    const rangeY = (maxY - minY) || 10;
    minX -= rangeX * 0.1; maxX += rangeX * 0.1;
    minY -= rangeY * 0.1; maxY += rangeY * 0.1;

    const scaleX = plotW / (maxX - minX);
    const scaleY = plotH / (maxY - minY);

    const toSX = v => pad.left + (v - minX) * scaleX;
    const toSY = v => pad.top + plotH - (v - minY) * scaleY;

    // Draw plot background
    ctx.fillStyle = 'rgba(10, 20, 35, 0.7)';
    ctx.fillRect(pad.left, pad.top, plotW, plotH);

    // Grid lines
    ctx.strokeStyle = this.colors.gridLine;
    ctx.lineWidth = 0.4;
    const nGrid = 6;
    ctx.font = '8px "Share Tech Mono", monospace';
    ctx.fillStyle = this.colors.axisLabel;
    ctx.textAlign = 'right';
    for (let i = 0; i <= nGrid; i++) {
      const val = minY + (maxY - minY) * i / nGrid;
      const sy = toSY(val);
      ctx.beginPath(); ctx.moveTo(pad.left, sy); ctx.lineTo(pad.left + plotW, sy); ctx.stroke();
      ctx.fillText(val.toFixed(1), pad.left - 4, sy + 3);
    }
    ctx.textAlign = 'center';
    for (let i = 0; i <= nGrid; i++) {
      const val = minX + (maxX - minX) * i / nGrid;
      const sx = toSX(val);
      ctx.beginPath(); ctx.moveTo(sx, pad.top); ctx.lineTo(sx, pad.top + plotH); ctx.stroke();
      ctx.fillText(val.toFixed(1), sx, pad.top + plotH + 14);
    }

    // Draw axis labels
    ctx.fillStyle = this.colors.text;
    ctx.font = '9px "Share Tech Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText(xLabel, pad.left + plotW / 2, H - 4);

    ctx.save();
    ctx.translate(12, pad.top + plotH / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText(yLabel, 0, 0);
    ctx.restore();

    // Title
    ctx.fillStyle = this.colors.text;
    ctx.font = '10px "Share Tech Mono", monospace';
    ctx.textAlign = 'left';
    ctx.fillText(title, pad.left, pad.top - 8);

    // Draw data
    trackIds.forEach(id => {
      const hist = this.trackHistories[id];
      const pred = this.predictedPaths[id] || [];

      // Flight path (grey line)
      if (hist.length >= 2) {
        ctx.strokeStyle = this.colors.flightPath;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        hist.forEach((p, i) => {
          const sx = toSX(p[xKey]), sy = toSY(p[yKey]);
          if (i === 0) ctx.moveTo(sx, sy); else ctx.lineTo(sx, sy);
        });
        ctx.stroke();
      }

      // Predicted path (blue dashed)
      if (pred.length > 0) {
        ctx.save();
        ctx.shadowColor = this.colors.predictedGlow;
        ctx.shadowBlur = 6;
        ctx.strokeStyle = this.colors.predicted;
        ctx.lineWidth = 2;
        ctx.setLineDash([4, 3]);
        ctx.beginPath();
        const last = hist[hist.length - 1];
        ctx.moveTo(toSX(last[xKey]), toSY(last[yKey]));
        pred.forEach(p => ctx.lineTo(toSX(p[xKey]), toSY(p[yKey])));
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.restore();

        // Predicted dots
        pred.forEach(p => {
          ctx.fillStyle = this.colors.predicted;
          ctx.beginPath();
          ctx.arc(toSX(p[xKey]), toSY(p[yKey]), 2.5, 0, Math.PI * 2);
          ctx.fill();
        });
      }

      // Actual dots (orange)
      const actualSlice = hist.slice(-40);
      actualSlice.forEach(p => {
        ctx.fillStyle = this.colors.actual;
        ctx.beginPath();
        ctx.arc(toSX(p[xKey]), toSY(p[yKey]), 3, 0, Math.PI * 2);
        ctx.fill();
      });
    });
  }
}

// Initialize global trajectory visualizer
window.addEventListener('DOMContentLoaded', () => {
  window.trajViz = new TrajectoryVisualizer('trajectoryCanvas');
});
