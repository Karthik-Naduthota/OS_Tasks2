"""
tracelog.py - shared helper used by all four programs.

Trace      : thread-safe, ordered event recorder. The synchronization code calls
             trace.log(...) at the moment each state change really happens
             (always while the relevant lock/semaphore is held).
write_html : turns the recorded events into a self-contained HTML replay viewer.
             The page contains NO hand-written scenario: everything it shows is
             re-computed from the event list embedded in the file.
"""
import json
import os
import threading
import time
import webbrowser
from pathlib import Path


class Trace:
    def __init__(self):
        self._lock = threading.Lock()   # protects the event list only
        self.events = []
        self._t0 = time.monotonic()

    def log(self, actor, kind, **data):
        with self._lock:
            event = {"seq": len(self.events),
                     "t": round(time.monotonic() - self._t0, 3),
                     "actor": actor, "kind": kind}
            event.update(data)
            self.events.append(event)


def write_html(path, title, mode, actors, trace, forks=0):
    """mode is 'rw' (readers-writers) or 'dp' (dining philosophers)."""
    payload = {"title": title, "mode": mode, "actors": actors,
               "forks": forks, "events": trace.events}
    html = (_TEMPLATE.replace("__TITLE__", title)
                     .replace("__DATA__", json.dumps(payload)))
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    path = os.path.abspath(path)
    print(f"HTML simulation written to: {path}  ({len(trace.events)} events)")

    # Open the simulation automatically in the default browser.
    try:
        opened = webbrowser.open(Path(path).as_uri())
    except Exception:
        opened = False
    if not opened:
        print("Could not auto-open a browser here. Open the file above manually.")


_TEMPLATE = r"""<!doctype html>
<html><head><meta charset="utf-8"><title>__TITLE__</title>
<style>
body{font-family:system-ui,sans-serif;margin:0;background:#0f172a;color:#e2e8f0}
header{padding:12px 20px;background:#1e293b;font-size:18px;font-weight:600}
.ctl{padding:10px 20px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
button,select{background:#334155;color:#e2e8f0;border:0;padding:6px 14px;border-radius:6px;cursor:pointer}
input[type=range]{flex:1;min-width:200px}
main{display:flex;flex-wrap:wrap;gap:16px;padding:0 20px 20px}
#stage{flex:2 1 460px;background:#1e293b;border-radius:10px;padding:14px;min-height:380px}
#log{flex:1 1 300px;background:#1e293b;border-radius:10px;padding:12px;height:440px;overflow:auto;font:12px monospace}
.card{display:inline-block;width:120px;margin:6px;padding:10px;border-radius:8px;text-align:center;color:#0f172a;font-weight:600}
.res{margin:14px 6px;padding:14px;border-radius:8px;border:2px solid #475569;font-size:15px}
.legend span{display:inline-block;margin-right:10px;font-size:12px}
.legend i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:4px}
.last{background:#334155}
</style></head><body>
<header>__TITLE__</header>
<div class="ctl">
 <button id="play">Play</button><button id="step">Step</button><button id="reset">Reset</button>
 Speed <select id="speed"><option value="1">1x</option><option value="2">2x</option>
 <option value="5">5x</option><option value=".5">0.5x</option></select>
 <input type="range" id="slider" min="0" value="0">
 <span id="clock"></span>
</div>
<main><div id="stage"></div><div id="log"></div></main>
<script>
const DATA = __DATA__;
const E = DATA.events, MODE = DATA.mode;
const COLORS = {idle:'#94a3b8',thinking:'#94a3b8',waiting:'#f59e0b',hungry:'#f59e0b',
  acquiring:'#a78bfa',reading:'#22c55e',writing:'#ef4444',eating:'#22c55e',
  releasing:'#38bdf8',done:'#475569'};
let idx = 0, timer = null;
const $ = id => document.getElementById(id);
$('slider').max = E.length;

// Re-compute the whole world from the first n recorded events.
function compute(n){
  const st = {}, forks = {};
  DATA.actors.forEach(a => st[a] = 'idle');
  for (let f = 0; f < DATA.forks; f++) forks[f] = null;
  for (let i = 0; i < n; i++){
    const e = E[i];
    if (e.kind === 'state') st[e.actor] = e.state;
    else if (e.kind === 'fork') forks[e.fork] = e.owner;
  }
  return {st, forks};
}
function lastAccess(n){
  for (let i = n - 1; i >= 0; i--) if (E[i].kind === 'access') return E[i];
  return null;
}
function legend(){
  return '<div class="legend">' + Object.keys(COLORS).filter(k=>!['idle'].includes(k))
    .map(k => `<span><i style="background:${COLORS[k]}"></i>${k}</span>`).join('') + '</div>';
}
function renderRW(st){
  let r = 0, w = 0;
  for (const a in st){ if (st[a]==='reading') r++; if (st[a]==='writing') w++; }
  const bad = w > 1 || (w > 0 && r > 0);
  const acc = lastAccess(idx);
  const status = bad ? 'VIOLATION - mutual exclusion broken!' :
    w ? 'LOCKED: 1 writer inside critical section' :
    r ? 'SHARED: ' + r + ' reader(s) inside critical section' : 'FREE: nobody inside';
  const col = bad ? '#ef4444' : w ? '#f97316' : r ? '#22c55e' : '#475569';
  let h = legend() + '<div>';
  for (const a in st)
    h += `<div class="card" style="background:${COLORS[st[a]]}">${a}<br><small>${st[a]}</small></div>`;
  h += `</div><div class="res" style="border-color:${col}"><b>Shared resource (counter)</b><br>
    value = ${acc ? acc.value : 0}<br>Status: <b style="color:${col}">${status}</b><br>
    Active readers: ${r} &nbsp; Active writers: ${w} &nbsp;
    Waiting: ${Object.values(st).filter(s=>s==='waiting').length}</div>`;
  return h;
}
function renderDP(st, forks){
  const N = DATA.actors.length, cx = 220, cy = 210, R = 135;
  let s = '<svg viewBox="0 0 440 420" width="100%"><circle cx="220" cy="210" r="70" fill="#334155"/>' +
          '<text x="220" y="215" text-anchor="middle" fill="#94a3b8" font-size="13">table</text>';
  const ang = i => (-Math.PI/2) + i * 2*Math.PI/N;
  const P = i => [cx + R*Math.cos(ang(i)), cy + R*Math.sin(ang(i))];
  for (let f = 0; f < N; f++){            // fork f lies between philosopher f and f+1
    const a = ang(f) + Math.PI/N, home = [cx + 85*Math.cos(a), cy + 85*Math.sin(a)];
    let pos = home, color = '#e2e8f0', label = 'F' + f;
    if (forks[f] !== null){
      const p = P(forks[f]); color = COLORS[st['P'+forks[f]]];
      pos = [home[0]*0.45 + p[0]*0.55, home[1]*0.45 + p[1]*0.55];
      label = 'F' + f + '\u2192P' + forks[f];
    }
    s += `<circle cx="${pos[0]}" cy="${pos[1]}" r="11" fill="${color}" stroke="#0f172a"/>
          <text x="${pos[0]}" y="${pos[1]+26}" text-anchor="middle" fill="#e2e8f0" font-size="11">${label}</text>`;
  }
  for (let i = 0; i < N; i++){
    const [x, y] = P(i), name = 'P' + i;
    s += `<circle cx="${x}" cy="${y}" r="34" fill="${COLORS[st[name]]}"/>
          <text x="${x}" y="${y-2}" text-anchor="middle" font-weight="700" fill="#0f172a">${name}</text>
          <text x="${x}" y="${y+14}" text-anchor="middle" font-size="11" fill="#0f172a">${st[name]}</text>`;
  }
  return legend() + s + '</svg>';
}
function render(){
  const {st, forks} = compute(idx);
  $('stage').innerHTML = MODE === 'rw' ? renderRW(st) : renderDP(st, forks);
  let l = '';
  for (let i = 0; i < idx; i++){
    const e = E[i];
    let msg = e.kind === 'state' ? e.actor + ' -> ' + e.state :
              e.kind === 'fork' ? 'fork ' + e.fork + (e.owner === null ? ' released' : ' taken by P' + e.owner) :
              e.actor + ' ' + (e.action || 'access') + ' value=' + e.value;
    l += `<div class="${i===idx-1?'last':''}">[${e.t.toFixed(3)}s] ${msg}</div>`;
  }
  $('log').innerHTML = l; $('log').scrollTop = $('log').scrollHeight;
  $('slider').value = idx;
  $('clock').textContent = idx + '/' + E.length + (idx ? '  t=' + E[idx-1].t + 's' : '');
}
function tick(){ if (idx < E.length) { idx++; render(); } else pause(); }
function play(){ pause(); if (idx >= E.length) idx = 0;
  timer = setInterval(tick, 400 / parseFloat($('speed').value)); $('play').textContent = 'Pause'; }
function pause(){ clearInterval(timer); timer = null; $('play').textContent = 'Play'; }
$('play').onclick = () => timer ? pause() : play();
$('step').onclick = () => { pause(); tick(); };
$('reset').onclick = () => { pause(); idx = 0; render(); };
$('speed').onchange = () => { if (timer) play(); };
$('slider').oninput = e => { pause(); idx = +e.target.value; render(); };
render();
</script></body></html>
"""
