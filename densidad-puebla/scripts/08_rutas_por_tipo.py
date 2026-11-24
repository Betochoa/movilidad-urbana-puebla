"""Versión del mapa de simulación con las rutas OSM coloreadas por tipo (troncal RUTA / otras RUTA / otras rutas de bus)."""
import json, os, re
from shapely.geometry import LineString, MultiLineString, mapping
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = "2026-11-20-"; S = os.path.join(BASE, "salida")
els = json.load(open(os.path.join(BASE, "datos/crudos/transporte", F + "osm-rutas-bus-puebla.json")))["elements"]
def tipo(t):
    n, ref, net = t.get("name", ""), t.get("ref", ""), t.get("network", "")
    if ref in ("L1", "L2", "brt", "Metrobús") or n.startswith("Metrobús") or "RUTA L3" in n or "L3 BRT" in net:
        return "troncal"
    if "RUTA" in net:
        return "ruta_otra"
    return "otras"
ETQ = {"troncal": "RUTA, línea troncal (L1, L2, L3)", "ruta_otra": "Red RUTA, ruta complementaria (OSM la marca como RUTA)", "otras": "Otra ruta de bus mapeada en OSM (sin operador ni red indicados)"}
feats, cuenta = [], {}
for e in els:
    ls = [LineString([(round(p["lon"], 5), round(p["lat"], 5)) for p in m["geometry"]]) for m in e.get("members", [])
          if m["type"] == "way" and m.get("geometry") and len(m["geometry"]) > 1]
    if not ls: continue
    t = e["tags"]; k = tipo(t); cuenta[k] = cuenta.get(k, 0) + 1
    feats.append({"type": "Feature", "properties": {"nombre": t.get("name") or t.get("ref") or str(e["id"]), "tipo": k, "etq": ETQ[k],
                  "operador": t.get("operator", "")}, "geometry": mapping(MultiLineString(ls))})
print("rutas dibujadas por tipo:", cuenta)
src = open(os.path.join(S, F + "mapa-3d-simulacion-ruta-densidad-puebla.html"), encoding="utf-8").read()
new_routes = json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":"), ensure_ascii=False)
m = re.search(r"const ROUTES = (\{.*?\});\nconst STOPS", src, re.S); assert m
src = src.replace(m.group(0), "const ROUTES = " + new_routes + ";\nconst STOPS")
C = {"troncal": "#0b57d0", "ruta_otra": "#37474f", "otras": "#e8590c"}
def cl(prop): return "['match',['get','tipo'],'troncal',%s,'ruta_otra',%s,%s]" % tuple(prop[k] for k in ("troncal", "ruta_otra", "otras"))
old_cas = "'line-width':['case',['get','brt'],7,5]"; assert old_cas in src
src = src.replace(old_cas, "'line-width':" + cl({"troncal": "7", "ruta_otra": "5.5", "otras": "5"}))
old_lin = "'line-color':['case',['get','brt'],'#0b57d0','#1a73e8'],'line-width':['case',['get','brt'],4,2.5]"; assert old_lin in src
src = src.replace(old_lin, "'line-color':" + cl({k: "'%s'" % v for k, v in C.items()}) + ",'line-width':" + cl({"troncal": "4", "ruta_otra": "3", "otras": "2.5"}))
old_pop = "${p.red||p.operador||'Ruta de bus'}"; assert old_pop in src
src = src.replace(old_pop, "${p.etq}${p.operador?'<br>Operador: '+p.operador:''}")
old_leg = '<div class="key"><i style="width:22px;border-top:3px solid #0b57d0"></i>Ruta mapeada &nbsp;'; assert old_leg in src
leg = ('<div class="key"><i style="width:22px;border-top:4px solid #0b57d0"></i>RUTA troncal (L1–L3)</div>'
       '<div class="key"><i style="width:22px;border-top:3px solid #37474f"></i>RUTA complementaria (44a, 68)</div>'
       '<div class="key"><i style="width:22px;border-top:3px solid #e8590c"></i>Otras rutas de bus en OSM &nbsp;')
src = src.replace(old_leg, leg)
dst = os.path.join(S, F + "mapa-3d-simulacion-ruta-densidad-puebla-v2.html")
open(dst, "w", encoding="utf-8").write(src); print("Escrito", dst)
t = open("/tmp/c.js", "w"); t.write(re.findall(r"<script>(.*?)</script>", src, re.S)[-1]); t.close()
