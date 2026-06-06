"""
ANH Bolivia — Script de Actualización Automática del Dashboard
==============================================================
Uso:
  python actualizar_dashboard.py

  O con argumentos:
  python actualizar_dashboard.py --accdb "ruta/al/archivo.accdb" --html "ruta/al/dashboard.html"
  python actualizar_dashboard.py --push          # también hace push a GitHub

Requisitos:
  pip install mdbtools-python pandas
  En Linux/WSL: sudo apt install mdbtools
  En macOS:     brew install mdbtools
  Windows:      usar WSL2 o Docker (ver README.md)
"""

import subprocess, csv, io, json, re, os, sys, argparse
from datetime import datetime
from collections import defaultdict
from pathlib import Path

# ── CONFIG ────────────────────────────────────────────────
DEFAULT_ACCDB  = "PRODUCCION_POR_CAMPO.accdb"   # mismo directorio por defecto
DEFAULT_HTML   = "ANH_Bolivia_Dashboard.html"
GITHUB_BRANCH  = "main"
# ──────────────────────────────────────────────────────────

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def mdb_export(accdb_path, table):
    result = subprocess.run(
        ['mdb-export', accdb_path, table],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Error leyendo tabla {table}: {result.stderr}")
    return list(csv.DictReader(io.StringIO(result.stdout)))

def safe_float(val):
    try: return float(val or 0)
    except: return 0.0

def build_data(accdb_path):
    log(f"Leyendo: {accdb_path}")

    rows   = mdb_export(accdb_path, 'PRODMENSUAL')
    campos_raw = mdb_export(accdb_path, 'HEADERID')
    campos_info = {r['ID']: r for r in campos_raw}

    log(f"  → {len(rows)} registros de producción, {len(campos_info)} campos")

    # ── Inicializar estructuras ──────────────────────────
    annual       = defaultdict(lambda: dict(gas=0, liquidos=0, condensado=0, petroleo=0, glp=0))
    monthly      = defaultdict(lambda: defaultdict(lambda: dict(gas=0, liquidos=0, condensado=0)))
    top_by_year  = defaultdict(lambda: defaultdict(lambda: dict(gas=0, liq=0)))
    regional     = defaultdict(lambda: dict(dept=defaultdict(lambda: dict(gas=0,liquidos=0,condensado=0,petroleo=0,glp=0)),
                                            prov=defaultdict(lambda: dict(gas=0,liquidos=0,condensado=0,petroleo=0,glp=0)),
                                            muni=defaultdict(lambda: dict(gas=0,liquidos=0,condensado=0,petroleo=0,glp=0))))
    op_by_year   = defaultdict(lambda: defaultdict(lambda: dict(gas=0,liquidos=0,condensado=0,petroleo=0)))
    campo_m_raw  = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: [0,0,0,0,0])))

    for r in rows:
        try:
            y   = int(r['AÑO'])
            m   = int(r['MES'])
            campo = r['CAMPO Y/O PLANTA'].strip('"').strip()
            gas = safe_float(r['PRODUCCION GAS (MPC)'])
            liq = safe_float(r['PRODUCCION DELIQUIDOS (BBL)'])
            cond= safe_float(r['CONDENSADO (BBL)'])
            pet = safe_float(r['PETROLEO (BBL)'])
            glp = safe_float(r['GLP RECUPERADO (TM)'])

            # annual
            annual[y]['gas']       += gas
            annual[y]['liquidos']  += liq
            annual[y]['condensado']+= cond
            annual[y]['petroleo']  += pet
            annual[y]['glp']       += glp

            # monthly national
            monthly[y][m]['gas']       += gas
            monthly[y][m]['liquidos']  += liq
            monthly[y][m]['condensado']+= cond

            # top by year campo
            top_by_year[y][campo]['gas'] += gas
            top_by_year[y][campo]['liq'] += liq

            # campo monthly
            cm = campo_m_raw[campo][y][m]
            cm[0] += gas; cm[1] += liq; cm[2] += cond; cm[3] += pet; cm[4] += glp

            # regional
            info = campos_info.get(campo)
            if info:
                dept = info['DEPARTAMENTO']
                prov = info['PROVINCIA']
                muni = info['MUNICIPIO']
                op   = info['OPERADOR']
                for lvl, key in [(regional[y]['dept'], dept),
                                 (regional[y]['prov'], prov),
                                 (regional[y]['muni'], muni)]:
                    lvl[key]['gas']       += gas
                    lvl[key]['liquidos']  += liq
                    lvl[key]['condensado']+= cond
                    lvl[key]['petroleo']  += pet
                    lvl[key]['glp']       += glp
                op_by_year[y][op]['gas']       += gas
                op_by_year[y][op]['liquidos']  += liq
                op_by_year[y][op]['condensado']+= cond
                op_by_year[y][op]['petroleo']  += pet
        except Exception as e:
            continue

    # ── Serializar ──────────────────────────────────────
    def round_dict(d):
        return {k: round(v) for k,v in d.items()}

    annual_out = {str(y): round_dict(v) for y,v in sorted(annual.items())}

    monthly_out = {str(y): {str(m): round_dict(v) for m,v in sorted(md.items())}
                   for y,md in sorted(monthly.items())}

    top_out = {}
    for y, campos_d in sorted(top_by_year.items()):
        gas_sorted = sorted(campos_d.items(), key=lambda x: x[1]['gas'], reverse=True)[:10]
        liq_sorted = sorted(campos_d.items(), key=lambda x: x[1]['liq'],  reverse=True)[:10]
        top_out[str(y)] = {
            'gas': [[c, round(v['gas'])] for c,v in gas_sorted],
            'liq': [[c, round(v['liq'])] for c,v in liq_sorted],
        }

    regional_out = {}
    for y, reg in sorted(regional.items()):
        regional_out[str(y)] = {
            'dept': {k: round_dict(v) for k,v in reg['dept'].items()},
            'prov': {k: round_dict(v) for k,v in reg['prov'].items()},
            'muni': {k: round_dict(v) for k,v in reg['muni'].items()},
        }

    op_out = {str(y): {op: round_dict(v) for op,v in ops.items()}
              for y,ops in sorted(op_by_year.items())}

    campo_m_out = {}
    for campo, years in campo_m_raw.items():
        campo_m_out[campo] = {}
        for y, months_d in years.items():
            campo_m_out[campo][str(y)] = {}
            for m, vals in months_d.items():
                if vals[0] > 0 or vals[1] > 0:
                    campo_m_out[campo][str(y)][str(m)] = [round(v) for v in vals]

    campos_list = [{'id':r['ID'], 'dept':r['DEPARTAMENTO'], 'prov':r['PROVINCIA'],
                    'muni':r['MUNICIPIO'], 'op':r['OPERADOR']} for r in campos_raw]

    hierarchy = {}
    for c in campos_raw:
        d,p,mu = c['DEPARTAMENTO'], c['PROVINCIA'], c['MUNICIPIO']
        hierarchy.setdefault(d, {}).setdefault(p, set()).add(mu)
    hierarchy_out = {d: {p: list(ms) for p,ms in pvs.items()} for d,pvs in hierarchy.items()}

    n_years = len(annual_out)
    n_records = len(rows)
    n_campos  = len(campos_list)

    log(f"  → {n_years} años · {n_records} registros · {n_campos} campos procesados")

    return {
        'annual': annual_out,
        'monthly': monthly_out,
        'top_by_year': top_out,
        'regional': regional_out,
        'op_by_year': op_out,
        'campo_monthly': campo_m_out,
        'campos': campos_list,
        'hierarchy': hierarchy_out,
        'meta': {
            'ultima_actualizacion': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'total_registros': n_records,
            'total_campos': n_campos,
            'anios': list(annual_out.keys()),
        }
    }

def inject_into_html(data, html_path):
    log(f"Actualizando HTML: {html_path}")
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    new_data_js = f"const DB={json.dumps(data, ensure_ascii=False, separators=(',',':'))};"

    # Replace existing DB= assignment
    new_html = re.sub(r'const DB=\{.*?\};', new_data_js, html, flags=re.DOTALL)

    # Update header pill counts
    meta = data['meta']
    new_html = re.sub(r'(<span id="hdr-campos">)\d+(</span>)',
                      rf'\g<1>{meta["total_campos"]}\2', new_html)

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(new_html)

    size_kb = len(new_html.encode('utf-8')) / 1024
    log(f"  → HTML actualizado ({size_kb:.0f} KB)")

def push_to_github(html_path, commit_msg=None):
    msg = commit_msg or f"Actualización datos ANH {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    repo_dir = Path(html_path).parent

    def git(args):
        result = subprocess.run(['git'] + args, cwd=repo_dir, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} falló: {result.stderr.strip()}")
        return result.stdout.strip()

    log("Haciendo push a GitHub...")
    git(['add', os.path.basename(html_path)])
    git(['commit', '-m', msg])
    git(['push', 'origin', GITHUB_BRANCH])
    log(f"  → Push exitoso: '{msg}'")

def main():
    parser = argparse.ArgumentParser(description='Actualizar dashboard ANH Bolivia')
    parser.add_argument('--accdb', default=DEFAULT_ACCDB, help='Ruta al archivo .accdb')
    parser.add_argument('--html',  default=DEFAULT_HTML,  help='Ruta al dashboard HTML')
    parser.add_argument('--push',  action='store_true',   help='Push automático a GitHub')
    args = parser.parse_args()

    if not os.path.exists(args.accdb):
        print(f"ERROR: No se encontró el archivo: {args.accdb}")
        print("Uso: python actualizar_dashboard.py --accdb ruta/al/archivo.accdb")
        sys.exit(1)

    if not os.path.exists(args.html):
        print(f"ERROR: No se encontró el dashboard: {args.html}")
        sys.exit(1)

    log("═══════════════════════════════════════")
    log("  ANH Bolivia — Actualizador Dashboard ")
    log("═══════════════════════════════════════")

    data   = build_data(args.accdb)
    inject_into_html(data, args.html)

    if args.push:
        push_to_github(args.html)

    log("✅ Actualización completada exitosamente")
    log(f"   Última actualización: {data['meta']['ultima_actualizacion']}")
    log(f"   Registros procesados: {data['meta']['total_registros']:,}")

if __name__ == '__main__':
    main()
