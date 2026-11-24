# Movilidad Puebla: densidad y transporte público

> ¿Dónde vive la gente y qué tan bien la alcanza el transporte público?

Proyecto abierto, hecho en el **Claude Build Day · Puebla, México**, que cruza la densidad de población de la zona metropolitana Puebla-Tlaxcala con las rutas y paradas de transporte público que existen en datos abiertos. El resultado es un mapa 3D interactivo.

## Qué hace

- **Densidad en 3D.** Cada bloque es una AGEB (Área Geoestadística Básica) del Censo 2020: más alto y más rojo significa más gente por km².
- **Rutas y paradas encima.** Muestra lo que existe en OpenStreetMap y calcula cuánta población queda a 400 m (unos 5 minutos a pie) de una parada o ruta.
- **Un día de RUTA (simulación).** Simulación ilustrativa con flota ajustable sobre los tramos L1, L2 y L3 mapeados.

## Lo que encontramos

- **35.6 %** de la población de los 13 municipios poblanos vive a 400 m o menos de una parada o ruta mapeada.
- **325,227 personas** viven en 92 zonas muy densas (10,000 hab/km² o más) con menos del 25 % de cobertura mapeada.

> **Ojo:** esto mide lo *mapeado en OpenStreetMap*, no el servicio real. Una zona sin cobertura puede estar bien servida, pero sin dato.

### El hallazgo: un hueco en los datos abiertos

No encontramos un GTFS oficial ni un portal con las rutas de transporte de Puebla. Sin ese dato, nadie puede medir quién se queda sin transporte. El siguiente paso es una solicitud de transparencia a la Secretaría de Movilidad y Transporte (trazados, flota, frecuencias y pasajeros); con esos datos el mismo cálculo se puede repetir con el sistema real. El método sirve para cualquier ciudad.

## Fuentes de datos

| Qué | Fuente |
|---|---|
| Población | INEGI, Censo de Población y Vivienda 2020, por AGEB |
| Zona metropolitana | SEDATU, CONAPO, INEGI (2020): 28 municipios, 13 de Puebla y 15 de Tlaxcala |
| Geometría | INEGI, Marco Geoestadístico 2020 |
| Rutas y paradas | OpenStreetMap (descarga del 20/11/2026), solo lo mapeado |
| Pasajeros de RUTA | INEGI, Estadística de Transporte Urbano de Pasajeros (ETUP), julio de 2026 |

Validación: la suma de los 28 municipios coincide con el total oficial (2,776,893 habitantes).

## Ver el mapa

**🗺️ Mapa en línea: https://betochoa.github.io/movilidad-urbana-puebla/**

Los mapas ya generados están en [`densidad-puebla/salida/`](densidad-puebla/salida/). Son archivos HTML autocontenidos: ábrelos en el navegador (necesitan internet para cargar el mapa base). El más completo es:

- `2026-11-20-mapa-3d-simulacion-ruta-densidad-puebla-v2.html`

## Estructura

```
densidad-puebla/
├── datos/
│   ├── crudos/        # censo, marco geoestadístico, rutas/paradas OSM, boletín ETUP
│   └── procesados/    # AGEB de la ZM unidas con población, resumen de cobertura
├── scripts/           # pipeline numerado 01 → 08 y plantillas HTML
├── herramientas/      # dependencias de Node (mapshaper)
└── salida/            # GeoJSON y mapas HTML finales
```

## Reproducir el análisis

Requisitos: Python 3.9+ y Node.js.

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cd densidad-puebla/herramientas && npm install && cd ..
```

Los scripts toman las rutas de forma relativa a `densidad-puebla/`. En orden:

| Script | Qué hace |
|---|---|
| `01_union_densidad.py` | Une las AGEB (Puebla + Tlaxcala) con la población del Censo 2020 y calcula densidad |
| `02_construir_mapa.py` | Genera el mapa 3D de densidad de la zona metropolitana |
| `03_construir_mapa_puebla.py` | Versión solo con los municipios de Puebla |
| `04_bajar_rutas_osm.sh` | Descarga las rutas de bus de OpenStreetMap (Overpass API) |
| `05_cobertura.py` | Calcula la cobertura a 400 m sobre cada AGEB |
| `06_construir_mapa_rutas.py` | Mapa final: densidad 3D + rutas, paradas y cobertura |
| `07_construir_simulacion.py` | Mapa con la simulación ilustrativa de un día de RUTA |
| `08_rutas_por_tipo.py` | Versión con las rutas coloreadas por tipo |

Los datos procesados y crudos ya están en el repo, así que puedes empezar directamente desde el script `05`.

## Limitaciones

- La densidad es residencial (Censo 2020), no refleja dónde trabaja o estudia la gente.
- El transporte es solo lo que está mapeado en OpenStreetMap.
- La cobertura asume población uniforme dentro de cada AGEB.
- La simulación de RUTA es ilustrativa: posiciones y frecuencias no son reales. La cifra de flota de 330 camiones viene de una tesis sin fecha verificable.

## Cómo contribuir

¡Toda ayuda es bienvenida! Algunas ideas:

- Mapear rutas y paradas de Puebla en [OpenStreetMap](https://www.openstreetmap.org) para mejorar la cobertura.
- Ayudar a redactar o dar seguimiento a la solicitud de transparencia por los datos reales del transporte.
- Revisar el método, encontrar errores o proponer mejoras en los scripts.
- Adaptar el análisis a otra ciudad.

Abre un *issue* para discutir una idea o un *pull request* con tu cambio.

## Créditos y atribución

Código bajo licencia [MIT](LICENSE). Datos © INEGI. Datos de rutas y paradas © colaboradores de [OpenStreetMap](https://www.openstreetmap.org/copyright), disponibles bajo la licencia ODbL. Mapa base de OpenFreeMap / OpenMapTiles, renderizado con MapLibre GL.
