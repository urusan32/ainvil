// Test helpers installed into the Ainvil page as window.__t after every page load.
// They record what the user would see or get (toasts, downloads, confirm dialogs, errors) and simulate input that
// WebDriver can't drive in a headless browser (file pickers, drag and drop, paste, canvas strokes).
(() => {
  if (window.__t) return;
  const T = window.__t = {
    toasts: [], errors: [], confirms: [], confirmAnswer: true, downloads: [], pending: [], nextFiles: [], pickers: 0,
    seen: {},  // selector -> texts it has shown (watch())
  };

  // ---------- recorders ----------
  const toasts = document.querySelector('#toasts');
  for (const el of toasts.children) T.toasts.push({ text: el.textContent, kind: el.className.replace('toast', '').trim() });
  new MutationObserver((ms) => {
    for (const m of ms) for (const el of m.addedNodes) if (el.nodeType === 1) T.toasts.push({ text: el.textContent, kind: el.className.replace('toast', '').trim() });
  }).observe(toasts, { childList: true });
  window.addEventListener('error', (e) => T.errors.push(String(e.message || e.error)));
  window.addEventListener('unhandledrejection', (e) => T.errors.push('Unhandled rejection: ' + String(e.reason?.stack || e.reason)));
  window.confirm = (msg) => { T.confirms.push(msg); return T.confirmAnswer; };

  // Downloads: <a download> clicks are captured with their content instead of saving files.
  const origClick = HTMLAnchorElement.prototype.click;
  HTMLAnchorElement.prototype.click = function () {
    if (!this.hasAttribute('download')) return origClick.call(this);
    const rec = { name: this.download, href: this.href, type: '', size: 0, b64: null, text: null };
    T.downloads.push(rec);
    T.pending.push(fetch(this.href).then((r) => r.blob()).then(async (b) => {
      rec.type = b.type; rec.size = b.size;
      rec.b64 = await T.b64(b);
      if (/json|text/.test(b.type)) rec.text = await b.text();
    }).catch((e) => { rec.error = String(e); }));
  };
  // File pickers: a click on <input type=file> takes the queued files instead of opening a dialog.
  const origInputClick = HTMLInputElement.prototype.click;
  HTMLInputElement.prototype.click = function () {
    if (this.type !== 'file') return origInputClick.call(this);
    T.pickers++;
    const files = T.nextFiles.shift();
    if (files) setTimeout(() => T.setFiles(this, files), 0);
  };

  // Records every text the element shows (e.g. the gallery info during a run).
  T.watch = (sel) => {
    const el = document.querySelector(sel), list = T.seen[sel] = [el.textContent];
    new MutationObserver(() => { if (list[list.length - 1] !== el.textContent) list.push(el.textContent); })
      .observe(el, { childList: true, subtree: true, characterData: true, attributes: true });
  };

  // ---------- files ----------
  T.b64 = (blob) => new Promise((resolve) => {
    const r = new FileReader();
    r.onload = () => resolve(String(r.result).split(',')[1] || '');
    r.readAsDataURL(blob);
  });
  T.fromB64 = (b64, name, type) => {
    const bin = atob(b64), u8 = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
    return new File([u8], name, { type });
  };
  T.textFile = (text, name, type = 'application/json') => new File([text], name, { type });
  // spec: {w, h, name, fill, type, rects: [{x, y, w, h, color}], gradient}
  T.makeImage = async (spec) => {
    const c = document.createElement('canvas');
    c.width = spec.w; c.height = spec.h;
    const ctx = c.getContext('2d');
    if (spec.gradient) {
      const g = ctx.createLinearGradient(0, 0, spec.w, spec.h);
      g.addColorStop(0, '#203060'); g.addColorStop(1, '#e0c080');
      ctx.fillStyle = g;
    } else ctx.fillStyle = spec.fill || '#808080';
    ctx.fillRect(0, 0, spec.w, spec.h);
    for (const r of spec.rects || []) { ctx.fillStyle = r.color; ctx.fillRect(r.x, r.y, r.w, r.h); }
    const type = spec.type || 'image/png';
    const blob = await new Promise((res) => c.toBlob(res, type, 0.95));
    return new File([blob], spec.name || 'image.png', { type });
  };
  T.file = async (f) => (f instanceof File ? f : f.b64 != null ? T.fromB64(f.b64, f.name, f.type) : f.text != null ? T.textFile(f.text, f.name, f.type) : T.makeImage(f));
  T.files = (list) => Promise.all(list.map(T.file));

  // ---------- simulated input ----------
  T.setFiles = (input, files) => {
    const dt = new DataTransfer();
    for (const f of files) dt.items.add(f);
    input.files = dt.files;
    input.dispatchEvent(new Event('change', { bubbles: true }));
  };
  T.drop = (el, files, { text } = {}) => {
    const dt = new DataTransfer();
    for (const f of files || []) dt.items.add(f);
    if (text) dt.setData('text/plain', text);
    for (const type of ['dragenter', 'dragover', 'drop']) el.dispatchEvent(new DragEvent(type, { dataTransfer: dt, bubbles: true, cancelable: true }));
  };
  T.paste = (files) => {
    const e = new Event('paste', { bubbles: true, cancelable: true });
    Object.defineProperty(e, 'clipboardData', { value: { files, getData: () => '' } });
    document.dispatchEvent(e);
  };
  T.key = (key, opts = {}, target = document.activeElement || document.body) => {
    const o = { key, bubbles: true, cancelable: true, ...opts };
    target.dispatchEvent(new KeyboardEvent('keydown', o));
    target.dispatchEvent(new KeyboardEvent('keyup', o));
  };
  // Client coordinates of image pixel (x, y) on a canvas (or any element showing `w`×`h` pixels).
  T.client = (el, x, y, w = el.width, h = el.height) => {
    const r = el.getBoundingClientRect();
    return { clientX: r.left + (x / w) * r.width, clientY: r.top + (y / h) * r.height };
  };
  T.pointer = (el, type, pos, opts = {}) => el.dispatchEvent(new PointerEvent(type, {
    bubbles: true, cancelable: true, pointerId: 1, pointerType: 'mouse', isPrimary: true,
    button: type === 'pointermove' ? -1 : (opts.button ?? 0), buttons: type === 'pointerup' ? 0 : (opts.button === 1 ? 4 : 1), ...pos, ...opts,
  }));
  // A drag through image pixel points on a canvas: pointerdown, moves, pointerup.
  T.stroke = (el, pts, opts = {}) => {
    const p = pts.map(([x, y]) => T.client(el, x, y));
    T.pointer(el, 'pointerdown', p[0], opts);
    for (const q of p.slice(1)) T.pointer(el, 'pointermove', q, { ...opts, buttons: 1 });
    T.pointer(el, 'pointerup', p[p.length - 1], opts);
  };

  // ---------- pixels ----------
  T.imageOf = async (src) => {
    if (src instanceof HTMLCanvasElement) return src;
    const url = src instanceof Blob ? URL.createObjectURL(src) : src;
    const img = new Image();
    img.src = url;
    await img.decode();
    const c = document.createElement('canvas');
    c.width = img.naturalWidth; c.height = img.naturalHeight;
    c.getContext('2d').drawImage(img, 0, 0);
    return c;
  };
  T.pixel = async (src, x, y) => [...(await T.imageOf(src)).getContext('2d').getImageData(x, y, 1, 1).data];
  T.size = async (src) => { const c = await T.imageOf(src); return [c.width, c.height]; };
  // Largest per-channel difference between two images inside (or, with outside, outside) box b.
  T.diff = async (a, b, box, { outside = false } = {}) => {
    const ca = await T.imageOf(a), cb = await T.imageOf(b);
    const da = ca.getContext('2d').getImageData(0, 0, ca.width, ca.height).data;
    const db = cb.getContext('2d').getImageData(0, 0, cb.width, cb.height).data;
    let max = 0;
    for (let y = 0; y < ca.height; y++) for (let x = 0; x < ca.width; x++) {
      const inside = !box || (x >= box.x && y >= box.y && x < box.x + box.w && y < box.y + box.h);
      if (inside === outside) continue;
      const i = (y * ca.width + x) * 4;
      for (let k = 0; k < 3; k++) max = Math.max(max, Math.abs(da[i + k] - db[i + k]));
    }
    return max;
  };

  // ---------- DOM lookup ----------
  const norm = (s) => String(s).replace(/\s+/g, ' ').trim();
  const visible = (el) => !!el && el.getClientRects().length > 0 && getComputedStyle(el).visibility !== 'hidden' &&
    (!el.checkVisibility || el.checkVisibility({ contentVisibilityAuto: true, visibilityProperty: true }));
  T.visible = visible;
  const SCOPES = {
    'main': '#sec-main', 'the main section': '#sec-main', 'generation parameters': '#sec-params', 'custom parameters': '#sec-custom',
    'the output gallery': '#sec-gallery', 'output gallery': '#sec-gallery', 'input image': '#sec-input', 'the input image section': '#sec-input',
    'input parameters': '#sec-inparams', 'cads': '#sec-cads', 'the cads section': '#sec-cads', 'lora': '#sec-lora', 'the lora section': '#sec-lora',
    'the mask editor': '#maskEditor', 'the image editor': '#imageEditor', 'the history': '#historyDlg', 'the history dialog': '#historyDlg',
    'the image stash': '#stashDlg', 'the stash': '#stashDlg', 'the jobs dialog': '#jobsDlg', 'the viewer': '#viewer',
    'extras': '#tab-extras', 'the extras tab': '#tab-extras', 'the extras output': '#ex-gallery', 'configuration': '#tab-config',
    'the image column': '#sec-input .imgcol:nth-child(1)', 'the mask column': '#sec-input .imgcol:nth-child(2)',
    'the header': '.topbar', 'the layout bar': '#layoutBar', 'the page': 'body',
  };
  // The first text of a heading (summaries hold the name, then a .sub span with details).
  const headText = (h) => {
    const w = document.createTreeWalker(h, NodeFilter.SHOW_TEXT);
    for (let n = w.nextNode(); n; n = w.nextNode()) if (n.textContent.trim()) return norm(n.textContent);
    return '';
  };
  // "txt2img of Anima" = the txt2img section inside the Anima section.
  T.scope = (name, root = document) => {
    if (!name) return document.body;
    const of = name.lastIndexOf(' of ');
    if (of > 0) return T.scope(name.slice(0, of), T.scope(name.slice(of + 4), root));
    const key = name.toLowerCase();
    if (SCOPES[key] && root === document) return document.querySelector(SCOPES[key]);
    // A card, dialog or collapsible section by its heading.
    const bare = key.replace(/^the /, '').replace(/ (functional|custom) workflow$/, '').replace(/^(functional|custom) workflow /, '');
    const heads = [...root.querySelectorAll('h2, h3, summary')].filter((h) => [key, bare].includes(headText(h).toLowerCase()));
    const h = heads.find(visible) || heads[0];
    if (!h) throw new Error(`No section named "${name}"`);
    return h.closest('details') || h.closest('.card') || h.closest('.dialog') || h.parentElement;
  };
  T.norm = norm;
  // A button by its text (own text, without the section tools) or title.
  T.button = (text, scopeName, { any = false } = {}) => {
    const root = T.scope(scopeName);
    const own = (b) => norm([...b.childNodes].filter((n) => n.nodeType === 3 || !n.classList?.contains('sec-tag')).map((n) => n.textContent).join(''));
    const all = [...root.querySelectorAll('button, [role=tab]')].filter((b) => own(b) === text || (own(b) === '' && b.title === text));
    const vis = all.filter(visible);
    if (!all.length) throw new Error(`No button "${text}"${scopeName ? ' in ' + scopeName : ''}`);
    if (vis.length > 1) throw new Error(`${vis.length} visible buttons "${text}"${scopeName ? ' in ' + scopeName : ''}; name a section`);
    if (any) return vis[0] || all[0];
    if (!vis.length) throw new Error(`Button "${text}"${scopeName ? ' in ' + scopeName : ''} is not visible`);
    return vis[0];
  };
  T.click = (text, scopeName) => {
    const b = T.button(text, scopeName);
    if (b.disabled) throw new Error(`Button "${text}" is disabled`);
    b.click();
  };
  // A form control by its label text (the label's own text, before the control).
  T.field = (label, scopeName) => {
    const root = T.scope(scopeName);
    const want = label.toLowerCase();
    const ownText = (l) => norm([...l.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent).join(' ')).toLowerCase();
    const all = [...root.querySelectorAll('label')];
    let labels = all.filter((l) => ownText(l) === want);
    if (!labels.length) labels = all.filter((l) => { const own = ownText(l); return own.startsWith(want + ' ') || own.replace(/\s*\(.*\)$/, '') === want; });
    const control = (l) => l.htmlFor ? document.getElementById(l.htmlFor) : l.querySelector('input, select, textarea') ||
      // Labels next to their control (e.g. "Model" with the select in the following .searchsel)
      l.nextElementSibling?.querySelector?.('input, select, textarea') || l.parentElement.querySelector('select, input:not([type=checkbox])');
    const vis = [...new Set(labels.filter(visible).map(control).filter(Boolean))];
    if (vis.length > 1) throw new Error(`${vis.length} visible fields "${label}"${scopeName ? ' in ' + scopeName : ''}; name a section`);
    if (vis.length) return vis[0];
    for (const l of labels) { const c = control(l); if (c) return c; }
    const ph = [...root.querySelectorAll('input, textarea')].find((x) => (x.placeholder || '').toLowerCase() === want);
    if (ph) return ph;
    throw new Error(`No field "${label}"${scopeName ? ' in ' + scopeName : ''}`);
  };
  T.set = (label, value, scopeName) => {
    const el = typeof label === 'string' ? T.field(label, scopeName) : label;
    if (el.disabled) throw new Error(`Field "${label}" is disabled`);
    el.focus?.();
    if (el.type === 'checkbox') {
      el.checked = value === true || value === 'true' || value === 'on';
      el.dispatchEvent(new Event('change', { bubbles: true }));
    } else if (el.tagName === 'SELECT') {
      const o = [...el.options].find((x) => x.value === value) || [...el.options].find((x) => norm(x.textContent) === value) ||
        [...el.options].find((x) => x.value.endsWith('/' + value));
      if (!o) throw new Error(`"${value}" is not an option of "${label}" (options: ${[...el.options].map((x) => x.value).join(', ')})`);
      el.value = o.value;
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
    } else {
      el.value = value;
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
    }
    el.blur?.();
  };
  T.value = (label, scopeName) => {
    const el = typeof label === 'string' ? T.field(label, scopeName) : label;
    return el.type === 'checkbox' ? el.checked : el.value;
  };
  T.options = (el) => [...el.options].map((o) => norm(o.textContent));
  // Waits for fn() to be truthy; returns its value.
  T.until = async (fn, ms = 30000, step = 50) => {
    const end = Date.now() + ms;
    let v;
    for (;;) {
      try { v = await fn(); } catch (e) { v = undefined; }
      if (v) return v;
      if (Date.now() > end) return v;
      await new Promise((r) => setTimeout(r, step));
    }
  };
  T.settle = async () => { await Promise.all(T.pending); await new Promise((r) => setTimeout(r, 50)); };
})();

// Safety guard for the shared test server: every queued Generate prompt must contain "safe," in its text and save
// under ainvil-test/. A prompt that doesn't is refused before it reaches ComfyUI.
(() => {
  const api = (0, eval)('api');
  if (api.__guarded) return;
  const queue = api.queuePrompt;
  api.queuePrompt = function (prompt) {
    const nodes = Object.values(prompt);
    const texts = nodes.filter((n) => n.class_type === 'CLIPTextEncode').map((n) => n.inputs.text).filter((x) => typeof x === 'string');
    if (texts.length && !texts.some((x) => x.includes('safe,'))) return Promise.reject(new Error('TEST GUARD: prompt without "safe,"'));
    for (const n of nodes) {
      if (n.class_type === 'SaveImage' && !String(n.inputs.filename_prefix).startsWith('ainvil-test/')) {
        return Promise.reject(new Error('TEST GUARD: SaveImage outside ainvil-test/: ' + n.inputs.filename_prefix));
      }
    }
    return queue.call(this, prompt);
  };
  api.__guarded = true;
})();
