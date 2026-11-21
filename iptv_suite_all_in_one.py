import os
import re
import io
import gzip
import json
import shutil
import socket
import threading
import subprocess
import webbrowser
import urllib.request
import urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

PROXY_HOST = "127.0.0.1"
PROXY_PORT = 18888

HTML_PLAYER = r"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IPTV Web Player & EPG (Proxy Integrato)</title>
<script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
<style>
  :root {
    --bg: #0f1117;
    --panel: #181c26;
    --card: #212736;
    --accent: #2563eb;
    --accent-hover: #1d4ed8;
    --text: #f1f5f9;
    --muted: #94a3b8;
    --border: #2e364a;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, sans-serif; }
  body { background: var(--bg); color: var(--text); height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
  header {
    background: var(--panel); padding: 10px 16px; border-bottom: 1px solid var(--border);
    display: flex; flex-wrap: wrap; gap: 10px; align-items: center; justify-content: space-between;
  }
  header h1 { font-size: 1.15rem; display: flex; align-items: center; gap: 8px; }
  .badge { background: #10b98122; color: #34d399; border: 1px solid #10b98155; font-size: 0.75rem; padding: 2px 8px; border-radius: 99px; }
  .toolbar {
    background: var(--panel); padding: 10px 16px; border-bottom: 1px solid var(--border);
    display: grid; grid-template-columns: 1fr 1fr auto; gap: 10px; align-items: center;
  }
  .input-group { display: flex; gap: 6px; align-items: center; }
  input[type="text"], select {
    background: var(--card); border: 1px solid var(--border); color: var(--text);
    padding: 7px 10px; border-radius: 6px; font-size: 0.9rem; width: 100%;
  }
  button {
    background: var(--accent); color: white; border: none; padding: 7px 12px;
    border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.85rem; white-space: nowrap;
  }
  button:hover { background: var(--accent-hover); }
  button.sec { background: #334155; }
  button.sec:hover { background: #475569; }
  .main { display: grid; grid-template-columns: 340px 1fr 340px; flex: 1; overflow: hidden; }
  .col { display: flex; flex-direction: column; border-right: 1px solid var(--border); overflow: hidden; background: var(--panel); }
  .col:last-child { border-right: none; }
  .col-head { padding: 10px; border-bottom: 1px solid var(--border); display: flex; gap: 6px; }
  .list { flex: 1; overflow-y: auto; padding: 6px; }
  .ch-item {
    padding: 9px 10px; border-radius: 6px; cursor: pointer; display: flex; justify-content: space-between;
    align-items: center; gap: 8px; margin-bottom: 4px; background: transparent;
  }
  .ch-item:hover { background: var(--card); }
  .ch-item.active { background: var(--accent); color: white; }
  .ch-name { font-weight: 600; font-size: 0.92rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .ch-grp { font-size: 0.75rem; color: var(--muted); }
  .ch-item.active .ch-grp { color: #dbeafe; }
  .player-area { background: #000; display: flex; flex-direction: column; justify-content: space-between; }
  video { width: 100%; height: 100%; max-height: calc(100vh - 210px); background: #000; }
  .now-bar {
    background: var(--panel); padding: 12px 16px; border-top: 1px solid var(--border);
    display: flex; justify-content: space-between; align-items: center; gap: 12px;
  }
  .epg-card {
    background: var(--card); padding: 10px; border-radius: 6px; margin-bottom: 8px;
    border-left: 3px solid #475569;
  }
  .epg-card.live { border-left-color: #3b82f6; background: #1e293b; }
  .epg-time { font-size: 0.78rem; color: #60a5fa; font-weight: 700; }
  .epg-title { font-size: 0.92rem; font-weight: 600; margin: 2px 0; }
  .epg-desc { font-size: 0.8rem; color: var(--muted); line-height: 1.35; }
  .status { font-size: 0.82rem; color: var(--muted); }
</style>
</head>
<body>
<header>
  <h1>📺 IPTV Web Player & Guida EPG <span class="badge">● Proxy Locale Attivo</span></h1>
  <div style="display:flex; align-items:center; gap:12px;">
    <label style="font-size:0.85rem; display:flex; align-items:center; gap:5px; cursor:pointer;">
      <input type="checkbox" id="useProxy" checked> Usa Proxy Anti-CORS (Consigliato per Pluto/Jmp2)
    </label>
    <span class="status" id="statusText">Pronto</span>
  </div>
</header>

<div class="toolbar">
  <div class="input-group">
    <input type="text" id="m3uUrl" placeholder="URL Playlist M3U o singolo link .m3u8 (es. https://jmp2.uk/plu-...)">
    <button onclick="loadM3UFromInput()">Carica M3U / Stream</button>
    <input type="file" id="m3uFile" accept=".m3u,.m3u8" style="display:none" onchange="loadM3UFile(event)">
    <button class="sec" onclick="document.getElementById('m3uFile').click()">File M3U</button>
  </div>
  <div class="input-group">
    <input type="text" id="epgUrl" placeholder="URL Guida EPG XMLTV (.xml o .xml.gz)">
    <button onclick="loadEPGFromInput()">Carica EPG</button>
    <input type="file" id="epgFile" accept=".xml,.gz" style="display:none" onchange="loadEPGFile(event)">
    <button class="sec" onclick="document.getElementById('epgFile').click()">File EPG</button>
  </div>
  <div>
    <button class="sec" onclick="openInVLC()">▶ Apri su VLC</button>
  </div>
</div>

<div class="main">
  <div class="col">
    <div class="col-head">
      <input type="text" id="searchBox" placeholder="Cerca canale..." oninput="renderChannels()">
      <select id="groupFilter" onchange="renderChannels()" style="max-width:130px;">
        <option value="ALL">Tutti</option>
      </select>
    </div>
    <div class="list" id="channelList"></div>
  </div>

  <div class="player-area">
    <video id="video" controls autoplay playsinline></video>
    <div class="now-bar">
      <div>
        <div style="font-weight:700; font-size:1rem;" id="curChName">Nessun canale selezionato</div>
        <div style="font-size:0.85rem; color:#93c5fd;" id="curProgInfo">Incolla una playlist M3U o un link .m3u8 in alto e premi Carica</div>
      </div>
      <div style="font-size:0.78rem; color:var(--muted); max-width:340px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" id="curUrlLabel"></div>
    </div>
  </div>

  <div class="col">
    <div class="col-head">
      <strong style="font-size:0.95rem;">📅 Guida Programmi (EPG)</strong>
    </div>
    <div class="list" id="epgList">
      <div style="padding:12px; color:var(--muted); font-size:0.85rem;">Carica un file EPG XMLTV per visualizzare la programmazione del canale.</div>
    </div>
  </div>
</div>

<script>
let channels = [];
let currentChannel = null;
let epgMap = {};
let epgNameMap = {};
let hls = null;

function setStatus(msg) {
  document.getElementById('statusText').textContent = msg;
}

function proxify(url) {
  if (!url) return url;
  if (!document.getElementById('useProxy').checked) return url;
  if (url.startsWith('http://127.0.0.1:') || url.startsWith('blob:')) return url;
  return '/proxy?url=' + encodeURIComponent(url);
}

async function loadM3UFromInput() {
  const input = document.getElementById('m3uUrl').value.trim();
  if (!input) return alert('Inserisci un URL M3U o un link diretto .m3u8');

  // Se e' un singolo stream .m3u8 diretto, lo aggiunge subito e lo avvia
  if (input.toLowerCase().includes('.m3u8') && !input.toLowerCase().endsWith('.m3u')) {
    try {
      setStatus('Verifica flusso diretto...');
      const res = await fetch(proxify(input));
      const text = await res.text();
      if (text.includes('#EXTINF:') && !text.includes('#EXT-X-TARGETDURATION')) {
        parseM3U(text);
      } else {
        channels = [{ name: 'Stream Diretto', group: 'Diretto', tvgId: '', tvgName: '', url: input }];
        updateGroups();
        renderChannels();
        playChannel(0);
      }
      return;
    } catch (e) {
      channels = [{ name: 'Stream Diretto', group: 'Diretto', tvgId: '', tvgName: '', url: input }];
      updateGroups();
      renderChannels();
      playChannel(0);
      return;
    }
  }

  setStatus('Download playlist M3U...');
  try {
    const res = await fetch(proxify(input));
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const text = await res.text();
    parseM3U(text);
  } catch (err) {
    setStatus('Errore caricamento M3U');
    alert('Impossibile scaricare la playlist M3U: ' + err.message);
  }
}

function loadM3UFile(ev) {
  const file = ev.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = e => parseM3U(e.target.result);
  reader.readAsText(file);
}

function parseM3U(text) {
  const lines = text.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
  const parsed = [];
  let info = null;

  for (const line of lines) {
    if (line.startsWith('#EXTINF:')) {
      const tvgId = (line.match(/tvg-id="([^"]*)"/i) || [])[1] || '';
      const tvgName = (line.match(/tvg-name="([^"]*)"/i) || [])[1] || '';
      const group = (line.match(/group-title="([^"]*)"/i) || [])[1] || 'Generale';
      const commaIdx = line.lastIndexOf(',');
      const name = commaIdx !== -1 ? line.slice(commaIdx + 1).trim() : (tvgName || 'Canale');
      info = { name, group, tvgId, tvgName };
    } else if (!line.startsWith('#') && info) {
      info.url = line;
      parsed.push(info);
      info = null;
    }
  }

  channels = parsed;
  updateGroups();
  renderChannels();
  setStatus(`Caricati ${channels.length} canali`);
  if (channels.length > 0) playChannel(0);
}

function updateGroups() {
  const sel = document.getElementById('groupFilter');
  const groups = [...new Set(channels.map(c => c.group))].sort();
  sel.innerHTML = '<option value="ALL">Tutti (' + channels.length + ')</option>' +
    groups.map(g => `<option value="${g.replace(/"/g, '&quot;')}">${g}</option>`).join('');
}

function renderChannels() {
  const q = document.getElementById('searchBox').value.toLowerCase();
  const grp = document.getElementById('groupFilter').value;
  const list = document.getElementById('channelList');
  list.innerHTML = '';

  channels.forEach((ch, idx) => {
    if (grp !== 'ALL' && ch.group !== grp) return;
    if (q && !ch.name.toLowerCase().includes(q) && !ch.group.toLowerCase().includes(q)) return;

    const div = document.createElement('div');
    div.className = 'ch-item' + (currentChannel === ch ? ' active' : '');
    div.innerHTML = `<div class="ch-name">${ch.name}</div><div class="ch-grp">${ch.group}</div>`;
    div.onclick = () => playChannel(idx);
    list.appendChild(div);
  });
}

function playChannel(idx) {
  const ch = channels[idx];
  if (!ch) return;
  currentChannel = ch;
  renderChannels();

  document.getElementById('curChName').textContent = ch.name;
  document.getElementById('curUrlLabel').textContent = ch.url;
  setStatus('Connessione a ' + ch.name + '...');

  const video = document.getElementById('video');
  const streamUrl = proxify(ch.url);

  if (hls) {
    hls.destroy();
    hls = null;
  }

  if (Hls.isSupported()) {
    hls = new Hls({
      enableWorker: true,
      lowLatencyMode: true,
      maxBufferLength: 30
    });
    hls.loadSource(streamUrl);
    hls.attachMedia(video);
    hls.on(Hls.Events.MANIFEST_PARSED, () => {
      video.play().catch(() => {});
      setStatus('In riproduzione: ' + ch.name);
    });
    hls.on(Hls.Events.ERROR, (event, data) => {
      if (data.fatal) {
        setStatus('Errore stream (' + data.details + ') - Prova "Apri su VLC"');
      }
    });
  } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
    video.src = streamUrl;
    video.play().catch(() => {});
  }

  renderEPGForChannel(ch);
}

async function openInVLC() {
  if (!currentChannel) return alert('Seleziona prima un canale.');
  try {
    const res = await fetch('/vlc?url=' + encodeURIComponent(currentChannel.url));
    const txt = await res.text();
    setStatus(txt);
  } catch (e) {
    alert('Errore comunicazione con il launcher VLC: ' + e.message);
  }
}

async function loadEPGFromInput() {
  const url = document.getElementById('epgUrl').value.trim();
  if (!url) return alert('Inserisci un URL EPG XMLTV');
  setStatus('Download guida EPG in corso...');
  try {
    const res = await fetch('/epg?url=' + encodeURIComponent(url));
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const xmlText = await res.text();
    parseEPGXml(xmlText);
  } catch (e) {
    setStatus('Errore caricamento EPG');
    alert('Errore EPG: ' + e.message);
  }
}

function loadEPGFile(ev) {
  const file = ev.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = e => parseEPGXml(e.target.result);
  reader.readAsText(file);
}

function parseXmltvDate(str) {
  if (!str || str.length < 14) return null;
  const y = +str.slice(0, 4), m = +str.slice(4, 6) - 1, d = +str.slice(6, 8);
  const H = +str.slice(8, 10), M = +str.slice(10, 12), S = +str.slice(12, 14);
  const tzMatch = str.slice(14).trim().match(/^([+-])(\d{2})(\d{2})$/);
  if (tzMatch) {
    const sign = tzMatch[1] === '+' ? 1 : -1;
    const offsetMin = sign * (+tzMatch[2] * 60 + +tzMatch[3]);
    return new Date(Date.UTC(y, m, d, H, M, S) - offsetMin * 60000);
  }
  return new Date(y, m, d, H, M, S);
}

function parseEPGXml(xmlText) {
  const doc = new DOMParser().parseFromString(xmlText, 'text/xml');
  epgMap = {};
  epgNameMap = {};

  doc.querySelectorAll('channel').forEach(ch => {
    const id = ch.getAttribute('id') || '';
    if (!id) return;
    epgNameMap[id.toLowerCase()] = id;
    ch.querySelectorAll('display-name').forEach(dn => {
      if (dn.textContent) epgNameMap[dn.textContent.trim().toLowerCase()] = id;
    });
  });

  let count = 0;
  doc.querySelectorAll('programme').forEach(p => {
    const cid = p.getAttribute('channel') || '';
    const start = parseXmltvDate(p.getAttribute('start') || '');
    const stop = parseXmltvDate(p.getAttribute('stop') || '');
    const title = p.querySelector('title')?.textContent?.trim() || 'Senza titolo';
    const desc = p.querySelector('desc')?.textContent?.trim() || '';
    if (cid && start && stop) {
      if (!epgMap[cid]) epgMap[cid] = [];
      epgMap[cid].push({ start, stop, title, desc });
      count++;
    }
  });

  Object.values(epgMap).forEach(arr => arr.sort((a, b) => a.start - b.start));
  setStatus(`EPG caricata (${count} programmi)`);
  if (currentChannel) renderEPGForChannel(currentChannel);
}

function renderEPGForChannel(ch) {
  const box = document.getElementById('epgList');
  const nowInfo = document.getElementById('curProgInfo');
  const keys = [ch.tvgId, ch.tvgName, ch.name].map(k => (k || '').toLowerCase()).filter(Boolean);

  let progs = [];
  for (const k of keys) {
    if (epgMap[k]) { progs = epgMap[k]; break; }
    if (epgNameMap[k] && epgMap[epgNameMap[k]]) { progs = epgMap[epgNameMap[k]]; break; }
  }

  if (!progs.length) {
    box.innerHTML = '<div style="padding:12px; color:var(--muted); font-size:0.85rem;">Nessun dato EPG trovato per questo canale.</div>';
    nowInfo.textContent = 'Nessuna info EPG per questo canale';
    return;
  }

  const now = new Date();
  const upcoming = progs.filter(p => p.stop >= now).slice(0, 30);
  box.innerHTML = '';
  let liveFound = false;

  upcoming.forEach(p => {
    const isLive = p.start <= now && now <= p.stop;
    const fmt = d => d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const timeStr = `${fmt(p.start)} - ${fmt(p.stop)}`;
    if (isLive) {
      liveFound = true;
      nowInfo.textContent = `IN ONDA (${timeStr}): ${p.title}`;
    }
    const card = document.createElement('div');
    card.className = 'epg-card' + (isLive ? ' live' : '');
    card.innerHTML = `<div class="epg-time">${isLive ? '▶ IN ONDA • ' : ''}${timeStr}</div>
      <div class="epg-title">${p.title}</div>
      ${p.desc ? `<div class="epg-desc">${p.desc}</div>` : ''}`;
    box.appendChild(card);
  });

  if (!liveFound) nowInfo.textContent = 'Prossimo programma: ' + (upcoming[0]?.title || '-');
}
</script>
</body>
</html>
"""

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Referer": "https://pluto.tv/",
    "Accept": "*/*"
}

def find_vlc():
    candidates = [
        shutil.which("vlc"),
        r"C:\Program Files\VideoLAN\VLC\vlc.exe",
        r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
    ]
    return next((p for p in candidates if p and os.path.exists(p)), None)

def launch_vlc_stream(url):
    vlc_exe = find_vlc()
    ua = DEFAULT_HEADERS["User-Agent"]
    if vlc_exe:
        subprocess.Popen([
            vlc_exe,
            url,
            f"--http-user-agent={ua}",
            "--http-referrer=https://pluto.tv/"
        ])
        return "Avviato su VLC Media Player"
    else:
        os.startfile(url)
        return "Aperto con il lettore predefinito"

class IPTVProxyHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _send_cors_headers(self, status=200, content_type="text/plain; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_OPTIONS(self):
        self._send_cors_headers(204)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if parsed.path in ("/", "/index.html"):
            self._send_cors_headers(200, "text/html; charset=utf-8")
            self.wfile.write(HTML_PLAYER.encode("utf-8"))
            return

        if parsed.path == "/vlc":
            target = params.get("url", [None])[0]
            if not target:
                self._send_cors_headers(400)
                self.wfile.write(b"URL mancante")
                return
            try:
                msg = launch_vlc_stream(target)
                self._send_cors_headers(200)
                self.wfile.write(msg.encode("utf-8"))
            except Exception as e:
                self._send_cors_headers(500)
                self.wfile.write(f"Errore VLC: {e}".encode("utf-8"))
            return

        if parsed.path == "/epg":
            target = params.get("url", [None])[0]
            if not target:
                self._send_cors_headers(400)
                self.wfile.write(b"URL EPG mancante")
                return
            try:
                req = urllib.request.Request(target, headers=DEFAULT_HEADERS)
                with urllib.request.urlopen(req, timeout=30) as resp:
                    raw = resp.read()
                if target.endswith(".gz") or raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                self._send_cors_headers(200, "application/xml; charset=utf-8")
                self.wfile.write(raw)
            except Exception as e:
                self._send_cors_headers(502)
                self.wfile.write(f"Errore EPG: {e}".encode("utf-8"))
            return

        if parsed.path == "/proxy":
            target = params.get("url", [None])[0]
            if not target:
                self._send_cors_headers(400)
                self.wfile.write(b"Parametro ?url= mancante")
                return
            try:
                req = urllib.request.Request(target, headers=DEFAULT_HEADERS)
                with urllib.request.urlopen(req, timeout=20) as resp:
                    data = resp.read()
                    final_url = resp.geturl()
                    ctype = resp.headers.get("Content-Type", "application/octet-stream")

                is_m3u = (
                    ".m3u" in target.lower()
                    or ".m3u" in final_url.lower()
                    or "mpegurl" in ctype.lower()
                    or data.lstrip()[:7] == b"#EXTM3U"
                )

                if is_m3u:
                    text = data.decode("utf-8", errors="replace")
                    rewritten = []
                    for line in text.splitlines():
                        s = line.strip()
                        if not s:
                            continue
                        if s.startswith("#"):
                            # Riscrive eventuali URI="..." nei tag HLS (es. #EXT-X-KEY o #EXT-X-MEDIA)
                            def repl_uri(m):
                                abs_u = urllib.parse.urljoin(final_url, m.group(1))
                                return f'URI="/proxy?url={urllib.parse.quote(abs_u, safe="")}"'
                            s = re.sub(r'URI="([^"]+)"', repl_uri, s)
                            rewritten.append(s)
                        else:
                            abs_u = urllib.parse.urljoin(final_url, s)
                            rewritten.append(f'/proxy?url={urllib.parse.quote(abs_u, safe="")}')
                    out_bytes = "\n".join(rewritten).encode("utf-8")
                    self._send_cors_headers(200, "application/vnd.apple.mpegurl; charset=utf-8")
                    self.wfile.write(out_bytes)
                else:
                    self._send_cors_headers(200, ctype)
                    self.wfile.write(data)
            except Exception as e:
                self._send_cors_headers(502)
                self.wfile.write(f"Errore Proxy: {e}".encode("utf-8"))
            return

        self._send_cors_headers(404)
        self.wfile.write(b"Non trovato")

def find_free_port(preferred=PROXY_PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex((PROXY_HOST, preferred)) != 0:
            return preferred
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((PROXY_HOST, 0))
        return s.getsockname()[1]

class LauncherApp:
    def __init__(self, root, port):
        self.root = root
        self.port = port
        self.base_url = f"http://{PROXY_HOST}:{self.port}/"

        self.root.title("IPTV Suite - Proxy + Web Player + VLC")
        self.root.geometry("560x360")
        self.root.resizable(False, False)
        self.root.configure(bg="#12141a")

        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 18, "pady": 8}

        tk.Label(
            self.root, text="📺 IPTV Suite All-in-One",
            bg="#12141a", fg="#ffffff", font=("Segoe UI", 15, "bold")
        ).pack(anchor="w", padx=18, pady=(16, 2))

        tk.Label(
            self.root, text=f"Proxy locale anti-CORS attivo su {self.base_url}",
            bg="#12141a", fg="#34d399", font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", padx=18, pady=(0, 12))

        # Bottone principale Web Player
        btn_web = tk.Button(
            self.root,
            text="🌐 Apri Lettore Web + Guida EPG nel Browser",
            bg="#2563eb", fg="white", activebackground="#1d4ed8", activeforeground="white",
            font=("Segoe UI", 11, "bold"), relief=tk.FLAT, cursor="hand2", pady=10,
            command=self.open_browser
        )
        btn_web.pack(fill=tk.X, **pad)

        # Riquadro test rapido URL diretto su VLC
        box = tk.Frame(self.root, bg="#1b1f2a", padx=12, pady=12)
        box.pack(fill=tk.X, padx=18, pady=10)

        tk.Label(
            box, text="Avvio rapido link M3U8 su VLC (con User-Agent & Referer):",
            bg="#1b1f2a", fg="#cbd5e1", font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(0, 6))

        self.url_var = tk.StringVar(value="https://jmp2.uk/plu-60940a07d88ba90007b9cb71.m3u8")
        entry = tk.Entry(
            box, textvariable=self.url_var, bg="#232836", fg="white",
            insertbackground="white", relief=tk.FLAT, font=("Segoe UI", 10)
        )
        entry.pack(fill=tk.X, ipady=5, pady=(0, 8))

        btn_vlc = tk.Button(
            box,
            text="▶ Riproduci subito su VLC Media Player",
            bg="#374151", fg="white", activebackground="#4b5563", activeforeground="white",
            font=("Segoe UI", 9, "bold"), relief=tk.FLAT, cursor="hand2", pady=6,
            command=self.open_vlc
        )
        btn_vlc.pack(fill=tk.X)

        self.status_lbl = tk.Label(
            self.root, text="Tieni questa finestra aperta mentre guardi i canali dal browser.",
            bg="#12141a", fg="#94a3b8", font=("Segoe UI", 8)
        )
        self.status_lbl.pack(anchor="w", padx=18, pady=(8, 0))

    def open_browser(self):
        webbrowser.open(self.base_url)
        self.status_lbl.config(text=f"Aperta pagina web su {self.base_url}")

    def open_vlc(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Attenzione", "Inserisci un URL .m3u8 valido.")
            return
        try:
            msg = launch_vlc_stream(url)
            self.status_lbl.config(text=msg)
        except Exception as e:
            messagebox.showerror("Errore VLC", str(e))

def main():
    port = find_free_port(PROXY_PORT)
    server = ThreadingHTTPServer((PROXY_HOST, port), IPTVProxyHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    root = tk.Tk()
    app = LauncherApp(root, port)
    # Apre automaticamente la pagina web all'avvio
    root.after(400, app.open_browser)
    root.mainloop()
    server.shutdown()

if __name__ == "__main__":
    main()
