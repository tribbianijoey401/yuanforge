// Yuan Insight Dashboard — 轮询 /api/state，Fact First 渲染
const POLL_MS = 3000;

function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

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
  renderAgents(data.snapshot, data.signals, data.registry, data.observation, data.coverage);
  renderSkills(data.snapshot, data.signals, data.registry, data.observation, data.coverage);
  renderSignals(data.signals, data.coverage);
  renderFootprint(data.footprint);
  renderMemory(data.signals);
}

function renderWork(snapshot) {
  const work = snapshot.work || {};
  const status = snapshot.status || {};
  const workflow = snapshot.workflow || {};
  const title = document.getElementById("work-title");
  const state = status.work_state || (work.has_active_work ? "active" : "idle");
  title.innerHTML =
    esc(status.work || "—") +
    '<span class="state ' + esc(state) + '">' + esc(state.toUpperCase()) + "</span>";

  // Stage Timeline：stage 之后 done，当前 current
  const currentStage = status.stage;
  const row = document.getElementById("stage-row");
  row.innerHTML = "";
  const stages = workflow.stages || (status.stage ? [status.stage] : []);
  stages.forEach((stage) => {
    const el = document.createElement("div");
    el.className = "stage";
    const idx = stages.indexOf(stage);
    const curIdx = stages.indexOf(currentStage);
    if (stage === currentStage) el.className += " current";
    else if (curIdx >= 0 && idx < curIdx) el.className += " done";
    el.textContent = stage;
    row.appendChild(el);
  });

  const agent = status.agent || {};
  document.getElementById("agent-current").textContent =
    agent.id ? "Current Agent: " + agent.id + " (" + (agent.state || "?") + ")" : "No active agent";
}

function agentStatus(agentId, snapshot, signals, observation, coverage) {
  const status = snapshot.status || {};
  const workflow = snapshot.workflow || {};
  const current = (status.agent || {}).id;
  if (agentId === current) return { cls: "active", tag: (status.agent || {}).state || "ACTIVE" };
  const observed = (observation || {}).agents || [];
  if (observed.includes(agentId)) return { cls: "completed", tag: "COMPLETED" };
  const miss = signals.find(
    (s) => s.level === "MISSING" && (s.entity === agentId || String(s.entity).split("|").includes(agentId))
  );
  if (miss) return { cls: "missing", tag: "MISSING" };
  const required = (workflow.required_agents || []).includes(agentId);
  const group = (workflow.required_agent_groups || []).find((members) => members.includes(agentId));
  if (required || group) {
    return coverage === "FULL"
      ? { cls: "unknown", tag: group ? "ONE OF / PENDING" : "PENDING" }
      : { cls: "unknown", tag: "UNKNOWN" };
  }
  if ((workflow.optional_agents || []).includes(agentId)) return { cls: "optional", tag: "OPTIONAL" };
  return { cls: "optional", tag: "NOT REQUIRED" };
}

function renderAgents(snapshot, signals, registry, observation, coverage) {
  const box = document.getElementById("agent-matrix");
  box.innerHTML = "";
  (registry.agents || []).forEach((id) => {
    const st = agentStatus(id, snapshot, signals, observation, coverage);
    const tile = document.createElement("div");
    tile.className = "tile " + st.cls;
    tile.innerHTML = '<div class="id">' + esc(id) + '</div><div class="tag">' + esc(st.tag) + "</div>";
    box.appendChild(tile);
  });
}

function renderSkills(snapshot, signals, registry, observation, coverage) {
  const box = document.getElementById("skill-matrix");
  box.innerHTML = "";
  const currentAgent = (((snapshot || {}).status || {}).agent || {}).id;
  const observedAgents = Array.from(new Set([
    ...((observation || {}).agents || []),
    currentAgent,
  ].filter(Boolean)));
  const required = Array.from(new Set(observedAgents.flatMap((agentId) =>
    (((registry.agent_skills || {})[agentId] || {}).required || [])
  )));
  const observed = Array.from(new Set([...((observation || {}).skills || []), ...extractObservedSkills(snapshot)]));
  (registry.skills || []).forEach((id) => {
    const tile = document.createElement("div");
    tile.className = "tile";
    const missing = signals.some((s) => s.level === "MISSING" && s.entity === id);
    if (observed.includes(id)) tile.className += " completed";
    else if (missing) tile.className += " missing";
    else if (required.includes(id)) tile.className += " unknown";
    else tile.className += " optional";
    const tag = observed.includes(id)
      ? "REPORTED"
      : missing
        ? "MISSING"
        : required.includes(id)
          ? coverage === "FULL" ? "EXPECTED" : "UNKNOWN"
          : "AVAILABLE";
    tile.innerHTML = '<div class="id">' + esc(id) + '</div><div class="tag">' + esc(tag) + "</div>";
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
      '<span class="lvl ' + esc(s.level) + '">' + esc(s.level) + "</span>" +
      "<b>" + esc(s.entity) + "</b>" +
      '<div class="summary">' + esc(s.summary) + "</div>" +
      '<div class="why" id="why-' + i + '">' +
      '<div class="row"><span class="label">Expected</span>' + esc(s.why.expected) + "</div>" +
      '<div class="row"><span class="label">Observed</span>' + esc(s.why.observed) + "</div>" +
      '<div class="row"><span class="label">Derived</span>' + esc(s.why.derived) + "</div>" +
      '<div class="row"><span class="label">Check</span>' + esc(s.why.check) + "</div>" +
      "</div>";
    el.onclick = () => {
      const why = el.querySelector(".why");
      why.classList.toggle("open");
    };
    box.appendChild(el);
  });
}

function renderMemory(signals) {
  const box = document.getElementById("memory");
  const memorySignals = signals.filter((signal) =>
    String(signal.entity).includes("memory") || String(signal.signal_id).includes("MEMORY")
  );
  box.innerHTML = memorySignals.length
    ? memorySignals.map((signal) => '<div class="tag">' + esc(signal.summary) + "</div>").join("")
    : '<div class="empty">Usage evidence unavailable / no selected Memory</div>';
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

async function renderHistory() {
  const box = document.getElementById("history");
  try {
    const res = await fetch("/api/history");
    const data = await res.json();
    const works = data.works || [];
    if (!works.length) {
      box.innerHTML = '<div class="empty">无历史（Work 完成后自动归档）</div>';
      return;
    }
    box.innerHTML = works
      .map((w) =>
        '<div class="history-item" style="padding:8px;border:1px solid var(--border);border-radius:6px;margin-bottom:6px;font-size:12px">' +
        "<b>" + esc(w.work_id) + "</b>" +
        '<span class="tag" style="float:right">' + esc(w.transition_count) + " transitions</span>" +
        '<div class="tag">stages: ' + esc(w.stages.join(" → ") || "—") + "</div>" +
        '<div class="tag">agents: ' + esc(w.agents.join(", ") || "—") + "</div>" +
        '<div class="tag">skills: ' + esc(w.skills.join(", ") || "—") + "</div>" +
        '<div class="tag">coverage: ' + esc(w.coverage || "UNKNOWN") +
        ' · gaps: ' + esc((w.gaps || []).length) + "</div>" +
        '<div class="tag">' + esc(w.last_observed_at ? "最后观察 " + w.last_observed_at : "") + "</div>" +
        "</div>"
      )
      .join("");
  } catch (err) {
    box.innerHTML = '<div class="empty">历史加载失败</div>';
  }
}

poll();
setInterval(poll, POLL_MS);
setInterval(renderHistory, 5000);
renderHistory();
