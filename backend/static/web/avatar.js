import { TalkingHead } from "talkinghead";

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

const OCULUS = ["sil", "PP", "FF", "TH", "DD", "kk", "CH", "SS", "nn", "RR", "aa", "E", "I", "O", "U"];

const RPM_TARGETS = "ARKit,Oculus Visemes,mouthOpen,mouthSmile,eyesClosed,eyesLookUp,eyesLookDown";

function rpmUrl(idOrUrl) {
  const raw = (idOrUrl || "").trim();
  if (!raw) return "";
  if (raw.startsWith("/")) return raw;
  if (raw.startsWith("http")) {
    const url = new URL(raw);
    if (!url.searchParams.get("morphTargets")) {
      url.searchParams.set("morphTargets", RPM_TARGETS);
      url.searchParams.set("textureSizeLimit", "1024");
      url.searchParams.set("textureFormat", "png");
    }
    return `${window.location.origin}/avatars/fetch?src=${encodeURIComponent(url.toString())}`;
  }
  return `${window.location.origin}/avatars/${raw.replace(/\.glb$/i, "")}.glb`;
}

const PRESETS = {
  peach: {
    name: "小雅",
    body: "F",
    file: "brunette",
    mood: "neutral",
  },
  cocoa: {
    name: "阿凯",
    body: "M",
    file: "avatarsdk",
    mood: "neutral",
  },
  snow: {
    name: "小雪",
    body: "F",
    file: "avaturn",
    mood: "happy",
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
  const w = Number(canvas.getAttribute("width")) || canvas.width || 280;
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

export class AvatarRig {
  constructor() {
    this.node = document.createElement("div");
    this.node.className = "avatar-world";
    this.node.style.width = "320px";
    this.node.style.height = "380px";
    this.head = null;
    this.ready = false;
    this.look = "peach";
    this.currentViseme = "sil";
    this.status = "正在加载真人数字人…";
  }

  async init() {
    if (this.head) return;
    this.head = new TalkingHead(this.node, {
      lipsyncModules: [],
      cameraView: "head",
      cameraZoomEnable: true,
      cameraRotateEnable: true,
      avatarMute: true,
      avatarMood: "neutral",
      modelPixelRatio: Math.min(window.devicePixelRatio || 1, 2),
      modelFPS: 30,
    });
    await this.setLook(this.look);
  }

  mount(host) {
    if (!host) return;
    host.querySelectorAll(".avatar-loading").forEach((node) => node.remove());
    if (this.node.parentElement !== host) {
      host.appendChild(this.node);
    }
    if (!this.ready) {
      let tip = host.querySelector(".avatar-status");
      if (!tip) {
        tip = document.createElement("p");
        tip.className = "avatar-status";
        host.appendChild(tip);
      }
      tip.textContent = this.status;
    } else {
      host.querySelector(".avatar-status")?.remove();
      this.head?.start();
    }
  }

  async setLook(name, customUrl) {
    const spec = { ...(PRESETS[name] || PRESETS.peach) };
    spec.url = customUrl ? rpmUrl(customUrl) : `${window.location.origin}/avatars/${spec.file}.glb`;
    this.look = PRESETS[name] ? name : "peach";
    this.status = `正在加载 ${spec.name}…`;
    this.ready = false;
    if (!this.head) return;
    try {
      await this.head.showAvatar({
        url: spec.url,
        body: spec.body || "F",
        avatarMood: spec.mood || "neutral",
        lipsyncHeadMovement: true,
      });
      this.ready = true;
      this.status = "";
      this.node.parentElement?.querySelector(".avatar-status")?.remove();
      this.head.setView("head");
      this.setViseme(this.currentViseme);
    } catch (error) {
      this.status = `数字人加载失败：${error.message || error}`;
      const host = this.node.parentElement;
      if (host) {
        let tip = host.querySelector(".avatar-status");
        if (!tip) {
          tip = document.createElement("p");
          tip.className = "avatar-status";
          host.appendChild(tip);
        }
        tip.textContent = this.status;
      }
      throw error;
    }
  }

  setViseme(viseme) {
    const key = OCULUS.includes(viseme) ? viseme : "sil";
    this.currentViseme = key;
    if (!this.head?.mtAvatar) return;
    const weight = key === "PP" || key === "FF" ? 0.9 : key === "sil" ? 0 : 0.72;
    OCULUS.forEach((name) => {
      this.head.setValue(`viseme_${name}`, name === key ? weight : 0, 90);
    });
  }
}

export const sharedRig = new AvatarRig();

export class DigitalHuman {
  constructor({ front, side, look = "peach" }) {
    this.front = front;
    this.sideView = prepareCanvas(side);
    this.rig = sharedRig;
    this.look = look;
    this.pose = { ...REST };
    this.target = { ...REST };
    this.track = null;
    this.audio = null;
    this.playing = false;
    this.label = "";
    this.viseme = "sil";
    this.t0 = performance.now();
    this.onFrame = null;
    this._loop = this._loop.bind(this);
    requestAnimationFrame(this._loop);
  }

  setLook(name, customUrl) {
    this.look = name;
    return this.rig.setLook(name, customUrl);
  }

  hold(pose, label = "", viseme = "sil") {
    this.playing = false;
    this.track = null;
    this.label = label;
    this.viseme = viseme || "sil";
    this.target = { ...REST, ...pose };
    this.pose = { ...this.target };
    this.rig.setViseme(this.viseme);
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
    this.rig.setViseme("sil");
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
        this.viseme = frame.viseme || "sil";
        this.label = frame.phoneme ? `/${frame.phoneme}/` : "";
        this.rig.setViseme(this.viseme);
        if (this.onFrame) this.onFrame(frame, timeMs);
      }
      const finished = this.audio ? this.audio.ended : timeMs >= this.track.duration_ms;
      if (finished) {
        this.playing = false;
        this.target = { ...REST };
        this.label = "";
        this.rig.setViseme("sil");
        if (this.onFrame) this.onFrame(null, timeMs);
      }
    }

    Object.keys(REST).forEach((key) => {
      this.pose[key] = lerp(this.pose[key], this.target[key], 1 - Math.exp(-dt * 14));
    });
    this.drawSide();
    requestAnimationFrame(this._loop);
  }

  drawSide() {
    const { ctx, w, h } = this.sideView;
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
    ctx.fillText(this.label || "口腔示意图", 22, 28);
    this.drawTongueChart(ctx, 20, 40, w - 40, h - 78, p);
    ctx.fillStyle = "#5b6666";
    ctx.font = "12px 'PingFang SC', sans-serif";
    ctx.fillText(this.tongueHint(p), 22, h - 18);
  }

  tongueHint(p) {
    if (p.tongue_tip > 0.6) return "舌尖伸到上下齿之间";
    if (p.tongue_high > 0.85 && p.tongue_front < 0.25) return "舌根抬起，贴近软腭";
    if (p.tongue_curl > 0.6) return "舌尖向后卷起";
    if (p.tongue_high > 0.75) return "舌面前部抬高";
    if (p.tongue_high < 0.2 && p.open > 0.55) return "嘴巴张开，舌头放低";
    return "看舌头在口腔里的位置";
  }

  drawTongueChart(ctx, x, y, w, h, p) {
    ctx.fillStyle = "#fff";
    roundRect(ctx, x, y, w, h, 16);
    ctx.fill();

    const ox = x + 18;
    const oy = y + 36;
    ctx.strokeStyle = "#1e2a2a";
    ctx.lineWidth = 2.4;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(ox + 16, oy + 8);
    ctx.quadraticCurveTo(ox + 8, oy + 70, ox + 24, oy + 140);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(ox + 16, oy + 8);
    ctx.quadraticCurveTo(ox + 110, oy - 8, ox + 168, oy + 48);
    ctx.stroke();

    ctx.strokeStyle = "#d2c6b6";
    ctx.lineWidth = 8;
    ctx.beginPath();
    ctx.moveTo(ox + 42, oy + 52);
    ctx.quadraticCurveTo(ox + 110, oy + 28, ox + 152, oy + 64);
    ctx.stroke();

    ctx.fillStyle = "#fff8f2";
    roundRect(ctx, ox + 40, oy + 50, 48, 12, 3);
    ctx.fill();
    const jaw = oy + 108 + Math.min(0.55, p.open) * 28;
    roundRect(ctx, ox + 62, jaw - 14, 36, 10, 3);
    ctx.fill();

    ctx.strokeStyle = "#1e2a2a";
    ctx.beginPath();
    ctx.moveTo(ox + 24, oy + 140);
    ctx.quadraticCurveTo(ox + 80, jaw + 12, ox + 150, jaw);
    ctx.stroke();

    const tipX = ox + 52 + p.tongue_front * 70 + p.tongue_tip * 24;
    const tipY = oy + 116 - p.tongue_high * 46 - p.tongue_curl * 16 + p.open * 8;
    ctx.fillStyle = "#f08b8b";
    ctx.beginPath();
    ctx.moveTo(ox + 36, oy + 120);
    ctx.quadraticCurveTo(ox + 64, tipY + 16, tipX, tipY);
    ctx.quadraticCurveTo(ox + 58, oy + 148, ox + 38, oy + 136);
    ctx.closePath();
    ctx.fill();

    ctx.fillStyle = "#1a7c75";
    ellipse(ctx, tipX, tipY, 3, 3);
    ctx.fill();
    ctx.font = "11px 'PingFang SC', sans-serif";
    ctx.fillText("舌尖", Math.min(tipX + 6, x + w - 40), tipY - 6);
    ctx.fillText("硬腭", ox + 112, oy + 24);
    ctx.fillText("齿", ox + 42, oy + 44);
  }
}

export { PRESETS, REST, mixPose, rpmUrl };
