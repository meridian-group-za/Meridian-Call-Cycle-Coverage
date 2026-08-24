#!/usr/bin/env python3
"""Local live data server for the Call Cycle Coverage dashboard.

Carin flagged that the dashboard was reading a static, manually-refreshed
copy of the Call Cycle Master (mock-data/call-cycle-master.json) instead of
the real, currently-synced file. This server reads run-latest.json fresh
from its actual OneDrive location on every request (no caching), transforms
combinedMaster into the same rep_rows/merch_rows shape the dashboard
expects, and serves it -- so the dashboard reflects whatever is on disk
right now, not a snapshot from whenever someone last ran an export script.

Reading the 69MB run-latest.json takes under a second (measured
2026-08-18), so reading it fresh per-request is fine for an internal tool
like this.

Run: python live_data_server.py [port]   (defaults to 8794)
"""
import json
import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

RUN_LATEST_PATH = Path.home() / 'OneDrive - Meridian Group' / 'Stock Fix Inventory - StockFix' / 'Call Cycles' / 'run-latest.json'
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8794


def norm_division(v):
    v = (v or '').strip().upper()
    return v.title() if v else 'Unknown'


DAY_KEYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


def slim(r):
    is_merch = 'MERCHANDISER' in (r.get('RESOURCE TYPE') or '')
    return {
        'storeCode': r.get('GEO REP STORE CODE') or r.get('STORE CODE'),
        'storeName': r.get('STORE NAME'),
        'banner': r.get('BANNER'),
        'division': norm_division(r.get('DIVISION')),
        'region': r.get('REGION'),
        'resourceId': r.get('RESOURCE EMP ID'),
        'resourceName': r.get('RESOURCE NAME'),
        'resourceType': r.get('RESOURCE TYPE'),
        'frequency': r.get('CALLING FREQUENCY'),
        'managerId': r.get('MANAGER EMP CODE'),
        'managerName': r.get('LINE MANAGER'),
        # Added for the "coverage by day" and "manager > rep > merchandiser
        # hierarchy" pages -- days is which weekdays this store/resource
        # pairing is actually scheduled for a visit (raw sheet uses "X" for
        # scheduled, blank otherwise). (Carin, 2026-08-24)
        'days': [k for k in DAY_KEYS if (r.get(k) or '').strip().upper() == 'X'],
    }, is_merch


def build_payload():
    with open(RUN_LATEST_PATH, encoding='utf-8') as f:
        d = json.load(f)
    rep_rows, merch_rows = [], []
    for raw in d['combinedMaster']:
        # "Office" banner is internal Meridian admin/conference-room
        # addresses (e.g. "MERIDIAN OFFICE - GAUTENG"), not real stores --
        # Carin confirmed 2026-08-20 these should be dropped entirely
        # rather than land in "Other / Unclassified".
        if (raw.get('BANNER') or '').strip().upper() == 'OFFICE':
            continue
        row, is_merch = slim(raw)
        (merch_rows if is_merch else rep_rows).append(row)
    return {'timestamp': d['timestamp'], 'processedBy': d.get('processedBy'), 'rep_rows': rep_rows, 'merch_rows': merch_rows}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.end_headers()

    def do_GET(self):
        try:
            payload = build_payload()
        except Exception as exc:
            body = json.dumps({'error': str(exc)}).encode('utf-8')
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        body = json.dumps(payload, default=str).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    server = ThreadingHTTPServer(('127.0.0.1', PORT), Handler)
    print(f'Live Call Cycle Master server on http://127.0.0.1:{PORT}/ -- reads run-latest.json fresh on every request')
    server.serve_forever()


if __name__ == '__main__':
    main()
