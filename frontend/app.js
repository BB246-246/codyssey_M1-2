const API_BASE_URL = ((window.APP_CONFIG && window.APP_CONFIG.API_BASE_URL) || "http://127.0.0.1:8000").replace(/\/+$/, "");

const REQUEST_TIMEOUT_MS = 90_000; // Render 무료 서버 콜드스타트(최대 ~1분) 고려
const WAKE_HINT_DELAY_MS = 3_000;  // 이 시간 넘게 걸리면 "서버 깨우는 중" 안내

const $ = (sel) => document.querySelector(sel);

const state = {
  conversationId: null,
  data: [],
  editingId: null,
  sending: false,
};

/* ---------------- API ---------------- */

let pendingSlow = 0;

function formatError(body, status) {
  const detail = body && body.detail;
  if (Array.isArray(detail)) {
    // FastAPI/Pydantic 검증 오류(422)
    return detail.map((d) => `${(d.loc || []).slice(-1)[0] || ""}: ${d.msg}`).join(", ");
  }
  return detail || `요청 실패 (HTTP ${status})`;
}

async function api(path, { method = "GET", body } = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  const slowTimer = setTimeout(() => {
    pendingSlow += 1;
    $("#wake-banner").hidden = false;
  }, WAKE_HINT_DELAY_MS);

  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
    setStatus("ok");
    if (res.status === 204) return null;
    const json = await res.json().catch(() => null);
    if (!res.ok) throw new Error(formatError(json, res.status));
    return json;
  } catch (err) {
    if (err.name === "AbortError") throw new Error("서버 응답이 너무 늦어요. 잠시 후 다시 시도해 주세요.");
    if (err instanceof TypeError) {
      setStatus("error");
      throw new Error("서버에 연결할 수 없어요. 네트워크 또는 서버 상태를 확인해 주세요.");
    }
    throw err;
  } finally {
    clearTimeout(timeout);
    clearTimeout(slowTimer);
    if (pendingSlow > 0) {
      pendingSlow -= 1;
      if (pendingSlow === 0) $("#wake-banner").hidden = true;
    }
  }
}

function setStatus(kind) {
  const elStatus = $("#server-status");
  const text = { pending: "서버 연결 중…", ok: "서버 연결됨", error: "서버 연결 실패" };
  elStatus.className = `status status-${kind}`;
  elStatus.textContent = text[kind];
}

/* ---------------- 공통 UI ---------------- */

let toastTimer;
function toast(message, isError = false) {
  const t = $("#toast");
  t.textContent = message;
  t.classList.toggle("error", isError);
  t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { t.hidden = true; }, 3000);
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// AI 답변의 제목(#)과 **굵게** 정도만 표시 (먼저 escape 해서 HTML 주입 방지)
function renderMarkdownLite(text) {
  return escapeHtml(text)
    .replace(/^#{1,6}\s+(.+)$/gm, "<strong>$1</strong>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
}

function formatDateTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleString("ko-KR", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

/* ---------------- 탭 / 테마 ---------------- */

function initTabs() {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((t) => {
        t.classList.toggle("active", t === tab);
        t.setAttribute("aria-selected", t === tab);
      });
      const name = tab.dataset.tab;
      $("#view-chat").hidden = name !== "chat";
      $("#view-data").hidden = name !== "data";
      if (name === "data") drawChart(); // 숨겨진 상태에선 크기를 몰라 탭 전환 시 다시 그림
    });
  });
}

function initTheme() {
  $("#theme-toggle").addEventListener("click", () => {
    const root = document.documentElement;
    const isDark = root.dataset.theme
      ? root.dataset.theme === "dark"
      : window.matchMedia("(prefers-color-scheme: dark)").matches;
    const next = isDark ? "light" : "dark";
    root.dataset.theme = next;
    try { localStorage.setItem("theme", next); } catch (e) {}
  });
}

/* ---------------- 데이터 요약 ---------------- */

async function loadSummary() {
  const box = $("#summary");
  try {
    const s = await api("/api/data/summary");
    renderSummary(s);
  } catch (err) {
    box.replaceChildren();
    const p = document.createElement("p");
    p.className = "muted small";
    p.textContent = `요약을 불러오지 못했어요: ${err.message}`;
    box.appendChild(p);
  }
}

function renderSummary(s) {
  const box = $("#summary");
  box.replaceChildren();
  const m = s.metrics;
  const items = [
    ["데이터 기간", s.period, `총 ${s.count}개 (월 단위)`],
    ["최근 트렌드", s.trend.split(" (")[0], s.trend.includes("(") ? s.trend.slice(s.trend.indexOf("(") + 1, -1) : ""],
  ];
  if (m) {
    items.push(
      ["최근 값", `${m.latest}`, `${m.latest_date} · 전년 동월 ${m.yoy_change ? m.yoy_change.split(" (")[1]?.replace(")", "") || "-" : "-"}`],
      ["전체 평균", `${m.average}`, m.recent_12m_average != null ? `최근 12개월 평균 ${m.recent_12m_average}` : ""],
      ["최고 / 최저", `${m.max} / ${m.min}`, `최고 ${m.max_date} · 최저 ${m.min_date}`],
    );
  }
  if (s.peak_season) items.push(["관심 높은 달", s.peak_season.split(" (")[0], "최근 5년 월별 평균 기준"]);

  for (const [label, value, sub] of items) {
    const row = document.createElement("div");
    const dt = document.createElement("dt");
    dt.textContent = label;
    const dd = document.createElement("dd");
    dd.textContent = value;
    if (label === "최근 트렌드" && value.startsWith("상승")) dd.classList.add("trend-up");
    if (label === "최근 트렌드" && value.startsWith("하락")) dd.classList.add("trend-down");
    if (sub) {
      const span = document.createElement("span");
      span.className = "sub";
      span.textContent = sub;
      dd.appendChild(span);
    }
    row.append(dt, dd);
    box.appendChild(row);
  }
}

/* ---------------- 채팅 ---------------- */

function clearMessages() {
  const box = $("#messages");
  box.querySelectorAll(".msg").forEach((n) => n.remove());
  $("#chat-empty").hidden = false;
}

function appendMessage(role, content) {
  $("#chat-empty").hidden = true;
  const div = document.createElement("div");
  div.className = `msg msg-${role}`;
  if (role === "assistant") div.innerHTML = renderMarkdownLite(content);
  else div.textContent = content;
  $("#messages").appendChild(div);
  div.scrollIntoView({ block: "end", behavior: "smooth" });
  return div;
}

function showTyping() {
  $("#chat-empty").hidden = true;
  const div = document.createElement("div");
  div.className = "msg msg-assistant";
  div.innerHTML = '<span class="typing"><span></span><span></span><span></span></span><span class="typing-label">데이터를 살펴보는 중…</span>';
  $("#messages").appendChild(div);
  div.scrollIntoView({ block: "end", behavior: "smooth" });
  return div;
}

function setSending(on) {
  state.sending = on;
  $("#chat-send").disabled = on;
  $("#chat-input").disabled = on;
  $("#chat-send").textContent = on ? "응답 중…" : "전송";
}

async function sendMessage(text) {
  const message = text.trim();
  if (!message || state.sending) return;

  appendMessage("user", message);
  $("#chat-input").value = "";
  autoGrow();
  setSending(true);
  const typing = showTyping();

  try {
    const res = await api("/api/chat", {
      method: "POST",
      body: { message, conversation_id: state.conversationId },
    });
    typing.remove();
    appendMessage("assistant", res.reply);
    const isNew = !state.conversationId;
    state.conversationId = res.conversation_id;
    if (isNew) $("#chat-title").textContent = message.length > 30 ? `${message.slice(0, 30)}…` : message;
    loadConversations();
  } catch (err) {
    typing.remove();
    appendMessage("error", `답변을 받지 못했어요: ${err.message}`);
  } finally {
    setSending(false);
    $("#chat-input").focus();
  }
}

function autoGrow() {
  const ta = $("#chat-input");
  ta.style.height = "auto";
  ta.style.height = `${Math.min(ta.scrollHeight, 140)}px`;
}

function initChat() {
  $("#chat-form").addEventListener("submit", (e) => {
    e.preventDefault();
    sendMessage($("#chat-input").value);
  });
  $("#chat-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      sendMessage($("#chat-input").value);
    }
  });
  $("#chat-input").addEventListener("input", autoGrow);
  document.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => sendMessage(chip.textContent));
  });
  $("#new-chat").addEventListener("click", startNewChat);
}

function startNewChat() {
  state.conversationId = null;
  $("#chat-title").textContent = "새 대화";
  clearMessages();
  highlightConversation();
  $("#chat-input").focus();
}

/* ---------------- 대화 기록 ---------------- */

async function loadConversations() {
  try {
    const list = await api("/api/conversations");
    renderConversations(list);
  } catch (err) {
    toast(`대화 목록을 불러오지 못했어요: ${err.message}`, true);
  }
}

function renderConversations(list) {
  const ul = $("#conv-list");
  ul.replaceChildren();
  $("#conv-empty").hidden = list.length > 0;

  for (const c of list) {
    const li = document.createElement("li");
    li.className = "conv-item";
    li.dataset.id = c.id;

    const open = document.createElement("button");
    open.className = "conv-open";
    open.type = "button";
    const title = document.createElement("span");
    title.className = "conv-title";
    title.textContent = c.title || "제목 없음";
    const meta = document.createElement("span");
    meta.className = "conv-meta";
    meta.textContent = `${formatDateTime(c.updated_at)} · 메시지 ${c.message_count}개`;
    open.append(title, meta);
    open.addEventListener("click", () => openConversation(c.id));

    const del = document.createElement("button");
    del.className = "conv-del";
    del.type = "button";
    del.textContent = "✕";
    del.setAttribute("aria-label", `${c.title} 대화 삭제`);
    del.addEventListener("click", () => deleteConversation(c.id, c.title));

    li.append(open, del);
    ul.appendChild(li);
  }
  highlightConversation();
}

function highlightConversation() {
  document.querySelectorAll(".conv-item").forEach((li) => {
    li.classList.toggle("active", li.dataset.id === state.conversationId);
  });
}

async function openConversation(id) {
  if (state.sending) return;
  try {
    const conv = await api(`/api/conversations/${encodeURIComponent(id)}`);
    state.conversationId = conv.id;
    $("#chat-title").textContent = conv.title;
    clearMessages();
    conv.messages.forEach((m) => appendMessage(m.role, m.content));
    highlightConversation();
  } catch (err) {
    toast(`대화를 불러오지 못했어요: ${err.message}`, true);
  }
}

async function deleteConversation(id, title) {
  if (!confirm(`'${title}' 대화를 삭제할까요?`)) return;
  try {
    await api(`/api/conversations/${encodeURIComponent(id)}`, { method: "DELETE" });
    if (state.conversationId === id) startNewChat();
    toast("대화를 삭제했어요.");
    loadConversations();
  } catch (err) {
    toast(`삭제 실패: ${err.message}`, true);
  }
}

/* ---------------- 데이터 관리 (CRUD) ---------------- */

async function loadData() {
  try {
    state.data = await api("/api/data");
    renderTable();
    drawChart();
  } catch (err) {
    toast(`데이터를 불러오지 못했어요: ${err.message}`, true);
  }
}

function drawChart() {
  if ($("#view-data").hidden) return;
  window.renderTrendChart($("#chart"), state.data);
}

function renderTable(flashId) {
  const tbody = $("#data-tbody");
  tbody.replaceChildren();
  $("#data-count").textContent = `(${state.data.length}개)`;

  // 최신 월이 위로 오게
  const rows = [...state.data].sort((a, b) => b.date.localeCompare(a.date));
  for (const r of rows) {
    const tr = document.createElement("tr");
    if (r.id === state.editingId) tr.classList.add("editing");
    if (r.id === flashId) tr.classList.add("flash");

    const tdDate = document.createElement("td");
    tdDate.textContent = r.date;
    const tdVal = document.createElement("td");
    tdVal.className = "num";
    tdVal.textContent = r.value;
    const tdMemo = document.createElement("td");
    tdMemo.textContent = r.memo || "";
    const tdAct = document.createElement("td");
    tdAct.className = "actions";

    const edit = document.createElement("button");
    edit.className = "btn btn-small";
    edit.type = "button";
    edit.textContent = "수정";
    edit.addEventListener("click", () => startEdit(r));
    const del = document.createElement("button");
    del.className = "btn btn-small btn-danger";
    del.type = "button";
    del.textContent = "삭제";
    del.addEventListener("click", () => deleteData(r));
    tdAct.append(edit, " ", del);

    tr.append(tdDate, tdVal, tdMemo, tdAct);
    tbody.appendChild(tr);
  }
}

function readForm() {
  const date = $("#f-date").value;          // <input type="month"> -> "YYYY-MM"
  const valueRaw = $("#f-value").value;
  const memo = $("#f-memo").value.trim();
  if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(date)) return { error: "월을 선택해 주세요." };
  const value = Number(valueRaw);
  if (valueRaw === "" || !Number.isInteger(value) || value < 0 || value > 100) {
    return { error: "값은 0~100 사이의 정수여야 해요." };
  }
  return { payload: { date, value, memo } };
}

function resetForm() {
  state.editingId = null;
  $("#data-form").reset();
  $("#form-title").textContent = "데이터 추가";
  $("#form-submit").textContent = "추가";
  $("#form-cancel").hidden = true;
  $("#form-error").textContent = "";
  renderTable();
}

function startEdit(row) {
  state.editingId = row.id;
  $("#f-date").value = row.date;
  $("#f-value").value = row.value;
  $("#f-memo").value = row.memo || "";
  $("#form-title").textContent = `데이터 수정 (${row.date})`;
  $("#form-submit").textContent = "저장";
  $("#form-cancel").hidden = false;
  $("#form-error").textContent = "";
  renderTable();
  $("#f-value").focus();
}

async function submitData(e) {
  e.preventDefault();
  const { payload, error } = readForm();
  const errBox = $("#form-error");
  if (error) { errBox.textContent = error; return; }
  errBox.textContent = "";

  const submit = $("#form-submit");
  submit.disabled = true;
  try {
    const editing = state.editingId;
    const saved = editing
      ? await api(`/api/data/${encodeURIComponent(editing)}`, { method: "PUT", body: payload })
      : await api("/api/data", { method: "POST", body: payload });

    if (editing) state.data = state.data.map((d) => (d.id === saved.id ? saved : d));
    else state.data.push(saved);

    toast(editing ? `${saved.date} 데이터를 수정했어요.` : `${saved.date} 데이터를 추가했어요.`);
    resetForm();
    renderTable(saved.id);
    drawChart();
    loadSummary(); // 요약이 바뀌므로 갱신 (AI 답변에도 바로 반영됨)
  } catch (err) {
    errBox.textContent = err.message;
  } finally {
    submit.disabled = false;
  }
}

async function deleteData(row) {
  if (!confirm(`${row.date} (값 ${row.value}) 데이터를 삭제할까요?`)) return;
  try {
    await api(`/api/data/${encodeURIComponent(row.id)}`, { method: "DELETE" });
    state.data = state.data.filter((d) => d.id !== row.id);
    if (state.editingId === row.id) resetForm();
    renderTable();
    drawChart();
    loadSummary();
    toast(`${row.date} 데이터를 삭제했어요.`);
  } catch (err) {
    toast(`삭제 실패: ${err.message}`, true);
  }
}

/* ---------------- 내보내기 ---------------- */

function download(filename, content, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function sortedForExport() {
  return [...state.data]
    .sort((a, b) => a.date.localeCompare(b.date))
    .map(({ date, value, memo }) => ({ date, value, memo: memo || "" }));
}

function exportCsv() {
  const esc = (v) => (/[",\n]/.test(String(v)) ? `"${String(v).replace(/"/g, '""')}"` : String(v));
  const lines = ["date,value,memo", ...sortedForExport().map((r) => [r.date, r.value, r.memo].map(esc).join(","))];
  // 엑셀에서 한글이 깨지지 않도록 BOM 추가
  download("maratang_trend.csv", "﻿" + lines.join("\n"), "text/csv;charset=utf-8");
}

function exportJson() {
  download("maratang_trend.json", JSON.stringify(sortedForExport(), null, 2), "application/json");
}

/* ---------------- 시작 ---------------- */

function initData() {
  $("#data-form").addEventListener("submit", submitData);
  $("#form-cancel").addEventListener("click", resetForm);
  $("#export-csv").addEventListener("click", exportCsv);
  $("#export-json").addEventListener("click", exportJson);
  $("#summary-refresh").addEventListener("click", loadSummary);

  let resizeTimer;
  window.addEventListener("resize", () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(drawChart, 150);
  });
}

async function init() {
  initTabs();
  initTheme();
  initChat();
  initData();

  setStatus("pending");
  try {
    // 콜드스타트 대비: 다른 요청보다 먼저 서버를 깨운다
    await api("/health");
  } catch (err) {
    toast(err.message, true);
  }
  loadSummary();
  loadConversations();
  loadData();
}

init();
