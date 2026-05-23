const API_BASE = "http://localhost:8000";

async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function atenderAlerta(alertaId) {
  return apiFetch("/api/alertas/atender", {
    method: "POST",
    body: JSON.stringify({ alerta_id: alertaId }),
  });
}

async function fetchRegistrosFallos(filtros = {}) {
  const params = new URLSearchParams();
  if (filtros.torno_id) params.set("torno_id", filtros.torno_id);
  if (filtros.estado) params.set("estado", filtros.estado);
  if (filtros.desde) params.set("desde", filtros.desde);
  if (filtros.hasta) params.set("hasta", filtros.hasta);
  if (filtros.limite) params.set("limite", filtros.limite);
  const qs = params.toString();
  return apiFetch(`/api/registros-fallo${qs ? "?" + qs : ""}`);
}

async function fetchEstadoPorTorno(tornoId) {
  return apiFetch(`/api/estado-actual?torno_id=${tornoId}`);
}

async function fetchTornosActivos() {
  return apiFetch("/api/estado-actual/todos");
}

async function fetchAlertas(noAtendidas = false) {
  const qs = noAtendidas ? "?no_atendidas=true" : "";
  return apiFetch(`/api/alertas${qs}`);
}
