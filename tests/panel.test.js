const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");
const app = require("../panel/app.js");

function ejemplo(nombre) {
  return app.parsearCsv(fs.readFileSync(path.join(__dirname, "..", "datos", "ejemplo", nombre), "utf8"));
}

test("parsea el CSV y respeta los comentarios", () => {
  const d = app.parsearCsv("# nota\nt_s,ax_g,ay_g,az_g,gx_dps,gy_dps,gz_dps\n0,0,0,1,0,0,0\n0.01,0,0,1,0,0,0\n0.02,0,0,1,0,0,0\n");
  assert.strictEqual(d.t_s.length, 3);
  assert.strictEqual(d.az_g[0], 1);
});

test("rechaza un CSV sin las columnas esperadas", () => {
  assert.throws(() => app.parsearCsv("a,b\n1,2\n3,4\n"));
});

test("pendulo de 60 cm: periodo cercano al teorico", () => {
  const d = ejemplo("pendulo_60cm.csv");
  const r = app.analizar(d, "giro");
  const teorico = 2 * Math.PI * Math.sqrt(0.6 / 9.81);
  assert.strictEqual(r.eje, "gy_dps");
  assert.ok(Math.abs(r.periodo - teorico) < 0.02, "periodo " + r.periodo + " vs " + teorico);
  assert.ok(Math.abs(1 / r.frecuencia - teorico) < 0.03);
});

test("g desde el pendulo ronda 9,8", () => {
  const d = ejemplo("pendulo_60cm.csv");
  const r = app.analizar(d, "giro");
  const g = app.gDesdePendulo(0.6, r.periodo);
  assert.ok(Math.abs(g - 9.81) < 0.3, "g = " + g);
});

test("viga de 12 cm: frecuencia cercana a 0,30 / L^2 (L en metros)", () => {
  const d = ejemplo("vibracion_12cm.csv");
  const r = app.analizar(d, "acel");
  const esperada = 0.3 / (0.12 * 0.12); // 20,8 Hz; los datos tienen 1 % de ruido en el largo
  assert.ok(Math.abs(r.frecuencia - esperada) < 1.0, "f = " + r.frecuencia + " vs " + esperada);
  assert.ok(Math.abs(r.fs - 400) < 2);
});

test("periodoPorCruces devuelve null con muy pocos ciclos", () => {
  const t = [0, 0.1, 0.2, 0.3];
  assert.strictEqual(app.periodoPorCruces(t, [0, 1, 0, 1]), null);
});

test("la FFT encuentra una senoide de 7 Hz", () => {
  const fs_ = 200, n = 800;
  const t = Array.from({ length: n }, (_, i) => i / fs_);
  const y = t.map((x) => Math.sin(2 * Math.PI * 7 * x));
  assert.ok(Math.abs(app.frecuenciaDominante(t, y) - 7) < 0.05);
});
