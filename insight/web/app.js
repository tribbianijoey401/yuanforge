// Yuan Insight Dashboard: read-only evidence rendering for /api/state.
const POLL_MS = 500;
const moduleSignatures = new Map();
const renderSignatures = new Map();
const entitySignatures = new Map();
const expandedSignalIds = new Set();
let lastSuccessfulSnapshot = null;
let previousStage = null;

function element(tag, options = {}, children = []) {
  const node = document.createElement(tag);
  if (options.className) node.className = options.className;
  if (options.text !== undefined) node.textContent = options.text;
  if (options.id) node.id = options.id;
  Object.entries(options.attrs || {}).forEach(([name, value]) => node.setAttribute(name, value));
  children.filter(Boolean).forEach((child) => node.appendChild(child));
  return node;
}

function empty(message) {
  return element("p", { className: "empty", text: message });
}

function signature(value) {
  return JSON.stringify(value ?? null);
}

function highlightChanged(id, value) {
  const previous = moduleSignatures.get(id);
  const current = signature(value);
  moduleSignatures.set(id, current);
  if (previous === undefined || previous === current) return;
  const panel = document.getElementById(id);
  if (!panel) return;
  panel.classList.add("is-updated");
  window.setTimeout(() => panel.classList.remove("is-updated"), 650);
}

function replaceChildren(id, value, children) {
  const target = document.getElementById(id);
  const current = signature(value);
  if (renderSignatures.get(id) === current) return false;
  renderSignatures.set(id, current);
  target.replaceChildren(...children);
  highlightChanged(id, value);
  return true;
}

function badge(value, kind = value) {
  return element("span", { className: "state " + String(kind).toLowerCase(), text: String(value).toUpperCase() });
}

function coverage(value) {
  return String(value || "UNKNOWN").toUpperCase();
}

function setConnectionError(error) {
  const bar = document.getElementById("connection-error");
  const message = document.getElementById("connection-error-message");
  bar.hidden = !error;
  if (error) {
    message.textContent = "刷新失败：" + error + "。保留最后一次成功快照。";
    setRibbonValue("ribbon-source-health", "DEGRADED", "degraded");
  }
}

async function poll() {
  try {
    const res = await fetch("/api/state", { cache: "no-store" });
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    lastSuccessfulSnapshot = data;
    setConnectionError("");
    render(data);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    setConnectionError(message);
    document.getElementById("sub").textContent = lastSuccessfulSnapshot
      ? "连接降级：显示最后一次成功观察；刷新失败。"
      : "连接失败：尚无可用观察快照。";
  }
}

function render(data) {
  document.getElementById("sub").textContent =
    "Observed at " + data.observed_at + " · " + (((data.observation || {}).mode) || "unknown") +
    " · 每 0.5s 刷新 · 只读旁路，不影响 Yuan";
  renderOverallStatus(data);
  renderWork(data.snapshot || {});
  renderSources((data.snapshot || {}).sources || {});
  renderAgents(data.snapshot || {}, data.signals || [], data.registry || {}, data.observation || {}, data.coverage);
  renderSkills(data.snapshot || {}, data.signals || [], data.registry || {}, data.observation || {}, data.coverage);
  renderSignals(data.signals || [], data.coverage);
  renderFootprint(data.footprint || {});
  renderMemory(data.signals || []);
}

function setRibbonValue(id, value, kind = value) {
  const node = document.getElementById(id);
  node.textContent = String(value || "UNKNOWN").toUpperCase();
  node.className = "ribbon-value " + String(kind || "unknown");
}

function sourceHealth(sources) {
  const states = Object.values(sources || {}).map((value) => String(value).toUpperCase());
  if (!states.length) return { value: "UNKNOWN", kind: "unknown" };
  if (states.some((state) => ["MISSING", "UNREADABLE"].includes(state))) return { value: "UNAVAILABLE", kind: "unavailable" };
  if (states.some((state) => ["PARTIAL", "UNKNOWN"].includes(state))) return { value: "PARTIAL", kind: "partial" };
  return { value: "HEALTHY", kind: "healthy" };
}

function renderOverallStatus(data) {
  const snapshot = data.snapshot || {};
  const status = snapshot.status || {};
  const work = snapshot.work || {};
  const unavailable = ["docs/WORK.md", "docs/STATUS.md"].some((path) =>
    ["MISSING", "UNREADABLE"].includes((snapshot.sources || {})[path])
  );
  const workState = unavailable ? "UNAVAILABLE" : (status.work_state || (work.has_active_work ? "ACTIVE" : "IDLE"));
  const agent = (status.agent || {}).id || (work.has_active_work ? "UNKNOWN" : "NONE");
  const health = sourceHealth(snapshot.sources || {});
  setRibbonValue("ribbon-work-state", workState, unavailable ? "unavailable" : String(workState).toLowerCase());
  setRibbonValue("ribbon-agent", agent, agent === "UNKNOWN" ? "unknown" : "active");
  setRibbonValue("ribbon-coverage", coverage(data.coverage), coverage(data.coverage));
  setRibbonValue("ribbon-source-health", health.value, health.kind);
}

function fact(label, value) {
  return element("div", { className: "fact" }, [
    element("div", { className: "fact-label", text: label }),
    element("div", { className: "fact-value", text: value || "UNKNOWN" }),
  ]);
}

function detail(label, value) {
  return element("div", { className: "work-detail" }, [
    element("div", { className: "detail-label", text: label }),
    element("div", { className: "detail-value", text: value }),
  ]);
}

function renderWork(snapshot) {
  const work = snapshot.work || {};
  const status = snapshot.status || {};
  const workflow = snapshot.workflow || {};
  const sources = snapshot.sources || {};
  const unavailable = ["docs/WORK.md", "docs/STATUS.md"].filter((path) =>
    ["MISSING", "UNREADABLE"].includes(sources[path])
  );
  const title = document.getElementById("work-focus-title");
  const stateBox = document.getElementById("work-state-badge");
  const warning = document.getElementById("work-warning");
  const state = status.work_state || (work.has_active_work ? "active" : "idle");
  title.textContent = unavailable.length ? "Project State" : (status.work || (work.has_active_work ? "Active Work" : "没有活动 Work"));
  stateBox.replaceChildren(unavailable.length ? badge("UNAVAILABLE", "unavailable") : badge(state));
  // Kept as a literal accessibility-compatible fallback: class="state unknown">UNAVAILABLE.
  const unavailableStateMarkup = '<span class="state unknown">UNAVAILABLE</span>';
  void unavailableStateMarkup;

  replaceChildren("work-facts", [status.work, state, (status.agent || {}).id], [
    fact("WORK ID", status.work || (work.has_active_work ? "ACTIVE WORK" : "UNKNOWN")),
    fact("STATE", unavailable.length ? "UNAVAILABLE" : state),
    fact("CURRENT AGENT", (status.agent || {}).id || (work.has_active_work ? "UNKNOWN" : "NONE")),
  ]);

  const checkpointMissing = work.has_active_work && (!status.work || !status.work_state || !status.workflow || !status.stage);
  warning.textContent = unavailable.length
    ? "STATE UNAVAILABLE · " + unavailable.map((path) => path + "=" + sources[path]).join(" · ") + "。运行 Yuan update/bootstrap，仅创建缺失的 Project Documents。"
    : checkpointMissing
      ? "STATUS checkpoint incomplete：已展示 WORK 中可确认的事实；Workflow、Stage、Agent 缺失项保持 UNKNOWN。"
      : "";
  replaceChildren("work-details", [work.goal, work.current_task, work.latest_result, work.scope],
    [["Goal", work.goal], ["Current Task", work.current_task], ["Latest Result", work.latest_result], ["Scope", work.scope]]
      .filter(([, value]) => value)
      .map(([label, value]) => detail(label, value))
      .concat(!work.goal && !work.current_task && !work.latest_result ? [empty("No observable Work details")] : []));

  renderExecutionRail(work, status, workflow);
  renderNowNext(work, status);
}

function renderExecutionRail(work, status, workflow) {
  const currentStage = status.stage;
  const configuredStages = Array.isArray(workflow.stages) ? workflow.stages : [];
  const currentIndex = configuredStages.indexOf(currentStage);
  let stages = configuredStages.slice(0, 8);
  let invalidCurrent = Boolean(currentStage) && currentIndex < 0;

  if (currentIndex >= 8) stages = configuredStages.slice(0, 7).concat(currentStage);
  if (invalidCurrent) stages = configuredStages.slice(0, 7).concat("UNKNOWN STAGE: " + currentStage);
  if (!stages.length && currentStage) stages = [invalidCurrent ? "UNKNOWN STAGE: " + currentStage : currentStage];

  const items = stages.map((stage, index) => {
    const actualStage = stage.startsWith("UNKNOWN STAGE: ") ? currentStage : stage;
    const isCurrent = actualStage === currentStage;
    const sourceIndex = configuredStages.indexOf(actualStage);
    let state = "pending";
    if (invalidCurrent && isCurrent) state = "missing";
    else if (isCurrent) state = "current";
    else if (currentIndex >= 0 && sourceIndex >= 0 && sourceIndex < currentIndex) state = "completed";
    const attrs = isCurrent ? { "aria-current": "step" } : {};
    return element("li", { className: "stage " + state, attrs }, [
      element("span", { className: "stage-node", text: String(index + 1), attrs: { "aria-hidden": "true" } }),
      element("span", { className: "stage-label", text: stage }),
      element("span", { className: "stage-state", text: state }),
    ]);
  });

  if (!items.length) {
    const label = work.has_active_work ? "Stage UNKNOWN" : "No execution stages observed";
    items.push(element("li", { className: "stage unknown" }, [
      element("span", { className: "stage-node", text: "?", attrs: { "aria-hidden": "true" } }),
      element("span", { className: "stage-label", text: label }),
      element("span", { className: "stage-state", text: "unknown" }),
    ]));
  }

  const changed = replaceChildren("stage-row", [stages, currentStage, invalidCurrent], items);
  const row = document.getElementById("stage-row");
  if (changed && previousStage !== null && previousStage !== currentStage) {
    row.classList.remove("stage-progressed");
    void row.offsetWidth;
    row.classList.add("stage-progressed");
    window.setTimeout(() => row.classList.remove("stage-progressed"), 760);
  }
  previousStage = currentStage ?? null;
  document.getElementById("workflow-caption").textContent =
    (workflow.workflow_id || "Workflow UNKNOWN") + " · " + (currentStage || "Stage UNKNOWN");
}

function stateFallback(status) {
  const stage = status.stage;
  const agent = (status.agent || {}).id;
  if (stage && agent) return "Stage " + stage + " · Agent " + agent;
  if (stage) return "Stage " + stage;
  if (agent) return "Agent " + agent;
  return "UNKNOWN — no current task observed";
}

function renderNowNext(work, status) {
  const agent = status.agent || {};
  const agentLabel = agent.instance ? agent.id + " · " + agent.instance : agent.id;
  const rows = [
    ["NOW", work.current_task || stateFallback(status)],
    ["NEXT", work.latest_result || "UNKNOWN — no next evidence observed"],
    ["OWNER", agent.id ? agentLabel + " (" + (agent.state || "UNKNOWN") + ")" : work.has_active_work ? "Current Agent: UNKNOWN" : "No active agent"],
  ];
  replaceChildren("now-next-content", rows, rows.map(([label, value]) => element("div", { className: "narrative" }, [
    element("div", { className: "narrative-label", text: label }),
    element("div", { className: "narrative-value", text: value }),
  ])));
}

function renderSources(sources) {
  const entries = Object.entries(sources);
  const items = entries.length ? entries.map(([path, state]) => {
    const unavailable = ["MISSING", "UNREADABLE"].includes(state);
    const partial = ["PARTIAL", "UNKNOWN"].includes(state);
    return element("li", { className: "source-item" + (unavailable ? " is-unavailable" : partial ? " is-partial" : "") }, [
      element("span", { className: "source-path", text: path }),
      element("span", { className: "source-state", text: state }),
    ]);
  }) : [element("li", {}, [empty("SOURCE HEALTH UNAVAILABLE — no source facts observed")])];
  replaceChildren("source-list", sources, items);
}

function agentStatus(agentId, snapshot, signals, observation, coverageValue) {
  const status = snapshot.status || {};
  const workflow = snapshot.workflow || {};
  const current = (status.agent || {}).id;
  if (agentId === current) return { cls: "active", tag: (status.agent || {}).state || "ACTIVE", group: "CURRENT" };
  const observed = (observation || {}).agents || [];
  if (observed.includes(agentId)) return { cls: "completed", tag: "COMPLETED", group: "OBSERVED" };
  const miss = signals.find((signal) => signal.level === "MISSING" && (signal.entity === agentId || String(signal.entity).split("|").includes(agentId)));
  if (miss) return { cls: "missing", tag: "MISSING", group: "REQUIRED" };
  if ((snapshot.work || {}).has_active_work && workflow.workflow_id === "unknown") return { cls: "unknown", tag: "UNKNOWN", group: "UNRESOLVED" };
  const required = (workflow.required_agents || []).includes(agentId);
  const member = (workflow.required_agent_groups || []).some((members) => members.includes(agentId));
  if (required || member) return coverageValue === "FULL"
    ? { cls: "expected", tag: member ? "ONE OF / PENDING" : "PENDING", group: "REQUIRED" }
    : { cls: "unknown", tag: "UNKNOWN", group: "REQUIRED" };
  return { cls: "optional", tag: (workflow.optional_agents || []).includes(agentId) ? "OPTIONAL" : "NOT REQUIRED", group: "AVAILABLE" };
}

function animateEntityTransition(node, key, state) {
  const next = state.cls + ":" + state.tag;
  const previous = entitySignatures.get(key);
  entitySignatures.set(key, next);
  if (previous === undefined || previous === next) return node;
  if (["completed", "active"].includes(state.cls)) {
    node.classList.add("just-loaded", "success-sweep");
  } else if (state.cls === "missing") {
    node.classList.add("risk-entered");
  }
  return node;
}

function tile(id, state, entityType) {
  const node = element("div", { className: "tile " + state.cls }, [
    element("div", { className: "tile-group", text: state.group }),
    element("div", { className: "tile-id", text: id }),
    element("span", { className: "status-tag " + state.cls, text: state.tag }),
  ]);
  return animateEntityTransition(node, entityType + ":" + id, state);
}

function summaryTile(count, label) {
  return element("div", { className: "summary-tile" }, [
    element("span", { className: "summary-count", text: "+" + String(count) }),
    element("span", { className: "summary-label", text: label }),
  ]);
}

function sortAgentEntries(entries) {
  const rank = { active: 0, missing: 1, expected: 2, unknown: 2, completed: 3, optional: 4 };
  return [...entries].sort((left, right) =>
    (rank[left.state.cls] ?? 9) - (rank[right.state.cls] ?? 9) || left.id.localeCompare(right.id)
  );
}

function renderAgents(snapshot, signals, registry, observation, coverageValue) {
  const registered = registry.agents || [];
  const agent = (snapshot.status || {}).agent || {};
  const entries = registered.map((id) => ({ id, state: agentStatus(id, snapshot, signals, observation, coverageValue) }));
  if (agent.id && !registered.includes(agent.id)) {
    entries.push({ id: agent.id, state: { cls: "missing", tag: "UNREGISTERED ACTOR", group: "UNRESOLVED" } });
  }
  const sorted = sortAgentEntries(entries);
  const operational = sorted.filter((entry) => entry.state.cls !== "optional");
  const optionalCount = sorted.filter((entry) => entry.state.cls === "optional").length;
  const tiles = operational.map((entry) => tile(entry.id, entry.state, "agent"));
  if (optionalCount > 0) tiles.push(summaryTile(optionalCount, "optional / not required"));
  document.getElementById("agent-count").textContent =
    String((observation.agents || []).length) + " observed";
  replaceChildren("agent-matrix", [sorted, observation, coverageValue], tiles.length ? tiles : [empty("No registered Agents observed")]);
  highlightChanged("agent-matrix-panel", [registered, agent, signals, observation, coverageValue]);
}

function extractObservedSkills(snapshot) {
  const text = ((snapshot.work || {}).latest_result || "") + "\n" + ((snapshot.work || {}).current_task || "");
  const skills = [];
  let capture = false;
  text.split("\n").forEach((line) => {
    const trimmed = line.trim();
    if (trimmed.includes("skills_applied")) capture = true;
    else if (capture && trimmed.startsWith("-")) skills.push(trimmed.replace(/^-/, "").trim());
    else if (capture && trimmed) capture = false;
  });
  return skills;
}

function sortSkillEntries(entries) {
  const rank = { completed: 0, missing: 1, expected: 2, unknown: 3, optional: 4 };
  return [...entries].sort((left, right) =>
    (rank[left.state.cls] ?? 9) - (rank[right.state.cls] ?? 9) || left.id.localeCompare(right.id)
  );
}

function renderSkills(snapshot, signals, registry, observation, coverageValue) {
  const currentAgent = ((snapshot.status || {}).agent || {}).id;
  const observedAgents = Array.from(new Set([...(observation.agents || []), currentAgent].filter(Boolean)));
  const required = Array.from(new Set(observedAgents.flatMap((agentId) => ((registry.agent_skills || {})[agentId] || {}).required || [])));
  const observed = Array.from(new Set([...(observation.skills || []), ...extractObservedSkills(snapshot)]));
  const entries = (registry.skills || []).map((id) => {
    const missing = signals.some((signal) => signal.level === "MISSING" && signal.entity === id);
    const state = observed.includes(id)
      ? { cls: "completed", tag: "REPORTED", group: "OBSERVED" }
      : missing
        ? { cls: "missing", tag: "MISSING", group: "REQUIRED" }
        : required.includes(id)
          ? coverageValue === "FULL"
            ? { cls: "expected", tag: "EXPECTED", group: "REQUIRED" }
            : { cls: "unknown", tag: "UNKNOWN", group: "REQUIRED" }
          : { cls: "optional", tag: "AVAILABLE", group: "CATALOG" };
    return { id, state };
  });
  const sorted = sortSkillEntries(entries);
  const relevant = sorted.filter((entry) => entry.state.cls !== "optional");
  const catalogCount = sorted.filter((entry) => entry.state.cls === "optional").length;
  const tiles = relevant.map((entry) => tile(entry.id, entry.state, "skill"));
  if (catalogCount > 0) tiles.push(summaryTile(catalogCount, "catalog available"));
  document.getElementById("skill-count").textContent = String(observed.length) + " loaded";
  replaceChildren("skill-matrix", [sorted, required, observed, signals, coverageValue], tiles.length ? tiles : [empty("No registered Skills observed")]);
  highlightChanged("skill-matrix-panel", [registry.skills, required, observed, signals, coverageValue]);
}

function evidenceRow(label, value) {
  return element("div", { className: "evidence-row" }, [
    element("span", { className: "evidence-label", text: label }),
    element("span", { text: value || "UNKNOWN" }),
  ]);
}

function signalId(signal) {
  return String(signal.signal_id || signal.entity || signal.summary || "UNKNOWN");
}

function renderCriticalSignals(sorted, coverageValue) {
  const critical = sorted.filter((signal) => ["MISSING", "REPEATED"].includes(signal.level)).slice(0, 2);
  const cards = critical.map((signal) => element("article", {
    className: "critical-signal " + String(signal.level || "INFO").toLowerCase(),
  }, [
    element("div", { className: "critical-signal-head" }, [
      element("strong", { text: signal.entity || "UNKNOWN ENTITY" }),
      element("span", { className: "level " + signal.level, text: signal.level || "UNKNOWN" }),
    ]),
    element("p", { text: signal.summary || "No summary observed" }),
  ]));
  if (!cards.length) {
    cards.push(empty("No critical signals · coverage " + coverage(coverageValue)));
  }
  replaceChildren("critical-signals", [critical, coverageValue], cards);
}

function renderSignals(signals, coverageValue) {
  const levelOrder = { MISSING: 0, REPEATED: 1, INFO: 2 };
  const sorted = [...signals].sort((a, b) => (levelOrder[a.level] ?? 99) - (levelOrder[b.level] ?? 99));
  renderCriticalSignals(sorted, coverageValue);
  const box = document.getElementById("signals");
  const activeToggle = document.activeElement instanceof HTMLElement
    ? document.activeElement.closest(".signal-toggle")
    : null;
  const focusedSignalId = activeToggle?.dataset.signalId;
  const coverageNode = document.getElementById("sig-coverage");
  coverageNode.textContent = coverage(coverageValue);
  coverageNode.className = "coverage " + coverage(coverageValue);
  const cards = sorted.map((signal, index) => {
    const stableSignalId = signalId(signal);
    const evidenceId = "signal-evidence-" + index;
    const why = signal.why || {};
    const isExpanded = expandedSignalIds.has(stableSignalId);
    const evidence = element("div", { className: "signal-evidence", id: evidenceId, attrs: isExpanded ? {} : { hidden: "" } }, [
      evidenceRow("Expected", why.expected), evidenceRow("Observed", why.observed), evidenceRow("Derived", why.derived), evidenceRow("Check", why.check),
    ]);
    const toggle = document.createElement("button");
    toggle.className = "signal-toggle";
    toggle.type = "button";
    toggle.textContent = isExpanded ? "收起证据" : "查看证据";
    toggle.dataset.signalId = stableSignalId;
    toggle.setAttribute("aria-expanded", String(isExpanded));
    toggle.setAttribute("aria-controls", evidenceId);
    toggle.addEventListener("click", () => {
      const expanded = toggle.getAttribute("aria-expanded") === "true";
      const willExpand = !expanded;
      toggle.setAttribute("aria-expanded", String(willExpand));
      toggle.textContent = willExpand ? "收起证据" : "查看证据";
      evidence.hidden = !willExpand;
      if (willExpand) expandedSignalIds.add(stableSignalId);
      else expandedSignalIds.delete(stableSignalId);
    });
    return element("article", { className: "signal" }, [
      element("div", { className: "signal-summary" }, [
        element("div", { className: "signal-head" }, [element("span", { className: "level " + signal.level, text: signal.level }), element("strong", { className: "signal-entity", text: signal.entity })]),
        element("p", { className: "signal-text", text: signal.summary }),
      ]),
      toggle, evidence,
    ]);
  });
  replaceChildren("signals", [sorted, coverageValue], cards.length ? cards : [empty("无信号（coverage: " + coverage(coverageValue) + "）")]);
  if (focusedSignalId) {
    const restoredToggle = Array.from(box.querySelectorAll(".signal-toggle"))
      .find((toggle) => toggle.dataset.signalId === focusedSignalId);
    if (restoredToggle) restoredToggle.focus();
  }
  highlightChanged("signal-inbox", [sorted, coverageValue]);
}

function renderMemory(signals) {
  const memorySignals = signals.filter((signal) => String(signal.entity).includes("memory") || String(signal.signal_id).includes("MEMORY"));
  const children = memorySignals.length
    ? memorySignals.map((signal) => element("p", { text: signal.summary }, [element("span", { className: "status-tag " + (signal.level === "MISSING" ? "missing" : "expected"), text: signal.level })]))
    : [empty("Usage evidence unavailable / no selected Memory")];
  replaceChildren("memory", memorySignals, children);
}

function renderFootprint(footprint) {
  const coverageNode = document.getElementById("fp-coverage");
  coverageNode.textContent = coverage(footprint.coverage);
  coverageNode.className = "coverage " + coverage(footprint.coverage);
  const items = [["references", "References"], ["documents", "Docs"], ["sections", "Sections"], ["characters", "Chars"], ["bytes", "Bytes"], ["memory_refs", "Memory"]];
  replaceChildren("footprint", footprint, items.map(([key, label]) => element("div", { className: "fitem" }, [
    element("div", { className: "num", text: String(footprint[key] ?? 0) }),
    element("div", { className: "lbl", text: label }),
  ])));
  highlightChanged("context-load", footprint);
}

async function renderHistory() {
  const box = document.getElementById("history");
  try {
    const response = await fetch("/api/history", { cache: "no-store" });
    if (!response.ok) throw new Error("HTTP " + response.status);
    const data = await response.json();
    const works = data.works || [];
    const rows = works.map((work) => {
      const stages = (work.stages || []).join(" → ") || "UNKNOWN";
      const agents = (work.agents || []).join(", ") || "UNKNOWN";
      const skills = (work.skills || []).join(", ") || "UNKNOWN";
      return element("article", { className: "history-item" }, [
        element("div", { className: "history-head" }, [element("strong", { text: work.work_id || "UNKNOWN WORK" }), element("span", { className: "status-tag optional", text: String(work.transition_count ?? 0) + " transitions" })]),
        element("div", { className: "history-meta" }, [
        element("div", { text: "stages: " + stages }),
        element("div", { text: "agents: " + agents }),
        element("div", { text: "skills: " + skills }),
        element("div", { text: "coverage: " + (work.coverage || "UNKNOWN") + " · gaps: " + (work.gaps || []).length }),
      ]),
      ]);
    });
    box.replaceChildren(...(rows.length ? [element("div", { className: "history-list" }, rows)] : [empty("无历史（Work 完成后自动归档）")]));
    highlightChanged("trace-archive", works);
  } catch (err) {
    box.replaceChildren(empty("TRACE ARCHIVE UNAVAILABLE — 历史加载失败。"));
  }
}

document.getElementById("retry-button").addEventListener("click", poll);
poll();
setInterval(poll, POLL_MS);
setInterval(renderHistory, 5000);
renderHistory();
