// Caja parametrica para el laboratorio de fisica de bolsillo (ESP32 DevKit + GY-521).
// Unidades: milimetros. Cambia "parte" y exporta cada pieza a STL por separado.
//   "caja_base" | "caja_tapa" | "viga" | "todo"
// AVISO: este archivo no fue renderizado ni impreso por quien lo escribio.
// Imprimi una prueba y verifica las medidas con tu placa y tu calibre antes de la version final.

parte = "todo";

// --- Medidas interiores (revisalas con tu placa) ---
int_x = 94;      // largo interior
int_y = 34;      // ancho interior
int_z = 18;      // alto interior
pared = 2.4;
piso = 2.4;
tapa_e = 3;      // espesor de la tapa
tol = 0.3;       // holgura de encastre

// --- Postes de tornillo en las cuatro esquinas ---
poste_d = 7;
tornillo_d = 2.6;   // agujero guia para tornillo autorroscante M3

// --- Boton y orejas ---
boton_d = 7.2;
oreja_w = 12;
oreja_agujero = 4.5;

// --- Viga en voladizo ---
largo_viga = 150;   // largo total que se imprime (se recorta en clase)
ancho_viga = 20;
espesor_viga = 3;
bloque_x = 30;
bloque_y = 30;
bloque_z = 12;
agujero_bloque = 4.4;

ext_x = int_x + 2 * pared;
ext_y = int_y + 2 * pared;
ext_z = int_z + piso;

$fn = 48;

module posiciones_postes() {
    for (x = [pared + poste_d / 2, pared + int_x - poste_d / 2])
        for (y = [pared + poste_d / 2, pared + int_y - poste_d / 2])
            translate([x, y, 0]) children();
}

module caja_base() {
    difference() {
        union() {
            difference() {
                cube([ext_x, ext_y, ext_z]);
                translate([pared, pared, piso]) cube([int_x, int_y, int_z + 1]);
            }
            posiciones_postes() cylinder(d = poste_d, h = ext_z);
            // orejas para abrazadera o precinto
            for (s = [0, 1])
                translate([s == 0 ? -oreja_w : ext_x, ext_y / 2 - 6, 0])
                    cube([oreja_w, 12, piso + 1.2]);
        }
        // agujeros guia en los postes
        posiciones_postes() translate([0, 0, ext_z - 10]) cylinder(d = tornillo_d, h = 11);
        // salida USB en la pared de x minimo
        translate([-1, ext_y / 2 - 6, piso + 3]) cube([pared + 2, 12, 8]);
        // agujeros de las orejas
        for (s = [0, 1])
            translate([s == 0 ? -oreja_w / 2 : ext_x + oreja_w / 2, ext_y / 2, -1])
                cylinder(d = oreja_agujero, h = piso + 4);
    }
    // rieles de apoyo del ESP32 (a lo largo de x, entre los postes)
    for (y = [pared + 4, pared + int_y - 4 - 1.6])
        translate([pared + 12, y, piso]) cube([55, 1.6, 3]);
    // cuna del GY-521: dos topes para que la placa no se deslice
    translate([pared + int_x - 12, pared + int_y / 2 - 10 - 1.6, piso]) cube([8, 1.6, 4]);
    translate([pared + int_x - 12, pared + int_y / 2 + 10, piso]) cube([8, 1.6, 4]);
}

module caja_tapa() {
    difference() {
        cube([ext_x, ext_y, tapa_e]);
        // agujeros de tornillo con avellanado simple
        posiciones_postes() translate([0, 0, -1]) {
            cylinder(d = 3.4, h = tapa_e + 2);
            translate([0, 0, tapa_e - 1.2 + 1]) cylinder(d1 = 3.4, d2 = 6.4, h = 1.3);
        }
        // agujero del boton
        translate([ext_x / 2, ext_y / 2, -1]) cylinder(d = boton_d, h = tapa_e + 2);
        // marca +X grabada (verifica el sentido real inclinando la caja)
        translate([ext_x / 2 + 12, ext_y / 2 - 3, tapa_e - 0.6])
            linear_extrude(1) text("+X", size = 6, halign = "left");
    }
    // reborde que entra en la caja, con espacio para los postes
    translate([pared + tol, pared + tol, tapa_e])
        difference() {
            cube([int_x - 2 * tol, int_y - 2 * tol, 2]);
            translate([2, 2, -1]) cube([int_x - 2 * tol - 4, int_y - 2 * tol - 4, 4]);
            for (x = [0, int_x - 2 * tol - poste_d])
                for (y = [0, int_y - 2 * tol - poste_d])
                    translate([x - 0.5, y - 0.5, -1]) cube([poste_d + 1, poste_d + 1, 4]);
        }
}

module viga() {
    // bloque de sujecion con dos agujeros y la lamina que vibra
    difference() {
        cube([bloque_x, bloque_y, bloque_z]);
        for (y = [bloque_y / 4, 3 * bloque_y / 4])
            translate([bloque_x / 2, y, -1]) cylinder(d = agujero_bloque, h = bloque_z + 2);
    }
    translate([bloque_x - 0.01, (bloque_y - ancho_viga) / 2, 0])
        cube([largo_viga, ancho_viga, espesor_viga]);
}

if (parte == "caja_base") caja_base();
else if (parte == "caja_tapa") caja_tapa();
else if (parte == "viga") viga();
else {
    caja_base();
    translate([0, ext_y + 15, 0]) caja_tapa();
    translate([0, -(bloque_y + 15), 0]) viga();
}
