"""Versión solo Puebla (13 municipios poblanos de la ZM): filtra el GeoJSON y construye el HTML."""
import json, os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = os.path.join(BASE, "salida", "2026-11-20-densidad-zm-puebla.geojson")
out_gj = os.path.join(BASE, "salida", "2026-11-20-densidad-puebla-solo-puebla.geojson")
out_html = os.path.join(BASE, "salida", "2026-11-20-mapa-3d-densidad-solo-puebla.html")
gj = json.load(open(src))
keep = ("cvegeo", "municipio", "estado", "pob", "area_km2", "dens", "est")
gj["features"] = [f for f in gj["features"] if f["properties"]["estado"] == "Puebla"]
for f in gj["features"]:
    f["properties"] = {k: f["properties"][k] for k in keep}
data = json.dumps(gj, separators=(",", ":"), ensure_ascii=False)
open(out_gj, "w", encoding="utf-8").write(data)
html = open(os.path.join(BASE, "scripts", "plantilla_mapa_puebla.html"), encoding="utf-8").read().replace("__DATA__", data)
open(out_html, "w", encoding="utf-8").write(html)
print(len(gj["features"]), "AGEB;", round(os.path.getsize(out_html) / 1e6, 2), "MB ->", out_html)
