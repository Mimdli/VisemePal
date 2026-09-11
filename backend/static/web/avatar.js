const REST = {
  open: 0.08,
  width: 0.35,
  round: 0,
  pucker: 0,
  close: 0,
  bite: 0,
  teeth: 0.15,
  tongue_front: 0.35,
  tongue_high: 0.35,
  tongue_tip: 0,
  tongue_curl: 0,
};

const PRESETS = {
  peach: {
    name: "小桃",
    skin: "#ffd8b5",
    blush: "#ff9aa8",
    hair: "#5a3826",
    shirt: "#2bb3a8",
    eyeWhite: "#fffdf8",
    iris: "#4f7a52",
    lip: "#e56b73",
    accent: "#ff8aa0",
    hairStyle: "bob",
  },
  cocoa: {
    name: "可可",
    skin: "#d19a6c",
    blush: "#e07a6a",
    hair: "#2b1810",
    shirt: "#ff8a65",
    eyeWhite: "#fffdf8",
    iris: "#5c3a24",
    lip: "#c45c58",
    accent: "#ffb347",
    hairStyle: "puffs",
  },
  snow: {
    name: "小雪",
    skin: "#ffe2cf",
    blush: "#ffb3c1",
    hair: "#8b572a",
    shirt: "#7b93e6",
    eyeWhite: "#fffdf8",
    iris: "#4a6fa5",
    lip: "#e07a84",
    accent: "#c5d0ff",
    hairStyle: "tails",
  },
};

function lerp(a, b, t) {
  return a + (b - a) * t;
}

function mixPose(from, to, t) {
  const out = {};
  Object.keys(REST).forEach((key) => {
    out[key] = lerp(from[key] ?? REST[key], to[key] ?? REST[key], t);
  });
  return out;
}

function prepareCanvas(canvas) {
  const w = Number(canvas.getAttribute("width")) || canvas.width || 320;
  const h = Number(canvas.getAttribute("height")) || canvas.height || 380;
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.round(w * dpr);
  canvas.height = Math.round(h * dpr);
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { w, h, ctx };
}

function roundRect(ctx, x, y, w, h, r) {
  const radius = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.arcTo(x + w, y, x + w, y + h, radius);
  ctx.arcTo(x + w, y + h, x, y + h, radius);
  ctx.arcTo(x, y + h, x, y, radius);
  ctx.arcTo(x, y, x + w, y, radius);
  ctx.closePath();
}

function ellipse(ctx, x, y, rx, ry) {
  ctx.beginPath();
  ctx.ellipse(x, y, rx, ry, 0, 0, Math.PI * 2);
}

export class DigitalHuman {
  constructor({ front, side, look = "peach" }) {
    this.frontCanvas = front;
    this.sideCanvas = side;
    this.frontView = prepareCanvas(front);
    this.sideView = prepareCanvas(side);
    this.look = { ...PRESETS[look] };
    this.pose = { ...REST };
    this.target = { ...REST };
    this.track = null;
    this.audio = null;
    this.playing = false;
    this.label = "";
    this.blink = 0;
    this.t0 = performance.now();
    this.onFrame = null;
    this._loop = this._loop.bind(this);
    requestAnimationFrame(this._loop);
  }

  setLook(name) {
    if (PRESETS[name]) this.look = { ...PRESETS[name] };
  }

  hold(pose, label = "") {
    this.playing = false;
    this.track = null;
    this.label = label;
    this.target = { ...REST, ...pose };
    this.pose = { ...this.target };
  }

  speak(track, audio, { play = true } = {}) {
    this.track = track;
    this.audio = audio || null;
    this.playing = true;
    this.startedAt = performance.now();
    if (this.audio && play) {
      this.audio.currentTime = 0;
      const start = () => {
        this.startedAt = performance.now();
        this.audio.play().catch(() => {});
      };
      if (this.audio.readyState >= 1) start();
      else this.audio.addEventListener("loadedmetadata", start, { once: true });
    }
  }

  stop() {
    this.playing = false;
    this.target = { ...REST };
    if (this.audio) this.audio.pause();
  }

  currentFrame(timeMs) {
    if (!this.track) return null;
    const frames = this.track.frames || [];
    let current = frames[0] || null;
    frames.forEach((frame) => {
      if (timeMs >= frame.start_ms) current = frame;
    });
    return current;
  }

  _loop(now) {
    const dt = Math.min(0.05, (now - this.t0) / 1000);
    this.t0 = now;
    const cycle = (now / 1000) % 3.6;
    this.blink = cycle < 0.16 ? Math.sin((cycle / 0.16) * Math.PI) : 0;
    this.bob = Math.sin(now / 740) * (this.playing ? 0.6 : 1.8);

    if (this.playing && this.track) {
      let timeMs = 0;
      if (this.audio && Number.isFinite(this.audio.currentTime) && !this.audio.paused && !this.audio.ended) {
        timeMs = this.audio.currentTime * 1000;
      } else if (this.audio && this.audio.ended) {
        timeMs = this.track.duration_ms;
      } else {
        timeMs = performance.now() - (this.startedAt || performance.now());
      }
      const frame = this.currentFrame(timeMs);
      if (frame) {
        this.target = { ...REST, ...frame.pose };
        this.label = frame.phoneme ? `/${frame.phoneme}/` : "";
        if (this.onFrame) this.onFrame(frame, timeMs);
      }
      const finished = this.audio ? this.audio.ended : timeMs >= this.track.duration_ms;
      if (finished) {
        this.playing = false;
        this.target = { ...REST };
        this.label = "";
        if (this.onFrame) this.onFrame(null, timeMs);
      }
    }

    Object.keys(REST).forEach((key) => {
      this.pose[key] = lerp(this.pose[key], this.target[key], 1 - Math.exp(-dt * 14));
    });
    this.drawFront();
    this.drawSide();
    requestAnimationFrame(this._loop);
  }

  drawFront() {
    const { ctx, w, h } = this.frontView;
    const look = this.look;
    const p = this.pose;
    ctx.clearRect(0, 0, w, h);
    const bg = ctx.createLinearGradient(0, 0, 0, h);
    bg.addColorStop(0, "#fffaf3");
    bg.addColorStop(1, "#f3ece2");
    ctx.fillStyle = bg;
    roundRect(ctx, 8, 8, w - 16, h - 16, 28);
    ctx.fill();

    ctx.save();
    ctx.translate(0, this.bob);

    this.drawBody(ctx, 160, 318, look);
    this.drawHairBack(ctx, 160, 156, look);
    this.drawNeck(ctx, 160, 252, look);
    this.drawHead(ctx, 160, 156, look);
    this.drawEars(ctx, 160, 168, look);
    this.drawHairFront(ctx, 160, 156, look);
    this.drawFace(ctx, 160, 156, p, look);

    ctx.restore();

    if (this.label) {
      ctx.fillStyle = "#1a7c75";
      ctx.font = "600 13px 'PingFang SC', sans-serif";
      ctx.fillText(this.label, 22, 32);
    }
  }

  drawBody(ctx, x, y, look) {
    ctx.fillStyle = "rgba(30, 42, 42, 0.08)";
    ellipse(ctx, x, y + 42, 70, 12);
    ctx.fill();
    ctx.fillStyle = look.shirt;
    ctx.beginPath();
    ctx.moveTo(x - 70, y + 44);
    ctx.quadraticCurveTo(x - 88, y - 8, x - 28, y - 22);
    ctx.lineTo(x + 28, y - 22);
    ctx.quadraticCurveTo(x + 88, y - 8, x + 70, y + 44);
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = "rgba(255,255,255,0.2)";
    roundRect(ctx, x - 36, y - 4, 28, 14, 7);
    ctx.fill();
  }

  drawNeck(ctx, x, y, look) {
    ctx.fillStyle = look.skin;
    roundRect(ctx, x - 16, y - 8, 32, 34, 12);
    ctx.fill();
  }

  drawHead(ctx, x, y, look) {
    ctx.fillStyle = look.skin;
    ellipse(ctx, x, y, 86, 94);
    ctx.fill();
  }

  drawEars(ctx, x, y, look) {
    ctx.fillStyle = look.skin;
    ellipse(ctx, x - 84, y + 8, 14, 20);
    ctx.fill();
    ellipse(ctx, x + 84, y + 8, 14, 20);
    ctx.fill();
    ctx.fillStyle = look.blush;
    ctx.globalAlpha = 0.35;
    ellipse(ctx, x - 84, y + 10, 8, 10);
    ctx.fill();
    ellipse(ctx, x + 84, y + 10, 8, 10);
    ctx.fill();
    ctx.globalAlpha = 1;
  }

  drawHairBack(ctx, x, y, look) {
    ctx.fillStyle = look.hair;
    if (look.hairStyle === "puffs") {
      ellipse(ctx, x - 78, y - 18, 36, 36);
      ctx.fill();
      ellipse(ctx, x + 78, y - 18, 36, 36);
      ctx.fill();
    } else if (look.hairStyle === "tails") {
      ellipse(ctx, x - 70, y + 46, 22, 38);
      ctx.fill();
      ellipse(ctx, x + 70, y + 46, 22, 38);
      ctx.fill();
      ctx.fillStyle = look.accent;
      ellipse(ctx, x - 70, y + 18, 10, 8);
      ctx.fill();
      ellipse(ctx, x + 70, y + 18, 10, 8);
      ctx.fill();
      ctx.fillStyle = look.hair;
    }
    ellipse(ctx, x, y - 18, 90, 78);
    ctx.fill();
  }

  drawHairFront(ctx, x, y, look) {
    ctx.fillStyle = look.hair;
    ctx.beginPath();
    ctx.moveTo(x - 82, y - 24);
    ctx.quadraticCurveTo(x - 50, y - 92, x, y - 98);
    ctx.quadraticCurveTo(x + 50, y - 92, x + 82, y - 24);
    ctx.quadraticCurveTo(x + 40, y - 8, x + 18, y - 28);
    ctx.quadraticCurveTo(x, y - 6, x - 18, y - 28);
    ctx.quadraticCurveTo(x - 40, y - 8, x - 82, y - 24);
    ctx.fill();

    if (look.hairStyle === "bob") {
      ctx.fillStyle = look.accent;
      ellipse(ctx, x + 48, y - 42, 11, 11);
      ctx.fill();
      ctx.fillStyle = "#fff6";
      ellipse(ctx, x + 45, y - 45, 4, 4);
      ctx.fill();
    }
  }

  drawFace(ctx, x, y, p, look) {
    ctx.fillStyle = look.blush;
    ctx.globalAlpha = 0.38;
    ellipse(ctx, x - 52, y + 28, 18, 10);
    ctx.fill();
    ellipse(ctx, x + 52, y + 28, 18, 10);
    ctx.fill();
    ctx.globalAlpha = 1;

    this.drawEye(ctx, x - 32, y - 4, look, -1);
    this.drawEye(ctx, x + 32, y - 4, look, 1);

    ctx.strokeStyle = look.hair;
    ctx.lineWidth = 3.2;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(x - 48, y - 28);
    ctx.quadraticCurveTo(x - 32, y - 38, x - 14, y - 28);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(x + 14, y - 28);
    ctx.quadraticCurveTo(x + 32, y - 38, x + 48, y - 28);
    ctx.stroke();

    ctx.strokeStyle = "rgba(90, 56, 48, 0.45)";
    ctx.lineWidth = 2.4;
    ctx.beginPath();
    ctx.moveTo(x - 5, y + 18);
    ctx.quadraticCurveTo(x, y + 26, x + 5, y + 18);
    ctx.stroke();

    this.drawMouth(ctx, x, y + 52, p, look);
  }

  drawEye(ctx, x, y, look, dir) {
    const open = 1 - this.blink * 0.92;
    ctx.fillStyle = look.eyeWhite;
    ellipse(ctx, x, y, 16, 18 * Math.max(open, 0.12));
    ctx.fill();

    if (open < 0.22) {
      ctx.strokeStyle = look.hair;
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(x - 15, y);
      ctx.quadraticCurveTo(x, y + 3, x + 15, y);
      ctx.stroke();
      return;
    }

    ctx.save();
    ctx.beginPath();
    ctx.ellipse(x, y, 16, 18 * open, 0, 0, Math.PI * 2);
    ctx.clip();
    ctx.fillStyle = look.iris;
    ellipse(ctx, x + dir * 2, y + 1, 10, 11);
    ctx.fill();
    ctx.fillStyle = "#1a1512";
    ellipse(ctx, x + dir * 2, y + 2, 5, 6);
    ctx.fill();
    ctx.fillStyle = "#fff";
    ellipse(ctx, x - 3, y - 4, 4, 5);
    ctx.fill();
    ellipse(ctx, x + 5, y + 4, 2, 2.4);
    ctx.fill();
    ctx.restore();

    ctx.strokeStyle = look.hair;
    ctx.lineWidth = 2.4;
    ctx.beginPath();
    ctx.moveTo(x - 16, y - 6 * open);
    ctx.quadraticCurveTo(x, y - 16 * open, x + 16, y - 6 * open);
    ctx.stroke();
  }

  drawMouth(ctx, cx, cy, p, look) {
    const closed = p.close > 0.55;
    const open = Math.min(0.82, p.open) * (1 - p.close * 0.95);
    const half = 11 + p.width * 15 - p.round * 6 - p.pucker * 7;
    const height = 5 + open * 32;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";

    if (closed) {
      ctx.strokeStyle = look.lip;
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.moveTo(cx - 10, cy);
      ctx.quadraticCurveTo(cx, cy + 2, cx + 10, cy);
      ctx.stroke();
      return;
    }

    if (open < 0.12) {
      ctx.strokeStyle = look.lip;
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.moveTo(cx - 12, cy);
      ctx.quadraticCurveTo(cx, cy + 6, cx + 12, cy);
      ctx.stroke();
      return;
    }

    ctx.fillStyle = "#9a4552";
    ctx.beginPath();
    ctx.moveTo(cx - half, cy);
    ctx.quadraticCurveTo(cx, cy - 3 + p.round * 5, cx + half, cy);
    ctx.quadraticCurveTo(cx, cy + height, cx - half, cy);
    ctx.fill();

    if (p.teeth > 0.18 && open > 0.2) {
      ctx.fillStyle = "#fff8f2";
      roundRect(ctx, cx - half * 0.58, cy + 1, half * 1.16, Math.min(6, height * 0.28), 2.5);
      ctx.fill();
    }

    if (open > 0.22) {
      const tip = p.tongue_tip;
      ctx.fillStyle = "#f29a9a";
      ellipse(
        ctx,
        cx + (p.tongue_front - 0.45) * 5,
        cy + height * 0.62 - p.tongue_high * 5 - tip * 7,
        6 + tip * 5,
        3.5 + open * 5 + tip * 5,
      );
      ctx.fill();
    }

    ctx.strokeStyle = look.lip;
    ctx.lineWidth = 3.4;
    ctx.beginPath();
    ctx.moveTo(cx - half, cy);
    ctx.quadraticCurveTo(cx, cy - 5 + p.pucker * 4 + p.round * 5, cx + half, cy);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(cx - half + 1, cy + 1);
    ctx.quadraticCurveTo(cx, cy + height + 1, cx + half - 1, cy + 1);
    ctx.stroke();

    if (p.bite > 0.4) {
      ctx.fillStyle = look.skin;
      ellipse(ctx, cx, cy + 9, 15, 5);
      ctx.fill();
      ctx.fillStyle = "#fff8f2";
      roundRect(ctx, cx - 13, cy + 1, 26, 4, 2);
      ctx.fill();
    }
  }

  drawSide() {
    const { ctx, w, h } = this.sideView;
    const look = this.look;
    const p = this.pose;
    ctx.clearRect(0, 0, w, h);
    const bg = ctx.createLinearGradient(0, 0, 0, h);
    bg.addColorStop(0, "#f7fbff");
    bg.addColorStop(1, "#eef4f8");
    ctx.fillStyle = bg;
    roundRect(ctx, 8, 8, w - 16, h - 16, 28);
    ctx.fill();

    ctx.fillStyle = "#1a7c75";
    ctx.font = "600 13px 'PingFang SC', sans-serif";
    ctx.fillText("侧面", 22, 28);

    ctx.save();
    ctx.translate(0, this.bob * 0.3);
    this.drawCuteProfile(ctx, 150, 118, p, look);
    ctx.restore();

    this.drawTongueChart(ctx, 24, 214, w - 48, 132, p);
    ctx.fillStyle = "#5b6666";
    ctx.font = "12px 'PingFang SC', sans-serif";
    ctx.fillText(this.tongueHint(p), 24, h - 18);
  }

  tongueHint(p) {
    if (p.tongue_tip > 0.6) return "舌尖伸到上下齿之间";
    if (p.tongue_high > 0.85 && p.tongue_front < 0.25) return "舌根抬起，贴近软腭";
    if (p.tongue_curl > 0.6) return "舌尖向后卷起";
    if (p.tongue_high > 0.75) return "舌面前部抬高";
    if (p.tongue_high < 0.2 && p.open > 0.55) return "嘴巴张开，舌头放低";
    return "看舌头在口腔里的位置";
  }

  drawCuteProfile(ctx, x, y, p, look) {
    ctx.fillStyle = look.shirt;
    ctx.beginPath();
    ctx.moveTo(x - 28, y + 92);
    ctx.quadraticCurveTo(x - 40, y + 58, x - 6, y + 50);
    ctx.lineTo(x + 22, y + 50);
    ctx.quadraticCurveTo(x + 48, y + 62, x + 36, y + 92);
    ctx.closePath();
    ctx.fill();

    ctx.fillStyle = look.skin;
    roundRect(ctx, x - 2, y + 38, 16, 22, 8);
    ctx.fill();

    ctx.fillStyle = look.hair;
    ellipse(ctx, x - 4, y - 2, 48, 52);
    ctx.fill();

    ctx.fillStyle = look.skin;
    ctx.beginPath();
    ctx.ellipse(x + 4, y + 6, 40, 46, 0.12, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = look.hair;
    ctx.beginPath();
    ctx.moveTo(x - 40, y - 4);
    ctx.quadraticCurveTo(x - 8, y - 58, x + 36, y - 28);
    ctx.quadraticCurveTo(x + 8, y - 12, x - 24, y + 2);
    ctx.fill();

    const eyeOpen = 1 - this.blink * 0.85;
    ctx.fillStyle = look.eyeWhite;
    ellipse(ctx, x + 16, y - 4, 7, 9 * Math.max(eyeOpen, 0.15));
    ctx.fill();
    if (this.blink < 0.7) {
      ctx.fillStyle = look.iris;
      ellipse(ctx, x + 18, y - 3, 4, 5);
      ctx.fill();
      ctx.fillStyle = "#fff";
      ellipse(ctx, x + 16, y - 6, 1.6, 2);
      ctx.fill();
    }

    ctx.strokeStyle = "rgba(90, 56, 48, 0.4)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x + 38, y + 8);
    ctx.quadraticCurveTo(x + 46, y + 14, x + 38, y + 18);
    ctx.stroke();

    ctx.fillStyle = look.blush;
    ctx.globalAlpha = 0.35;
    ellipse(ctx, x + 8, y + 18, 8, 5);
    ctx.fill();
    ctx.globalAlpha = 1;

    const open = Math.min(0.55, p.open) * (1 - p.close * 0.95);
    const mx = x + 34;
    const my = y + 28;
    if (p.close > 0.55 || open < 0.1) {
      ctx.beginPath();
      ctx.moveTo(mx - 8, my);
      ctx.quadraticCurveTo(mx, my + 4, mx + 8, my);
      ctx.lineWidth = 3.4;
      ctx.strokeStyle = look.lip;
      ctx.lineCap = "round";
      ctx.stroke();
    } else {
      ctx.fillStyle = look.lip;
      ctx.beginPath();
      ctx.ellipse(mx, my + open * 6, 7 - p.round * 2, 3 + open * 8, 0.15, 0, Math.PI * 2);
      ctx.fill();
      if (p.tongue_tip > 0.5) {
        ctx.fillStyle = "#f08b8b";
        ellipse(ctx, mx + 6, my + 2, 5, 3);
        ctx.fill();
      }
    }
  }

  drawTongueChart(ctx, x, y, w, h, p) {
    ctx.fillStyle = "#fff";
    roundRect(ctx, x, y, w, h, 16);
    ctx.fill();
    ctx.fillStyle = "#1a7c75";
    ctx.font = "600 12px 'PingFang SC', sans-serif";
    ctx.fillText("口腔示意图", x + 12, y + 20);

    const ox = x + 18;
    const oy = y + 28;
    ctx.strokeStyle = "#1e2a2a";
    ctx.lineWidth = 2.4;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(ox + 16, oy + 8);
    ctx.quadraticCurveTo(ox + 8, oy + 40, ox + 22, oy + 78);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(ox + 16, oy + 8);
    ctx.quadraticCurveTo(ox + 90, oy - 4, ox + 128, oy + 28);
    ctx.stroke();

    ctx.strokeStyle = "#d2c6b6";
    ctx.lineWidth = 7;
    ctx.beginPath();
    ctx.moveTo(ox + 36, oy + 32);
    ctx.quadraticCurveTo(ox + 86, oy + 18, ox + 118, oy + 40);
    ctx.stroke();

    ctx.fillStyle = "#fff8f2";
    roundRect(ctx, ox + 34, oy + 30, 36, 10, 3);
    ctx.fill();
    const jaw = oy + 62 + Math.min(0.55, p.open) * 18;
    roundRect(ctx, ox + 48, jaw - 12, 28, 8, 3);
    ctx.fill();

    ctx.strokeStyle = "#1e2a2a";
    ctx.lineWidth = 2.4;
    ctx.beginPath();
    ctx.moveTo(ox + 22, oy + 78);
    ctx.quadraticCurveTo(ox + 60, jaw + 8, ox + 110, jaw - 4);
    ctx.stroke();

    const tipX = ox + 40 + p.tongue_front * 54 + p.tongue_tip * 20;
    const tipY = oy + 68 - p.tongue_high * 30 - p.tongue_curl * 12 + p.open * 6;
    ctx.fillStyle = "#f08b8b";
    ctx.beginPath();
    ctx.moveTo(ox + 28, oy + 70);
    ctx.quadraticCurveTo(ox + 48, tipY + 12, tipX, tipY);
    ctx.quadraticCurveTo(ox + 44, oy + 86, ox + 30, oy + 80);
    ctx.closePath();
    ctx.fill();

    ctx.fillStyle = "#1a7c75";
    ellipse(ctx, tipX, tipY, 3, 3);
    ctx.fill();
    ctx.font = "11px 'PingFang SC', sans-serif";
    ctx.fillText("舌尖", Math.min(tipX + 6, x + w - 40), tipY - 6);
    ctx.fillText("硬腭", ox + 86, oy + 16);
    ctx.fillText("齿", ox + 34, oy + 26);
  }
}

export { PRESETS, REST, mixPose };
