"""Print page-1 lines up to (not including) the abstract. Usage: python3 -I header.py PAGEFILE [maxlines]"""
import sys, re
p = sys.argv[1]; mx = int(sys.argv[2]) if len(sys.argv) > 2 else 25
t = open(p, encoding='utf-8').read()
out = []
for ln in t.splitlines():
    if re.search(r'\bAbstract\b|\bABSTRACT\b', ln):
        out.append('[--- stop at abstract ---]'); break
    out.append(ln)
    if len(out) >= mx: out.append('[--- maxlines ---]'); break
print('\n'.join(out))
# arXiv stamp lines anywhere on page 1
for m in re.finditer(r'arXiv:\S+\s*\[[^\]]*\]\s*\d{1,2}\s*\w{3}\s*\d{4}', t):
    print('STAMP:', m.group(0))
