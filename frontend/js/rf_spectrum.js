/**
 * INDIAN AIR FORCE - IACCS AIR DEFENCE SECTOR CONSOLE
 * ESM (Electronic Support Measures) & ECCM Spectrum Analyzer
 * Real-time Wideband RF Signal Strobe & Jamming Detection
 */

class MilitaryESMSpectrum {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.width = this.canvas.width;
    this.height = this.canvas.height;
    this.numChannels = 40;
    this.noiseFloor = -88; // dBm
    this.isJamming = false;
    this.activeChannel = 6; // Initial channel
  }

  updateAndDraw(isJammingActive, activeChannel) {
    this.isJamming = isJammingActive;
    this.activeChannel = activeChannel || this.activeChannel;

    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.width, this.height);

    // 1. Grid & dBm Markers (-100dBm to -20dBm)
    this.drawDbmGrid(ctx);

    // 2. FFT Power Spectral Density Bars
    this.drawFftBars(ctx);

    // 3. Active C2 Frequency Marker & Strobe Alert
    this.drawChannelMarkers(ctx);
  }

  drawDbmGrid(ctx) {
    ctx.save();
    ctx.strokeStyle = 'rgba(26, 54, 93, 0.4)';
    ctx.lineWidth = 1;
    ctx.font = '8px "Share Tech Mono"';
    ctx.fillStyle = '#4a5d78';

    // Horizontal dBm grid lines: -80, -60, -40 dBm
    [-80, -60, -40].forEach(dbm => {
      const y = this.height - ((dbm + 100) / 80) * this.height;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(this.width, y);
      ctx.stroke();
      ctx.fillText(`${dbm} dBm`, 4, y - 2);
    });
    ctx.restore();
  }

  drawFftBars(ctx) {
    const ctx = this.ctx;
    const barWidth = this.width / this.numChannels;

    for (let i = 0; i < this.numChannels; i++) {
      // Calculate signal level
      let powerDbm = this.noiseFloor + (Math.random() * 6 - 3);

      // Signal peaks at Drone C2 bands (CH 6, CH 20, CH 36)
      if (i === this.activeChannel) {
        powerDbm += 38; // Normal C2 encrypted link
      } else if (i === 18) {
        powerDbm += 25; // 2.4GHz Telemetry beacon
      } else if (i === 32) {
        powerDbm += 22; // 5.8GHz FLIR downlink
      }

      // If hostile jamming is active: broadband barrage noise across multiple channels
      if (this.isJamming) {
        powerDbm += (Math.random() * 45 + 15);
      }

      // Convert dBm to screen height
      const barHeight = Math.max(Math.min(((powerDbm + 100) / 80) * this.height, this.height), 2);
      const x = i * barWidth;
      const y = this.height - barHeight;

      // Color coding: Red if jamming or high threat, Cyan/Green if nominal
      ctx.fillStyle = this.isJamming ? 'rgba(255, 42, 58, 0.85)' : (i === this.activeChannel ? 'rgba(0, 229, 255, 0.9)' : 'rgba(0, 255, 102, 0.35)');
      ctx.fillRect(x + 1, y, barWidth - 2, barHeight);

      // Peak hold indicator line
      ctx.fillStyle = this.isJamming ? '#ff2a3a' : '#00e5ff';
      ctx.fillRect(x + 1, y - 2, barWidth - 2, 2);
    }
  }

  drawChannelMarkers(ctx) {
    const barWidth = this.width / this.numChannels;
    const activeX = this.activeChannel * barWidth + (barWidth / 2);

    ctx.save();
    if (this.isJamming) {
      // Hostile Jamming Strobe Banner
      ctx.fillStyle = 'rgba(255, 42, 58, 0.2)';
      ctx.fillRect(0, 0, this.width, 22);
      ctx.fillStyle = '#ff2a3a';
      ctx.font = 'bold 9px "Share Tech Mono"';
      ctx.fillText('⚠️ HOSTILE ELECTRONIC ATTACK (BARRAGE NOISE DETECTED)', 10, 14);
    } else {
      // Active Frequency Hopped Channel Indicator
      ctx.strokeStyle = '#00e5ff';
      ctx.lineWidth = 1;
      ctx.setLineDash([2, 2]);
      ctx.beginPath();
      ctx.moveTo(activeX, 0);
      ctx.lineTo(activeX, this.height);
      ctx.stroke();

      ctx.fillStyle = '#00e5ff';
      ctx.font = 'bold 8px "Share Tech Mono"';
      ctx.fillText(`AFNET SECURE CH-${this.activeChannel}`, Math.max(activeX - 35, 6), 14);
    }
    ctx.restore();
  }
}

window.militaryESM = new MilitaryESMSpectrum('spectrumCanvas');
