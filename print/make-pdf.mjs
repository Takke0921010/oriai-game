// HTML を実寸の PDF にする: node make-pdf.mjs
import {spawn} from 'node:child_process';
import {writeFileSync, mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
const CHROME = process.env.HOME + '/Library/Caches/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-mac-arm64/chrome-headless-shell';
const jobs = [
  ['board.html?a3', 'oriai_01_board_A3x4.pdf'],
  ['board.html?a2', 'oriai_02_board_A2.pdf'],
  ['cards.html', 'oriai_03_cards_tiles_A4.pdf'],
  ['answer-sheet.html', 'oriai_04_answer_sheet_A4_film.pdf'],
  ['reflection-sheet.html', 'oriai_05_reflection_A4.pdf'],
];
const port = 9400 + Math.floor(Math.random() * 400);
const proc = spawn(CHROME, ['--no-sandbox', '--disable-gpu', `--remote-debugging-port=${port}`, 'about:blank'], {stdio: 'ignore'});
const sleep = ms => new Promise(r => setTimeout(r, ms));
let info; for (let i = 0; i < 50; i++) { try { info = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json(); if (info.length) break; } catch {} await sleep(200); }
const ws = new WebSocket(info.find(x => x.type === 'page').webSocketDebuggerUrl); await new Promise(r => ws.onopen = r);
let id = 0; const pend = new Map();
ws.onmessage = m => { const d = JSON.parse(m.data); if (d.id && pend.has(d.id)) { pend.get(d.id)(d); pend.delete(d.id); } };
const send = (method, params = {}) => new Promise(r => { const i = ++id; pend.set(i, r); ws.send(JSON.stringify({id: i, method, params})); });
await send('Page.enable');
mkdirSync('pdf', {recursive: true});
for (const [src, out] of jobs) {
  const [file, q] = src.split('?');
  await send('Page.navigate', {url: 'file://' + resolve(file) + (q ? '?' + q : '')});
  await sleep(1500);
  const r = await send('Page.printToPDF', {preferCSSPageSize: true, printBackground: true, marginTop: 0, marginBottom: 0, marginLeft: 0, marginRight: 0});
  if (!r.result) { console.log('fail', out, JSON.stringify(r.error)); continue; }
  writeFileSync('pdf/' + out, Buffer.from(r.result.data, 'base64'));
  console.log('ok', out);
}
ws.close(); proc.kill(); process.exit(0);
