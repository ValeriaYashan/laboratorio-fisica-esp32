// Visor de experimentos del laboratorio de fisica de bolsillo.
// Funciones puras arriba (se prueban con node --test), interfaz abajo.
// Todo el texto del usuario entra al DOM con textContent, nunca con innerHTML.

const CANALES = ["ax_g", "ay_g", "az_g", "gx_dps", "gy_dps", "gz_dps"];
const GRUPOS = { acel: ["ax_g", "ay_g", "az_g"], giro: ["gx_dps", "gy_dps", "gz_dps"] };

const TEXTOS = {
  es: {
    titulo: "Laboratorio de física de bolsillo",
    subtitulo: "Abrí un CSV grabado con el ESP32 + MPU-6050 y mirá qué dice la física.",
    cargar: "Abrir CSV:",
    péndulo: "Ejemplo: péndulo 60 cm",
    viga: "Ejemplo: viga 12 cm",
    grupo: "Magnitud",
    acel: "Aceleración (g)",
    giro: "Velocidad angular (dps)",
    canales: "Canales",
    tiempo: "Tiempo (s)",
    estadisticas: "Estadísticas",
    muestras: "Muestras",
    duracion: "Duración (s)",
    fs: "Frecuencia de muestreo (Hz)",
    eje: "Eje dominante",
    período: "Período por cruces por cero (s)",
    frecuencia: "Frecuencia dominante FFT (Hz)",
    teoria: "Si es un péndulo de largo L (m), g = 4π²L/T² = ",
    largo: "Largo L (m):",
    sinDatos: "Todavía no hay datos.",
    error: "No se pudo leer el archivo: ",
    simulado: "Los datos de ejemplo son simulados.",
    ninguno: "sin datos suficientes",
  },
  en: {
    titulo: "Pocket physics lab",
    subtitulo: "Open a CSV recorded with the ESP32 + MPU-6050 and see what the physics says.",
    cargar: "Open CSV:",
    pendulo: "Example: 60 cm pendulum",
    viga: "Example: 12 cm beam",
    grupo: "Quantity",
    acel: "Acceleration (g)",
    giro: "Angular velocity (dps)",
    canales: "Channels",
    tiempo: "Time (s)",
    estadisticas: "Statistics",
    muestras: "Samples",
    duracion: "Duration (s)",
    fs: "Sampling rate (Hz)",
    eje: "Dominant axis",
    periodo: "Period from zero crossings (s)",
    frecuencia: "Dominant FFT frequency (Hz)",
    teoria: "If it is a pendulum of length L (m), g = 4π²L/T² = ",
    largo: "Length L (m):",
    sinDatos: "No data yet.",
    error: "Could not read the file: ",
    simulado: "The example data are simulated.",
    ninguno: "not enough data",
  },
};

function parsearCsv(texto) {
  const lineas = texto.split(/\r?\n/).filter((l) => l.trim() !== "" && !l.startsWith("#"));
  if (lineas.length < 2) throw new Error("CSV vacio");
  const cabecera = lineas[0].split(",").map((s) => s.trim());
  const idx = {};
  for (const c of ["t_s", ...CANALES]) {
    idx[c] = cabecera.indexOf(c);
    if (idx[c] < 0) throw new Error("falta la columna " + c);
  }
  const datos = { t_s: [] };
  for (const c of CANALES) datos[c] = [];
  for (let i = 1; i < lineas.length; i++) {
    const partes = lineas[i].split(",");
    const fila = {};
    let ok = true;
    for (const c of ["t_s", ...CANALES]) {
      const v = parseFloat(partes[idx[c]]);
      if (!Number.isFinite(v)) { ok = false; break; }
      fila[c] = v;
    }
    if (!ok) continue;
    for (const c of ["t_s", ...CANALES]) datos[c].push(fila[c]);
  }
  if (datos.t_s.length < 3) throw new Error("muy pocas filas");
  return datos;
}

function frecuenciaMuestreo(t) {
  const n = t.length;
  return (n - 1) / (t[n - 1] - t[0]);
}

function media(v) {
  let s = 0;
  for (const x of v) s += x;
  return s / v.length;
}

function desvio(v) {
  const m = media(v);
  let s = 0;
  for (const x of v) s += (x - m) * (x - m);
  return Math.sqrt(s / v.length);
}

function ejeDominante(datos, canales) {
  let mejor = canales[0];
  let mayor = -1;
  for (const c of canales) {
    const d = desvio(datos[c]);
    if (d > mayor) { mayor = d; mejor = c; }
  }
  return mejor;
}

// Periodo medio entre cruces ascendentes por la media, con histeresis del 10 % de la amplitud.
function periodoPorCruces(t, y) {
  const m = media(y);
  const c = y.map((v) => v - m);
  let maxAbs = 0;
  for (const v of c) maxAbs = Math.max(maxAbs, Math.abs(v));
  const umbral = 0.1 * maxAbs;
  if (maxAbs === 0) return null;
  const cruces = [];
  let armado = c[0] < -umbral;
  for (let i = 1; i < c.length; i++) {
    if (c[i] < -umbral) armado = true;
    if (armado && c[i] >= 0 && c[i - 1] < 0) {
      const f = -c[i - 1] / (c[i] - c[i - 1]);
      cruces.push(t[i - 1] + f * (t[i] - t[i - 1]));
      armado = false;
    }
  }
  if (cruces.length < 3) return null;
  return (cruces[cruces.length - 1] - cruces[0]) / (cruces.length - 1);
}

function fft(re, im) {
  const n = re.length;
  for (let i = 1, j = 0; i < n; i++) {
    let bit = n >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) { [re[i], re[j]] = [re[j], re[i]]; [im[i], im[j]] = [im[j], im[i]]; }
  }
  for (let len = 2; len <= n; len <<= 1) {
    const ang = (-2 * Math.PI) / len;
    for (let i = 0; i < n; i += len) {
      for (let k = 0; k < len / 2; k++) {
        const wr = Math.cos(ang * k);
        const wi = Math.sin(ang * k);
        const ur = re[i + k], ui = im[i + k];
        const vr = re[i + k + len / 2] * wr - im[i + k + len / 2] * wi;
        const vi = re[i + k + len / 2] * wi + im[i + k + len / 2] * wr;
        re[i + k] = ur + vr; im[i + k] = ui + vi;
        re[i + k + len / 2] = ur - vr; im[i + k + len / 2] = ui - vi;
      }
    }
  }
}

// Frecuencia del pico del espectro (ventana de Hann, interpolacion parabolica).
function frecuenciaDominante(t, y, fMin = 0.3) {
  const n = y.length;
  const fs = frecuenciaMuestreo(t);
  let N = 1;
  while (N < n) N <<= 1;
  N <<= 1; // relleno con ceros para afinar la grilla
  const m = media(y);
  const re = new Array(N).fill(0);
  const im = new Array(N).fill(0);
  for (let i = 0; i < n; i++) {
    const w = 0.5 - 0.5 * Math.cos((2 * Math.PI * i) / (n - 1));
    re[i] = (y[i] - m) * w;
  }
  fft(re, im);
  const mag = [];
  for (let k = 0; k <= N / 2; k++) mag.push(Math.hypot(re[k], im[k]));
  const kMin = Math.max(1, Math.ceil((fMin * N) / fs));
  let kp = kMin;
  for (let k = kMin; k < mag.length - 1; k++) if (mag[k] > mag[kp]) kp = k;
  let delta = 0;
  if (kp > 0 && kp < mag.length - 1) {
    const a = mag[kp - 1], b = mag[kp], c = mag[kp + 1];
    const den = a - 2 * b + c;
    if (den !== 0) delta = (0.5 * (a - c)) / den;
  }
  return ((kp + delta) * fs) / N;
}

function gDesdePendulo(largoM, periodoS) {
  return (4 * Math.PI * Math.PI * largoM) / (periodoS * periodoS);
}

function analizar(datos, grupo) {
  const canales = GRUPOS[grupo];
  const eje = ejeDominante(datos, canales);
  return {
    muestras: datos.t_s.length,
    duracion: datos.t_s[datos.t_s.length - 1] - datos.t_s[0],
    fs: frecuenciaMuestreo(datos.t_s),
    eje,
    periodo: periodoPorCruces(datos.t_s, datos[eje]),
    frecuencia: frecuenciaDominante(datos.t_s, datos[eje]),
  };
}

if (typeof module !== "undefined") {
  module.exports = {
    parsearCsv, frecuenciaMuestreo, ejeDominante, periodoPorCruces,
    frecuenciaDominante, gDesdePendulo, analizar, TEXTOS, GRUPOS, CANALES,
  };
}

// ---------------------------------------------------------------- interfaz
if (typeof document !== "undefined") {
  const COLORES = ["#378ADD", "#D85A30", "#1D9E75"];
  const estado = { datos: null, grupo: "acel", activos: new Set(), idioma: "es", cursor: null, largo: 0.6 };
  const $ = (id) => document.getElementById(id);

  const t = (clave) => TEXTOS[estado.idioma][clave];

  function textos() {
    document.documentElement.lang = estado.idioma;
    document.querySelectorAll("[data-t]").forEach((el) => { el.textContent = t(el.dataset.t); });
    document.title = t("titulo");
    dibujar();
    estadisticas();
  }

  function mensaje(texto) { $("mensaje").textContent = texto; }

  function cargarTexto(texto, aviso) {
    try {
      estado.datos = parsearCsv(texto);
      estado.activos = new Set(GRUPOS[estado.grupo]);
      mensaje(aviso || "");
      opciones();
      dibujar();
      estadisticas();
    } catch (e) {
      mensaje(t("error") + e.message);
    }
  }

  function opciones() {
    const caja = $("canales");
    caja.textContent = "";
    GRUPOS[estado.grupo].forEach((c, i) => {
      const etiqueta = document.createElement("label");
      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.checked = estado.activos.has(c);
      cb.addEventListener("change", () => {
        if (cb.checked) estado.activos.add(c); else estado.activos.delete(c);
        dibujar();
      });
      const muestra = document.createElement("span");
      muestra.textContent = " ■ ";
      muestra.style.color = COLORES[i];
      etiqueta.append(cb, muestra, document.createTextNode(c));
      caja.append(etiqueta);
    });
  }

  function dibujar() {
    const lienzo = $("grafico");
    const ratio = window.devicePixelRatio || 1;
    const w = lienzo.clientWidth, h = lienzo.clientHeight;
    lienzo.width = w * ratio; lienzo.height = h * ratio;
    const g = lienzo.getContext("2d");
    g.setTransform(ratio, 0, 0, ratio, 0, 0);
    const estilo = getComputedStyle(document.body);
    const texto = estilo.color;
    g.clearRect(0, 0, w, h);
    g.font = "12px system-ui, sans-serif";
    if (!estado.datos) {
      g.fillStyle = texto;
      g.fillText(t("sinDatos"), 16, 24);
      return;
    }
    const d = estado.datos;
    const canales = GRUPOS[estado.grupo].filter((c) => estado.activos.has(c));
    const m = { l: 56, r: 12, t: 12, b: 36 };
    let lo = Infinity, hi = -Infinity;
    for (const c of canales) for (const v of d[c]) { lo = Math.min(lo, v); hi = Math.max(hi, v); }
    if (!canales.length) { lo = -1; hi = 1; }
    if (lo === hi) { lo -= 1; hi += 1; }
    const pad = (hi - lo) * 0.05; lo -= pad; hi += pad;
    const t0 = d.t_s[0], t1 = d.t_s[d.t_s.length - 1];
    const X = (v) => m.l + ((v - t0) / (t1 - t0)) * (w - m.l - m.r);
    const Y = (v) => h - m.b - ((v - lo) / (hi - lo)) * (h - m.t - m.b);

    g.strokeStyle = "rgba(128,128,128,.3)"; g.fillStyle = texto; g.lineWidth = 1;
    for (let i = 0; i <= 5; i++) {
      const v = lo + ((hi - lo) * i) / 5;
      g.beginPath(); g.moveTo(m.l, Y(v)); g.lineTo(w - m.r, Y(v)); g.stroke();
      g.fillText(v.toFixed(2), 6, Y(v) + 4);
    }
    for (let i = 0; i <= 5; i++) {
      const v = t0 + ((t1 - t0) * i) / 5;
      g.fillText(v.toFixed(1), X(v) - 8, h - m.b + 16);
    }
    g.fillText(t("tiempo"), w / 2 - 24, h - 6);

    GRUPOS[estado.grupo].forEach((c, i) => {
      if (!estado.activos.has(c)) return;
      g.strokeStyle = COLORES[i]; g.lineWidth = 1.5; g.beginPath();
      const paso = Math.max(1, Math.floor(d.t_s.length / (w * 2)));
      for (let k = 0; k < d.t_s.length; k += paso) {
        const x = X(d.t_s[k]), y = Y(d[c][k]);
        if (k === 0) g.moveTo(x, y); else g.lineTo(x, y);
      }
      g.stroke();
    });

    if (estado.cursor !== null) {
      const tc = estado.cursor;
      g.strokeStyle = texto; g.setLineDash([4, 4]);
      g.beginPath(); g.moveTo(X(tc), m.t); g.lineTo(X(tc), h - m.b); g.stroke();
      g.setLineDash([]);
      let k = 0;
      while (k < d.t_s.length - 1 && d.t_s[k] < tc) k++;
      let linea = "t=" + d.t_s[k].toFixed(3) + " s";
      for (const c of canales) linea += "   " + c + "=" + d[c][k].toFixed(3);
      g.fillStyle = texto; g.fillText(linea, m.l + 6, m.t + 12);
    }
    lienzo._escala = { m, t0, t1, w };
  }

  function fila(tabla, nombre, valor) {
    const tr = document.createElement("tr");
    const a = document.createElement("td"); a.textContent = nombre;
    const b = document.createElement("td"); b.textContent = valor;
    tr.append(a, b); tabla.append(tr);
  }

  function estadisticas() {
    const tabla = $("tabla");
    tabla.textContent = "";
    if (!estado.datos) return;
    const r = analizar(estado.datos, estado.grupo);
    fila(tabla, t("muestras"), String(r.muestras));
    fila(tabla, t("duracion"), r.duracion.toFixed(2));
    fila(tabla, t("fs"), r.fs.toFixed(1));
    fila(tabla, t("eje"), r.eje);
    fila(tabla, t("periodo"), r.periodo === null ? t("ninguno") : r.periodo.toFixed(4));
    fila(tabla, t("frecuencia"), r.frecuencia.toFixed(3));
    const g = r.periodo === null ? null : gDesdePendulo(estado.largo, r.periodo);
    $("pendulo-g").textContent = t("teoria") + (g === null ? "-" : g.toFixed(2) + " m/s²");
  }

  function elegirGrupo(grupo) {
    estado.grupo = grupo;
    estado.activos = new Set(GRUPOS[grupo]);
    document.querySelector("input[name=grupo][value=" + grupo + "]").checked = true;
  }

  async function ejemplo(nombre, grupo) {
    elegirGrupo(grupo);
    try {
      const resp = await fetch("../datos/ejemplo/" + nombre);
      if (!resp.ok) throw new Error(String(resp.status));
      cargarTexto(await resp.text(), t("simulado"));
    } catch (e) {
      mensaje(t("error") + e.message);
    }
  }

  $("idioma").addEventListener("change", (e) => { estado.idioma = e.target.value; textos(); });
  $("archivo").addEventListener("change", (e) => {
    const f = e.target.files[0];
    if (!f) return;
    const lector = new FileReader();
    lector.onload = () => cargarTexto(String(lector.result), "");
    lector.readAsText(f);
  });
  $("btn-pendulo").addEventListener("click", () => { estado.largo = 0.6; $("largo").value = "0.6"; ejemplo("pendulo_60cm.csv", "giro"); });
  $("btn-viga").addEventListener("click", () => { ejemplo("vibracion_12cm.csv", "acel"); });
  $("largo").addEventListener("input", (e) => {
    const v = parseFloat(e.target.value.replace(",", "."));
    if (Number.isFinite(v) && v > 0) { estado.largo = v; estadisticas(); }
  });
  document.querySelectorAll("input[name=grupo]").forEach((r) => r.addEventListener("change", () => {
    estado.grupo = r.value;
    estado.activos = new Set(GRUPOS[estado.grupo]);
    opciones(); dibujar(); estadisticas();
  }));
  const lienzo = $("grafico");
  lienzo.addEventListener("mousemove", (e) => {
    if (!estado.datos || !lienzo._escala) return;
    const { m, t0, t1, w } = lienzo._escala;
    const x = e.clientX - lienzo.getBoundingClientRect().left;
    const f = (x - m.l) / (w - m.l - m.r);
    estado.cursor = f < 0 || f > 1 ? null : t0 + f * (t1 - t0);
    dibujar();
  });
  lienzo.addEventListener("mouseleave", () => { estado.cursor = null; dibujar(); });
  window.addEventListener("resize", dibujar);

  opciones();
  textos();
}
