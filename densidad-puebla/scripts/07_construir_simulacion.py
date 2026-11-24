"""Mapa con simulación ilustrativa de un día de RUTA sobre los tramos L1, L2 y L3 mapeados en OSM."""
import json, os
from shapely.geometry import LineString
from shapely.ops import linemerge
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = "2026-11-20-"; S = os.path.join(BASE, "salida")
els = {e["id"]: e for e in json.load(open(os.path.join(BASE, "datos/crudos/transporte", F + "osm-rutas-bus-puebla.json")))["elements"]}
LINEAS = {"L1": 8653170, "L2": 8669456, "L3": 10587766}   # relaciones OSM (L1 solo un sentido: los buses van y vienen)
feats, resumen = [], {}
for nombre, rid in LINEAS.items():
    ways = [LineString([(p["lon"], p["lat"]) for p in m["geometry"]]) for m in els[rid]["members"]
            if m["type"] == "way" and m.get("geometry") and len(m["geometry"]) > 1]
    mg = linemerge(ways)
    partes = list(mg.geoms) if mg.geom_type == "MultiLineString" else [mg]
    tot = 0
    for p in partes:
        km = p.length * 111.0   # aprox. (solo para mostrar); la animación recalcula con coseno de latitud
        if km < 0.3: continue
        coords = [[round(x, 5), round(y, 5)] for x, y in p.simplify(0.00003).coords]
        feats.append({"type": "Feature", "properties": {"linea": nombre}, "geometry": {"type": "LineString", "coordinates": coords}})
        tot += km
    resumen[nombre] = round(tot, 1)
print("tramos:", len(feats), "| km aprox por línea:", resumen)
sim = {"type": "FeatureCollection", "features": feats}
json.dump(sim, open(os.path.join(S, F + "rutas-brt-simulacion.geojson"), "w"), separators=(",", ":"))

t = open(os.path.join(BASE, "scripts", "plantilla_mapa_rutas.html"), encoding="utf-8").read()
# 1) quitar el panel de notas abierto por defecto (para dejar espacio al panel de simulación)
t = t.replace('<details id="note" class="panel" open>', '<details id="note" class="panel">')
# 2) CSS + panel HTML
css = """
  #sim{top:190px;right:14px;width:285px}
  #sim h2{font-size:12px;margin:0 0 8px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:600}
  #sim .tag{font-size:11px;color:var(--muted);margin:0 0 8px}
  #sim .big{font-size:26px;font-weight:700;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
  #sim .big small{font-size:12px;font-weight:500;color:var(--muted);margin-left:4px}
  #sim .bar{height:6px;background:var(--line);border-radius:3px;margin:6px 0 10px;overflow:hidden}
  #sim .bar i{display:block;height:100%;width:0;background:#f5a300}
  #sim .grid{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:6px}
  #sim .grid div{border:1px solid var(--line);border-radius:8px;padding:6px 8px}
  #sim .grid b{display:block;font-size:15px;font-variant-numeric:tabular-nums} #sim .grid span{font-size:10.5px;color:var(--muted);line-height:1.2;display:block}
  #sim .ctl{display:flex;gap:6px;margin-top:8px} #sim .ctl button{flex:1;padding:6px;border:1px solid var(--line);background:transparent;color:var(--ink);border-radius:8px;font:inherit;font-size:12px;cursor:pointer}
  #sim .ctl button[aria-pressed=true]{background:var(--ink);color:var(--bg)}
  #sim label{display:block;margin-top:8px;font-size:12px;color:var(--muted)} #sim input[type=range]{width:100%;accent-color:#f5a300}
  #sim .fine{font-size:10.5px;color:var(--muted);margin:8px 0 0;line-height:1.35}
  @media (max-width:760px){ #sim{display:none} }
</style>"""
t = t.replace("</style>", css, 1)
panel = """
<div id="sim" class="panel">
  <h2>Un día de RUTA (simulación)</h2>
  <p class="tag">Ilustrativa: camiones sobre los tramos L1, L2 y L3 mapeados. Posiciones y frecuencias no son reales.</p>
  <div class="big"><span id="s-pax">0</span><small>pasajeros hoy</small></div>
  <div class="bar"><i id="s-bar"></i></div>
  <div class="grid">
    <div><b id="s-n">330</b><span>camiones (supuesto)</span></div>
    <div><b id="s-ppb">—</b><span>pasajeros por camión al día</span></div>
    <div><b id="s-kmb">—</b><span>km por camión al día</span></div>
    <div><b id="s-km">0</b><span>km recorridos hoy</span></div>
  </div>
  <label>Camiones en la flota: <b id="s-nv">330</b>
    <input id="s-fleet" type="range" min="100" max="600" step="10" value="330"></label>
  <div class="ctl"><button id="s-play" aria-pressed="true">Pausa</button><button data-sp="1" aria-pressed="true">1×</button><button data-sp="2" aria-pressed="false">2×</button><button data-sp="4" aria-pressed="false">4×</button></div>
  <p class="fine"><b>Datos:</b> 9.0 M pasajeros en julio de 2026 y 2.6 M km (INEGI, ETUP) ÷ 31 días = ~290 mil pasajeros y ~84 mil km al día, promedio con fines de semana. <b>Flota 330:</b> cifra de una tesis (sin fecha ni verificar); muévela. El conteo avanza parejo, sin horas pico.</p>
</div>
"""
t = t.replace('<div id="legend" class="panel"></div>', panel + '\n<div id="legend" class="panel"></div>', 1)
# 3) JS de la simulación, dentro del handler style.load (antes de 'let top=false;')
js = r"""
  // ===== Simulación ilustrativa de un día de RUTA =====
  const SIM = __SIMDATA__;
  const PAX_DIA = 9.0e6/31, KM_DIA = 2.6e6/31, DIA_SEG = 360;   // un día simulado = 6 min reales a 1×
  const kmLL=(a,b)=>{const la=(a[1]+b[1])/2*Math.PI/180;return Math.hypot((b[0]-a[0])*111.32*Math.cos(la),(b[1]-a[1])*110.57);};
  const tramos = SIM.features.map(f=>{const c=f.geometry.coordinates,cum=[0];for(let i=1;i<c.length;i++)cum.push(cum[i-1]+kmLL(c[i-1],c[i]));return {c,cum,km:cum[cum.length-1],linea:f.properties.linea};});
  const totKm = tramos.reduce((s,t)=>s+t.km,0);
  const posEn=(t,s)=>{let lo=0,hi=t.cum.length-1;while(hi-lo>1){const m=(lo+hi)>>1;(t.cum[m]<=s)?lo=m:hi=m;}
    const seg=(t.cum[hi]-t.cum[lo])||1e-9,u=(s-t.cum[lo])/seg;return [t.c[lo][0]+(t.c[hi][0]-t.c[lo][0])*u,t.c[lo][1]+(t.c[hi][1]-t.c[lo][1])*u];};
  let buses=[], N=330;
  const armar=n=>{N=n;buses=[];tramos.forEach((t,ti)=>{const k=Math.max(1,Math.round(n*t.km/totKm));for(let i=0;i<k;i++)buses.push({ti,s:Math.random()*t.km,d:Math.random()<.5?1:-1});});
    document.getElementById('s-n').textContent=n;document.getElementById('s-nv').textContent=n;
    document.getElementById('s-ppb').textContent=Math.round(PAX_DIA/n).toLocaleString('es-MX');
    document.getElementById('s-kmb').textContent=Math.round(KM_DIA/n).toLocaleString('es-MX');};
  map.addSource('buses',{type:'geojson',data:{type:'FeatureCollection',features:[]}});
  map.addLayer({id:'buses-pt',type:'circle',source:'buses',paint:{'circle-radius':['interpolate',['linear'],['zoom'],10,3,14,6],'circle-color':'#f5a300','circle-stroke-color':'#1d1b18','circle-stroke-width':1.2}});
  let playing=true, speed=1, prog=0, last=performance.now(), ultSet=0;
  const el=id=>document.getElementById(id), nf=n=>Math.round(n).toLocaleString('es-MX');
  function frame(now){
    const dt=Math.min(0.1,(now-last)/1000); last=now;
    if(playing){
      prog+=dt*speed/DIA_SEG; if(prog>=1)prog-=1;
      const v=(KM_DIA/N)*speed/DIA_SEG;     // km por segundo real de cada camión
      for(const b of buses){const t=tramos[b.ti];b.s+=b.d*v*dt;if(b.s>t.km){b.s=2*t.km-b.s;b.d=-1;}else if(b.s<0){b.s=-b.s;b.d=1;}}
      if(now-ultSet>33){ ultSet=now; map.getSource('buses').setData({type:'FeatureCollection',features:buses.map(b=>({type:'Feature',properties:{},geometry:{type:'Point',coordinates:posEn(tramos[b.ti],b.s)}}))}); }
      el('s-pax').textContent=nf(PAX_DIA*prog); el('s-km').textContent=nf(KM_DIA*prog); el('s-bar').style.width=(100*prog)+'%';
    }
    requestAnimationFrame(frame);
  }
  armar(330); requestAnimationFrame(frame);
  el('s-fleet').addEventListener('input',e=>armar(+e.target.value));
  el('s-play').onclick=e=>{playing=!playing;e.target.textContent=playing?'Pausa':'Seguir';e.target.setAttribute('aria-pressed',playing);last=performance.now();};
  document.querySelectorAll('#sim [data-sp]').forEach(b=>b.onclick=()=>{speed=+b.dataset.sp;document.querySelectorAll('#sim [data-sp]').forEach(x=>x.setAttribute('aria-pressed',x===b));});

"""
anchor = "  let top=false;"
assert t.count(anchor) == 1
t = t.replace(anchor, js + anchor)
t = t.replace("<title>Transporte y densidad · Puebla</title>", "<title>Simulación RUTA y densidad · Puebla</title>")
# 4) rellenar datos igual que el builder principal
res = json.load(open(os.path.join(BASE, "datos/procesados", F + "resumen-cobertura.json")))
gj = json.loads(open(os.path.join(S, F + "densidad-cobertura-puebla.geojson"), encoding="utf-8").read())
keep = ("cvegeo", "municipio", "estado", "pob", "area_km2", "dens", "est", "cob", "pob_cub")
for f in gj["features"]: f["properties"] = {k: f["properties"][k] for k in keep}
import sys
prueba = "--prueba" in sys.argv
t = t.replace("__STYLE__", "about:blank-prueba" if prueba else "https://tiles.openfreemap.org/styles/positron")
fmt = lambda x: f"{x:g}".replace(".", ",") if isinstance(x, float) else str(x)
for k, v in {"__PCT__": fmt(res["pct"]), "__PCTP__": fmt(res["pct_paradas"]), "__PCTR__": fmt(res["pct_rutas"]),
             "__NRUTAS__": str(res["n_rutas"]), "__NPAR__": f"{res['n_paradas']:,}".replace(",", " ")}.items():
    t = t.replace(k, v)
rd = lambda n: open(os.path.join(S, F + n), encoding="utf-8").read()
t = (t.replace("__DATA__", json.dumps(gj, separators=(",", ":"), ensure_ascii=False)).replace("__ROUTES__", rd("rutas-osm-puebla.geojson"))
      .replace("__STOPS__", rd("paradas-osm-puebla.geojson")).replace("__SIMDATA__", json.dumps(sim, separators=(",", ":"))))
dst = "/tmp/sim_prueba.html" if prueba else os.path.join(S, F + "mapa-3d-simulacion-ruta-densidad-puebla.html")
open(dst, "w", encoding="utf-8").write(t)
print("Escrito", dst, round(os.path.getsize(dst) / 1e6, 2), "MB")
