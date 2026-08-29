#!/usr/bin/env python3
"""Rebuilds hierarchy.json's base rep-level entries directly from the
National Reporting Hierarchy.xlsx Organogram sheet -- the actual source of
truth for Head of Syndicated / General Manager / Regional Manager / Manager.

Until now, those 139 base entries were hand-built once (2026-08-20, "Wire
National Reporting Hierarchy") with no script anywhere to redo the match --
so a name added to the Organogram since then (e.g. Sanele Pato, flagged by
Carin 2026-08-29) never made it into hierarchy.json, and there was no way to
regenerate it short of repeating that one-off manual process. This script
replaces that gap: re-run it any time the Organogram sheet is updated.

This only rebuilds the REP-level base entries (one hierarchy.json key per
"Reps" row in the Organogram). It deliberately does NOT touch merchandiser
entries -- run scripts/build_hierarchy.py straight after this to reapply
the merchandiser -> rep walk on top of the freshly rebuilt base, exactly as
you would after any hierarchy.json change:

    python scripts/build_hierarchy_from_organogram.py
    python scripts/build_hierarchy.py

Unmatched names (in the Call Cycle Master's rep list but with no row here)
are written to scripts/hierarchy_unmatched_reps.csv for review, the same
diagnostic the original 2026-08-20 build produced.
"""
import csv
import json
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
HIERARCHY_PATH = ROOT / 'hierarchy.json'
UNMATCHED_CSV_PATH = Path(__file__).resolve().parent / 'hierarchy_unmatched_reps.csv'
ORGANOGRAM_PATH = (Path.home() / 'OneDrive - Meridian Group' / 'Meridian Nexus - Documents'
                   / 'Call Cycle Coverage' / 'National Reporting Hierarchy.xlsx')
RUN_LATEST_PATH = Path.home() / 'OneDrive - Meridian Group' / 'Stock Fix Inventory - StockFix' / 'Call Cycles' / 'run-latest.json'


def norm_key(s):
    return (s or '').upper().strip().replace('  ', ' ')


def load_organogram():
    wb = openpyxl.load_workbook(ORGANOGRAM_PATH, data_only=True)
    ws = wb['Organogram']
    rows = list(ws.iter_rows(values_only=True))
    header = [norm_key(h).lower() for h in rows[0]]
    expected = ['division', 'region', 'head of syndicated', 'general manager', 'regional manager', 'manager', 'reps']
    if header != expected:
        raise RuntimeError(f'Organogram header changed -- expected {expected}, got {header}')
    return [r for r in rows[1:] if any(r)]


def main():
    rows = load_organogram()

    hierarchy = {}
    for division, region, head_of_syndicated, general_manager, regional_manager, manager, rep in rows:
        rep_key = norm_key(rep)
        if not rep_key:
            continue
        hierarchy[rep_key] = {
            'headOfSyndicated': head_of_syndicated,
            'generalManager': general_manager,
            'regionalManager': regional_manager,
            'manager2': manager,
        }

    with open(HIERARCHY_PATH, 'w', encoding='utf-8') as f:
        json.dump(hierarchy, f)
    print(f'Rebuilt hierarchy.json from Organogram: {len(hierarchy)} rep-level entries.')

    # Diagnostic: reps in the live Call Cycle Master with no Organogram row.
    try:
        with open(RUN_LATEST_PATH, encoding='utf-8') as f:
            combined_master = json.load(f)['combinedMaster']
    except FileNotFoundError:
        print('run-latest.json not found -- skipping unmatched-reps diagnostic.')
        return

    live_reps = {}
    for r in combined_master:
        rtype = r.get('RESOURCE TYPE') or ''
        if 'MERCHANDISER' in rtype:
            continue
        name = r.get('RESOURCE NAME')
        if name:
            live_reps[norm_key(name)] = name

    unmatched = sorted(name for key, name in live_reps.items() if key not in hierarchy)
    with open(UNMATCHED_CSV_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Rep name (in Call Cycle Master, no matching Organogram row)'])
        for name in unmatched:
            writer.writerow([name])
    print(f'{len(unmatched)} reps in the live Call Cycle Master have no Organogram row -- see {UNMATCHED_CSV_PATH.name}')


if __name__ == '__main__':
    main()
