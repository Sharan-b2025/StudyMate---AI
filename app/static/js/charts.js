// StudyMate AI — Chart.js dashboard visualizations

function initTopicsDonut(elId, counts) {
  const ctx = document.getElementById(elId);
  if (!ctx) return;
  new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Completed", "In Progress", "Pending"],
      datasets: [{
        data: [counts.completed, counts.in_progress, counts.pending],
        backgroundColor: ["#34d399", "#6366f1", "#2b2f42"],
        borderWidth: 0,
        hoverOffset: 6,
      }],
    },
    options: {
      cutout: "72%",
      plugins: { legend: { display: false } },
    },
  });
}

function initQuizLine(elId, points) {
  const ctx = document.getElementById(elId);
  if (!ctx) return;
  const gradient = ctx.getContext("2d").createLinearGradient(0, 0, 0, 220);
  gradient.addColorStop(0, "rgba(139, 92, 246, 0.35)");
  gradient.addColorStop(1, "rgba(139, 92, 246, 0)");

  new Chart(ctx, {
    type: "line",
    data: {
      labels: points.map((p) => p.date),
      datasets: [{
        label: "Score %",
        data: points.map((p) => p.percentage),
        borderColor: "#8b5cf6",
        backgroundColor: gradient,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: "#8b5cf6",
        pointBorderColor: "#fff",
        pointRadius: 4,
      }],
    },
    options: {
      scales: {
        y: { min: 0, max: 100, grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#9ba0b8" } },
        x: { grid: { display: false }, ticks: { color: "#9ba0b8" } },
      },
      plugins: { legend: { display: false } },
    },
  });
}
