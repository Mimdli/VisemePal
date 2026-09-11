const state = {
  lessons: [],
  selected: null,
  audioBlob: null,
  recording: false,
  recorder: null,
};

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
  if (name === "viseme") loadPhonemes();
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
  const audio = $("demo-audio");
  if (lesson.audio_url) {
    audio.src = lesson.audio_url;
    audio.hidden = false;
    $("play-demo").disabled = false;
  } else {
    audio.removeAttribute("src");
    audio.hidden = true;
    $("play-demo").disabled = true;
  }
  $("rec-btn").disabled = false;
  $("eval-btn").disabled = true;
  $("rec-state").textContent = "可以开始跟读或上传音频。";
}

$("play-demo").addEventListener("click", () => {
  const audio = $("demo-audio");
  audio.hidden = false;
  audio.play();
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
      document.querySelector(`.tabs button[data-tab="viseme"]`).classList.add("active");
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
  drawFace(viseme);
  $("viseme-text").classList.remove("empty");
  $("viseme-text").innerHTML = `
    <p><b>/${viseme.phoneme}/</b></p>
    <p>口型：${viseme.mouth_shape}</p>
    <p>舌位：${viseme.tongue_position}</p>
    <p>${viseme.child_tip}</p>
    <p class="hint">动画资源键：${viseme.animation_key}</p>
  `;
}

function drawFace(viseme) {
  const blob = `${viseme.mouth_shape}${viseme.tongue_position}`;
  const open = /大开口|张大|下降/.test(blob) ? 22 : /中开口|微开/.test(blob) ? 10 : 4;
  const round = /圆/.test(blob);
  const bite = /咬|下唇/.test(viseme.mouth_shape);
  const mouth = $("mouth");
  const tongue = $("tongue");
  const left = round ? 92 : 78;
  const right = round ? 128 : 142;
  const mid = 110;
  const top = 154;
  const bottom = top + open;
  if (bite) {
    mouth.setAttribute("d", `M80 158 C110 162 110 162 140 158 M86 166 H134`);
    mouth.setAttribute("fill", "none");
  } else {
    mouth.setAttribute(
      "d",
      `M${left} ${top} Q${mid} ${bottom} ${right} ${top} Q${mid} ${top - 4} ${left} ${top}Z`,
    );
    mouth.setAttribute("fill", "#6b1f1f");
  }
  if (/上卷/.test(viseme.tongue_position)) {
    tongue.setAttribute("d", "M88 170 C110 150 110 150 132 170 C124 186 96 186 88 170Z");
  } else if (/抬高|硬腭/.test(viseme.tongue_position)) {
    tongue.setAttribute("d", "M90 160 C110 148 110 148 130 160 C124 176 96 176 90 160Z");
  } else if (/放低/.test(viseme.tongue_position)) {
    tongue.setAttribute("d", "M88 176 C110 198 110 198 132 176 C120 188 100 188 88 176Z");
  } else if (/上齿|齿龈|伸/.test(viseme.tongue_position)) {
    tongue.setAttribute("d", "M96 168 C110 156 110 156 124 168 C118 186 102 186 96 168Z");
  } else {
    tongue.setAttribute("d", "M90 168 C110 176 110 176 130 168 C128 182 92 182 90 168Z");
  }
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

loadStatus();
loadLessons();
loadPhonemes();
loadRecords();
