// 월별 관심도 선 그래프 (라이브러리 없이 SVG로 직접 그림)
// 단일 시리즈라 범례 없이 제목으로 대신하고, 최고점에만 직접 라벨을 단다.
(function () {
  const SVG_NS = "http://www.w3.org/2000/svg";
  const PAD = { top: 24, right: 16, bottom: 28, left: 36 };

  function el(name, attrs = {}) {
    const node = document.createElementNS(SVG_NS, name);
    for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
    return node;
  }

  function renderTrendChart(container, rows) {
    container.innerHTML = "";
    if (!rows.length) {
      const empty = document.createElement("div");
      empty.className = "chart-empty";
      empty.textContent = "데이터가 없어요.";
      container.appendChild(empty);
      return;
    }

    const data = [...rows].sort((a, b) => a.date.localeCompare(b.date));
    const width = container.clientWidth || 800;
    const height = container.clientHeight || 280;
    const innerW = width - PAD.left - PAD.right;
    const innerH = height - PAD.top - PAD.bottom;

    const x = (i) => PAD.left + (data.length === 1 ? innerW / 2 : (i / (data.length - 1)) * innerW);
    const y = (v) => PAD.top + innerH - (v / 100) * innerH;

    const svg = el("svg", { viewBox: `0 0 ${width} ${height}`, role: "img" });

    // 가로 격자 + y축 눈금 (0~100 고정 스케일)
    for (const v of [0, 25, 50, 75, 100]) {
      svg.appendChild(el("line", { class: "grid-line", x1: PAD.left, x2: width - PAD.right, y1: y(v), y2: y(v) }));
      const t = el("text", { class: "axis-label", x: PAD.left - 8, y: y(v) + 4, "text-anchor": "end" });
      t.textContent = v;
      svg.appendChild(t);
    }

    // x축: 연도 시작(1월)마다 라벨, 화면이 좁으면 간격을 늘린다
    const yearIdx = data.map((d, i) => (d.date.endsWith("-01") ? i : -1)).filter((i) => i >= 0);
    const step = Math.max(1, Math.ceil(yearIdx.length / Math.max(1, Math.floor(innerW / 60))));
    yearIdx.forEach((i, n) => {
      if (n % step) return;
      const t = el("text", { class: "axis-label", x: x(i), y: height - 8, "text-anchor": "middle" });
      t.textContent = data[i].date.slice(0, 4);
      svg.appendChild(t);
    });

    // 선
    const d = data.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p.value).toFixed(1)}`).join("");
    svg.appendChild(el("path", { class: "series-line", d }));

    // 최고점 직접 라벨
    let peak = 0;
    data.forEach((p, i) => { if (p.value > data[peak].value) peak = i; });
    svg.appendChild(el("circle", { class: "peak-dot", cx: x(peak), cy: y(data[peak].value), r: 4 }));
    const nearRight = x(peak) > width - 120;
    const label = el("text", {
      class: "peak-label",
      x: x(peak) + (nearRight ? -8 : 8),
      y: y(data[peak].value) - 8,
      "text-anchor": nearRight ? "end" : "start",
    });
    label.textContent = `최고점 ${data[peak].value} (${data[peak].date})`;
    svg.appendChild(label);

    // 호버 레이어: 세로 크로스헤어 + 점 + 툴팁 (가장 가까운 월로 스냅)
    const cross = el("line", { class: "crosshair", y1: PAD.top, y2: PAD.top + innerH, visibility: "hidden" });
    const dot = el("circle", { class: "hover-dot", r: 5, visibility: "hidden" });
    const hit = el("rect", { x: PAD.left, y: 0, width: innerW, height, fill: "transparent" });
    svg.append(cross, dot, hit);
    container.appendChild(svg);

    const tip = document.createElement("div");
    tip.className = "chart-tooltip";
    tip.hidden = true;
    container.appendChild(tip);

    let current = -1;
    function show(i) {
      current = Math.max(0, Math.min(data.length - 1, i));
      const p = data[current];
      const px = x(current);
      const py = y(p.value);
      cross.setAttribute("x1", px);
      cross.setAttribute("x2", px);
      dot.setAttribute("cx", px);
      dot.setAttribute("cy", py);
      cross.setAttribute("visibility", "visible");
      dot.setAttribute("visibility", "visible");

      // 사용자 입력(memo)이 들어가므로 textContent로만 채운다
      tip.replaceChildren();
      const strong = document.createElement("strong");
      strong.textContent = p.value;
      const date = document.createElement("span");
      date.className = "tt-date";
      date.textContent = p.date;
      tip.append(strong, date);
      if (p.memo) {
        const memo = document.createElement("span");
        memo.className = "tt-memo";
        memo.textContent = p.memo;
        tip.appendChild(memo);
      }
      tip.hidden = false;
      const scale = container.clientWidth / width;
      const left = Math.min(Math.max(px * scale, 60), container.clientWidth - 60);
      tip.style.left = `${left}px`;
      tip.style.top = `${py * (container.clientHeight / height)}px`;
    }
    function hide() {
      cross.setAttribute("visibility", "hidden");
      dot.setAttribute("visibility", "hidden");
      tip.hidden = true;
    }

    hit.addEventListener("pointermove", (e) => {
      const rect = svg.getBoundingClientRect();
      const sx = ((e.clientX - rect.left) / rect.width) * width;
      show(Math.round(((sx - PAD.left) / innerW) * (data.length - 1)));
    });
    hit.addEventListener("pointerleave", hide);

    // 키보드 접근: 좌우 방향키로 이동
    container.onkeydown = (e) => {
      if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
      e.preventDefault();
      show(current < 0 ? data.length - 1 : current + (e.key === "ArrowRight" ? 1 : -1));
    };
    container.onblur = hide;
  }

  window.renderTrendChart = renderTrendChart;
})();
