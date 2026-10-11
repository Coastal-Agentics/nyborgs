# Screenshots the splash and checks every link on it in headless Chromium.
# The splash links into the Nyborg app at /arena/play/, so the check serves this repo at
# /nyborgs/ and an arena web build at /arena/ from one local origin, the way Pages serves them:
#   python3 tools/shoot.py [path/to/arena/web]     (default: ../arena/web)
#   python3 tools/shoot.py --live                  (check the links on the live site instead)
# Also checks "Welcome back": a Nyborg saved by the app is greeted by name.
import functools, http.server, json, os, sys, tempfile, threading
from playwright.sync_api import sync_playwright
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
SHOTS = os.environ.get('SHOTS', os.path.join(ROOT, 'screenshots'))
os.makedirs(SHOTS, exist_ok=True)
LIVE = '--live' in sys.argv
args = [a for a in sys.argv[1:] if not a.startswith('--')]
ARENA = os.path.abspath(args[0] if args else os.path.join(ROOT, '..', 'arena', 'web'))
site = tempfile.mkdtemp(prefix='nyborgs-site-')
os.symlink(ROOT, os.path.join(site, 'nyborgs'))
if not LIVE:
    assert os.path.exists(os.path.join(ARENA, 'play', 'index.html')), f'no arena build with the app (play/index.html) in {ARENA}'
    os.symlink(ARENA, os.path.join(site, 'arena'))
    # Pages generates the field notes index at deploy time; the arena repo's own script makes it.
    if not os.path.exists(os.path.join(ARENA, 'fieldnotes', 'index.json')):
        print('note: no', os.path.join(ARENA, 'fieldnotes', 'index.json'), '- run `node scripts/fieldnotes_index.mjs` in the arena repo first')
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=site))
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f'http://127.0.0.1:{srv.server_address[1]}'
LINKS = 'https://coastal-agentics.github.io' if LIVE else BASE
bad = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--headless=new'])
    def page(vp, mobile=False):
        ctx = b.new_context(viewport=vp, device_scale_factor=2 if mobile else 1)
        pg = ctx.new_page(); errs = []
        pg.on('console', lambda m: m.type == 'error' and errs.append(m.text))
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('requestfailed', lambda r: errs.append('failed ' + r.url))
        return ctx, pg, errs
    for name, vp in [('desktop-1280x800', dict(width=1280, height=800)), ('mobile-390', dict(width=390, height=844))]:
        ctx, pg, errs = page(vp, 'mobile' in name)
        pg.goto(BASE + '/nyborgs/'); pg.wait_for_load_state('networkidle')
        pg.screenshot(path=f'{SHOTS}/{name}.png')
        if 'mobile' in name: pg.screenshot(path=f'{SHOTS}/{name}-full.png', full_page=True)
        sw = pg.evaluate('document.documentElement.scrollWidth')
        print(name, 'scrollWidth', sw, 'errors', errs)
        if errs or sw > vp['width']: bad.append(name)
        ctx.close()
    # Every link on the splash: same-site ones must load (the app ones must render a screen).
    ctx, pg, errs = page(dict(width=1280, height=800))
    pg.goto(BASE + '/nyborgs/'); pg.wait_for_load_state('networkidle')
    hrefs = sorted(set(pg.eval_on_selector_all('a[href]', 'es => es.map(e => e.getAttribute("href"))')))
    for h in hrefs:
        if h.startswith('http') or h == '/':
            print('skip (other site)', h); continue
        errs.clear()
        pg.goto('about:blank')  # so a hash-only link is a real load with a response
        resp = pg.goto(LINKS + h); pg.wait_for_load_state('networkidle')
        st = resp.status if resp else None
        screen = None
        if '/arena/play/' in h:
            pg.wait_for_function('() => document.querySelector("#screen h1")', timeout=10000)
            screen = pg.text_content('#screen h1')
        ok = st == 200 and not errs
        print('ok ' if ok else 'BAD', st, h, '->', screen or pg.title(), errs or '')
        if not ok: bad.append(h)
    ctx.close()
    # Welcome back: seed a Nyborg the way the app stores one, then reload the splash.
    if not LIVE:
        ctx, pg, errs = page(dict(width=1280, height=800))
        pg.goto(BASE + '/nyborgs/'); pg.wait_for_load_state('networkidle')
        first = pg.text_content('#cta')
        pg.evaluate("""() => {
          localStorage.setItem('arena.nyborg.index', JSON.stringify({ format: 2, order: ['ny-pip'], selected: 'ny-pip' }));
          localStorage.setItem('arena.nyborg.p.ny-pip', JSON.stringify({ format: 2, id: 'ny-pip', name: '<b>Pip</b>' }));
        }""")
        pg.reload(); pg.wait_for_load_state('networkidle')
        cta, hello = pg.text_content('#cta'), pg.text_content('#welcome')
        pg.screenshot(path=f'{SHOTS}/welcome-back.png')
        print('welcome:', repr(first), '->', repr(cta), '|', repr(hello), '| markup escaped:', pg.locator('#welcome b').count() == 0)
        if first != 'Make your Nyborg' or cta != 'Play with <b>Pip</b> ▶' or pg.locator('#welcome b').count(): bad.append('welcome')
        pg.evaluate("() => localStorage.setItem('arena.nyborg.index', '{not json')"); pg.reload(); pg.wait_for_load_state('networkidle')
        print('broken storage keeps default:', pg.text_content('#cta'), errs)
        if pg.text_content('#cta') != 'Make your Nyborg' or errs: bad.append('welcome-broken')
        ctx.close()
    b.close()
srv.shutdown()
print('FAILED: ' + ', '.join(bad) if bad else 'all checks passed')
sys.exit(1 if bad else 0)
