
import json
import csv
import io
from datetime import datetime

class SimpleExporter:
    def export_csv(self, data):
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['NASA Space Weather Export'])
        writer.writerow(['Generated:', datetime.now().isoformat()])
        writer.writerow(['Events:', len(data.get('events', []))])
        return output.getvalue()
    
    def export_json(self, data):
        return json.dumps(data, indent=2)

print('Export service created')
