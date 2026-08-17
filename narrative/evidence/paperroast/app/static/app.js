/* paperroast SPA — Design / Templates / Verify */
(() => {
  "use strict";

  const COL_TYPES = ["serial", "int", "dec", "date", "yn", "choice", "name", "text"];
  const HDR_TYPES = ["text", "date", "name", "int"];
  const FLAG_COLORS = {
    domain: "rgba(232,120,40,0.4)",
    unread_ink: "rgba(200,150,20,0.45)",
    serial_mismatch: "rgba(200,40,40,0.45)",
    shape: "rgba(200,40,40,0.25)",
    shift_fixed: "#dbeafe",
    cell_mode: "#ccfbf1",
  };
  const ROW_FLAGS = new Set(["shape", "shift_fixed", "cell_mode"]);

  const EXAMPLES = {
    growth: {
      title: "PHC Child Growth Monitoring Register",
      orientation: "portrait",
      rows: 16,
      header_fields: [
        { label: "PHC Name", type: "text" },
        { label: "Village", type: "text" },
        { label: "Session Date", type: "date" },
        { label: "ANM Name", type: "name" },
      ],
      columns: [
        { label: "S.No", type: "serial" },
        { label: "Child Name", type: "name" },
        { label: "Age (Mo)", type: "int", min: 0, max: 60 },
        { label: "Sex", type: "choice", domain: ["M", "F"], legend: "M=Male, F=Female" },
        { label: "Weight (kg)", type: "dec", min: 0, max: 40 },
        { label: "Height (cm)", type: "dec", min: 30, max: 130 },
        { label: "MUAC (cm)", type: "dec", min: 5, max: 25 },
        {
          label: "Status",
          type: "choice",
          domain: ["N", "MAM", "SAM"],
          legend: "N=Normal, MAM=Moderate, SAM=Severe",
        },
      ],
    },
    attendance: {
      title: "Monthly Student Attendance Register",
      orientation: "landscape",
      rows: 12,
      header_fields: [
        { label: "School Name", type: "text" },
        { label: "Class", type: "text" },
        { label: "Month", type: "text" },
        { label: "Year", type: "int" },
      ],
      columns: [
        { label: "Roll No", type: "serial" },
        { label: "Student Name", type: "name" },
        { label: "D1", type: "choice", domain: ["P", "A", "L"], legend: "P=Present, A=Absent, L=Late" },
        { label: "D2", type: "choice", domain: ["P", "A", "L"] },
        { label: "D3", type: "choice", domain: ["P", "A", "L"] },
        { label: "D4", type: "choice", domain: ["P", "A", "L"] },
        { label: "D5", type: "choice", domain: ["P", "A", "L"] },
        { label: "D6", type: "choice", domain: ["P", "A", "L"] },
        { label: "D7", type: "choice", domain: ["P", "A", "L"] },
        { label: "D8", type: "choice", domain: ["P", "A", "L"] },
      ],
    },
  };

  // ── state ──────────────────────────────────────────────────────
  let headers = [];
  let columns = [];
  let lastFormId = null;
  let templatesCache = [];
  let hoverRow = null;
  let resultState = null; // last /api/extract payload (+ _rowRects helpers)
  let cellEdit = null; // { r, c, td } while modal open

  // ── helpers ────────────────────────────────────────────────────
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

  function el(tag, attrs = {}, kids = []) {
    const n = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === "class") n.className = v;
      else if (k === "text") n.textContent = v;
      else if (k === "html") n.innerHTML = v;
      else if (k.startsWith("on") && typeof v === "function") n.addEventListener(k.slice(2).toLowerCase(), v);
      else if (v === false || v == null) continue;
      else n.setAttribute(k, v === true ? "" : String(v));
    }
    for (const c of kids) {
      if (c == null) continue;
      n.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    }
    return n;
  }

  function selectOpts(values, selected) {
    return values.map((v) => {
      const o = document.createElement("option");
      o.value = v;
      o.textContent = v;
      if (v === selected) o.selected = true;
      return o;
    });
  }

  async function api(path, opts) {
    const r = await fetch(path, opts);
    const ct = r.headers.get("content-type") || "";
    let body = null;
    if (ct.includes("application/json")) body = await r.json();
    else body = await r.text();
    if (!r.ok) {
      const detail = body && typeof body === "object" ? body.detail : body;
      const err = new Error(typeof detail === "string" ? detail : r.statusText);
      err.status = r.status;
      err.body = body;
      throw err;
    }
    return body;
  }

  // ── tabs ───────────────────────────────────────────────────────
  function showTab(name) {
    $$(".tab").forEach((t) => {
      const on = t.dataset.tab === name;
      t.classList.toggle("active", on);
      t.setAttribute("aria-selected", on ? "true" : "false");
    });
    $$(".panel").forEach((p) => {
      const on = p.id === `tab-${name}`;
      p.hidden = !on;
      p.classList.toggle("active", on);
    });
    if (name === "templates") loadTemplates();
  }

  $$(".tab").forEach((t) =>
    t.addEventListener("click", () => showTab(t.dataset.tab))
  );

  // ── Design: list editors ───────────────────────────────────────
  function blankHeader() {
    return { label: "", type: "text" };
  }
  function blankColumn() {
    return { label: "", type: "text", domain: [], legend: "", min: null, max: null };
  }

  function syncOrientHint() {
    const hint = $("#orient-hint");
    const need = columns.length > 7;
    hint.hidden = !need;
    if (need && $("#d-orient").value === "portrait") {
      // soft suggest — only auto-switch if user hasn't touched many cols yet
    }
  }

  function maybeSuggestLandscape() {
    if (columns.length > 7) {
      $("#d-orient").value = "landscape";
    }
    syncOrientHint();
  }

  function renderHeaderList() {
    const list = $("#header-list");
    list.innerHTML = "";
    headers.forEach((h, i) => {
      const typeSel = el("select", {});
      selectOpts(HDR_TYPES, h.type).forEach((o) => typeSel.appendChild(o));
      typeSel.addEventListener("change", () => {
        h.type = typeSel.value;
      });

      const labelIn = el("input", {
        type: "text",
        value: h.label,
        placeholder: "Label",
        required: true,
      });
      labelIn.addEventListener("input", () => {
        h.label = labelIn.value;
      });

      const row = el("div", { class: "editor-row" }, [
        el("label", {}, ["Label", labelIn]),
        el("label", {}, ["Type", typeSel]),
        el("div"),
        rowActions(
          () => {
            if (i > 0) {
              [headers[i - 1], headers[i]] = [headers[i], headers[i - 1]];
              renderHeaderList();
            }
          },
          () => {
            if (i < headers.length - 1) {
              [headers[i + 1], headers[i]] = [headers[i], headers[i + 1]];
              renderHeaderList();
            }
          },
          () => {
            headers.splice(i, 1);
            renderHeaderList();
          }
        ),
      ]);
      list.appendChild(row);
    });
  }

  function renderColumnList() {
    const list = $("#column-list");
    list.innerHTML = "";
    columns.forEach((c, i) => {
      const typeSel = el("select", {});
      selectOpts(COL_TYPES, c.type).forEach((o) => typeSel.appendChild(o));

      const labelIn = el("input", {
        type: "text",
        value: c.label,
        placeholder: "Label",
        required: true,
      });
      labelIn.addEventListener("input", () => {
        c.label = labelIn.value;
      });

      const extras = el("div", { class: "extras" });

      function rebuildExtras() {
        extras.innerHTML = "";
        if (c.type === "choice") {
          const domIn = el("input", {
            type: "text",
            value: (c.domain || []).join(", "),
            placeholder: "A, B, C",
          });
          domIn.addEventListener("input", () => {
            c.domain = domIn.value
              .split(",")
              .map((s) => s.trim())
              .filter(Boolean);
          });
          const legIn = el("input", {
            type: "text",
            value: c.legend || "",
            placeholder: "A=..., B=...",
          });
          legIn.addEventListener("input", () => {
            c.legend = legIn.value;
          });
          extras.append(
            el("label", {}, ["Allowed values", domIn]),
            el("label", {}, ["Legend (optional)", legIn])
          );
        } else if (c.type === "int" || c.type === "dec") {
          const minIn = el("input", {
            type: "number",
            step: c.type === "dec" ? "any" : "1",
            value: c.min != null ? c.min : "",
            placeholder: "min",
          });
          minIn.addEventListener("input", () => {
            c.min = minIn.value === "" ? null : Number(minIn.value);
          });
          const maxIn = el("input", {
            type: "number",
            step: c.type === "dec" ? "any" : "1",
            value: c.max != null ? c.max : "",
            placeholder: "max",
          });
          maxIn.addEventListener("input", () => {
            c.max = maxIn.value === "" ? null : Number(maxIn.value);
          });
          extras.append(
            el("label", {}, ["Min (optional)", minIn]),
            el("label", {}, ["Max (optional)", maxIn])
          );
        }
      }

      typeSel.addEventListener("change", () => {
        c.type = typeSel.value;
        if (c.type === "yn") c.domain = ["Y", "N"];
        if (c.type !== "choice") {
          /* keep domain for yn */
        }
        rebuildExtras();
      });
      rebuildExtras();

      const row = el("div", { class: "editor-row" }, [
        el("label", {}, ["Label", labelIn]),
        el("label", {}, ["Type", typeSel]),
        extras,
        rowActions(
          () => {
            if (i > 0) {
              [columns[i - 1], columns[i]] = [columns[i], columns[i - 1]];
              renderColumnList();
            }
          },
          () => {
            if (i < columns.length - 1) {
              [columns[i + 1], columns[i]] = [columns[i], columns[i + 1]];
              renderColumnList();
            }
          },
          () => {
            columns.splice(i, 1);
            renderColumnList();
            maybeSuggestLandscape();
          }
        ),
      ]);
      list.appendChild(row);
    });
    syncOrientHint();
  }

  function rowActions(up, down, remove) {
    return el("div", { class: "row-actions" }, [
      el("button", { type: "button", class: "btn icon", title: "Move up", text: "↑", onClick: up }),
      el("button", { type: "button", class: "btn icon", title: "Move down", text: "↓", onClick: down }),
      el("button", {
        type: "button",
        class: "btn icon danger",
        title: "Remove",
        text: "×",
        onClick: remove,
      }),
    ]);
  }

  $("#add-header").addEventListener("click", () => {
    headers.push(blankHeader());
    renderHeaderList();
  });
  $("#add-column").addEventListener("click", () => {
    columns.push(blankColumn());
    renderColumnList();
    maybeSuggestLandscape();
  });

  function applySpec(spec) {
    $("#d-title").value = spec.title || "";
    $("#d-orient").value = spec.orientation === "landscape" ? "landscape" : "portrait";
    $("#d-rows").value = spec.rows != null ? spec.rows : 16;
    headers = (spec.header_fields || []).map((h) => ({
      label: h.label || "",
      type: HDR_TYPES.includes(h.type) ? h.type : "text",
    }));
    columns = (spec.columns || []).map((c) => ({
      label: c.label || "",
      type: COL_TYPES.includes(c.type) ? c.type : "text",
      domain: c.domain ? [...c.domain] : c.type === "yn" ? ["Y", "N"] : [],
      legend: c.legend || "",
      min: c.min != null ? c.min : null,
      max: c.max != null ? c.max : null,
    }));
    renderHeaderList();
    renderColumnList();
    syncOrientHint();
    $("#design-error").hidden = true;
    $("#design-preview").hidden = true;
  }

  function loadExample(key) {
    applySpec(EXAMPLES[key]);
    $("#sample-warning").hidden = true;
  }

  $("#ex-growth").addEventListener("click", () => loadExample("growth"));
  $("#ex-attendance").addEventListener("click", () => loadExample("attendance"));

  $("#propose-sample").addEventListener("click", async () => {
    const file = $("#d-sample").files[0];
    const errBox = $("#design-error");
    const warnBox = $("#sample-warning");
    errBox.hidden = true;
    warnBox.hidden = true;
    if (!file) {
      errBox.textContent = "Choose an image or PDF of a paper form first.";
      errBox.hidden = false;
      return;
    }
    const btn = $("#propose-sample");
    const prev = btn.textContent;
    btn.disabled = true;
    btn.textContent = "Proposing…";
    try {
      const fd = new FormData();
      fd.append("f", file);
      const res = await api("/api/design_from_sample", { method: "POST", body: fd });
      if (!res || !res.spec) throw new Error("No template proposal returned.");
      applySpec(res.spec);
      if (res.warning) {
        warnBox.textContent = "proposal needs fixing: " + res.warning;
        warnBox.hidden = false;
      }
      $("#design-form").scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (err) {
      errBox.textContent = err.message || String(err);
      errBox.hidden = false;
    } finally {
      btn.disabled = false;
      btn.textContent = prev;
    }
  });

  function buildSpec() {
    const title = $("#d-title").value.trim();
    const orientation = $("#d-orient").value;
    const rows = Number($("#d-rows").value);
    const header_fields = headers
      .filter((h) => h.label.trim())
      .map((h) => ({ label: h.label.trim(), type: h.type }));
    const cols = columns
      .filter((c) => c.label.trim())
      .map((c) => {
        const o = { label: c.label.trim(), type: c.type };
        if (c.type === "choice") {
          o.domain = c.domain || [];
          if (c.legend) o.legend = c.legend;
        }
        if (c.type === "int" || c.type === "dec") {
          if (c.min != null && c.min !== "") o.min = Number(c.min);
          if (c.max != null && c.max !== "") o.max = Number(c.max);
        }
        return o;
      });
    return { title, orientation, rows, header_fields, columns: cols };
  }

  $("#design-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const errBox = $("#design-error");
    errBox.hidden = true;
    const btn = $("#create-btn");
    btn.disabled = true;
    try {
      const spec = buildSpec();
      if (!spec.columns.length) throw new Error("Add at least one column with a label.");
      const res = await api("/api/templates", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(spec),
      });
      lastFormId = res.form_id;
      showPreview(res);
      // refresh template dropdown quietly
      loadTemplates(true);
    } catch (err) {
      errBox.textContent = err.message || String(err);
      errBox.hidden = false;
      $("#design-preview").hidden = true;
    } finally {
      btn.disabled = false;
    }
  });

  function showPreview(res) {
    const pane = $("#design-preview");
    pane.hidden = false;
    $("#preview-id").textContent = res.form_id;
    $("#preview-img").src = res.preview + "?t=" + Date.now();
    $("#dl-pdf").href = res.pdf;
    $("#dl-pdf").download = `${res.form_id}_blank.pdf`;
    $("#sample-figure").hidden = true;
    $("#regen-sample").hidden = true;
  }

  async function generateSample() {
    if (!lastFormId) return;
    const btn = $("#gen-sample");
    const regen = $("#regen-sample");
    btn.disabled = true;
    regen.disabled = true;
    btn.textContent = "Generating…";
    try {
      const fd = new FormData();
      fd.append("seed", String(Math.floor(Math.random() * 1e6)));
      fd.append("density", "0.6");
      const res = await api(`/api/templates/${lastFormId}/sample`, {
        method: "POST",
        body: fd,
      });
      $("#sample-img").src = res.image;
      $("#sample-figure").hidden = false;
      regen.hidden = false;
    } catch (err) {
      alert("Sample failed: " + err.message);
    } finally {
      btn.disabled = false;
      regen.disabled = false;
      btn.textContent = "Generate sample fill";
    }
  }

  $("#gen-sample").addEventListener("click", generateSample);
  $("#regen-sample").addEventListener("click", generateSample);

  // ── Templates gallery ──────────────────────────────────────────
  async function loadTemplates(silent) {
    try {
      templatesCache = await api("/api/templates");
      renderGallery();
      fillTemplateSelect();
    } catch (err) {
      if (!silent) console.error(err);
    }
  }

  function renderGallery() {
    const grid = $("#templates-grid");
    const empty = $("#templates-empty");
    grid.innerHTML = "";
    if (!templatesCache.length) {
      empty.hidden = false;
      return;
    }
    empty.hidden = true;
    // newest first
    const items = [...templatesCache].sort((a, b) => (b.created || 0) - (a.created || 0));
    for (const t of items) {
      const card = el("div", { class: "gallery-card" }, [
        el("img", {
          class: "thumb",
          src: `/api/templates/${t.form_id}/preview.png`,
          alt: t.title,
          loading: "lazy",
        }),
        el("div", { class: "meta" }, [
          el("p", { class: "title", text: t.title }),
          el("p", {
            class: "sub",
            html: `<span class="mono">${t.form_id}</span> · ${t.columns}×${t.rows}`,
          }),
          el("div", { class: "actions" }, [
            el("a", {
              class: "btn small",
              href: `/api/templates/${t.form_id}/blank.pdf`,
              download: `${t.form_id}_blank.pdf`,
              text: "PDF",
            }),
            el("button", {
              type: "button",
              class: "btn small",
              text: "Sample fill",
              onClick: () => sampleFromGallery(t.form_id),
            }),
            el("button", {
              type: "button",
              class: "btn small primary",
              text: "Upload photo",
              onClick: () => jumpToVerify(t.form_id),
            }),
          ]),
        ]),
      ]);
      grid.appendChild(card);
    }
  }

  async function sampleFromGallery(formId) {
    try {
      const fd = new FormData();
      fd.append("seed", String(Math.floor(Math.random() * 1e6)));
      const res = await api(`/api/templates/${formId}/sample`, { method: "POST", body: fd });
      // open image in new tab via blob
      const w = window.open("");
      if (w) {
        w.document.write(
          `<title>${formId} sample</title><body style="margin:0;background:#111;text-align:center">` +
            `<img src="${res.image}" style="max-width:100%;height:auto"></body>`
        );
      } else {
        // fallback: download
        const a = document.createElement("a");
        a.href = res.image;
        a.download = `${formId}_sample.jpg`;
        a.click();
      }
    } catch (err) {
      alert("Sample failed: " + err.message);
    }
  }

  function jumpToVerify(formId) {
    showTab("verify");
    const sel = $("#v-template");
    if (![...sel.options].some((o) => o.value === formId)) {
      sel.appendChild(el("option", { value: formId, text: formId }));
    }
    sel.value = formId;
  }

  function fillTemplateSelect() {
    const sel = $("#v-template");
    const cur = sel.value;
    sel.innerHTML = "";
    sel.appendChild(el("option", { value: "", text: "auto (read QR)" }));
    for (const t of templatesCache) {
      sel.appendChild(
        el("option", {
          value: t.form_id,
          text: `${t.title} (${t.form_id})`,
        })
      );
    }
    if (cur && [...sel.options].some((o) => o.value === cur)) sel.value = cur;
  }

  $("#refresh-templates").addEventListener("click", () => loadTemplates());

  // ── Verify ─────────────────────────────────────────────────────
  async function loadProviders() {
    try {
      const p = await api("/api/providers");
      const sel = $("#v-provider");
      sel.innerHTML = "";
      for (const name of p.providers) {
        const o = el("option", { value: name, text: name });
        if (name === p.default) o.selected = true;
        sel.appendChild(o);
      }
    } catch (err) {
      console.error(err);
    }
  }

  const PROGRESS_STAGES = [
    "Reading form ID from QR…",
    "Aligning photo to template…",
    "Reading header fields…",
    "Reading table rows…",
    "Checking domains and ink…",
    "Assembling grid…",
  ];

  $("#verify-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const file = $("#v-file").files[0];
    if (!file) return;
    const errBox = $("#extract-error");
    errBox.hidden = true;
    $("#result").hidden = true;
    const prog = $("#extract-progress");
    prog.hidden = false;
    const btn = $("#extract-btn");
    btn.disabled = true;

    let stage = 0;
    $("#progress-text").textContent = PROGRESS_STAGES[0];
    const tick = setInterval(() => {
      stage = Math.min(stage + 1, PROGRESS_STAGES.length - 1);
      $("#progress-text").textContent = PROGRESS_STAGES[stage] + " (approx.)";
    }, 4000);

    try {
      const fd = new FormData();
      fd.append("f", file);
      fd.append("provider", $("#v-provider").value);
      const override = $("#v-template").value;
      if (override) fd.append("form_id", override);
      const res = await api("/api/extract", { method: "POST", body: fd });
      renderResult(res);
    } catch (err) {
      errBox.textContent = err.message || String(err);
      errBox.hidden = false;
    } finally {
      clearInterval(tick);
      prog.hidden = true;
      btn.disabled = false;
    }
  });

  function renderResult(res) {
    resultState = res;
    $("#result").hidden = false;

    const verdict = res.verdict || "review";
    const banner = $("#verdict-banner");
    banner.className = "verdict " + verdict;
    const labels = {
      detected: "Ready to use",
      review: "Needs review",
      reject: "Rejected",
    };
    $("#verdict-label").textContent = labels[verdict] || verdict;
    $("#verdict-id").textContent = res.form_id ? `form ${res.form_id}` : "no form id";

    const reasons = $("#verdict-reasons");
    reasons.innerHTML = "";
    for (const r of res.reasons || []) {
      reasons.appendChild(el("li", { text: r }));
    }

    const s = res.stats || {};
    const flags = (s.flags && typeof s.flags === "object") ? s.flags : {};
    $("#verdict-stats").textContent = [
      `model_calls=${s.model_calls ?? "—"}`,
      `latency=${s.latency_s ?? "—"}s`,
      `inliers=${s.inliers ?? "—"}`,
      `align_ok=${s.align_ok ?? "—"}`,
      `id_how=${s.id_how ?? "—"}`,
      `inked=${s.inked_cells ?? "—"}`,
      flags.domain != null
        ? `flags{domain=${flags.domain},unread=${flags.unread_ink},serial=${flags.serial_mismatch},shape=${flags.shape},shift=${flags.shift_fixed},cell=${flags.cell_mode}}`
        : null,
    ]
      .filter(Boolean)
      .join(" · ");

    const xlsx = $("#dl-xlsx");
    const csvBtn = $("#export-csv");
    if (res.xlsx) {
      xlsx.hidden = false;
      xlsx.href = res.xlsx;
    } else {
      xlsx.hidden = true;
    }
    csvBtn.hidden = !(res.grid && res.grid.table && res.grid.table.length);

    $("#raw-json").textContent = JSON.stringify(res, null, 2);

    renderHeaderChips(res.grid && res.grid.header);
    renderExtractTable(res.grid && res.grid.table, res.flags || []);
    renderAligned(res);
  }

  function renderHeaderChips(header) {
    const box = $("#header-chips");
    box.innerHTML = "";
    if (!header || !header.length) return;
    for (const pair of header) {
      const label = pair[0];
      const value = pair[1] == null || pair[1] === "" ? "—" : String(pair[1]);
      box.appendChild(
        el("span", { class: "chip" }, [
          el("span", { class: "k", text: label + ":" }),
          el("span", { class: "v", text: value }),
        ])
      );
    }
  }

  function flagMap(flags) {
    // key: `${row}:${col}` or `${row}:*` for shape
    const map = new Map();
    for (const f of flags) {
      const key = f.col == null ? `${f.row}:*` : `${f.row}:${f.col}`;
      if (!map.has(key)) map.set(key, f.flag);
    }
    return map;
  }

  function renderExtractTable(table, flags) {
    const tbl = $("#extract-table");
    const noGrid = $("#no-grid");
    tbl.innerHTML = "";
    if (!table || !table.length) {
      noGrid.hidden = false;
      return;
    }
    noGrid.hidden = true;
    const fmap = flagMap(flags);
    const thead = el("thead");
    const hr = el("tr");
    for (const cell of table[0]) {
      hr.appendChild(el("th", { text: cell == null ? "" : String(cell) }));
    }
    thead.appendChild(hr);
    tbl.appendChild(thead);

    const tbody = el("tbody");
    for (let r = 1; r < table.length; r++) {
      const dataRow = r - 1; // 0-based data row
      const tr = el("tr", { class: "data-row", "data-row": String(dataRow) });
      const rowFl = fmap.get(`${dataRow}:*`);
      if (rowFl && ROW_FLAGS.has(rowFl)) tr.classList.add("flag-" + rowFl);
      for (let c = 0; c < table[r].length; c++) {
        const val = table[r][c];
        const td = el("td", {
          class: "data-cell",
          text: val == null || val === "" ? "" : String(val),
          "data-row": String(dataRow),
          "data-col": String(c),
          title: "Click to zoom & correct",
        });
        const fl = fmap.get(`${dataRow}:${c}`);
        if (fl) td.classList.add("flag-" + fl);
        td.addEventListener("click", (ev) => {
          ev.stopPropagation();
          openCellModal(dataRow, c, td);
        });
        tr.appendChild(td);
      }
      tr.addEventListener("mouseenter", () => setHoverRow(dataRow));
      tr.addEventListener("mouseleave", () => setHoverRow(null));
      tbody.appendChild(tr);
    }
    tbl.appendChild(tbody);
  }

  function setHoverRow(row) {
    hoverRow = row;
    $$("#extract-table tr.data-row").forEach((tr) => {
      tr.classList.toggle("hl", row != null && Number(tr.dataset.row) === row);
    });
    const hl = $("#grid-overlay .row-hl");
    if (hl) {
      if (row == null || !resultState || !resultState._rowRects) {
        hl.setAttribute("visibility", "hidden");
      } else {
        const rr = resultState._rowRects[row];
        if (rr) {
          hl.setAttribute("x", rr.x);
          hl.setAttribute("y", rr.y);
          hl.setAttribute("width", rr.w);
          hl.setAttribute("height", rr.h);
          hl.setAttribute("visibility", "visible");
        } else {
          hl.setAttribute("visibility", "hidden");
        }
      }
    }
  }

  function svgEl(tag, attrs) {
    const n = document.createElementNS("http://www.w3.org/2000/svg", tag);
    for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, String(v));
    return n;
  }

  function appendRowHl(svg) {
    const hl = svgEl("rect", {
      class: "row-hl",
      fill: "rgba(47,111,228,0.18)",
      visibility: "hidden",
      "pointer-events": "none",
    });
    svg.appendChild(hl);
  }

  function paintFlagsAndHits(parent, fmap, nData, nCols, rowBounds, colXs, scale) {
    // rowBounds[r] = { y0, y1 } in the same coordinate space as colXs (pre-scale if scale≠1)
    // Parent may be a scaled <g> (template path) or the svg itself (overlay path, scale=1).
    const s = scale == null ? 1 : scale;
    resultState._rowRects = [];

    for (let r = 0; r < nData; r++) {
      const { y0, y1 } = rowBounds[r];
      const xL = colXs[0];
      const xR = colXs[colXs.length - 1];
      resultState._rowRects[r] = {
        x: xL * s,
        y: y0 * s,
        w: (xR - xL) * s,
        h: (y1 - y0) * s,
      };

      const hit = svgEl("rect", {
        x: xL, y: y0,
        width: xR - xL,
        height: y1 - y0,
        fill: "transparent",
        class: "flag-cell",
        "data-row": r,
      });
      hit.addEventListener("mouseenter", () => setHoverRow(r));
      hit.addEventListener("mouseleave", () => setHoverRow(null));
      parent.appendChild(hit);

      const rowFl = fmap.get(`${r}:*`);
      if (rowFl && ROW_FLAGS.has(rowFl)) {
        parent.appendChild(svgEl("rect", {
          x: xL, y: y0,
          width: xR - xL,
          height: y1 - y0,
          fill: FLAG_COLORS[rowFl],
          class: "flag-cell",
          "pointer-events": "none",
        }));
      }
      for (let c = 0; c < nCols; c++) {
        const fl = fmap.get(`${r}:${c}`);
        const cellHit = svgEl("rect", {
          x: colXs[c], y: y0,
          width: colXs[c + 1] - colXs[c],
          height: y1 - y0,
          fill: fl && !ROW_FLAGS.has(fl) ? (FLAG_COLORS[fl] || "rgba(0,0,0,0.15)") : "transparent",
          class: "flag-cell",
          "data-row": r,
          "data-col": c,
          style: "cursor:pointer",
        });
        cellHit.addEventListener("mouseenter", () => setHoverRow(r));
        cellHit.addEventListener("mouseleave", () => setHoverRow(null));
        cellHit.addEventListener("click", () => {
          const td = $(`#extract-table td.data-cell[data-row="${r}"][data-col="${c}"]`);
          openCellModal(r, c, td);
        });
        parent.appendChild(cellHit);
      }
    }
  }

  function drawOverlayGrid(svg, overlay, flags) {
    const left = overlay.left || [];
    const right = overlay.right || [];
    const colX = overlay.col_x || [];
    if (left.length < 3 || right.length < 3 || colX.length < 2) return false;

    const stroke = "rgba(47,111,228,0.55)";
    const sw = 1.2;
    const nMarks = Math.min(left.length, right.length);

    // horizontals from detected marks (skip index 0 = table top rule)
    for (let i = 1; i < nMarks; i++) {
      svg.appendChild(svgEl("line", {
        x1: left[i][0], y1: left[i][1],
        x2: right[i][0], y2: right[i][1],
        stroke, "stroke-width": sw,
      }));
    }

    const yTop = Math.min(left[1][1], right[1][1]);
    const yBot = Math.max(left[nMarks - 1][1], right[nMarks - 1][1]);
    for (const x of colX) {
      svg.appendChild(svgEl("line", {
        x1: x, x2: x, y1: yTop, y2: yBot,
        stroke, "stroke-width": sw,
      }));
    }

    // data row r spans boundary r+1 → r+2
    const nData = nMarks - 2;
    const nCols = colX.length - 1;
    const rowBounds = [];
    for (let r = 0; r < nData; r++) {
      const y0 = Math.min(left[r + 1][1], right[r + 1][1]);
      const y1 = Math.max(left[r + 2][1], right[r + 2][1]);
      rowBounds.push({ y0, y1 });
    }
    paintFlagsAndHits(svg, flagMap(flags || []), nData, nCols, rowBounds, colX, 1);
    return true;
  }

  function drawTemplateGrid(svg, geo, nw, flags) {
    if (!geo || !geo.page || !geo.table) return false;
    const scale = nw / geo.page[0];
    const xs = geo.table.x;
    const headerY = geo.table.header_y || [];
    const rowY = geo.table.row_y || [];
    const ys = [];
    if (headerY.length) ys.push(headerY[0]);
    for (const y of rowY) {
      if (!ys.length || Math.abs(ys[ys.length - 1] - y) > 0.01) ys.push(y);
    }
    if (!xs.length || ys.length < 2) return false;

    const g = svgEl("g", { transform: `scale(${scale})` });
    const stroke = "rgba(47,111,228,0.55)";
    const sw = 0.7 / scale;

    for (const x of xs) {
      g.appendChild(svgEl("line", {
        x1: x, x2: x, y1: ys[0], y2: ys[ys.length - 1],
        stroke, "stroke-width": sw,
      }));
    }
    for (const y of ys) {
      g.appendChild(svgEl("line", {
        x1: xs[0], x2: xs[xs.length - 1], y1: y, y2: y,
        stroke, "stroke-width": sw,
      }));
    }

    const nData = rowY.length - 1;
    const nCols = xs.length - 1;
    const rowBounds = [];
    for (let r = 0; r < nData; r++) {
      rowBounds.push({ y0: rowY[r], y1: rowY[r + 1] });
    }
    paintFlagsAndHits(g, flagMap(flags || []), nData, nCols, rowBounds, xs, scale);
    svg.appendChild(g);
    return true;
  }

  function renderAligned(res) {
    const img = $("#aligned-img");
    const svg = $("#grid-overlay");
    const noA = $("#no-aligned");
    const stage = $("#image-stage");
    svg.innerHTML = "";
    resultState._rowRects = null;

    if (!res.aligned) {
      img.removeAttribute("src");
      img.hidden = true;
      stage.hidden = true;
      noA.hidden = false;
      return;
    }
    noA.hidden = true;
    stage.hidden = false;
    img.hidden = false;

    const draw = () => {
      svg.innerHTML = "";
      const nw = img.naturalWidth;
      if (!nw) return;

      svg.setAttribute("viewBox", `0 0 ${nw} ${img.naturalHeight}`);
      svg.setAttribute("preserveAspectRatio", "none");

      let drawn = false;
      if (res.overlay && res.overlay.left && res.overlay.right && res.overlay.col_x) {
        drawn = drawOverlayGrid(svg, res.overlay, res.flags);
      }
      if (!drawn) {
        const tpl = res.template;
        const geo = tpl && tpl.geometry;
        drawTemplateGrid(svg, geo, nw, res.flags);
      }
      appendRowHl(svg);
    };

    img.addEventListener("load", draw, { once: true });
    img.src = res.aligned;
    if (img.complete && img.naturalWidth) draw();
  }

  // ── cell zoom & correct ────────────────────────────────────────
  function openCellModal(r, c, td) {
    if (!resultState || !resultState.token) return;
    cellEdit = { r, c, td };
    const modal = $("#cell-modal");
    const img = $("#cell-modal-img");
    const input = $("#cell-modal-input");
    const title = $("#cell-modal-title");
    title.textContent = `Correct cell R${r + 1} · C${c + 1}`;
    img.removeAttribute("src");
    img.alt = `Cell row ${r}, col ${c}`;
    const cur = td ? td.textContent : "";
    input.value = cur;
    modal.hidden = false;
    img.src = `/api/cell/${encodeURIComponent(resultState.token)}/${r}/${c}?t=${Date.now()}`;
    setTimeout(() => {
      input.focus();
      input.select();
    }, 0);
  }

  function closeCellModal() {
    $("#cell-modal").hidden = true;
    cellEdit = null;
    $("#cell-modal-img").removeAttribute("src");
  }

  function saveCellCorrection() {
    if (!cellEdit) return;
    const { r, c, td } = cellEdit;
    const val = $("#cell-modal-input").value;
    const cell =
      td || $(`#extract-table td.data-cell[data-row="${r}"][data-col="${c}"]`);
    if (cell) {
      cell.textContent = val;
      cell.classList.add("human-corrected");
    }
    // keep resultState.grid in sync for CSV export
    if (resultState && resultState.grid && resultState.grid.table) {
      const table = resultState.grid.table;
      if (table[r + 1]) table[r + 1][c] = val;
    }
    closeCellModal();
  }

  $("#cell-modal-save").addEventListener("click", saveCellCorrection);
  $("#cell-modal-close").addEventListener("click", closeCellModal);
  $$("[data-close-modal]").forEach((n) =>
    n.addEventListener("click", closeCellModal)
  );
  $("#cell-modal-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      saveCellCorrection();
    } else if (e.key === "Escape") {
      closeCellModal();
    }
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !$("#cell-modal").hidden) closeCellModal();
  });

  function csvEscape(v) {
    const s = v == null ? "" : String(v);
    if (/[",\r\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
    return s;
  }

  function exportCorrectedCsv() {
    if (!resultState || !resultState.grid || !resultState.grid.table) return;
    // Prefer live DOM (includes human corrections) over stored grid
    const table = [];
    const ths = $$("#extract-table thead th");
    if (ths.length) table.push(ths.map((th) => th.textContent));
    $$("#extract-table tbody tr.data-row").forEach((tr) => {
      table.push($$("td", tr).map((td) => td.textContent));
    });
    if (!table.length) {
      // fallback to stored grid
      for (const row of resultState.grid.table) {
        table.push(row.map((c) => (c == null ? "" : String(c))));
      }
    }
    const csv = table.map((row) => row.map(csvEscape).join(",")).join("\r\n") + "\r\n";
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const a = document.createElement("a");
    const formId = resultState.form_id || "form";
    a.href = URL.createObjectURL(blob);
    a.download = `${formId}_corrected.csv`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  $("#export-csv").addEventListener("click", exportCorrectedCsv);

  // ── init ───────────────────────────────────────────────────────
  headers = [blankHeader(), blankHeader()];
  headers[0].label = "PHC Name";
  headers[1].label = "Date";
  headers[1].type = "date";
  columns = [
    { label: "S.No", type: "serial", domain: [], legend: "", min: null, max: null },
    { label: "Name", type: "name", domain: [], legend: "", min: null, max: null },
    { label: "Age", type: "int", domain: [], legend: "", min: 0, max: 120 },
    { label: "Remarks", type: "text", domain: [], legend: "", min: null, max: null },
  ];
  renderHeaderList();
  renderColumnList();
  loadProviders();
  loadTemplates(true);
})();
