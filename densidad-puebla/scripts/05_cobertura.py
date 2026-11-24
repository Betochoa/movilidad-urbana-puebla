"""Cobertura de transporte mapeado (OSM) sobre AGEB de Puebla: distancia de caminata 400 m.
Servicio mapeado = paradas OSM (bus_stop / platform / stop_position) + trazo de rutas de bus OSM.
Supuesto: población uniforme dentro de cada AGEB (cobertura = fracción del área a <=400 m)."""
import json, os
from collections import Counter
from pyproj import Transformer
from shapely.geometry import shape, mapping, Point, LineString, MultiLineString
from shapely.ops import transform, unary_union

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = "2026-11-20-"
D = 400  # m
to_m = Transformer.from_crs("EPSG:4326", "EPSG:6372", always_xy=True).transform
to_ll = Transformer.from_crs("EPSG:6372", "EPSG:4326", always_xy=True).transform

# --- rutas (relaciones OSM) ---------------------------------------------------------------
rel = json.load(open(os.path.join(BASE, "datos/crudos/transporte", F + "osm-rutas-bus-puebla.json")))["elements"]
rutas, lineas_m = [], []
for e in rel:
    ls = []
    for m in e.get("members", []):
        if m.get("type") == "way" and m.get("geometry") and len(m["geometry"]) > 1:
            ls.append(LineString([(p["lon"], p["lat"]) for p in m["geometry"]]))
    if not ls:
        continue
    t = e["tags"]
    nombre = t.get("name") or t.get("ref") or f"relación {e['id']}"
    red = t.get("network") or ""
    es_brt = "RUTA" in red or "Metrob" in nombre or "BRT" in nombre or t.get("ref", "").startswith("L") and "Metrob" in nombre
    mls = MultiLineString(ls)
    rutas.append({"type": "Feature", "properties": {"nombre": nombre, "ref": t.get("ref", ""), "red": red,
                  "operador": t.get("operator", ""), "brt": bool(es_brt)}, "geometry": mapping(mls)})
    lineas_m.extend(transform(to_m, l) for l in ls)
print("rutas con trazo:", len(rutas), "| BRT/RUTA:", sum(r["properties"]["brt"] for r in rutas))

# --- paradas ----------------------------------------------------------------------------------------
par = json.load(open(os.path.join(BASE, "datos/crudos/transporte", F + "osm-paradas-bus-puebla.json")))["elements"]
pts_ll = [(e["lon"], e["lat"]) for e in par]
pts_m = [Point(to_m(x, y)) for x, y in pts_ll]
print("paradas:", len(pts_m))

buf_par = unary_union([p.buffer(D) for p in pts_m])
buf_rut = unary_union([l.buffer(D) for l in lineas_m])
buf_all = unary_union([buf_par, buf_rut])

# --- AGEB (solo Puebla) ------------------------------------------------------------------------------
gj = json.load(open(os.path.join(BASE, "salida", F + "densidad-puebla-solo-puebla.geojson")))
tot = cub = cub_par = cub_rut = 0.0
filas = []
for f in gj["features"]:
    g = transform(to_m, shape(f["geometry"]))
    if not g.is_valid:
        g = g.buffer(0)
    a = g.area or 1
    s_all = g.intersection(buf_all).area / a
    s_par = g.intersection(buf_par).area / a
    s_rut = g.intersection(buf_rut).area / a
    p = f["properties"]; pob = p["pob"] or 0
    p["cob"] = round(s_all, 3)
    p["pob_cub"] = int(round(pob * s_all))
    tot += pob; cub += pob * s_all; cub_par += pob * s_par; cub_rut += pob * s_rut
    filas.append((p["cvegeo"], p["municipio"], pob, p["dens"] or 0, s_all))
print(f"\nPoblación AGEB (13 mun. Puebla): {tot:,.0f}")
print(f"A <=400 m de parada o ruta OSM: {cub:,.0f} = {100*cub/tot:.1f}%")
print(f"  solo paradas: {100*cub_par/tot:.1f}% | solo trazo de rutas: {100*cub_rut/tot:.1f}%")
print("\nPor rango de densidad (hab/km²):")
bins = [(0, 2000), (2000, 5000), (5000, 10000), (10000, 20000), (20000, 1e9)]
for lo, hi in bins:
    sel = [r for r in filas if lo <= r[3] < hi]
    pb = sum(r[2] for r in sel); pc = sum(r[2] * r[4] for r in sel)
    print(f"  {lo:>6,.0f}-{hi if hi<1e9 else '+':>6}: {len(sel):>4} AGEB | {pb:>9,.0f} hab | cubierta {100*pc/max(pb,1):5.1f}%")
dens_sin = [r for r in filas if r[3] >= 10000 and r[4] < 0.25]
print(f"\nAGEB densas (>=10 000 hab/km²) con <25% de cobertura mapeada: {len(dens_sin)} | población: {sum(r[2] for r in dens_sin):,}")
print("Por municipio (hab en AGEB densas y mal cubiertas):", Counter({m: sum(r[2] for r in dens_sin if r[1] == m) for m in {r[1] for r in dens_sin}}).most_common(6))
print("Top 12 más pobladas entre densas y mal cubiertas:")
for r in sorted(dens_sin, key=lambda r: -r[2])[:12]:
    print(f"  {r[0]} {r[1]:<22} pob {r[2]:>5,} dens {r[3]:>7,.0f} cob {100*r[4]:3.0f}%")

# --- salidas ------------------------------------------------------------------------------------------------
sal = os.path.join(BASE, "salida")
json.dump(gj, open(os.path.join(sal, F + "densidad-cobertura-puebla.geojson"), "w"), separators=(",", ":"), ensure_ascii=False)
json.dump({"type": "FeatureCollection", "features": rutas}, open(os.path.join(sal, F + "rutas-osm-puebla.geojson"), "w"), separators=(",", ":"))
json.dump({"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {}, "geometry": {"type": "Point", "coordinates": [round(x, 5), round(y, 5)]}} for x, y in pts_ll]},
          open(os.path.join(sal, F + "paradas-osm-puebla.geojson"), "w"), separators=(",", ":"))
res = {"pob_total": round(tot), "pob_cubierta": round(cub), "pct": round(100 * cub / tot, 1), "pct_paradas": round(100 * cub_par / tot, 1),
       "pct_rutas": round(100 * cub_rut / tot, 1), "n_rutas": len(rutas), "n_paradas": len(pts_m),
       "n_densas_sin": len(dens_sin), "pob_densas_sin": sum(r[2] for r in dens_sin)}
json.dump(res, open(os.path.join(BASE, "datos/procesados", F + "resumen-cobertura.json"), "w"), indent=1)
print("\nresumen:", res)
