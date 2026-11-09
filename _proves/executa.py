# Proves automàtiques de HandPulse: serveix el repositori per web (com GitHub Pages) i passa les proves principals amb Chrome.
# GitHub les executa sol a cada pujada (.github/workflows/proves.yml). Són a _proves perquè GitHub no deixa pujar carpetes amb punt des del navegador. Si alguna falla, el resultat surt en vermell i GitHub avisa per correu.
# Per passar-ne només algunes: HP_NOMES="smoke.py,test_regles.py" python _proves/executa.py
import os, sys, re, time, subprocess, threading, functools, http.server, socketserver
DIR = os.path.dirname(os.path.abspath(__file__)); ARREL = os.path.abspath(os.path.join(DIR, ".."))   # la carpeta _proves és a l'arrel del repositori
PORT = int(os.environ.get("HP_PORT", "8765"))
PROVES = [("smoke.py", []), ("test_regles.py", []), ("test_idiomes.py", [os.path.join(ARREL, "index.html"), "es,en,fr,de,pt"]), ("test_guia.py", []), ("test_incoh.py", []),
          ("test_5claus.py", []), ("test_radar.py", []), ("test_edita.py", []), ("test_perpartit.py", []), ("test_pastis.py", []),
          ("test_pantalla.py", []), ("test_idb.py", []), ("test_focus.py", []), ("test_pdf_logos.py", []), ("test_3d.py", []), ("test_estrelles.py", []), ("test_wp.py", []), ("test_tfix.py", []), ("test_neu.py", []), ("test_sw.py", []), ("test_fitxa_pdf.py", []), ("test_dorsal.py", [])]
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
fallen = []; files = []; detalls = []; t00 = time.time()
for f, args in PROVES:
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, os.path.join(DIR, f)] + args, cwd=DIR, env=env, capture_output=True, text=True, timeout=1200, encoding="utf-8", errors="replace")
        out, codi = (r.stdout or "") + (r.stderr or ""), r.returncode
    except subprocess.TimeoutExpired:
        out, codi = "massa temps (més de 20 minuts)", 1
    dolent = codi != 0 or any(re.search(p, out) for p in MAL)
    print(("✗ " if dolent else "✓ ") + f + " (%d s)" % (time.time() - t0), flush=True)
    files.append((f, dolent, round(time.time() - t0)))
    if dolent:
        fallen.append(f); print("  ---- detall ----\n  " + "\n  ".join(out.strip().split("\n")[-40:]), flush=True)
        # a GitHub, una anotació amb la prova i el motiu: surt a la pàgina de l'execució sense iniciar la sessió
        if os.environ.get("GITHUB_ACTIONS"):
            linies = [l.strip() for l in out.strip().split("\n") if l.strip()]
            clau = [l for l in linies if re.search("|".join(MAL), l)] or linies[-6:]
            msg = "\n".join((clau[:6] + ["…"] + linies[-4:]) if len(clau) > 6 else clau + [l for l in linies[-4:] if l not in clau])[:1500]
            print("::error title=Falla " + f + "::" + msg.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A"), flush=True)
            detalls.append((f, "\n".join(linies[-30:])))
print("RESUM: %d proves en %d min · %s" % (len(PROVES), round((time.time() - t00) / 60), "totes correctes" if not fallen else "fallen: " + ", ".join(fallen)))
# a GitHub, un resum a la pàgina de l'execució: una fila per prova, i el detall de les que fallen
if os.environ.get("GITHUB_STEP_SUMMARY"):
    try:
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fs:
            fs.write("## Proves de HandPulse\n\n| Prova | Resultat | Temps |\n|---|---|---|\n")
            fs.write("".join("| %s | %s | %d s |\n" % (f, "✗ falla" if d else "✓ correcta", t) for f, d, t in files))
            for f, txt in detalls: fs.write("\n### %s\n\n```\n%s\n```\n" % (f, txt))
    except Exception as e: print("no s'ha pogut escriure el resum:", e)
srv.shutdown()
sys.exit(1 if fallen else 0)
