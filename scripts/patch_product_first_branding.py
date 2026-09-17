from pathlib import Path

trainer = Path('trainer.html')
text = trainer.read_text(encoding='utf-8')

replacements = [
    (
        '<title>Moon→Mars Mission Trainer | NASA Space Apps 2026</title>',
        '<title>Moon→Mars Mission Trainer | NASA Architecture Training</title>'
    ),
    (
        '<span class="pill">NASA SPACE APPS 2026</span>',
        '<span class="pill">NASA MOON→MARS DATA</span>'
    ),
    (
        '<div class="eyebrow">2026 Challenge · Build a Junior Astronaut Mission Trainer</div>',
        '<div class="eyebrow">NASA ARCHITECTURE · INTERACTIVE MISSION TRAINING</div>'
    ),
    (
        'Run a lunar or Martian outpost training scenario. You have limited engineering credits, so you cannot address every problem at once. Choose which NASA-documented technology gaps to tackle, then see which mission systems still carry other unresolved dependencies.',
        'Take command of a lunar or Martian outpost. Allocate limited engineering credits across real NASA-documented technology gaps, then discover which mission systems your choices protect—and which dependencies still remain.'
    ),
]

for old, new in replacements:
    if old not in text:
        raise SystemExit(f'Branding patch anchor not found: {old[:120]}')
    text = text.replace(old, new, 1)

# Add a product-first trust line beneath the hero actions without changing gameplay.
anchor = '<div class="truthbar">'
insert = '<div style="margin-top:14px;font:700 .52rem var(--mono);letter-spacing:.08em;color:var(--muted)">REAL NASA ARCHITECTURE DATA · AUDITABLE PROVENANCE · NO INVENTED READINESS SCORES</div><div class="truthbar">'
if anchor not in text:
    raise SystemExit('Truthbar anchor not found')
text = text.replace(anchor, insert, 1)

trainer.write_text(text, encoding='utf-8')

validator = Path('scripts/validate_competition_readiness.py')
v = validator.read_text(encoding='utf-8')
old_marker = '        "locked 2026 challenge": "Build a Junior Astronaut Mission Trainer",\n'
new_marker = '        "product-first hero": "NASA ARCHITECTURE · INTERACTIVE MISSION TRAINING",\n        "challenge metadata retained": "Build a Junior Astronaut Mission Trainer",\n'
if old_marker not in v:
    raise SystemExit('Validator challenge marker anchor not found')
v = v.replace(old_marker, new_marker, 1)

anchor2 = '    require_markers(trainer, trainer_markers, "Trainer", errors)\n'
insert2 = '''    require_markers(trainer, trainer_markers, "Trainer", errors)\n\n    # Product identity must lead. The official challenge title belongs in footer/submission metadata,\n    # not as the primary hero label.\n    if "2026 Challenge · Build a Junior Astronaut Mission Trainer" in trainer:\n        fail("Trainer hero still exposes the challenge title as product branding", errors)\n    else:\n        ok("Trainer hero is product-first rather than challenge-title-first")\n'''
if anchor2 not in v:
    raise SystemExit('Validator require_markers anchor not found')
v = v.replace(anchor2, insert2, 1)
validator.write_text(v, encoding='utf-8')

print('Product-first branding patch applied')
