// Yuan Insight Dashboard — 轮询 /api/state，Fact First 渲染
const POLL_MS = 3000;

const STAGES = ["orient", "diagnose", "implement", "regression", "review", "memory"];

async function poll() {
  try {
    const res = await fetch("/api/state");
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    render(data);
  } catch (err) {
    document.getElementById("sub").textContent = "连接失败: " + err.message;
  }
}

function render(data) {
  document.getElementById("sub").textContent =
    "Observed at " + data.observed_at + " · 每 3s 刷新 · 只读旁路，不影响 Yuan";
  renderWork(data.snapshot);
  renderAgents(data.snapshot, data.signals, data.registry);
  renderSkills(data.snapshot, data.signals, data.registry);
  renderSignals(data.signals, data.coverage);
  renderFootprint(data.footprint);
}

function renderWork(snapshot) {
  const work = snapshot.work || {};
  const status = snapshot.status || {};
  const title = document.getElementById("work-title");
  const state = status.work_state || (work.has_active_work ? "active" : "idle");
  title.innerHTML =
    (status.work || "—") +
    '<span class="state ' + state + '">' + state.toUpperCase() + "</span>";

  // Stage Timeline：stage 之后 done，当前 current
  const currentStage = status.stage;
  const row = document.getElementById("stage-row");
  row.innerHTML = "";
  STAGES.forEach((stage) => {
    const el = document.createElement("div");
    el.className = "stage";
    const idx = STAGES.indexOf(stage);
    const curIdx = STAGES.indexOf(currentStage);
    if (stage === currentStage) el.className += " current";
    else if (curIdx >= 0 && idx < curIdx) el.className += " done";
    el.textContent = stage;
    row.appendChild(el);
  });

  const agent = status.agent || {};
  document.getElementById("agent-current").textContent =
    agent.id ? "Current Agent: " + agent.id + " (" + (agent.state || "?") + ")" : "No active agent";
}

function agentStatus(agentId, snapshot, signals) {
  const status = snapshot.status || {};
  const current = (status.agent || {}).id;
  if (agentId === current) return { cls: "active", tag: (status.agent || {}).state || "ACTIVE" };
  const miss = signals.find((s) => s.entity === agentId && s.level === "MISSING");
  if (miss) return { cls: "missing", tag: "MISSING" };
  return { cls: "optional", tag: "NOT REQUIRED" };
}

function renderAgents(snapshot, signals, registry) {
  const box = document.getElementById("agent-matrix");
  box.innerHTML = "";
  (registry.agents || []).forEach((id) => {
    const st = agentStatus(id, snapshot, signals);
    const tile = document.createElement("div");
    tile.className = "tile " + st.cls;
    tile.innerHTML = '<div class="id">' + id + '</div><div class="tag">' + st.tag + "</div>";
    box.appendChild(tile);
  });
}

function renderSkills(snapshot, signals, registry) {
  const box = document.getElementById("skill-matrix");
  box.innerHTML = "";
  const workflow = snapshot.workflow || {};
  const required = workflow.required_skills || [];
  const observed = extractObservedSkills(snapshot);
  (registry.skills || []).forEach((id) => {
    const tile = document.createElement("div");
    tile.className = "tile";
    if (observed.includes(id)) tile.className += " completed";
    else if (required.includes(id)) tile.className += " missing";
    else tile.className += " optional";
    const tag = observed.includes(id) ? "REPORTED" : required.includes(id) ? "MISSING" : "AVAILABLE";
    tile.innerHTML = '<div class="id">' + id + '</div><div class="tag">' + tag + "</div>";
    box.appendChild(tile);
  });
}

function extractObservedSkills(snapshot) {
  const text = ((snapshot.work || {}).latest_result || "") + "\n" + ((snapshot.work || {}).current_task || "");
  const skills = [];
  let capture = false;
  text.split("\n").forEach((line) => {
    const s = line.trim();
    if (s.includes("skills_applied")) capture = true;
    else if (capture && s.startsWith("-")) skills.push(s.replace(/^-/, "").trim());
    else if (capture && s) capture = false;
  });
  return skills;
}

function renderSignals(signals, coverage) {
  document.getElementById("sig-coverage").textContent = coverage || "UNKNOWN";
  const box = document.getElementById("signals");
  box.innerHTML = "";
  if (!signals.length) {
    box.innerHTML = '<div class="empty">无信号（coverage: ' + coverage + "）</div>";
    return;
  }
  signals.forEach((s, i) => {
    const el = document.createElement("div");
    el.className = "signal";
    el.innerHTML =
      '<span class="lvl ' + s.level + '">' + s.level + "</span>" +
      "<b>" + s.entity + "</b>" +
      '<div class="summary">' + s.summary + "</div>" +
      '<div class="why" id="why-' + i + '">' +
      '<div class="row"><span class="label">Expected</span>' + s.why.expected + "</div>" +
      '<div class="row"><span class="label">Observed</span>' + s.why.observed + "</div>" +
      '<div class="row"><span class="label">Derived</span>' + s.why.derived + "</div>" +
      '<div class="row"><span class="label">Check</span>' + s.why.check + "</div>" +
      "</div>";
    el.onclick = () => {
      const why = el.querySelector(".why");
      why.classList.toggle("open");
    };
    box.appendChild(el);
  });
}

function renderFootprint(fp) {
  document.getElementById("fp-coverage").textContent = fp.coverage || "UNKNOWN";
  const box = document.getElementById("footprint");
  const items = [
    ["references", "References"], ["documents", "Docs"], ["sections", "Sections"],
    ["characters", "Chars"], ["bytes", "Bytes"], ["memory_refs", "Memory"],
  ];
  box.innerHTML = items
    .map(([key, label]) => '<div class="fitem"><div class="num">' + (fp[key] ?? 0) + '</div><div class="lbl">' + label + "</div></div>")
    .join("");
}

poll();
setInterval(poll, POLL_MS);
