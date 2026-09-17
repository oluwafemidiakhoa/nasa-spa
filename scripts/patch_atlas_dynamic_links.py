from pathlib import Path

p = Path('trainer.html')
text = p.read_text(encoding='utf-8')
old = '/index.html?gap=${encodeURIComponent(g.id)}'
count = text.count(old)
if count == 0:
    raise SystemExit('No remaining dynamic Atlas links found')
text = text.replace(old, '/atlas?gap=${encodeURIComponent(g.id)}')
p.write_text(text, encoding='utf-8')
print(f'Updated {count} dynamic Atlas links')
