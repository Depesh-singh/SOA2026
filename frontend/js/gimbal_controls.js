/**
 * CINEMATIC AIR FORCE STRATEGIC COMMAND & CONTROL WAR ROOM
 * Master Web Audio API Sound Effects Engine (Movie-Grade Radio Beeps, Klaxon, Lock Tones)
 */

class CinematicWarroomAudio {
  constructor() {
    this.ctx = null;
    this.klaxonOsc = null;
    this.isKlaxonPlaying = false;
  }

  initAudio() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      this.ctx = new AudioCtx();
    }
  }

  // Classic Top Gun / Military VHF Radio Mic-Click Squawk Beep
  playRadioCommsBeep() {
    this.initAudio();
    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(2450, this.ctx.currentTime);
      osc.frequency.setValueAtTime(1750, this.ctx.currentTime + 0.04);

      gain.gain.setValueAtTime(0.12, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.08);

      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + 0.08);
    } catch (e) {}
  }

  // Master ADA Dual-Tone Warble Klaxon Siren
  startAdaKlaxon() {
    this.initAudio();
    if (this.isKlaxonPlaying) return;
    try {
      this.isKlaxonPlaying = true;
      const osc1 = this.ctx.createOscillator();
      const osc2 = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc1.type = 'sawtooth';
      osc2.type = 'square';
      osc1.frequency.setValueAtTime(800, this.ctx.currentTime);
      osc2.frequency.setValueAtTime(1200, this.ctx.currentTime);

      const lfo = this.ctx.createOscillator();
      const lfoGain = this.ctx.createGain();
      lfo.frequency.setValueAtTime(2.2, this.ctx.currentTime);
      lfoGain.gain.setValueAtTime(300, this.ctx.currentTime);

      lfo.connect(osc1.frequency);
      lfo.connect(osc2.frequency);

      gain.gain.setValueAtTime(0.07, this.ctx.currentTime);

      osc1.connect(gain);
      osc2.connect(gain);
      gain.connect(this.ctx.destination);

      lfo.start();
      osc1.start();
      osc2.start();

      this.klaxonOsc = [osc1, osc2, lfo];
    } catch (e) {}
  }

  stopAdaKlaxon() {
    if (this.klaxonOsc) {
      this.klaxonOsc.forEach(osc => {
        try { osc.stop(); } catch (e) {}
      });
      this.klaxonOsc = null;
    }
    this.isKlaxonPlaying = false;
  }

  // Jet Scramble / Afterburner Sound Burst
  playScrambleRoar() {
    this.initAudio();
    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(80, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(350, this.ctx.currentTime + 0.8);

      gain.gain.setValueAtTime(0.18, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.9);

      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + 0.9);
    } catch (e) {}
  }

  // Laser DEW Pulse Sound
  playHardKillLaser() {
    this.initAudio();
    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(160, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(30, this.ctx.currentTime + 0.5);

      gain.gain.setValueAtTime(0.2, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.5);

      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + 0.5);
    } catch (e) {}
  }

  // Directed RF Jammer Chirp
  playSoftKillBeam() {
    this.initAudio();
    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(2400, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(400, this.ctx.currentTime + 0.4);

      gain.gain.setValueAtTime(0.12, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.4);

      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + 0.4);
    } catch (e) {}
  }
}

window.warroomAudio = new CinematicWarroomAudio();
