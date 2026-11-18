#!/usr/bin/env python3
"""Build adjusted price series from TSETMC raw + event ledger."""
import argparse, csv, hashlib, json
from pathlib import Path
from datetime import datetime

def sha256_file(path):
    h = hashlib.sha256()
    h.update(Path(path).read_bytes())
    return h.hexdigest()

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def classify_price_adjust(rec):
    not_adj = rec.get('pClosingNotAdjusted')
    adj = rec.get('pClosing')
    if not not_adj or not_adj == 0 or adj is None:
        return 'invalid', 1.0
    f = adj / not_adj
    if f < 0.9999: return 'forward', f
    if f > 1.0001: return 'reverse', f
    return 'neutral', 1.0

def build_events(price_adjust_records):
    by_date = {}
    for rec in price_adjust_records:
        d = str(rec['dEven'])
        kind, f = classify_price_adjust(rec)
        if kind == 'forward':
            by_date.setdefault(d, []).append(f)
        elif kind == 'reverse':
            by_date.setdefault(d + '_reverse', []).append(f)
    events = []
    for d in sorted(k for k in by_date if not k.endswith('_reverse')):
        factors = by_date[d]
        net = 1.0
        for f in factors:
            net *= f
        events.append({'date': d, 'factors': factors, 'net_factor': net})
    return events

def build_adjusted_series(daily_rows, events):
    if not daily_rows: return []
    daily_desc = sorted(daily_rows, key=lambda r: r['date'], reverse=True)
    events_desc = sorted(events, key=lambda e: e['date'], reverse=True)
    cumulative = 1.0
    out = []
    ei = 0
    for row in daily_desc:
        d_int = int(row['date'].replace('-', ''))
        while ei < len(events_desc) and int(events_desc[ei]['date']) > d_int:
            cumulative *= events_desc[ei]['net_factor']
            ei += 1
        out.append({
            'date': row['date'],
            'raw_close': row['close'],
            'adjustment_factor': round(cumulative, 8),
            'adjusted_close': round(row['close'] * cumulative, 4),
        })
    return list(reversed(out))

def read_raw_csv(path):
    """Prefer Gregorian date column. Detect jdate/jalali and exclude it."""
    rows = []
    with open(path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for r in reader:
            date_col = close_col = None
            date_candidates = []
            close_candidates = []
            for k in r:
                kl = k.lower()
                # Skip Jalali columns
                if 'jdate' in kl or 'jalali' in kl or 'shamsi' in kl:
                    continue
                if kl == 'date' or 'date' in kl or 'd_even' in kl or kl == 'd':
                    date_candidates.append(k)
                if 'close' in kl or 'pclosing' in kl or 'final' in kl:
                    close_candidates.append(k)
            # Prefer exact 'date' > 'dEven' > others
            for cand in ['date', 'dEven', 'd_even', 'd']:
                for k in date_candidates:
                    if k.lower() == cand.lower():
                        date_col = k
                        break
                if date_col:
                    break
            if not date_col and date_candidates:
                date_col = date_candidates[0]
            # Prefer 'close' > 'pClosing' > 'final_price'
            for cand in ['close', 'pclosing', 'final_price', 'final']:
                for k in close_candidates:
                    if k.lower() == cand.lower():
                        close_col = k
                        break
                if close_col:
                    break
            if not close_col and close_candidates:
                close_col = close_candidates[0]

            if date_col and close_col and r[date_col] and r[close_col]:
                try:
                    d = str(r[date_col]).strip()
                    if len(d) == 8 and d.isdigit():
                        d = f'{d[:4]}-{d[4:6]}-{d[6:8]}'
                    # Skip if date looks Jalali (13xx/14xx)
                    year_part = d.split('-')[0] if '-' in d else d[:4]
                    if year_part.isdigit() and int(year_part) < 1900:
                        continue
                    rows.append({'date': d, 'close': float(r[close_col])})
                except (ValueError, TypeError):
                    continue
    rows.sort(key=lambda r: r['date'])
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--symbol-dir', required=True)
    args = ap.parse_args()
    sd = Path(args.symbol_dir)
    raw_tsetmc = sd / 'raw' / 'tsetmc'
    out_dir = sd / 'derived'
    out_dir.mkdir(parents=True, exist_ok=True)

    pa_files = list(raw_tsetmc.glob('*price_adjust*.json'))
    if not pa_files:
        print(f'❌ no price_adjust JSON in {raw_tsetmc}')
        return 1
    pa_path = pa_files[0]
    pa_data = load_json(pa_path)
    events = build_events(pa_data.get('priceAdjust', []))

    price_candidates = []
    for pattern in ['*raw.csv', '*full.csv', '*adjusted_all.csv']:
        price_candidates.extend(list((sd / 'raw').glob(pattern)))
    if not price_candidates:
        print(f'❌ no raw price CSV in {sd / "raw"}')
        return 1
    price_csv = price_candidates[0]
    daily = read_raw_csv(price_csv)
    adjusted = build_adjusted_series(daily, events)

    out_csv = out_dir / 'adjusted_close.csv'
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['date', 'raw_close', 'adjustment_factor', 'adjusted_close'])
        w.writeheader()
        w.writerows(adjusted)

    manifest = {
        'symbol_dir': str(sd),
        'generated_at': datetime.now(__import__('datetime').timezone.utc).isoformat(),
        'engine_version': '1.0',
        'input_hashes': {'price_adjust': sha256_file(pa_path), 'raw_prices': sha256_file(price_csv)},
        'output_hashes': {'adjusted_close': sha256_file(out_csv)},
        'counts': {'price_adjust_records': len(pa_data.get('priceAdjust', [])),
                   'forward_events': len(events), 'daily_rows': len(daily), 'adjusted_rows': len(adjusted)},
    }
    manifest_path = out_dir / 'manifest.json'
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f'✅ adjusted series: {len(adjusted)} rows -> {out_csv}')
    print(f'✅ events derived: {len(events)} forward events')
    print(f'✅ manifest -> {manifest_path}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
