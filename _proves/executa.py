# Proves automàtiques de HandPulse: serveix el repositori per web (com GitHub Pages) i passa les proves principals amb Chrome.
# GitHub les executa sol a cada pujada (.github/workflows/proves.yml). Són a _proves perquè GitHub no deixa pujar carpetes amb punt des del navegador. Si alguna falla, el resultat surt en vermell i GitHub avisa per correu.
# Per passar-ne només algunes: HP_NOMES="smoke.py,test_regles.py" python _proves/executa.py
import os, sys, re, time, subprocess, threading, functools, http.server, socketserver
DIR = os.path.dirname(os.path.abspath(__file__)); ARREL = os.path.abspath(os.path.join(DIR, ".."))   # la carpeta _proves és a l'arrel del repositori
PORT = int(os.environ.get("HP_PORT", "8765"))
PROVES = [("smoke.py", []), ("test_regles.py", []), ("test_idiomes.py", [os.path.join(ARREL, "index.html"), "es,en,fr,de,pt"]), ("test_guia.py", []), ("test_incoh.py", []),
          ("test_5claus.py", []), ("test_radar.py", []), ("test_edita.py", []), ("test_perpartit.py", []), ("test_pastis.py", []),
          ("test_pantalla.py", []), ("test_idb.py", []), ("test_focus.py", [])]
nomes = [x.strip() for x in os.environ.get("HP_NOMES", "").split(",") if x.strip()]
if nomes: PROVES = [p for p in PROVES if p[0] in nomes]
# senyals d'error a la sortida de les proves
MAL = [r"✗", r"Traceback", r"(incorrectes|amb problemes)\s*:\s*[1-9]", r"RESUM: [1-9]\d* problemes", r"errors:? \[", r"sense traduir: [1-9]",
       r"paraules catalanes: [1-9]", r"o sense traduir: (?!cap)", r"surt de la pantalla: [1-9]", r"xifres del \d+: \[", r"no es veien: (?!cap)"]
class Silenci(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
socketserver.TCPServer.allow_reuse_address = True
srv = socketserver.ThreadingTCPServer(("127.0.0.1", PORT), functools.partial(Silenci, directory=ARREL))
threading.Thread(target=srv.serve_forever, daemon=True).start()
env = dict(os.environ, HP_URL="http://127.0.0.1:%d/index.html" % PORT, PYTHONIOENCODING="utf-8")
fallen = []; t00 = time.time()
for f, args in PROVES:
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, os.path.join(DIR, f)] + args, cwd=DIR, env=env, capture_output=True, text=True, timeout=1200, encoding="utf-8", errors="replace")
        out, codi = (r.stdout or "") + (r.stderr or ""), r.returncode
    except subprocess.TimeoutExpired:
        out, codi = "massa temps (més de 20 minuts)", 1
    dolent = codi != 0 or any(re.search(p, out) for p in MAL)
    print(("✗ " if dolent else "✓ ") + f + " (%d s)" % (time.time() - t0), flush=True)
    if dolent:
        fallen.append(f); print("  ---- detall ----\n  " + "\n  ".join(out.strip().split("\n")[-40:]), flush=True)
print("RESUM: %d proves en %d min · %s" % (len(PROVES), round((time.time() - t00) / 60), "totes correctes" if not fallen else "fallen: " + ", ".join(fallen)))
srv.shutdown()
sys.exit(1 if fallen else 0)
