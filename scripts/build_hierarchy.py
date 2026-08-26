#!/usr/bin/env python3
"""Extends hierarchy.json to cover merchandisers, not just reps.

hierarchy.json (added 2026-08-20, "Wire National Reporting Hierarchy") was
built by matching rep names against a National Reporting Hierarchy export --
it only ever covered reps (102/139 names matched at the time), and
merchandisers were never in that source file at all. Because the dashboard's
Regional Manager / General Manager / Head of Syndicated filters look each
row up by its OWN name in hierarchy.json (index.html's hierarchyMap[normKey(
r.resourceName)]), every merchandiser silently fails that lookup and
disappears from those filters -- for every manager, everywhere, not just one
person's team. Carin caught this 2026-08-26 asking "why does Charl have no
merchandisers" when the underlying data clearly shows he has ~109.

Fix: for each merchandiser row in the live Call Cycle Master, walk MANAGER
EMP CODE up to the rep they report to (same join key the Team Hierarchy tab
already uses), then copy that rep's already-correct headOfSyndicated /
generalManager / regionalManager onto the merchandiser's own hierarchy.json
entry (manager2 becomes the rep's name, since that IS the merchandiser's
direct manager one level up -- mirroring what manager2 already means for a
rep entry). Existing rep entries are left untouched; this only adds new keys
for merchandisers that weren't there before.

Run: python build_hierarchy.py   (writes hierarchy.json in place)
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HIERARCHY_PATH = ROOT / 'hierarchy.json'
RUN_LATEST_PATH = Path.home() / 'OneDrive - Meridian Group' / 'Stock Fix Inventory - StockFix' / 'Call Cycles' / 'run-latest.json'


def norm_key(s):
    return (s or '').upper().strip().replace('  ', ' ')


def main():
    with open(HIERARCHY_PATH, encoding='utf-8') as f:
        hierarchy = json.load(f)

    with open(RUN_LATEST_PATH, encoding='utf-8') as f:
        combined_master = json.load(f)['combinedMaster']

    # Canonical rep id/name -> hierarchy record, built once from rows whose
    # RESOURCE TYPE contains REP (not MERCHANDISER).
    rep_name_by_id = {}
    for r in combined_master:
        rtype = (r.get('RESOURCE TYPE') or '')
        if 'REP' not in rtype or 'MERCHANDISER' in rtype:
            continue
        rid = r.get('RESOURCE EMP ID')
        name = r.get('RESOURCE NAME')
        if rid and name:
            rep_name_by_id[rid] = name

    added, skipped_no_rep_id, skipped_no_hierarchy = 0, 0, 0
    for r in combined_master:
        rtype = (r.get('RESOURCE TYPE') or '')
        if 'MERCHANDISER' not in rtype:
            continue
        merch_name = r.get('RESOURCE NAME')
        if not merch_name:
            continue
        merch_key = norm_key(merch_name)
        if merch_key in hierarchy:
            continue  # already has an entry (e.g. also appears as a rep elsewhere)

        rep_id = r.get('MANAGER EMP CODE')
        rep_name = rep_name_by_id.get(rep_id)
        if not rep_name:
            skipped_no_rep_id += 1
            continue

        rep_record = hierarchy.get(norm_key(rep_name))
        if not rep_record:
            skipped_no_hierarchy += 1
            continue

        hierarchy[merch_key] = {
            'headOfSyndicated': rep_record.get('headOfSyndicated'),
            'generalManager': rep_record.get('generalManager'),
            'regionalManager': rep_record.get('regionalManager'),
            'manager2': norm_key(rep_name),
        }
        added += 1

    with open(HIERARCHY_PATH, 'w', encoding='utf-8') as f:
        json.dump(hierarchy, f)

    print(f'Added {added} merchandiser entries to hierarchy.json')
    print(f'Skipped (no rep found for MANAGER EMP CODE): {skipped_no_rep_id}')
    print(f'Skipped (rep found but rep itself missing from hierarchy.json): {skipped_no_hierarchy}')
    print(f'Total hierarchy.json entries now: {len(hierarchy)}')


if __name__ == '__main__':
    main()
