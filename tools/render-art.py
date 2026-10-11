# Writes ../nyborgs.png: three Nyborgs for the splash header, drawn by the Nyborg app's own
# renderer (arena repo, web/nyborg-draw.js), so the splash shows exactly the hair the app draws.
# Usage: python3 tools/render-art.py [path/to/arena/web]   (default: ../arena/web)
# Needs Playwright and Chrome. Output: 600x244 transparent PNG, shown at 300x122 (2x).
import functools, http.server, os, sys, threading
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "nyborgs.png")
WEB = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..", "arena", "web"))
assert os.path.exists(os.path.join(WEB, "nyborg-draw.js")), f"no nyborg-draw.js in {WEB}"
# The trio: hair A Shaggy mop (red), C Muppet fringe (blue), B Pom cloud (yellow). Fixed ids
# seed the fur jitter, so the art is the same on every run.
TRIO = [
    dict(id="splash-red", hair="#D9534F", style="mop", x=58, facing=1),
    dict(id="splash-blue", hair="#3F6FD8", style="fringe", x=150, facing=1),
    dict(id="splash-yellow", hair="#F2C14E", style="pom", x=244, facing=-1),
]
PAGE = """<!doctype html><meta charset=utf-8><body style="margin:0;background:transparent">
<canvas id=c width=600 height=244 style="width:300px;height:122px"></canvas>
<script type=module>
import { drawNyborg } from "./nyborg-draw.js";
const ctx = document.getElementById("c").getContext("2d");
ctx.scale(2, 2);
for (const n of %s) { ctx.save(); ctx.translate(n.x, 84); drawNyborg(ctx, { ...n, scale: 1.25, accessories: [] }); ctx.restore(); }
window.done = true;
</script>"""
import json
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(http.server.SimpleHTTPRequestHandler, directory=WEB))
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", headless=True)
    pg = b.new_page(viewport=dict(width=300, height=122))
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: m.type == "error" and errs.append(m.text))
    pg.route(base + "/__art.html", lambda r: r.fulfill(content_type="text/html", body=PAGE % json.dumps(TRIO)))
    pg.goto(base + "/__art.html"); pg.wait_for_function("window.done")
    url = pg.evaluate("document.getElementById('c').toDataURL('image/png')")
    assert not errs, errs
    import base64
    open(OUT, "wb").write(base64.b64decode(url.split(",", 1)[1]))
    b.close()
srv.shutdown()
print("wrote", os.path.normpath(OUT))
