#!/bin/zsh
# Descarga rutas de transporte público (bus/minibus/colectivo) de OSM para el área de Puebla, con reintentos espaciados.
OUT=datos/crudos/transporte/2026-11-20-osm-rutas-bus-puebla.json
Q='[out:json][timeout:180];relation["route"~"^(bus|minibus|share_taxi|trolleybus)$"](18.85,-98.45,19.25,-97.85);out geom;'
for espera in 0 40 80 160 240; do
  sleep $espera
  code=$(curl -s -m 200 -G -A "density-transit-research/1.0 (civic mapping project, one-off query)" --data-urlencode "data=$Q" https://overpass-api.de/api/interpreter -o "$OUT.tmp" -w "%{http_code}")
  echo "intento tras ${espera}s: http $code"
  if [ "$code" = "200" ] && grep -q '"elements"' "$OUT.tmp"; then mv "$OUT.tmp" "$OUT"; echo "OK $(wc -c < $OUT) bytes"; exit 0; fi
done
echo "FALLÓ"; exit 1
