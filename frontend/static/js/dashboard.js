// ─── Средняя цена м² новостроек Москвы (тыс. руб.), помесячно ─────────────────
// Источник: IRN.ru, Росреестр, ЦИАН (агрегированные данные)
const PRICE_PER_M2 = {
  "2018-01": 168, "2018-02": 169, "2018-03": 170, "2018-04": 171,
  "2018-05": 171, "2018-06": 172, "2018-07": 173, "2018-08": 174,
  "2018-09": 175, "2018-10": 176, "2018-11": 177, "2018-12": 178,
  "2019-01": 179, "2019-02": 180, "2019-03": 181, "2019-04": 182,
  "2019-05": 183, "2019-06": 184, "2019-07": 184, "2019-08": 185,
  "2019-09": 186, "2019-10": 187, "2019-11": 188, "2019-12": 189,
  "2020-01": 190, "2020-02": 191, "2020-03": 191, "2020-04": 193,
  "2020-05": 196, "2020-06": 200, "2020-07": 207, "2020-08": 214,
  "2020-09": 221, "2020-10": 228, "2020-11": 233, "2020-12": 238,
  "2021-01": 243, "2021-02": 248, "2021-03": 252, "2021-04": 256,
  "2021-05": 259, "2021-06": 263, "2021-07": 266, "2021-08": 269,
  "2021-09": 271, "2021-10": 274, "2021-11": 276, "2021-12": 279,
  "2022-01": 281, "2022-02": 283, "2022-03": 291, "2022-04": 287,
  "2022-05": 281, "2022-06": 276, "2022-07": 270, "2022-08": 267,
  "2022-09": 265, "2022-10": 264, "2022-11": 263, "2022-12": 263,
  "2023-01": 264, "2023-02": 265, "2023-03": 266, "2023-04": 267,
  "2023-05": 269, "2023-06": 271, "2023-07": 274, "2023-08": 278,
  "2023-09": 282, "2023-10": 286, "2023-11": 289, "2023-12": 292,
  "2024-01": 295, "2024-02": 298, "2024-03": 300, "2024-04": 303,
  "2024-05": 306, "2024-06": 309, "2024-07": 313, "2024-08": 316,
  "2024-09": 318, "2024-10": 320, "2024-11": 319, "2024-12": 318,
  "2025-01": 316, "2025-02": 314, "2025-03": 313, "2025-04": 312,
  "2025-05": 311, "2025-06": 310, "2025-07": 309, "2025-08": 308,
  "2025-09": 308, "2025-10": 307, "2025-11": 307, "2025-12": 306,
  "2026-01": 305, "2026-02": 305, "2026-03": 305, "2026-04": 305,
};

// ─── Ключевые события для аннотаций на графике ───────────────────────────────
const KEY_EVENTS = [
  { date: "2018-01-01", label: "Санкции США", color: "#f97316" },
  { date: "2020-03-01", label: "COVID-19", color: "#a78bfa" },
  { date: "2020-04-01", label: "Старт льготной ипотеки 6.5%", color: "#34d399" },
  { date: "2022-02-24", label: "Начало СВО", color: "#ef4444" },
  { date: "2022-02-28", label: "Ставка ЦБ 20%", color: "#ef4444" },
  { date: "2022-04-01", label: "Отмена льготной ипотеки обсуждается", color: "#f97316" },
  { date: "2022-07-01", label: "Снижение ставки до 8%", color: "#34d399" },
  { date: "2023-07-01", label: "Отмена льготной ипотеки под давлением", color: "#f97316" },
  { date: "2023-08-15", label: "Курс рубля — экстренное повышение", color: "#ef4444" },
  { date: "2024-07-01", label: "Ставка 18% — исторический максимум", color: "#ef4444" },
  { date: "2024-10-25", label: "Ставка 21%", color: "#ef4444" },
  { date: "2025-06-01", label: "Начало цикла снижения ставки", color: "#34d399" },
];

// ─── Вспомогательные функции ──────────────────────────────────────────────────
window.catLabel = (cat) => ({
  cbr_rate:   "ЦБ: ставка",
  mortgage:   "Ипотека",
  regulation: "Регулир.",
  demand:     "Спрос",
  supply:     "Предлож.",
  macro:      "Макро",
  other:      "Прочее",
}[cat] || cat || "—");

window.scoreClass = (score) => {
  if (score > 0) return "event-score score-up";
  if (score < 0) return "event-score score-down";
  return "event-score score-neutral";
};

window.scoreLabel = (score) => {
  if (score === null || score === undefined) return "—";
  if (score > 0) return `▲ +${score}`;
  if (score < 0) return `▼ ${score}`;
  return "— 0";
};

window.formatDate = (iso) => {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("ru-RU", { day: "2-digit", month: "short", year: "numeric" });
};

// ─── Кастомный плагин: вертикальные линии событий ────────────────────────────
const eventLinesPlugin = {
  id: "eventLines",
  afterDraw(chart, _args, options) {
    const { ctx, scales: { x } } = chart;
    if (!x) return;

    const { top, bottom } = chart.chartArea;
    const events = options.events || [];
    const visibleMin = x.min;
    const visibleMax = x.max;

    // фильтруем только видимые события
    const visible = events.filter(({ date }) => {
      const idx = chart.data.labels.findIndex(l => l >= date.slice(0, 7));
      return idx >= 0 && idx >= visibleMin && idx <= visibleMax;
    });

    const LABEL_H    = 13;   // высота строки подписи
    const LEVELS     = 4;    // количество уровней по высоте
    const levelStep  = (bottom - top) * 0.22; // шаг между уровнями

    visible.forEach(({ date, label, color }, i) => {
      const idx = chart.data.labels.findIndex(l => l >= date.slice(0, 7));
      if (idx < 0) return;
      const xPx  = x.getPixelForValue(idx);
      const level = i % LEVELS;
      const labelY = top + 14 + level * levelStep;

      ctx.save();

      // вертикальная пунктирная линия
      ctx.strokeStyle = color;
      ctx.lineWidth   = 1.2;
      ctx.setLineDash([3, 4]);
      ctx.globalAlpha = 0.75;
      ctx.beginPath();
      ctx.moveTo(xPx, top);
      ctx.lineTo(xPx, bottom);
      ctx.stroke();

      // маркер-точка на линии на уровне подписи
      ctx.globalAlpha = 1;
      ctx.setLineDash([]);
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(xPx, labelY - 2, 3, 0, Math.PI * 2);
      ctx.fill();

      // горизонтальный соединитель от точки до подписи
      const textWidth = ctx.measureText(label).width + 8;
      const boxX = Math.min(xPx + 6, chart.chartArea.right - textWidth - 4);

      ctx.strokeStyle = color;
      ctx.lineWidth   = 0.8;
      ctx.globalAlpha = 0.5;
      ctx.beginPath();
      ctx.moveTo(xPx, labelY - 2);
      ctx.lineTo(boxX, labelY - 2);
      ctx.stroke();

      // фон подписи
      ctx.globalAlpha = 0.9;
      ctx.fillStyle   = "#0f1117";
      ctx.fillRect(boxX, labelY - LABEL_H, textWidth, LABEL_H + 2);

      // текст подписи
      ctx.globalAlpha = 1;
      ctx.fillStyle   = color;
      ctx.font        = "bold 10px Inter, system-ui, sans-serif";
      ctx.textAlign   = "left";
      ctx.textBaseline = "middle";
      ctx.fillText(label, boxX + 4, labelY - LABEL_H / 2);

      ctx.restore();
    });
  },
};

// ─── Alpine.js компонент дашборда ─────────────────────────────────────────────
function dashboard() {
  return {
    summary: {},
    events: [],
    latestKeyEvents: [],
    loading: false,
    total: 0,
    offset: 0,
    pageSize: 20,
    filter: { category: "", price_direction: "", key_only: false },

    async init() {
      await Promise.all([this.loadSummary(), this.loadEvents(true), this.loadRateChart()]);
    },

    async loadSummary() {
      try {
        const r = await fetch("/api/dashboard/summary");
        this.summary = await r.json();
        this.latestKeyEvents = this.summary.latest_key_events || [];
      } catch (e) {
        console.error("Summary load error:", e);
      }
    },

    async loadEvents(reset = false) {
      if (reset) this.offset = 0;
      this.loading = true;
      try {
        const params = new URLSearchParams({ limit: this.pageSize, offset: this.offset });
        if (this.filter.category)        params.set("category", this.filter.category);
        if (this.filter.price_direction) params.set("price_direction", this.filter.price_direction);
        if (this.filter.key_only)        params.set("key_only", "true");
        const r = await fetch(`/api/events?${params}`);
        const data = await r.json();
        this.events = data.items || [];
        this.total  = data.total  || 0;
      } catch (e) {
        console.error("Events load error:", e);
      } finally {
        this.loading = false;
      }
    },

    async loadRateChart() {
      try {
        const r = await fetch("/api/cbr/history?days=3000");
        const rates = await r.json();
        if (!rates.length) return;

        // ── 1. Генерируем единую ось: все месяцы с 2018-01 по сегодня ──────────
        const now = new Date();
        const labels = [];
        const cur = new Date("2018-01-01");
        while (cur <= now) {
          labels.push(cur.toISOString().slice(0, 7));
          cur.setMonth(cur.getMonth() + 1);
        }

        // ── 2. Заполняем ставку ЦБ (ступенчато) ──────────────────────────────
        const rateValues = labels.map(() => null);
        for (let i = 0; i < rates.length; i++) {
          const from  = rates[i].rate_date.slice(0, 7);
          const until = i + 1 < rates.length ? rates[i + 1].rate_date.slice(0, 7) : null;
          const val   = parseFloat(rates[i].rate_value);
          for (let j = 0; j < labels.length; j++) {
            if (labels[j] >= from && (!until || labels[j] < until)) {
              rateValues[j] = val;
            }
          }
        }

        // ── 3. Заполняем цену м² (из справочника) ────────────────────────────
        const priceValues = labels.map(lbl => PRICE_PER_M2[lbl] ?? null);

        const ctx = document.getElementById("rateChart");
        if (!ctx) return;

        Chart.register(eventLinesPlugin);

        window._rateChart = new Chart(ctx, {
          type: "line",
          data: {
            labels,
            datasets: [
              {
                label: "Ключевая ставка ЦБ, %",
                data: rateValues,
                yAxisID: "yRate",
                borderColor: "#6366f1",
                backgroundColor: "rgba(99,102,241,.06)",
                borderWidth: 2.5,
                pointRadius: 0,
                pointHoverRadius: 5,
                fill: true,
                stepped: true,
                order: 2,
              },
              {
                label: "Цена м² новостройки, тыс. ₽",
                data: priceValues,
                yAxisID: "yPrice",
                borderColor: "#f59e0b",
                backgroundColor: "rgba(245,158,11,.07)",
                borderWidth: 2,
                pointRadius: 0,
                pointHoverRadius: 5,
                fill: true,
                tension: 0.35,
                order: 1,
              },
            ],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            plugins: {
              legend: {
                display: true,
                position: "top",
                align: "end",
                labels: {
                  color: "#94a3b8",
                  boxWidth: 14,
                  padding: 16,
                  font: { size: 12 },
                },
              },
              tooltip: {
                backgroundColor: "#1a1d27",
                borderColor: "#2e3248",
                borderWidth: 1,
                titleColor: "#7c8db5",
                bodyColor: "#e2e8f0",
                padding: 12,
                callbacks: {
                  title: (items) => items[0].label,
                  label: (item) => {
                    if (item.datasetIndex === 0) return `  Ставка ЦБ: ${item.raw}%`;
                    return `  Цена м²: ${item.raw} тыс. ₽`;
                  },
                },
              },
              eventLines: { events: KEY_EVENTS },
              zoom: {
                pan: { enabled: true, mode: "x" },
                zoom: {
                  wheel: { enabled: true },
                  pinch: { enabled: true },
                  mode: "x",
                  onZoom: () => {
                    document.getElementById("zoomResetBtn").style.opacity = "1";
                  },
                },
              },
            },
            scales: {
              x: {
                grid: { color: "#2e3248" },
                ticks: {
                  color: "#7c8db5",
                  maxTicksLimit: 16,
                  autoSkip: true,
                  callback(val) {
                    const lbl = this.getLabelForValue(val);
                    if (!lbl) return "";
                    const [year, month] = lbl.split("-");
                    const months = ["янв","фев","мар","апр","май","июн",
                                    "июл","авг","сен","окт","ноя","дек"];
                    const monthName = months[parseInt(month, 10) - 1];
                    // при полном диапазоне — только год (январь)
                    // при зуме — месяц + год
                    const totalVisible = this.chart.scales.x.max - this.chart.scales.x.min;
                    if (totalVisible > 36) {
                      return month === "01" ? year : "";
                    }
                    if (totalVisible > 12) {
                      return month === "01" || month === "07"
                        ? `${monthName} ${year}` : "";
                    }
                    return `${monthName} ${year}`;
                  },
                },
              },
              yRate: {
                position: "left",
                grid: { color: "#2e3248" },
                ticks: { color: "#6366f1", callback: (v) => v + "%" },
                min: 3,
                max: 23,
                title: { display: true, text: "Ставка ЦБ, %", color: "#6366f1", font: { size: 11 } },
              },
              yPrice: {
                position: "right",
                grid: { drawOnChartArea: false },
                ticks: { color: "#f59e0b", callback: (v) => v + "k" },
                min: 100,
                max: 380,
                title: { display: true, text: "₽/м², тыс.", color: "#f59e0b", font: { size: 11 } },
              },
            },
          },
        });

        const resetBtn = document.getElementById("zoomResetBtn");
        if (resetBtn) resetBtn.style.opacity = "0.4";
      } catch (e) {
        console.error("Rate chart error:", e);
      }
    },

    dirClass(dir) {
      return { up: "event-card dir-up", down: "event-card dir-down" }[dir] || "event-card dir-neutral";
    },
    prevPage()  { this.offset = Math.max(0, this.offset - this.pageSize); this.loadEvents(false); },
    nextPage()  { this.offset += this.pageSize; this.loadEvents(false); },
    pageLabel() {
      const from = this.offset + 1;
      const to   = Math.min(this.offset + this.pageSize, this.total);
      return `${from}–${to} из ${this.total}`;
    },
    catLabel:   window.catLabel,
    scoreClass: window.scoreClass,
    scoreLabel: window.scoreLabel,
    formatDate: window.formatDate,
  };
}

window.resetChartZoom = () => {
  if (window._rateChart) {
    window._rateChart.resetZoom();
    const btn = document.getElementById("zoomResetBtn");
    if (btn) btn.style.opacity = "0.4";
  }
};
