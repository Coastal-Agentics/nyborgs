# Screenshots the splash and checks the live Customize / Tank Arena links in headless Chromium.
import http.server, threading, functools, os, sys
from playwright.sync_api import sync_playwright
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 8765), functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT))
threading.Thread(target=srv.serve_forever, daemon=True).start()
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--headless=new'])
    for name, vp in [('desktop-1280x800', dict(width=1280, height=800)), ('mobile-390', dict(width=390, height=844))]:
        ctx = b.new_context(viewport=vp, device_scale_factor=2 if 'mobile' in name else 1)
        pg = ctx.new_page(); errs = []
        pg.on('console', lambda m: m.type == 'error' and errs.append(m.text))
        pg.on('requestfailed', lambda r: errs.append('failed ' + r.url))
        pg.goto('http://127.0.0.1:8765/index.html'); pg.wait_for_load_state('networkidle')
        pg.screenshot(path=f'{ROOT}/screenshots/{name}.png')
        if 'mobile' in name: pg.screenshot(path=f'{ROOT}/screenshots/{name}-full.png', full_page=True)
        sw = pg.evaluate('document.documentElement.scrollWidth')
        print(name, 'scrollWidth', sw, 'errors', errs)
        ctx.close()
    # live link checks
    pg = b.new_page()
    for url in ['https://coastal-agentics.github.io/arena/arena.html?tab=customize',
                'https://coastal-agentics.github.io/arena/arena.html',
                'https://coastal-agentics.github.io/arena/arena.html?game=racing',
                'https://coastal-agentics.github.io/arena/customizer.html']:
        resp = pg.goto(url); pg.wait_for_timeout(2500)
        st = pg.evaluate("""() => ({
          customizeSelected: document.getElementById('tab-customize')?.getAttribute('aria-selected'),
          customizeHidden: document.getElementById('panel-customize')?.hidden,
          watchSelected: document.getElementById('tab-watch')?.getAttribute('aria-selected'),
          game: document.querySelector('.game.on')?.dataset.game,
          url: location.href, title: document.title })""")
        print(resp.status, st)
    b.close()
srv.shutdown()
