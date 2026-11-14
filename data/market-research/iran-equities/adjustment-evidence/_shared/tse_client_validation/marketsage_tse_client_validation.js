#!/usr/bin/env node
'use strict';

/*
 * Read-only validation of three TSETMC symbols using m-ahmadi/tse-client.
 * Fetches raw prices + adjustInfo + both adjustment modes, then compares them
 * with TSETMC Financial.aspx a=0/a=1 chart series and the existing candidate CSVs.
 * It never changes source or candidate files.
 *
 * Requires Node.js 18+ and tse-client@2.27.6 (MIT).
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const zlib = require('zlib');
const crypto = require('crypto');
const { spawnSync } = require('child_process');

const BASE = path.join(process.env.HOME || '.', 'marketsage-data', 'tsetmc-three-adjusted');
const OUT = path.join(BASE, 'tse_client_validation');
const SYMBOLS = [
  { symbol: 'فولاد', slug: 'foolad', insCode: '46348559193224090', candidate: 'foolad_combined_total_return_adjusted_candidate.csv' },
  { symbol: 'وغدیر', slug: 'vaghdir', insCode: '26014913469567886', candidate: 'vaghdir_combined_total_return_adjusted_candidate.csv' },
  { symbol: 'پارسیان', slug: 'parsian', insCode: '9481703061634967', candidate: 'parsian_combined_total_return_adjusted_candidate.csv' },
];
const PACKAGE_VERSION_EXPECTED = '2.27.6';
const UA = 'MarketSage-readonly-adjustment-validation/1.0';

function sha256(buf) { return crypto.createHash('sha256').update(buf).digest('hex'); }
function asNumber(x) {
  if (x === null || x === undefined || x === '') return null;
  const n = Number(String(x).replace(/,/g, ''));
  return Number.isFinite(n) ? n : null;
}
function toISODate(x) {
  const s = String(x ?? '').replace(/\D/g, '');
  if (s.length !== 8) return null;
  const y = Number(s.slice(0, 4)), m = Number(s.slice(4, 6)), d = Number(s.slice(6, 8));
  const dt = new Date(Date.UTC(y, m - 1, d));
  if (dt.getUTCFullYear() !== y || dt.getUTCMonth() !== m - 1 || dt.getUTCDate() !== d) return null;
  return `${s.slice(0,4)}-${s.slice(4,6)}-${s.slice(6,8)}`;
}
function parseCSV(text) {
  // Small RFC4180-style parser; candidate data contains no quoted embedded newlines.
  const lines = text.replace(/^\uFEFF/, '').split(/\r?\n/).filter(Boolean);
  if (!lines.length) return [];
  const parseLine = (line) => {
    const out = []; let cur = ''; let q = false;
    for (let i = 0; i < line.length; i++) {
      const c = line[i];
      if (c === '"') {
        if (q && line[i + 1] === '"') { cur += '"'; i++; }
        else q = !q;
      } else if (c === ',' && !q) { out.push(cur); cur = ''; }
      else cur += c;
    }
    out.push(cur); return out;
  };
  const headers = parseLine(lines[0]);
  return lines.slice(1).map(line => {
    const vals = parseLine(line); const row = {};
    headers.forEach((h, i) => row[h] = vals[i] ?? ''); return row;
  });
}
function parseChart(text) {
  const out = new Map(); let bad = 0;
  for (const item of text.replace(/\r/g, ';').split(';')) {
    const line = item.trim(); if (!line) continue;
    const c = line.split(',').map(x => x.trim());
    const date = toISODate(c[0]);
    if (!date || c.length < 7) { bad++; continue; }
    // Financial.aspx?t=ph: date,pmax,pmin,pf,pl,tvol,pc
    const row = {
      high: asNumber(c[1]), low: asNumber(c[2]), open: asNumber(c[3]),
      last: asNumber(c[4]), volume: asNumber(c[5]), close: asNumber(c[6]),
    };
    if (Object.values(row).some(v => v === null)) { bad++; continue; }
    if (out.has(date)) throw new Error(`duplicate chart date ${date}`);
    out.set(date, row);
  }
  if (!out.size) throw new Error(`no chart rows parsed (bad_lines=${bad}); prefix=${JSON.stringify(text.slice(0,100))}`);
  return { rows: out, badLines: bad };
}
function csvMap(rows, dateKey='date') {
  const out = new Map();
  for (const r of rows) {
    const d = toISODate(r[dateKey]);
    if (!d) continue;
    if (out.has(d)) throw new Error(`duplicate candidate date ${d}`);
    out.set(d, r);
  }
  return out;
}
function percentile(values, q) {
  if (!values.length) return null;
  const s = [...values].sort((a,b) => a-b);
  return s[Math.min(s.length - 1, Math.max(0, Math.ceil(q * s.length) - 1))];
}
function median(values) {
  if (!values.length) return null;
  const s = [...values].sort((a,b) => a-b); const mid = Math.floor(s.length/2);
  return s.length % 2 ? s[mid] : (s[mid-1] + s[mid]) / 2;
}
function metricSummary(modelMap, chartMap, field, anchor=true) {
  const dates = [...modelMap.keys()].filter(d => chartMap.has(d)).sort();
  const pairs = dates.map(d => ({ d, m: asNumber(modelMap.get(d)[field]), c: chartMap.get(d)[field] }))
    .filter(x => x.m !== null && x.c !== null && x.m > 0 && x.c > 0);
  if (!pairs.length) return { common: 0, exact_rate: null, median_relative_error_pct: null, p95_relative_error_pct: null, max_relative_error_pct: null };
  const scale = anchor ? pairs[pairs.length - 1].c / pairs[pairs.length - 1].m : 1;
  const errs = pairs.map(x => Math.abs((x.m * scale / x.c) - 1));
  const exact = pairs.filter(x => Math.abs(x.m * scale - x.c) < 0.005).length;
  return {
    common: pairs.length, anchor_scale: scale,
    exact_rate_pct: 100 * exact / pairs.length,
    median_relative_error_pct: 100 * median(errs),
    p95_relative_error_pct: 100 * percentile(errs, 0.95),
    max_relative_error_pct: 100 * Math.max(...errs),
    first_common_date: pairs[0].d, last_common_date: pairs[pairs.length - 1].d,
  };
}
function resolveTse() {
  const paths = [];
  if (process.env.TSE_CLIENT_NODE_PATH) paths.push(path.resolve(process.env.TSE_CLIENT_NODE_PATH));
  paths.push(path.join(OUT, 'nodeenv', 'node_modules'));
  paths.push(path.join(process.cwd(), 'node_modules'));
  for (const p of paths) {
    try { return require(require.resolve('tse-client', { paths: [p] })); } catch (_) {}
  }
  try { return require('tse-client'); } catch (e) {
    throw new Error('tse-client not found. Install it with: npm install --prefix "$HOME/marketsage-data/tsetmc-three-adjusted/tse_client_validation/nodeenv" tse-client@2.27.6');
  }
}
function httpGetText(url) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, { headers: {
      'User-Agent': UA,
      'Accept': 'text/plain, */*',
      'Accept-Encoding': 'gzip, deflate, br',
      'Cache-Control': 'no-cache',
    }, timeout: 45000 }, res => {
      const chunks = [];
      res.on('data', c => chunks.push(c));
      res.on('end', () => {
        const buf = Buffer.concat(chunks);
        const enc = String(res.headers['content-encoding'] || '').toLowerCase();
        try {
          let dec = buf;
          if (enc.includes('gzip')) dec = zlib.gunzipSync(buf);
          else if (enc.includes('deflate')) dec = zlib.inflateSync(buf);
          else if (enc.includes('br')) dec = zlib.brotliDecompressSync(buf);
          if (res.statusCode < 200 || res.statusCode >= 300) return reject(new Error(`HTTP ${res.statusCode}: ${dec.toString('utf8').slice(0,200)}`));
          resolve({ text: dec.toString('utf8'), status: res.statusCode, headers: res.headers, rawSha256: sha256(buf), decodedSha256: sha256(dec), bytes: buf.length, encoding: enc || 'identity' });
        } catch (e) { reject(new Error(`decompression/decoding error (${enc || 'identity'}): ${e.message}`)); }
      });
      res.on('error', reject);
    });
    req.on('timeout', () => req.destroy(new Error('timeout after 45s')));
    req.on('error', reject);
  });
}
function arrayToMap(data, field) {
  const out = new Map();
  if (!data || !Array.isArray(data.date)) return out;
  const values = data[field] || [];
  for (let i = 0; i < data.date.length; i++) {
    const d = toISODate(data.date[i]);
    const n = asNumber(values[i]);
    if (d && n !== null) out.set(d, n);
  }
  return out;
}
function normalizeEvent(e) {
  const before = asNumber(e.priceBeforeEvent), after = asNumber(e.priceAfterEvent);
  const oldShares = asNumber(e.oldShares), newShares = asNumber(e.newShares);
  return {
    date: e.date ?? null,
    type: e.type ?? null,
    priceBeforeEvent: e.priceBeforeEvent ?? null,
    priceAfterEvent: e.priceAfterEvent ?? null,
    priceRatio: before && after ? after / before : null,
    dividend: e.dividend ?? null,
    increasePct: e.increasePct ?? null,
    oldShares: e.oldShares ?? null,
    newShares: e.newShares ?? null,
    shareRatio: oldShares && newShares ? oldShares / newShares : null,
  };
}

async function selfTest() {
  const chart = new Map([['2026-01-01',{close:50}],['2026-01-02',{close:50}]]);
  const model = new Map([['2026-01-01',{close:100}],['2026-01-02',{close:100}]]);
  const m = metricSummary(model, chart, 'close', true);
  if (m.common !== 2 || Math.abs(m.median_relative_error_pct) > 1e-9) throw new Error('anchor comparison self-test failed');
  const date = toISODate(20261112);
  if (date !== '2026-11-12') throw new Error('date parser self-test failed');
  console.log('SELF_TEST: PASS');
}

async function main() {
  if (process.argv.includes('--self-test')) {
    await selfTest();
    if (process.argv.length <= 3) return;
  }
  fs.mkdirSync(OUT, { recursive: true });
  const tse = resolveTse();
  // The package defaults to HTTP. Use the HTTPS endpoint proven reachable
  // by the user's transport probe; isolate cache under this diagnostic run.
  const apiUrl = process.env.MARKETSAGE_TSE_API_URL || 'https://service.tsetmc.com/tsev2/data/TseClient2.aspx';
  if (!('API_URL' in tse)) throw new Error('Installed tse-client does not expose documented API_URL setting');
  tse.API_URL = apiUrl;
  if (tse.API_URL !== apiUrl) throw new Error('Could not set tse-client API_URL');
  if ('CACHE_DIR' in tse) tse.CACHE_DIR = path.join(OUT, 'node-cache');
  if ('UPDATE_INTERVAL' in tse) tse.UPDATE_INTERVAL = 0;
  console.log('TSE_CLIENT_API_URL:', tse.API_URL);
  console.log('TSE_CLIENT_CACHE_DIR:', tse.CACHE_DIR || '(not exposed)');
  let pkgVersion = 'unknown';
  try { pkgVersion = require(require.resolve('tse-client/package.json', { paths: [path.join(OUT,'nodeenv','node_modules')] })).version; }
  catch (_) { try { pkgVersion = require('tse-client/package.json').version; } catch (_) {} }

  if (pkgVersion !== 'unknown' && pkgVersion !== PACKAGE_VERSION_EXPECTED) {
    console.warn(`WARNING: expected tse-client ${PACKAGE_VERSION_EXPECTED}, found ${pkgVersion}`);
  }
  console.log(`TSE_CLIENT_VERSION: ${pkgVersion}`);
  console.log('Read-only mode: source and candidate CSVs will not be modified.');

  const report = {
    created_at: new Date().toISOString(), status: 'diagnostic_only_not_acceptance',
    library: { name: 'tse-client', version: pkgVersion, expected_version: PACKAGE_VERSION_EXPECTED },
    settings: { daysWithoutTrade: false, mergeSimilarSymbols: false, cache: false, adjusted_modes: [1,2] },
    symbols: {}, failures: [],
  };
  const eventsAll = [];
  const metricsAll = [];

  const instrumentResult = await tse.getInstruments(true, true);
  const instruments = Array.isArray(instrumentResult) ? instrumentResult : Object.values(instrumentResult || {});

  const reqSettings = { daysWithoutTrade: false, mergeSimilarSymbols: false, cache: false };
  const rawRes = await tse.getPrices(SYMBOLS.map(x => x.symbol), { ...reqSettings, adjustPrices: 0, getAdjustInfo: true });
  if (rawRes && (rawRes.error || rawRes.err)) throw new Error(`raw getPrices failed: ${JSON.stringify(rawRes.error || rawRes.err)}`);
  const adj1Res = await tse.getPrices(SYMBOLS.map(x => x.symbol), { ...reqSettings, adjustPrices: 1 });
  if (adj1Res && (adj1Res.error || adj1Res.err)) throw new Error(`adjustPrices=1 failed: ${JSON.stringify(adj1Res.error || adj1Res.err)}`);
  const adj2Res = await tse.getPrices(SYMBOLS.map(x => x.symbol), { ...reqSettings, adjustPrices: 2 });
  if (adj2Res && (adj2Res.error || adj2Res.err)) throw new Error(`adjustPrices=2 failed: ${JSON.stringify(adj2Res.error || adj2Res.err)}`);

  for (let i = 0; i < SYMBOLS.length; i++) {
    const spec = SYMBOLS[i];
    console.log(`\n===== ${spec.symbol} =====`);
    const matches = instruments.filter(x => x && x.Symbol === spec.symbol);
    const ident = matches.map(x => ({ Symbol: x.Symbol, Name: x.Name, InsCode: String(x.InsCode), CIsin: x.CIsin, CompanyCode: x.CompanyCode, YVal: x.YVal }));
    const srep = { instrument_matches: ident, expected_insCode: spec.insCode, identity_status: 'unknown' };
    if (matches.length !== 1 || String(matches[0].InsCode) !== spec.insCode) {
      srep.identity_status = 'FAIL_CLOSED';
      report.symbols[spec.symbol] = srep;
      console.log('IDENTITY CHECK FAILED:', JSON.stringify(ident));
      report.failures.push(`${spec.symbol}: instrument identity mismatch or ambiguous`);
      continue;
    }
    srep.identity_status = 'exact_symbol_and_insCode_match';

    const raw = rawRes.data && rawRes.data[i];
    const adj1 = adj1Res.data && adj1Res.data[i];
    const adj2 = adj2Res.data && adj2Res.data[i];
    if (!raw || !adj1 || !adj2) {
      srep.status = 'missing_library_data'; report.symbols[spec.symbol] = srep;
      report.failures.push(`${spec.symbol}: missing tse-client data object`); continue;
    }

    const info = raw.adjustInfo || null;
    const events = info && Array.isArray(info.events) ? info.events.map(normalizeEvent) : [];
    srep.validGPLRatio = info ? info.validGPLRatio : null;
    srep.adjustInfo_present = !!info;
    srep.event_count = events.length;
    srep.event_type_counts = events.reduce((o,e) => { o[e.type || 'unknown'] = (o[e.type || 'unknown'] || 0) + 1; return o; }, {});
    srep.events = events;

    const chartRawUrl = `https://members.tsetmc.com/tsev2/chart/data/Financial.aspx?i=${spec.insCode}&t=ph&a=0`;
    const chartAdjUrl = `https://members.tsetmc.com/tsev2/chart/data/Financial.aspx?i=${spec.insCode}&t=ph&a=1`;
    let chartRaw, chartAdj, chartMeta = {};
    try {
      const [r0, r1] = await Promise.all([httpGetText(chartRawUrl), httpGetText(chartAdjUrl)]);
      chartRaw = parseChart(r0.text).rows; chartAdj = parseChart(r1.text).rows;
      chartMeta = { raw: { status: r0.status, bytes: r0.bytes, content_encoding: r0.encoding, raw_sha256: r0.rawSha256, decoded_sha256: r0.decodedSha256 }, adjusted: { status: r1.status, bytes: r1.bytes, content_encoding: r1.encoding, raw_sha256: r1.rawSha256, decoded_sha256: r1.decodedSha256 } };
    } catch (e) {
      srep.chart_error = e.message; report.symbols[spec.symbol] = srep;
      report.failures.push(`${spec.symbol}: chart request/parse failed: ${e.message}`); continue;
    }
    srep.chart = { raw_rows: chartRaw.size, adjusted_rows: chartAdj.size, metadata: chartMeta };

    const libRaw = new Map();
    const libAdj1 = new Map();
    const libAdj2 = new Map();
    for (const [field, out] of [['close',libRaw],['close',libAdj1],['close',libAdj2]]) { /* explicit below */ }
    const dset = (data, target) => {
      if (!data || !Array.isArray(data.date) || !Array.isArray(data.close)) return;
      for (let j = 0; j < data.date.length; j++) {
        const d = toISODate(data.date[j]); const v = asNumber(data.close[j]);
        if (d && v !== null) target.set(d, { close: v });
      }
    };
    dset(raw, libRaw); dset(adj1, libAdj1); dset(adj2, libAdj2);

    const candidateRows = parseCSV(fs.readFileSync(path.join(BASE, spec.candidate), 'utf8'));
    const candidateMap = csvMap(candidateRows);
    const candidateAdj = new Map();
    const candidateRaw = new Map();
    for (const [d, r] of candidateMap) {
      const cr = asNumber(r.close_raw), ca = asNumber(r.close_adjusted);
      if (cr !== null) candidateRaw.set(d, { close: cr });
      if (ca !== null) candidateAdj.set(d, { close: ca });
    }

    const comparisons = {
      tse_client_raw_vs_chart_raw: metricSummary(libRaw, chartRaw, 'close', false),
      tse_client_adjust1_vs_chart_adjusted: metricSummary(libAdj1, chartAdj, 'close', true),
      tse_client_adjust2_vs_chart_adjusted: metricSummary(libAdj2, chartAdj, 'close', true),
      candidate_raw_vs_chart_raw: metricSummary(candidateRaw, chartRaw, 'close', false),
      candidate_adjusted_vs_chart_adjusted: metricSummary(candidateAdj, chartAdj, 'close', true),
      tse_client_adjust1_vs_candidate_adjusted: metricSummary(libAdj1, candidateAdj, 'close', true),
      tse_client_adjust2_vs_candidate_adjusted: metricSummary(libAdj2, candidateAdj, 'close', true),
    };
    srep.tse_client_rows = { raw: libRaw.size, adjust1: libAdj1.size, adjust2: libAdj2.size };
    srep.comparisons = comparisons;
    srep.status = 'ok';
    report.symbols[spec.symbol] = srep;

    console.log('validGPLRatio:', srep.validGPLRatio, 'events:', events.length, JSON.stringify(srep.event_type_counts));
    for (const [name, m] of Object.entries(comparisons)) {
      console.log(`${name}: common=${m.common} exact=${m.exact_rate_pct === null ? 'N/A' : m.exact_rate_pct.toFixed(2)+'%'} median=${m.median_relative_error_pct === null ? 'N/A' : m.median_relative_error_pct.toFixed(4)+'%'} p95=${m.p95_relative_error_pct === null ? 'N/A' : m.p95_relative_error_pct.toFixed(4)+'%'} max=${m.max_relative_error_pct === null ? 'N/A' : m.max_relative_error_pct.toFixed(4)+'%'}`);
    }

    for (const mode of ['raw','adjust1','adjust2','candidate_adjusted']) {
      const src = mode === 'raw' ? libRaw : mode === 'adjust1' ? libAdj1 : mode === 'adjust2' ? libAdj2 : candidateAdj;
      const chart = mode === 'raw' ? chartRaw : chartAdj;
      const dates = [...src.keys()].filter(d => chart.has(d)).sort();
      const lastDate = dates[dates.length - 1];
      const scale = lastDate ? chart.get(lastDate).close / src.get(lastDate).close : 1;
      for (const d of dates) {
        const m = src.get(d).close * scale, c = chart.get(d).close;
        metricsAll.push({ symbol: spec.symbol, mode, date: d, source_close: src.get(d).close, chart_close: c, anchor_scale: scale, normalized_source_close: m, relative_error_pct: c ? Math.abs(m/c - 1)*100 : null });
      }
    }
    for (const e of events) eventsAll.push({ symbol: spec.symbol, ...e });
  }

  const jsonPath = path.join(OUT, 'tse_client_validation.json');
  fs.writeFileSync(jsonPath, JSON.stringify(report, null, 2), 'utf8');
  const csvPath = path.join(OUT, 'tse_client_adjusted_close_comparison.csv');
  const fields = ['symbol','mode','date','source_close','chart_close','anchor_scale','normalized_source_close','relative_error_pct'];
  const csv = [fields.join(','), ...metricsAll.map(r => fields.map(k => JSON.stringify(r[k] ?? '')).join(','))].join('\n') + '\n';
  fs.writeFileSync(csvPath, '\uFEFF' + csv, 'utf8');
  const evPath = path.join(OUT, 'tse_client_adjust_info_events.json');
  fs.writeFileSync(evPath, JSON.stringify(eventsAll, null, 2), 'utf8');
  const pkgPath = path.join(OUT, 'tse_client_validation.zip');
  try {
    const py = 'import sys,zipfile; z=zipfile.ZipFile(sys.argv[1], \"w\", zipfile.ZIP_DEFLATED); [z.write(p, __import__(\"os\").path.basename(p)) for p in sys.argv[2:]]; z.close()';
    const result = spawnSync('python3', ['-c', py, pkgPath, jsonPath, csvPath, evPath], { encoding: 'utf8' });
    if (result.status !== 0) throw new Error(result.stderr || `python zip exited ${result.status}`);
    console.log('PACKAGE:', pkgPath, 'SHA256:', sha256(fs.readFileSync(pkgPath)));
  } catch (e) {
    console.log('ZIP not created:', e.message);
  }
  console.log('\nREPORT:', jsonPath);
  console.log('DETAIL_CSV:', csvPath);
  console.log('EVENTS:', evPath);
  console.log('NOTE: Diagnostic only. validGPLRatio=false or chart mismatch blocks acceptance.');
  if (report.failures.length) {
    console.log('FAILURES:', JSON.stringify(report.failures));
    process.exitCode = 2;
  }
}

main().catch(err => { console.error('FATAL:', err && err.stack || err); console.error('DIAGNOSTIC_API_URL:', process.env.MARKETSAGE_TSE_API_URL || 'https://service.tsetmc.com/tsev2/data/TseClient2.aspx'); process.exit(1); });
