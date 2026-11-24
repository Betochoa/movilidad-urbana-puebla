"""Une AGEB urbanas (Puebla + Tlaxcala) de la ZM Puebla-Tlaxcala con POBTOT del Censo 2020
y calcula densidad. Área en la proyección original (LCC, metros). Salida: GeoJSON WGS84 sin simplificar
+ reportes de calidad de la unión."""
import csv, json, os, sys
import shapefile  # pyshp
from pyproj import CRS, Transformer
from shapely.geometry import shape, mapping
from shapely.ops import transform

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "datos", "crudos")
OUT = os.path.join(BASE, "datos", "procesados")
F = "2026-11-20-"

# --- 1. municipios de la ZM (verificados en SEDATU/CONAPO/INEGI) -------------
zm = {}
with open(os.path.join(OUT, F + "municipios-zm-puebla-tlaxcala.csv"), encoding="utf-8") as f:
    for r in csv.DictReader(f):
        zm[r["CVE_MUN5"]] = (r["NOMBRE"], int(r["POB_2020_OFICIAL"]))
assert len(zm) == 28

# --- 2. CRS: ITRF2008 LCC. Se construye desde el .prj y se compara con EPSG:6372 ------
prj = open(os.path.join(RAW, "marco", "21_puebla", "conjunto_de_datos", "21a.prj")).read()
crs_src = CRS.from_wkt(prj)
crs_epsg = CRS.from_epsg(6372)
d1, d2 = crs_src.to_dict(), crs_epsg.to_dict()
assert d1 == d2, (d1, d2)  # mismos parámetros LCC/GRS80 -> .prj equivale a EPSG:6372 (difiere solo el nombre)
print("CRS del .prj:", crs_src.name, "-> parámetros idénticos a EPSG:6372:", d1)
to_wgs = Transformer.from_crs(crs_epsg, "EPSG:4326", always_xy=True).transform
# EPSG:6372 se usa para reproyectar; el área se calcula en las coordenadas originales (metros)

# --- 3. AGEB urbanas de los municipios ZM -------------------------------------------------
def leer_mun_nombres(ent, carpeta):
    sf = shapefile.Reader(os.path.join(RAW, "marco", carpeta, "conjunto_de_datos", f"{ent}mun"), encoding="latin-1")
    fn = [x[0] for x in sf.fields[1:]]
    return {r[fn.index("CVEGEO")]: r[fn.index("NOMGEO")] for r in sf.records()}

nom_mun = {}
nom_mun.update(leer_mun_nombres("21", "21_puebla"))
nom_mun.update(leer_mun_nombres("29", "29_tlaxcala"))

feats, n_total_marco = {}, 0
for ent, carpeta in (("21", "21_puebla"), ("29", "29_tlaxcala")):
    sf = shapefile.Reader(os.path.join(RAW, "marco", carpeta, "conjunto_de_datos", f"{ent}a"), encoding="latin-1")
    fn = [x[0] for x in sf.fields[1:]]
    for sr in sf.iterShapeRecords():
        n_total_marco += 1
        rec = dict(zip(fn, sr.record))
        cve_mun5 = rec["CVE_ENT"] + rec["CVE_MUN"]
        if cve_mun5 not in zm:
            continue
        geom = shape(sr.shape.__geo_interface__)
        if not geom.is_valid:
            geom = geom.buffer(0)
        area_km2 = geom.area / 1e6  # metros² en LCC -> km²
        g84 = transform(to_wgs, geom)
        feats[rec["CVEGEO"]] = dict(
            cvegeo=rec["CVEGEO"], cve_mun=cve_mun5, municipio=nom_mun.get(cve_mun5, zm[cve_mun5][0]),
            estado="Puebla" if ent == "21" else "Tlaxcala", area_km2=area_km2, geom=g84)
print(f"AGEB en marco (PUE+TLX): {n_total_marco} | en municipios ZM: {len(feats)}")

# --- 4. población por AGEB (filas 'Total AGEB urbana', MZA=000, AGEB!=0000) --------
pob, mun_total_censo, filas_agb_censo = {}, {}, 0
for ent in ("21", "29"):
    p = os.path.join(RAW, "censo", f"ageb_mza_urbana_{ent}_cpv2020", "conjunto_de_datos",
                     f"conjunto_de_datos_ageb_urbana_{ent}_cpv2020.csv")
    with open(p, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            key_mun5 = r["ENTIDAD"].zfill(2) + r["MUN"].zfill(3)
            if r["NOM_LOC"] == "Total del municipio":
                mun_total_censo[key_mun5] = int(r["POBTOT"])
            if r["MZA"] == "000" and r["NOM_LOC"] == "Total AGEB urbana" and r["AGEB"] != "0000":
                cve = r["ENTIDAD"].zfill(2) + r["MUN"].zfill(3) + r["LOC"].zfill(4) + r["AGEB"]
                filas_agb_censo += 1
                pob[cve] = r["POBTOT"].strip()   # texto: puede venir '*' u 'N/D'
print("filas 'Total AGEB urbana' en censo (PUE+TLX):", filas_agb_censo)

# --- 5. unión y densidad; reportes ------------------------------------------------------------------
zm_pob = {c: v for c, v in pob.items() if c[:5] in zm}
sin_censo = sorted(set(feats) - set(pob))                # AGEB del marco sin fila en censo
sin_marco = sorted(c for c in zm_pob if c not in feats)  # filas del censo sin polígono
confid, ceros = [], []
salida = []
for cve, ft in feats.items():
    raw = pob.get(cve)
    if raw is None:
        n = None
    elif raw.isdigit():
        n = int(raw)
    else:
        n = None; confid.append((cve, raw))
    if n == 0:
        ceros.append(cve)
    dens = (n / ft["area_km2"]) if (n is not None and ft["area_km2"] > 0) else None
    salida.append(dict(ft, pobtot=n, dens=dens, estado_pob=("ok" if n else ("cero" if n == 0 else "sin_dato"))))

def lista(x, n=15):
    return x[:n] + (["... (+%d)" % (len(x) - n)] if len(x) > n else [])
print("\n== REPORTE DE UNIÓN ==")
print(f"AGEB marco ZM: {len(feats)} | filas censo ZM: {len(zm_pob)}")
print(f"Marco sin fila de censo ({len(sin_censo)}):", lista(sin_censo))
print(f"Censo sin polígono ({len(sin_marco)}):", lista(sin_marco))
print(f"Población confidencial/no numérica ({len(confid)}):", lista(confid))
print(f"Población = 0 ({len(ceros)}):", lista(ceros))

# --- 6. validación de población ----------------------------------------------------------------------------
suma_agb = sum(s["pobtot"] or 0 for s in salida)
oficial = sum(v[1] for v in zm.values())
suma_mun_censo = sum(mun_total_censo.get(c, 0) for c in zm)
print("\n== VALIDACIÓN ==")
print(f"Suma POBTOT AGEB urbanas ZM : {suma_agb:,}")
print(f"Total municipal (censo, mismos 28 municipios): {suma_mun_censo:,}")
print(f"Total oficial ZM (SEDATU)   : {oficial:,}")
print(f"Cobertura urbana (AGEB / oficial): {100*suma_agb/oficial:.1f}%  <- el resto vive en localidades rurales fuera de AGEB")
print("Por municipio: cobertura AGEB/total municipal")
for c, (nombre, p_of) in sorted(zm.items(), key=lambda kv: -kv[1][1]):
    s = sum(x["pobtot"] or 0 for x in salida if x["cve_mun"] == c)
    t = mun_total_censo.get(c)
    flag = "" if t == p_of else f"  !! censo municipal {t} != oficial {p_of}"
    print(f"  {c} {nombre:<38} AGEB {s:>9,} / muni {t:>9,} = {100*s/t:5.1f}%{flag}")
ds = sorted((s["dens"], s["cvegeo"], s["municipio"], s["pobtot"], s["area_km2"]) for s in salida if s["dens"] is not None)
print("\nDensidad hab/km²: min %.0f | mediana %.0f | p95 %.0f | máx %.0f" % (
    ds[0][0], ds[len(ds)//2][0], ds[int(len(ds)*.95)][0], ds[-1][0]))
print("10 más densas:");  [print("  %.0f  %s %s pob=%s area=%.3f" % x) for x in ds[::-1][:10]]
print("10 menos densas:"); [print("  %.1f  %s %s pob=%s area=%.2f" % x) for x in ds[:10]]
print("AGEB con área < 0.02 km² :", sum(1 for s in salida if s["area_km2"] < 0.02))

# --- 7. GeoJSON completo WGS84 (sin simplificar; intermedio) -------------------------------------
fc = {"type": "FeatureCollection", "features": [{
    "type": "Feature", "id": i,
    "properties": {"cvegeo": s["cvegeo"], "municipio": s["municipio"], "estado": s["estado"],
                   "pob": s["pobtot"], "area_km2": round(s["area_km2"], 4),
                   "dens": round(s["dens"], 1) if s["dens"] is not None else None, "est": s["estado_pob"]},
    "geometry": mapping(s["geom"])} for i, s in enumerate(salida)]}
dest = os.path.join(OUT, F + "ageb-zm-wgs84-completo.geojson")
json.dump(fc, open(dest, "w"))
print("\nEscrito:", dest, f"({os.path.getsize(dest)/1e6:.1f} MB)")
