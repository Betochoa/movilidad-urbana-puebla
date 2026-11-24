"""Genera el HTML del mapa 3D con el GeoJSON incrustado."""
import json, os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = os.path.join(BASE, "salida", "2026-11-20-densidad-zm-puebla.geojson")
dst = os.path.join(BASE, "salida", "2026-11-20-mapa-3d-densidad-puebla.html")
gj = json.load(open(src))
keep = ("cvegeo", "municipio", "estado", "pob", "area_km2", "dens", "est")
for f in gj["features"]:
    f["properties"] = {k: f["properties"][k] for k in keep}
data = json.dumps(gj, separators=(",", ":"), ensure_ascii=False)
html = open(os.path.join(BASE, "scripts", "plantilla_mapa.html"), encoding="utf-8").read().replace("__DATA__", data)
open(dst, "w", encoding="utf-8").write(html)
print("Escrito", dst, round(os.path.getsize(dst) / 1e6, 2), "MB")
