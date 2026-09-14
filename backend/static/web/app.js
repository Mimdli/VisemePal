import { DigitalHuman, PRESETS, sharedRig } from "./avatar.js";

const state = {
  lessons: [],
  selected: null,
  audioBlob: null,
  recording: false,
  recorder: null,
};

const practiceHuman = new DigitalHuman({
  front: document.getElementById("practice-front"),
  side: document.getElementById("practice-side"),
});
const inspectHuman = new DigitalHuman({
  front: document.getElementById("inspect-front"),
  side: document.getElementById("inspect-side"),
});
practiceHuman.onFrame = (frame) => highlightTrack("practice-track", frame);
const $ = (id) => document.getElementById(id);

document.querySelectorAll(".tabs button").forEach((button) => {
  button.addEventListener("click", () => showTab(button.dataset.tab));
});

function showTab(name) {
  document.querySelectorAll(".tabs button").forEach((button) => {
    button.classList.toggle("active", button.dataset.tab === name);
  });
  document.querySelectorAll(".panel").forEach((panel) => {
    panel.classList.toggle("active", panel.id === name);
  });
  if (name === "records") loadRecords();
  if (name === "plan") loadPlan();
  if (name === "viseme") {
    loadPhonemes();
    sharedRig.mount($("inspect-front"));
  }
  if (name === "practice") sharedRig.mount($("practice-front"));
}

async function api(path, options) {
  const response = await fetch(path, options);
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      detail = body.detail || JSON.stringify(body);
    } catch (_) {
      /* keep status text */
    }
    throw new Error(detail);
  }
  const type = response.headers.get("content-type") || "";
  if (type.includes("application/json")) return response.json();
  return response.text();
}

async function loadStatus() {
  try {
    const health = await api("/health");
    $("status").innerHTML = `
      <span class="pill ok">服务正常</span>
      <span class="pill ${health.ise_ready ? "ok" : "warn"}">ISE ${health.ise_ready ? "已配置" : "占位"}</span>
      <span class="pill ${health.llm_ready ? "ok" : "warn"}">DeepSeek ${health.llm_ready ? "已配置" : "规则推荐"}</span>
      <a class="pill" href="/docs" target="_blank" rel="noreferrer">API 文档</a>
    `;
  } catch (error) {
    $("status").innerHTML = `<span class="pill warn">${error.message}</span>`;
  }
}

async function loadLessons() {
  const lessons = await api("/lessons");
  state.lessons = lessons;
  $("lessons").innerHTML = lessons
    .map(
      (lesson) => `
      <button type="button" class="lesson" data-id="${lesson.id}">
        <b>${lesson.title}</b>
        <span class="ipa">${lesson.text} ${lesson.ipa}</span>
      </button>`,
    )
    .join("");
  $("lessons").querySelectorAll(".lesson").forEach((node) => {
    node.addEventListener("click", () => selectLesson(Number(node.dataset.id)));
  });
  if (lessons[0]) selectLesson(lessons[0].id);
}

function selectLesson(id) {
  const lesson = state.lessons.find((item) => item.id === id);
  if (!lesson) return;
  state.selected = lesson;
  state.audioBlob = null;
  document.querySelectorAll(".lesson").forEach((node) => {
    node.classList.toggle("active", Number(node.dataset.id) === id);
  });
  $("practice-title").textContent = lesson.title;
  $("practice-meta").textContent = `${lesson.text}  ${lesson.ipa}  ·  ${lesson.tip}`;
  renderTrack("practice-track", lesson.viseme_track);
  const focus = lesson.viseme_track?.frames?.find((frame) => frame.focus);
  if (focus) practiceHuman.hold(focus.pose, `/${focus.phoneme}/`, focus.viseme);
  else practiceHuman.hold({});
  const audio = $("demo-audio");
  if (lesson.audio_url) {
    audio.src = lesson.audio_url;
    audio.hidden = false;
  } else {
    audio.removeAttribute("src");
    audio.hidden = true;
  }
  $("play-demo").disabled = !lesson.viseme_track;
  $("rec-btn").disabled = false;
  $("eval-btn").disabled = true;
  $("rec-state").textContent = "可以开始跟读或上传音频。";
}

$("play-demo").addEventListener("click", () => {
  const audio = $("demo-audio");
  const track = state.selected?.viseme_track;
  if (!track) return;
  audio.hidden = false;
  practiceHuman.speak(track, audio.src ? audio : null);
});

$("file-input").addEventListener("change", (event) => {
  const file = event.target.files[0];
  if (!file) return;
  state.audioBlob = file;
  $("eval-btn").disabled = !state.selected;
  $("rec-state").textContent = `已选择文件：${file.name}`;
});

$("rec-btn").addEventListener("click", async () => {
  if (state.recording) {
    const blob = await state.recorder.stop();
    state.recording = false;
    state.audioBlob = blob;
    $("rec-btn").textContent = "开始录音";
    $("eval-btn").disabled = !state.selected;
    $("rec-state").textContent = "录音完成，可以评测。";
    return;
  }
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  state.recorder = await startWavRecorder(stream);
  state.recording = true;
  $("rec-btn").textContent = "停止录音";
  $("rec-state").textContent = "正在录音…再读一遍目标词。";
});

$("eval-btn").addEventListener("click", async () => {
  if (!state.selected || !state.audioBlob) return;
  $("eval-btn").disabled = true;
  $("result").classList.remove("empty");
  $("result").textContent = "正在评测…";
  const data = new FormData();
  data.append("lesson_id", String(state.selected.id));
  data.append("audio", state.audioBlob, state.audioBlob.name || "record.wav");
  try {
    const result = await api("/evaluate", { method: "POST", body: data });
    renderResult(result);
    loadRecords();
  } catch (error) {
    $("result").textContent = `评测失败：${error.message}`;
  } finally {
    $("eval-btn").disabled = false;
  }
});

function renderResult(result) {
  const errors = result.error_phonemes || [];
  $("result").innerHTML = `
    <div class="score">
      <span>总分 ${Math.round(result.overall_score)}</span>
      <span>准确 ${Math.round(result.accuracy)}</span>
      <span>流畅 ${Math.round(result.fluency)}</span>
      <span>完整 ${Math.round(result.completeness)}</span>
      <span>来源 ${result.provider || "stub"}</span>
    </div>
    ${(result.tips || []).map((tip) => `<p>${tip}</p>`).join("")}
    ${errors
      .map(
        (item) =>
          `<button type="button" class="error-btn" data-phoneme="${item.phoneme}">看 /${item.phoneme}/ 口型舌位</button>`,
      )
      .join("")}
  `;
  $("result").querySelectorAll(".error-btn").forEach((button) => {
    button.addEventListener("click", () => {
      showTab("viseme");
      showViseme(button.dataset.phoneme);
    });
  });
}

let phonemePromise = null;

async function loadPhonemes() {
  if (phonemePromise) return phonemePromise;
  phonemePromise = (async () => {
    const items = await api("/phonemes");
    $("phonemes").innerHTML = items
      .map(
        (item) => `
        <button type="button" class="chip" data-ipa="${item.ipa}">
          <b>/${item.ipa}/</b>
          <span>${(item.examples || []).join(" / ")}</span>
        </button>`,
      )
      .join("");
    $("phonemes").querySelectorAll(".chip").forEach((node) => {
      node.addEventListener("click", () => showViseme(node.dataset.ipa));
    });
  })();
  return phonemePromise;
}

async function showViseme(phoneme) {
  await loadPhonemes();
  const viseme = await api(`/visemes/${encodeURIComponent(phoneme)}`);
  document.querySelectorAll(".chip").forEach((node) => {
    node.classList.toggle("active", node.dataset.ipa === viseme.phoneme);
  });
  inspectHuman.hold(viseme.pose || {}, `/${viseme.phoneme}/`, viseme.oculus);
  $("viseme-text").classList.remove("empty");
  $("viseme-text").innerHTML = `
    <p><b>/${viseme.phoneme}/</b> · Oculus viseme <b>${viseme.oculus}</b></p>
    <p>口型：${viseme.mouth_shape}</p>
    <p>舌位：${viseme.tongue_position}</p>
    <p>${viseme.child_tip}</p>
  `;
}

function renderTrack(id, track) {
  const node = $(id);
  if (!node) return;
  if (!track) {
    node.innerHTML = "";
    return;
  }
  node.innerHTML = (track.frames || [])
    .filter((frame) => frame.phoneme)
    .map(
      (frame) =>
        `<span data-start="${frame.start_ms}" data-phoneme="${frame.phoneme}" class="${frame.focus ? "focus" : ""}">/${frame.phoneme}/</span>`,
    )
    .join("");
  node.querySelectorAll("span").forEach((span) => {
    span.addEventListener("click", () => {
      const phone = span.dataset.phoneme;
      const frame = (track.frames || []).find((item) => String(item.start_ms) === span.dataset.start);
      if (frame) practiceHuman.hold(frame.pose, `/${phone}/`, frame.viseme);
      showTab("viseme");
      showViseme(phone);
    });
  });
}

function highlightTrack(id, frame) {
  const node = $(id);
  if (!node) return;
  node.querySelectorAll("span").forEach((span) => {
    span.classList.toggle("on", Boolean(frame && span.dataset.start === String(frame.start_ms)));
  });
}

const LOOK_KEY = "visemepal-look";

function applyLook(name, customUrl) {
  if (!PRESETS[name] && !customUrl) return;
  const look = PRESETS[name] ? name : "peach";
  inspectHuman.look = look;
  localStorage.setItem(LOOK_KEY, look);
  document.querySelectorAll("[data-looks] button").forEach((button) => {
    button.classList.toggle("active", button.dataset.look === look);
  });
  if (!customUrl && sharedRig.ready && sharedRig.look === look) return;
  practiceHuman.setLook(look, customUrl).catch((error) => {
    $("rec-state").textContent = error.message;
  });
}

function renderLooks() {
  const html = Object.entries(PRESETS)
    .map(([key, value]) => `<button type="button" data-look="${key}">${value.name}</button>`)
    .join("");
  document.querySelectorAll("[data-looks]").forEach((node) => {
    node.innerHTML = html;
    node.querySelectorAll("button").forEach((button) => {
      button.addEventListener("click", () => applyLook(button.dataset.look));
    });
  });
  applyLook(localStorage.getItem(LOOK_KEY) || "peach");
}

async function loadRecords() {
  const [stats, records] = await Promise.all([api("/records/stats"), api("/records")]);
  $("stats").innerHTML = `
    <p>练习次数 <b>${stats.practice_count}</b></p>
    <p>平均分 <b>${stats.average_score}</b></p>
    <p>高频错误：${
      stats.top_errors.length
        ? stats.top_errors.map((item) => `/${item.phoneme}/ × ${item.count}`).join("，")
        : "暂无"
    }</p>
  `;
  $("record-list").innerHTML = records.length
    ? records
        .map(
          (item) => `
      <div class="record">
        课程 #${item.lesson_id} · ${Math.round(item.overall_score)} 分
        · ${item.error_phonemes.join(" / ") || "无明显错误音素"}
        <div class="hint">${item.created_at}</div>
      </div>`,
        )
        .join("")
    : "<p class='hint'>还没有记录。</p>";
}

async function loadPlan() {
  $("plan-body").textContent = "生成中…";
  try {
    const plan = await api("/recommend");
    $("plan-source").textContent = `来源：${plan.source === "deepseek" ? "DeepSeek" : "规则推荐"}`;
    $("plan-body").innerHTML = `
      <h3>${plan.plan_title}</h3>
      <p>${plan.summary}</p>
      ${(plan.items || [])
        .map(
          (item) => `
        <div class="record">
          <b>${item.title}</b>
          <div>${item.text}</div>
          <div class="hint">${item.reason} · 焦点音素 ${(item.focus_phonemes || []).join(" ")}</div>
        </div>`,
        )
        .join("")}
    `;
  } catch (error) {
    $("plan-body").textContent = error.message;
  }
}

$("refresh-plan").addEventListener("click", loadPlan);

async function startWavRecorder(stream) {
  const context = new AudioContext();
  const source = context.createMediaStreamSource(stream);
  const processor = context.createScriptProcessor(4096, 1, 1);
  const gain = context.createGain();
  gain.gain.value = 0;
  const chunks = [];
  processor.onaudioprocess = (event) => {
    chunks.push(new Float32Array(event.inputBuffer.getChannelData(0)));
  };
  source.connect(processor);
  processor.connect(gain);
  gain.connect(context.destination);
  return {
    async stop() {
      processor.disconnect();
      source.disconnect();
      stream.getTracks().forEach((track) => track.stop());
      const blob = encodeWav(chunks, context.sampleRate);
      await context.close();
      return blob;
    },
  };
}

function encodeWav(buffers, sampleRate) {
  let length = 0;
  buffers.forEach((part) => {
    length += part.length;
  });
  const pcm = new Int16Array(length);
  let offset = 0;
  buffers.forEach((part) => {
    for (let i = 0; i < part.length; i += 1, offset += 1) {
      const sample = Math.max(-1, Math.min(1, part[i]));
      pcm[offset] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
    }
  });
  const bytes = pcm.byteLength;
  const buffer = new ArrayBuffer(44 + bytes);
  const view = new DataView(buffer);
  const ascii = (at, text) => {
    for (let i = 0; i < text.length; i += 1) view.setUint8(at + i, text.charCodeAt(i));
  };
  ascii(0, "RIFF");
  view.setUint32(4, 36 + bytes, true);
  ascii(8, "WAVE");
  ascii(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  ascii(36, "data");
  view.setUint32(40, bytes, true);
  new Uint8Array(buffer, 44).set(new Uint8Array(pcm.buffer));
  return new File([buffer], "record.wav", { type: "audio/wav" });
}

async function bootAvatar() {
  sharedRig.mount($("practice-front"));
  try {
    await sharedRig.init();
    sharedRig.mount($("practice-front"));
    renderLooks();
  } catch (error) {
    $("rec-state").textContent = error.message;
    renderLooks();
  }
}

$("avatar-url-apply").addEventListener("click", () => {
  const url = $("avatar-url").value.trim();
  if (!url) return;
  applyLook("peach", url);
});

loadStatus();
loadLessons();
loadPhonemes();
loadRecords();
bootAvatar();
