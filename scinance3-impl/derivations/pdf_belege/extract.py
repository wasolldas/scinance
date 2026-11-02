"""Extract per-page text from PDFs (untrusted) into an output dir.
Usage: python3 -I extract.py OUTDIR PDF [PDF ...]
Writes OUTDIR/<slug>/p###.txt and prints page count + metadata only (no content)."""
import sys, os, re
import pypdf

def slug(name):
    base = os.path.splitext(os.path.basename(name))[0]
    s = re.sub(r'[^A-Za-z0-9._-]+', '_', base)
    return s[:60]

out = sys.argv[1]
for p in sys.argv[2:]:
    sd = os.path.join(out, slug(p))
    os.makedirs(sd, exist_ok=True)
    try:
        r = pypdf.PdfReader(p)
        n = len(r.pages)
        meta = r.metadata or {}
        md = {k: str(v)[:80] for k, v in meta.items() if k in ('/CreationDate', '/ModDate', '/Producer', '/Creator')}
        for i, pg in enumerate(r.pages, 1):
            try:
                t = pg.extract_text() or ''
            except Exception as e:
                t = '[EXTRACT ERROR %s]' % type(e).__name__
            with open(os.path.join(sd, 'p%03d.txt' % i), 'w', encoding='utf-8') as f:
                f.write(t)
        print(slug(p), 'pages=%d' % n, md)
    except Exception as e:
        print(slug(p), 'ERROR', type(e).__name__, str(e)[:100])
