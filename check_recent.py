#!/usr/bin/env python3
import json
import urllib.request
from datetime import datetime, timedelta

url = 'http://localhost:8000/api/predictions/recent?limit=500'
with urllib.request.urlopen(url) as response:
    data = json.loads(response.read().decode())

predictions = data if isinstance(data, list) else data.get('predictions', [])
cutoff = datetime.utcnow() - timedelta(days=2)
recent = []

for p in predictions:
    captured = p.get('captured_at', '')
    if captured:
        try:
            dt = datetime.fromisoformat(captured.replace('Z', '+00:00').replace('+00:00', ''))
            if dt > cutoff:
                recent.append(p)
        except:
            pass

print(f'Total predictions fetched: {len(predictions)}')
print(f'Predictions added in last 2 days: {len(recent)}')
print()
if recent:
    print('By pundit:')
    pundits = {}
    for p in recent:
        name = p.get('pundit', {}).get('name', 'Unknown')
        pundits[name] = pundits.get(name, 0) + 1
    for name, count in sorted(pundits.items(), key=lambda x: -x[1]):
        print(f'  {name}: {count}')
