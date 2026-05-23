const WS_HOST = "localhost";
const WS_PORT = 8000;

let ws = null;
let alertas = [];
let reconnectTimeout = null;
let estadoTimeout = null;
const ESTADO_TIMEOUT_MS = 3000;

/* ----- DOM refs ----- */
const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);
const statusDot = $("#statusDot");
const statusText = $("#statusText");
const views = { operador: $("#view-operador"), supervisor: $("#view-supervisor") };
const tabs = document.querySelectorAll(".tab-btn");

/* ----- Panel operador ----- */
const pIcon = $("#panelIcon");
const pModo = $("#panelModo");
const pTorno = $("#panelTorno");
const pTemp = $("#panelTemp");
const pVib = $("#panelVib");
const panelO = $("#panelOperador");

/* ----- Gauges ----- */
const gTemp = $("#gaugeTemp");
const gVib = $("#gaugeVib");
const gTempVal = $("#gaugeTempValue");
const gVibVal = $("#gaugeVibValue");

/* ----- Prediccion card ----- */
const predCard = $("#predCard");
const predBar = $("#predBar");
const predValue = $("#predValue");
const predRul = $("#predRul");
const predModo = $("#predModo");
const predPendTemp = $("#predPendTemp");
const predPendVib = $("#predPendVib");
const predSeveridad = $("#predSeveridad");

/* ----- Panel supervisor ----- */
const sIcon = $("#sPanelIcon");
const sModo = $("#sPanelModo");
const sTorno = $("#sPanelTorno");
const sTemp = $("#sPanelTemp");
const sVib = $("#sPanelVib");
const panelS = $("#panelSupervisor");
const alertasLista = $("#alertasLista");
const alertaBadge = $("#alertaBadge");
const btnExportarCSV = $("#btnExportarCSV");

/* ----- Filtros ----- */
const filtroEstado = $("#filtroEstado");
const filtroDesdeFecha = $("#filtroDesdeFecha");
const filtroDesdeHora = $("#filtroDesdeHora");
const filtroHastaFecha = $("#filtroHastaFecha");
const filtroHastaHora = $("#filtroHastaHora");
const btnFiltrar = $("#btnFiltrar");
const btnLimpiar = $("#btnLimpiar");
const rapidoBtns = $$(".rapido-btn");
const tablaBody = $("#tablaBody");
const totalRegistros = $("#totalRegistros");

/* ----- Tab Navigation ----- */
tabs.forEach((btn) => {
  btn.addEventListener("click", () => {
    tabs.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    const view = btn.dataset.view;
    Object.entries(views).forEach(([k, el]) => {
      el.classList.toggle("active", k === view);
    });
    if (view === "supervisor") cargarRegistros();
  });
});

/* ----- Helpers ----- */
function pct(value, min, max) {
  return Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100));
}

function gaugeColor(value, warning, danger) {
  if (value >= danger) return "#ff0044";
  if (value >= warning) return "#ffcc00";
  return "#00ff88";
}

/* ----- Panel ---- */
function updatePanel(panel, iconEl, modoEl, tornoEl, tempEl, vibEl, estado) {
  const isEmergencia = estado.paro_emergencia;
  const isAlerta = estado.alerta_activa === "PREDICTIVA_AMARILLA";

  panel.className = "panel-control";
  if (isEmergencia) panel.classList.add("emergencia");
  else if (isAlerta) panel.classList.add("alerta");

  iconEl.textContent = isEmergencia ? "🔴" : isAlerta ? "🟡" : "🟢";
  modoEl.textContent = isEmergencia
    ? "PARO DE EMERGENCIA"
    : isAlerta
    ? "ALERTA PREDICTIVA"
    : "OPERACIÓN NORMAL";
  tornoEl.textContent = `Torno #${estado.torno_id}`;
  tempEl.textContent = `${estado.temperatura.toFixed(1)}°C`;
  vibEl.textContent = `${estado.vibracion_total.toFixed(2)}G`;
}

function updateGauges(estado) {
  const tempPct = pct(estado.temperatura, 30, 100);
  const vibPct = pct(estado.vibracion_total, 0, 6);

  const tempColor = gaugeColor(estado.temperatura, 38, 40);
  const vibColor = gaugeColor(estado.vibracion_total, 3.0, 4.0);

  gTemp.style.width = `${tempPct}%`;
  gTemp.style.background = tempColor;
  gTempVal.textContent = `${estado.temperatura.toFixed(1)} °C`;
  gTempVal.style.color = tempColor;

  gVib.style.width = `${vibPct}%`;
  gVib.style.background = vibColor;
  gVibVal.textContent = `${estado.vibracion_total.toFixed(2)} G`;
  gVibVal.style.color = vibColor;
}

function updateBodyBg(estado) {
  const isEmergencia = estado.paro_emergencia;
  const isAlerta = estado.alerta_activa === "PREDICTIVA_AMARILLA";
  document.body.className = "";
  if (isEmergencia) document.body.classList.add("emergencia-bg");
  else if (isAlerta) document.body.classList.add("alerta-bg");
}

/* ----- Prediccion ----- */
function updatePrediccion(p) {
  const pctVal = Math.round(p.probabilidad * 100);
  predBar.style.width = `${pctVal}%`;
  predValue.textContent = `${pctVal}%`;

  let color = "#00ff88";
  if (p.probabilidad >= 0.8) color = "#da3633";
  else if (p.probabilidad >= 0.6) color = "#d29922";
  else if (p.probabilidad >= 0.3) color = "#2f81f7";
  predBar.style.background = color;
  predValue.style.color = color;

  predSeveridad.textContent = p.severidad || "—";
  predSeveridad.className = "pred-severidad";
  if (p.severidad === "CRITICA") predSeveridad.classList.add("critica");
  else if (p.severidad === "ADVERTENCIA") predSeveridad.classList.add("advertencia");
  else if (p.severidad === "OBSERVACION") predSeveridad.classList.add("observacion");

  predRul.textContent = p.rul_estimado != null ? `${p.rul_estimado}s` : "—";
  predModo.textContent = p.modo_fallo || "—";
  predPendTemp.textContent = p.pendiente_temperatura != null ? p.pendiente_temperatura.toFixed(4) : "—";
  predPendVib.textContent = p.pendiente_vibracion != null ? p.pendiente_vibracion.toFixed(4) : "—";
}

/* ----- Alertas ---- */
function renderAlertas() {
  if (alertas.length === 0) {
    alertasLista.innerHTML = '<div class="alerta-empty">Sin alertas registradas</div>';
    alertaBadge.textContent = "0 pendientes";
    return;
  }

  const pendientes = alertas.filter((a) => a.atendida === 0).length;
  alertaBadge.textContent = `${pendientes} pendientes`;

  alertasLista.innerHTML = alertas
    .map((a) => {
      const isRoja = a.tipo_alerta === "EMERGENCIA_ROJA";
      const isAmarilla = a.tipo_alerta === "PREDICTIVA_AMARILLA";
      const cls = `alerta-card${isRoja ? " roja" : ""}${isAmarilla ? " amarilla" : ""}${a.atendida === 1 ? " atendida" : ""}`;
      const tipo = isRoja ? "🚨 EMERGENCIA" : "⚠ PREDICTIVA";
      const fecha = new Date(a.timestamp).toLocaleTimeString();
      const atendidaHtml = a.atendida === 1 ? '<div class="alerta-atendida">✓ Atendida</div>' : "";
      return `
        <div class="${cls}" data-id="${a.id}" data-atendida="${a.atendida}">
          <div class="alerta-header">
            <span class="alerta-tipo">${tipo}</span>
            <span class="alerta-fecha">${fecha}</span>
          </div>
          <div class="alerta-desc">${a.descripcion || ""}</div>
          ${atendidaHtml}
        </div>
      `;
    })
    .join("");

  document.querySelectorAll(".alerta-card:not(.atendida)").forEach((card) => {
    card.addEventListener("click", async () => {
      const id = parseInt(card.dataset.id);
      try {
        await atenderAlerta(id);
        card.classList.add("atendida");
        if (!card.querySelector(".alerta-atendida")) {
          card.insertAdjacentHTML("beforeend", '<div class="alerta-atendida">✓ Atendida</div>');
        }
        const pend = alertas.filter((a) => a.atendida === 0).length - 1;
        alertaBadge.textContent = `${pend} pendientes`;
      } catch (e) {
        console.error("Error al atender alerta:", e);
      }
    });
  });
}

/* ----- FILTROS ----- */
function formatearFechaLocal(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString() + " " + d.toLocaleTimeString();
}

function estadoHtml(tipo) {
  if (tipo === "EMERGENCIA_ROJA") return '<span class="estado-badge rojo">🔴 Emergencia</span>';
  if (tipo === "PREDICTIVA_AMARILLA") return '<span class="estado-badge amarillo">🟡 Alerta</span>';
  return '<span class="estado-badge verde">✅ Normal</span>';
}

function estadoClase(tipo) {
  if (tipo === "EMERGENCIA_ROJA") return "roja";
  if (tipo === "PREDICTIVA_AMARILLA") return "amarilla";
  return "normal";
}

async function cargarRegistros() {
  const filtros = {};
  if (filtroEstado.value) filtros.estado = filtroEstado.value;

  if (filtroDesdeFecha.value) {
    let iso = filtroDesdeFecha.value;
    if (filtroDesdeHora.value) iso += "T" + filtroDesdeHora.value + ":00";
    else iso += "T00:00:00";
    filtros.desde = new Date(iso).toISOString();
  }
  if (filtroHastaFecha.value) {
    let iso = filtroHastaFecha.value;
    if (filtroHastaHora.value) iso += "T" + filtroHastaHora.value + ":00";
    else iso += "T23:59:59";
    filtros.hasta = new Date(iso).toISOString();
  }

  filtros.limite = 200;

  try {
    const data = await fetchRegistrosFallos(filtros);
    totalRegistros.textContent = data.length;

    if (data.length === 0) {
      tablaBody.innerHTML = '<tr><td colspan="4" class="tabla-empty">Sin registros</td></tr>';
      return;
    }

    tablaBody.innerHTML = data
      .map((r) => {
        return `
          <tr class="${estadoClase(r.tipo_alerta)}">
            <td>${r.temperatura.toFixed(1)}°C</td>
            <td>${r.vibracion_total ? r.vibracion_total.toFixed(2) + " G" : "—"}</td>
            <td>${estadoHtml(r.tipo_alerta)}</td>
            <td>${formatearFechaLocal(r.timestamp)}</td>
          </tr>
        `;
      })
      .join("");
  } catch (e) {
    tablaBody.innerHTML = `<tr><td colspan="4" class="tabla-empty">Error al cargar: ${e.message}</td></tr>`;
  }
}

function limpiarFiltros() {
  filtroEstado.value = "";
  filtroDesdeFecha.value = "";
  filtroDesdeHora.value = "";
  filtroHastaFecha.value = "";
  filtroHastaHora.value = "";
  rapidoBtns.forEach((b) => b.classList.remove("activo"));
  cargarRegistros();
}

function aplicarRapido(minutos) {
  rapidoBtns.forEach((b) => b.classList.toggle("activo", parseInt(b.dataset.minutos) === minutos));
  if (minutos === 0) {
    filtroDesdeFecha.value = "";
    filtroDesdeHora.value = "";
    filtroHastaFecha.value = "";
    filtroHastaHora.value = "";
  } else {
    const desde = new Date(Date.now() - minutos * 60000);
    filtroDesdeFecha.value = desde.toISOString().slice(0, 10);
    filtroDesdeHora.value = desde.toISOString().slice(11, 16);
    filtroHastaFecha.value = "";
    filtroHastaHora.value = "";
  }
  cargarRegistros();
}

btnFiltrar.addEventListener("click", cargarRegistros);
btnLimpiar.addEventListener("click", limpiarFiltros);
rapidoBtns.forEach((btn) => {
  btn.addEventListener("click", () => aplicarRapido(parseInt(btn.dataset.minutos)));
});

/* ----- Exportar CSV ----- */
btnExportarCSV.addEventListener("click", () => {
  const a = document.createElement("a");
  a.href = `${API_BASE}/api/alertas/exportar-csv`;
  a.download = "alertas_mantenimiento.csv";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
});

/* ----- WebSocket ----- */
function reiniciarWatchdog() {
  clearTimeout(estadoTimeout);
  statusDot.classList.add("online");
  statusText.textContent = "Conectado · Torno #1";
  estadoTimeout = setTimeout(() => {
    statusDot.classList.remove("online");
    statusText.textContent = "Sin datos · Torno #1";
  }, ESTADO_TIMEOUT_MS);
}

function conectarWS() {
  if (ws) {
    ws.onclose = null;
    ws.close();
    ws = null;
  }
  clearTimeout(reconnectTimeout);

  ws = new WebSocket(`ws://${WS_HOST}:${WS_PORT}/ws/1`);

  ws.onopen = () => {
    statusDot.classList.add("online");
    statusText.textContent = "Esperando datos...";
    estadoTimeout = setTimeout(() => {
      statusDot.classList.remove("online");
      statusText.textContent = "Sin datos · Torno #1";
    }, ESTADO_TIMEOUT_MS);
  };

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);

      if (msg.type === "estado") {
        const e = msg.data;
        reiniciarWatchdog();
        updatePanel(panelO, pIcon, pModo, pTorno, pTemp, pVib, e);
        updatePanel(panelS, sIcon, sModo, sTorno, sTemp, sVib, e);
        updateGauges(e);
        updateBodyBg(e);
      }

      if (msg.type === "prediccion") {
        updatePrediccion(msg.data);
      }
        const idx = alertas.findIndex((a) => a.id === msg.data.id);
        if (idx >= 0) {
          alertas[idx] = msg.data;
        } else {
          alertas.unshift(msg.data);
          alertas = alertas.slice(0, 100);
        }
        renderAlertas();
      }
    } catch (e) {
      // ignore
    }
  };

  ws.onclose = () => {
    clearTimeout(estadoTimeout);
    statusDot.classList.remove("online");
    statusText.textContent = "Desconectado · reconectando...";
    reconnectTimeout = setTimeout(conectarWS, 3000);
  };

  ws.onerror = () => {
    ws.close();
  };
}

async function cargarAlertasIniciales() {
  try {
    const data = await fetchAlertas();
    alertas = data.slice(0, 100);
    renderAlertas();
  } catch (e) {
    // ignore
  }
}

cargarAlertasIniciales();
conectarWS();
