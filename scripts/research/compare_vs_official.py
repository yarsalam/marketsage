#!/usr/bin/env python3
"""Compare our adjusted_close with TSETMC official adjusted chart."""
import argparse, csv, json


def load_official(path):
    data = json.load(open(path, encoding='utf-8'))
    rows = []
    for key in ['closingPriceDaily', 'closingPrice', 'priceHistory', 'data']:
        if key in data and isinstance(data[key], list):
            for r in data[key]:
                d = r.get('dEven') or r.get('date')
                p = r.get('pClosing') or r.get('close')
                if d and p:
                    ds = str(d)
                    if len(ds) == 8:
                        ds = f'{ds[:4]}-{ds[4:6]}-{ds[6:8]}'
                    rows.append({'date': ds, 'official_close': float(p)})
            break
    rows.sort(key=lambda r: r['date'])
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--official-json', required=True)
    ap.add_argument('--adjusted-csv', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    official = {r['date']: r['official_close'] for r in load_official(args.official_json)}
    ours = {}
    with open(args.adjusted_csv, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            ours[r['date']] = float(r['adjusted_close'])

    common = sorted(set(official) & set(ours))
    rows = []
    max_err = 0
    for d in common:
        o, m = official[d], ours[d]
        err_pct = abs(o - m) / o * 100 if o else 0
        max_err = max(max_err, err_pct)
        rows.append({'date': d, 'official': o, 'ours': m, 'abs_diff': round(abs(o-m),4), 'err_pct': round(err_pct, 4)})

    with open(args.out, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['date','official','ours','abs_diff','err_pct'])
        w.writeheader(); w.writerows(rows)

    print(f'Compared {len(common)} common dates')
    print(f'Max error: {round(max_err, 4)}%')
    print(f'Rows with err > 1%: {sum(1 for r in rows if r["err_pct"] > 1)}')
    print(f'Rows with err > 5%: {sum(1 for r in rows if r["err_pct"] > 5)}')
    print(f'Output: {args.out}')


if __name__ == '__main__':
    main()
