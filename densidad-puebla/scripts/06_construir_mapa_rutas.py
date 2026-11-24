"""Construye el mapa final: densidad 3D + rutas/paradas OSM + cobertura. Uso: python 06_construir_mapa_rutas.py [--prueba]"""
import json, os, sys
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = "2026-11-20-"
S = os.path.join(BASE, "salida")
rd = lambda n: open(os.path.join(S, F + n), encoding="utf-8").read()
res = json.load(open(os.path.join(BASE, "datos/procesados", F + "resumen-cobertura.json")))
gj = json.loads(rd("densidad-cobertura-puebla.geojson"))
keep = ("cvegeo", "municipio", "estado", "pob", "area_km2", "dens", "est", "cob", "pob_cub")
for f in gj["features"]:
    f["properties"] = {k: f["properties"][k] for k in keep}
prueba = "--prueba" in sys.argv
style = "about:blank-prueba" if prueba else "https://tiles.openfreemap.org/styles/positron"
html = open(os.path.join(BASE, "scripts", "plantilla_mapa_rutas.html"), encoding="utf-8").read().replace("__STYLE__", style)
fmt = lambda x: f"{x:g}".replace(".", ",") if isinstance(x, float) else str(x)
for k, v in {"__PCT__": fmt(res["pct"]), "__PCTP__": fmt(res["pct_paradas"]), "__PCTR__": fmt(res["pct_rutas"]),
             "__NRUTAS__": str(res["n_rutas"]), "__NPAR__": f"{res['n_paradas']:,}".replace(",", " ")}.items():
    html = html.replace(k, v)
html = (html.replace("__DATA__", json.dumps(gj, separators=(",", ":"), ensure_ascii=False))
            .replace("__ROUTES__", rd("rutas-osm-puebla.geojson")).replace("__STOPS__", rd("paradas-osm-puebla.geojson")))
dst = "/tmp/mapa_rutas_prueba.html" if prueba else os.path.join(S, F + "mapa-3d-transporte-densidad-puebla.html")
open(dst, "w", encoding="utf-8").write(html)
print("Escrito", dst, round(os.path.getsize(dst) / 1e6, 2), "MB")
