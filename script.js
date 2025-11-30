const state = {
  tasks: [],
  apiBase: "https://your-render-service.onrender.com/api", 
};

function showTaskList() {
  document.getElementById("task-list").textContent = JSON.stringify(state.tasks, null, 2);
}

function parseDeps(val) {
  if (!val) return [];
  return val.split(",").map(s => s.trim()).filter(Boolean);
}

function getTaskForm() {
  const title = document.getElementById("title").value.trim();
  const due_date = document.getElementById("due_date").value.trim();
  const estimated_hours = document.getElementById("estimated_hours").value.trim();
  const importance = document.getElementById("importance").value.trim();
  const task_id = document.getElementById("task_id").value.trim();
  const dependencies = parseDeps(document.getElementById("dependencies").value.trim());

  const payload = { title, dependencies };
  if (task_id) payload.id = task_id;
  if (due_date) payload.due_date = due_date;
  if (estimated_hours) payload.estimated_hours = Number(estimated_hours);
  if (importance) payload.importance = Number(importance);
  return payload;
}

function validateTask(task) {
  if (!task.title) return "Title is required.";
  if (task.importance !== undefined && (task.importance < 1 || task.importance > 10)) return "Importance must be 1-10.";
  if (task.estimated_hours !== undefined && task.estimated_hours < 0) return "Estimated hours must be >= 0.";
  return null;
}

function badgeClass(band) {
  const lower = (band || "").toLowerCase();
  if (lower === "high") return "badge high";
  if (lower === "medium") return "badge medium";
  return "badge low";
}

function renderResults(items) {
  const container = document.getElementById("results");
  container.innerHTML = "";
  items.forEach(item => {
    const div = document.createElement("div");
    div.className = "result-item";
    div.innerHTML = `
      <div>
        <span class="${badgeClass(item.priority_band)}">${item.priority_band}</span>
        <strong>${item.title}</strong>
      </div>
      <div class="kv"><div class="key">Score</div><div>${item.score}</div></div>
      <div class="kv"><div class="key">Due date</div><div>${item.due_date || "—"}</div></div>
      <div class="kv"><div class="key">Estimated hours</div><div>${item.estimated_hours ?? "—"}</div></div>
      <div class="kv"><div class="key">Importance</div><div>${item.importance ?? "—"}</div></div>
      <div class="kv"><div class="key">Dependencies</div><div>${(item.dependencies || []).join(", ") || "—"}</div></div>
      <p style="color:#9ca3af;margin-top:8px">${item.explanation}</p>
    `;
    container.appendChild(div);
  });
}

function setFeedback(msg) {
  document.getElementById("feedback").textContent = msg;
}

document.getElementById("add-task").addEventListener("click", () => {
  const t = getTaskForm();
  const err = validateTask(t);
  if (err) { setFeedback(err); return; }
  state.tasks.push(t);
  showTaskList();
  setFeedback("Task added.");
});

document.getElementById("clear-tasks").addEventListener("click", () => {
  state.tasks = [];
  showTaskList();
  setFeedback("Task list cleared.");
});

document.getElementById("load-bulk").addEventListener("click", () => {
  const raw = document.getElementById("bulk-json").value.trim();
  if (!raw) { setFeedback("Paste a JSON array first."); return; }
  try {
    const arr = JSON.parse(raw);
    if (!Array.isArray(arr)) throw new Error("JSON must be an array.");
    // Basic validation
    for (const t of arr) {
      const err = validateTask(t);
      if (err) { setFeedback(`Invalid task: ${err}`); return; }
    }
    state.tasks = arr;
    showTaskList();
    setFeedback("Loaded bulk tasks.");
  } catch (e) {
    setFeedback("Invalid JSON: " + e.message);
  }
});

document.getElementById("analyze").addEventListener("click", async () => {
  if (!state.tasks.length) { setFeedback("Add at least one task."); return; }
  const strategy = document.getElementById("strategy").value;
  setFeedback("Analyzing…");
  try {
    const res = await fetch(`${state.apiBase}/tasks/analyze/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tasks: state.tasks, strategy }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || "Request failed");
    }
    const data = await res.json();
    renderResults(data.results || []);
    setFeedback(`Done (${strategy}).`);
  } catch (e) {
    setFeedback("Error: " + e.message);
  }
});

// Initialize
showTaskList();