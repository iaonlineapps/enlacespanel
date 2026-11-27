// Panel de EnlacesPanel: JavaScript sin frameworks.
(() => {
const $ = id => document.getElementById(id);
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const BASE = location.origin + '/';
let me = null, info = null, pages = [], P = null, links = [], clicks = {}, tab = 'links';
let lastDeleted = null, toastT, previewT, saveT;

async function api(path, opts = {}) {
  const o = {method: opts.method || 'GET', headers: {'X-EnlacesPanel': '1'}, credentials: 'same-origin'};
  if (opts.body !== undefined) { o.headers['Content-Type'] = 'application/json'; o.body = JSON.stringify(opts.body); }
  const r = await fetch(path, o);
  let d = null; try { d = await r.json(); } catch (e) {}
  if (!r.ok) {
    if (r.status === 401 && path !== '/api/login') { showAuth(); }
    throw new Error(d && d.detail ? (typeof d.detail === 'string' ? d.detail : 'Datos no válidos') : 'Error ' + r.status);
  }
  return d;
}
function toast(msg, undo) {
  $('toastMsg').textContent = msg; $('undo').hidden = !undo;
  $('toast').classList.add('show'); clearTimeout(toastT);
  toastT = setTimeout(() => $('toast').classList.remove('show'), undo ? 5000 : 2200);
}
function refreshPreview(now) {
  clearTimeout(previewT);
  previewT = setTimeout(() => { if (P) $('screen').src = '/' + P.slug + '?vista=1&t=' + Date.now(); }, now ? 0 : 350);
}

// ---------- entrar ----------
let registering = false;
function showAuth(adding = false) {
  $('app').hidden = true; $('auth').hidden = false; $('accMenu').hidden = true;
  registering = !!(info && info.first_user) && !adding;
  setAuthMode();
  $('authCancel').hidden = !adding;
  if (adding) { $('uName').value = ''; $('uPass').value = ''; $('authLead').textContent = 'Añadir otra cuenta'; }
  paintAuthAccounts(adding);
}
// ---------- cambio rápido de usuario ----------
// El servidor recuerda las cuentas abiertas en este dispositivo (en una cookie que el
// JavaScript no puede leer) y deja pasar de una a otra sin volver a poner la contraseña.
async function getAccounts() { try { return (await api('/api/accounts')).accounts || []; } catch (e) { return []; } }
const accInitial = n => esc(String(n || '?')[0].toUpperCase());
const accRow = (a, forget) => `<div class="accrow"><button type="button" class="ghost accpick" data-user="${esc(a.username)}" translate="no"><span class="accav">${accInitial(a.username)}</span><span>${esc(a.username)}</span></button>` +
  (forget ? `<button type="button" class="ghost small accforget" data-forget="${esc(a.username)}" title="Quitar de este dispositivo" aria-label="Quitar de este dispositivo">✕</button>` : '') + `</div>`;
async function paintAuthAccounts(adding) {
  const list = adding || (info && info.first_user) ? [] : await getAccounts();
  $('authAccs').hidden = !list.length;
  $('authAccList').innerHTML = list.map(a => accRow(a, true)).join('');
}
async function switchAccount(username) {
  try { await api('/api/accounts/switch', {method: 'POST', body: {username}}); }
  catch (err) { showAuth(); $('authErr').textContent = err.message; $('uName').value = username; $('uPass').focus(); return; }
  location.reload();
}
$('authAccList').onclick = async e => {
  const f = e.target.closest('[data-forget]');
  if (f) { await api('/api/accounts/forget', {method: 'POST', body: {username: f.dataset.forget}}).catch(() => {}); return paintAuthAccounts(false); }
  const p = e.target.closest('[data-user]'); if (p) switchAccount(p.dataset.user);
};
$('authCancel').onclick = () => location.reload();
$('accBtn').onclick = async () => {
  const m = $('accMenu');
  if (!m.hidden) { m.hidden = true; $('accBtn').setAttribute('aria-expanded', 'false'); return; }
  const list = await getAccounts();
  $('accList').innerHTML = list.map(a => accRow(a, false)).join('');
  $('accSec').hidden = $('logoutAll').hidden = !list.length;
  m.hidden = false; $('accBtn').setAttribute('aria-expanded', 'true');
};
document.addEventListener('click', e => { if (!e.target.closest('.accwrap')) $('accMenu').hidden = true; });
$('accList').onclick = e => { const p = e.target.closest('[data-user]'); if (p) switchAccount(p.dataset.user); };
$('accAdd').onclick = () => showAuth(true);
$('logoutAll').onclick = async () => { await api('/api/logout', {method: 'POST', body: {all: true}}); location.reload(); };
function setAuthMode() {
  $('authBtn').textContent = registering ? 'Crear cuenta' : 'Entrar';
  $('authSwitch').textContent = registering ? 'Ya tengo cuenta' : 'Crear cuenta';
  $('authSwitch').hidden = !info.allow_register || info.first_user;
  $('acceptRow').hidden = !registering;
  $('uPass').autocomplete = registering ? 'new-password' : 'current-password';
  $('authLead').textContent = info.first_user
    ? 'Bienvenido. Crea la primera cuenta: será la del administrador.'
    : 'Tu página de enlaces, en tu propio servidor.';
  $('authErr').textContent = '';
}
$('authSwitch').onclick = () => { registering = !registering; setAuthMode(); };
$('authForm').onsubmit = async e => {
  e.preventDefault();
  const body = {username: $('uName').value.trim(), password: $('uPass').value};
  try {
    if (registering) {
      const r = await api('/api/register', {method: 'POST', body: {...body, accept: $('uAccept').checked}});
      if (r.recovery_code) await recoveryCodeDialog(r.recovery_code, body.username);
      if (!r.approved) { registering = false; setAuthMode(); $('authErr').textContent = 'Cuenta creada. El administrador tiene que aprobarla antes de que puedas entrar.'; return; }
    }
    const adding = !$('authCancel').hidden;
    const lr = await api('/api/login', {method: 'POST', body});
    $('uPass').value = '';
    if (lr && lr.recovery_code) await recoveryCodeDialog(lr.recovery_code, body.username);
    if (adding) { location.reload(); return; }
    start();
  } catch (err) { $('authErr').textContent = err.message; }
};
// ---------- código de recuperación ----------
// Cada cuenta tiene un código que se enseña una sola vez (al crearla, o al entrar la primera vez
// si la cuenta es de antes). Con él se ve el usuario y se pone una contraseña nueva, aunque se
// hayan olvidado los dos. No hace falta servidor de correo.
// abre la ventana y espera a que se cierre; sticky = no se cierra con Escape (que no se pierda el código sin verlo)
function recDialog(html, sticky, onOpen) {
  const d = $('recDlg');
  return new Promise(res => {
    d.innerHTML = html;
    d.oncancel = e => { if (sticky) e.preventDefault(); };
    d.onclose = () => res(d.returnValue);
    d.returnValue = '';
    onOpen && onOpen(d);
    d.showModal();
  });
}
function recoveryCodeDialog(code, user, other) {
  const name = t('Código de recuperación de EnlacesPanel');
  const text = name + (user ? ` (${t('usuario')} ${user})` : '') + ': ' + code + '\n' + location.origin + '\n' +
    t('Sirve para entrar si olvidas el usuario o la contraseña: «¿Has olvidado tu usuario o contraseña?».');
  const open = u => window.open(u, '_blank', 'noopener');
  const html = `<h2 id="recTitle">${other ? `Código de recuperación de <span translate="no">${esc(user)}</span>` : 'Tu código de recuperación'}</h2>
    ${user && !other ? `<p>Tu usuario es <b translate="no">${esc(user)}</b></p>` : ''}
    <p class="hint">${other ? 'Pásaselo junto con su contraseña. Con este código podrá entrar si olvida su usuario o su contraseña. Solo se enseña ahora.'
      : 'Si algún día olvidas tu usuario o tu contraseña, con este código podrás entrar otra vez. Apúntalo o hazle una foto y guárdalo en un sitio seguro: solo se enseña ahora.'}</p>
    <div class="rec-code" translate="no">${esc(code)}</div>
    <p class="hint">Guárdalo donde quieras: cópialo, mándatelo por WhatsApp o Telegram (a ti mismo o a «Mensajes guardados») o bájalo como archivo.</p>
    <div class="row rec-send">
      <button type="button" class="ghost small" data-r="copy">📋 Copiar</button>
      <button type="button" class="small rec-wa" data-r="wa">WhatsApp</button>
      <button type="button" class="small rec-tg" data-r="tg">Telegram</button>
      <button type="button" class="ghost small" data-r="mail">✉️ Correo</button>
      ${window.EnlacesPanelAndroid ? '' : '<button type="button" class="ghost small" data-r="file">⬇️ Bajar archivo</button>'}
      ${navigator.share || window.EnlacesPanelAndroid ? '<button type="button" class="ghost small" data-r="more">Otras apps</button>' : ''}
    </div>
    <form method="dialog" class="row" style="justify-content:flex-end;margin-top:14px"><button value="ok">Ya lo he guardado</button></form>`;
  return recDialog(html, true, d => d.querySelector('.rec-send').onclick = async e => {
    const b = e.target.closest('[data-r]'); if (!b) return;
    const a = b.dataset.r;
    if (a === 'copy') { try { await navigator.clipboard.writeText(text); } catch (er) { const x = document.createElement('textarea'); x.value = text; d.appendChild(x); x.select(); try { document.execCommand('copy'); } catch (e2) {} x.remove(); } toast('Copiado'); }
    if (a === 'wa') open('https://wa.me/?text=' + encodeURIComponent(text));
    if (a === 'tg') open('https://t.me/share/url?url=' + encodeURIComponent(location.origin) + '&text=' + encodeURIComponent(text.replace('\n' + location.origin, '')));
    if (a === 'mail') location.href = 'mailto:?subject=' + encodeURIComponent(name) + '&body=' + encodeURIComponent(text);
    if (a === 'file') {
      const l = document.createElement('a');
      l.href = URL.createObjectURL(new Blob([text.replace(/\n/g, '\r\n') + '\r\n'], {type: 'text/plain'}));
      l.download = 'EnlacesPanel-' + t('codigo-recuperacion') + (user ? '-' + user : '') + '.txt';
      document.body.appendChild(l); l.click(); l.remove(); setTimeout(() => URL.revokeObjectURL(l.href), 5000);
    }
    if (a === 'more') { if (window.EnlacesPanelAndroid) window.EnlacesPanelAndroid.share(text, name); else navigator.share({title: name, text}).catch(() => {}); }
  });
}
$('authForgot').onclick = async () => {
  let res = null;
  await recDialog(`<h2 id="recTitle">Recuperar mi cuenta</h2>
    <p class="hint">Escribe tu código de recuperación (te lo enseñamos al crear la cuenta) y elige una contraseña nueva. Si no tienes el código, pide al administrador que te ponga una contraseña nueva.</p>
    <form id="fgForm">
      <label for="fgCode">Código de recuperación</label><input id="fgCode" placeholder="XXXX-XXXX-XXXX" autocomplete="off" autocapitalize="characters" spellcheck="false" maxlength="40" required>
      <label for="fgUser">Usuario (si no lo recuerdas, déjalo vacío)</label><input id="fgUser" autocomplete="username" autocapitalize="off" maxlength="64">
      <label for="fgP1">Contraseña nueva <span class="opt">(mínimo 8 caracteres)</span></label><input id="fgP1" type="password" autocomplete="new-password" required>
      <label for="fgP2">Repite la contraseña nueva</label><input id="fgP2" type="password" autocomplete="new-password" required>
      <div class="err" id="fgErr" role="alert"></div>
      <div class="row" style="justify-content:flex-end"><button type="button" class="ghost" id="fgCancel">Cancelar</button><button type="submit">Recuperar</button></div>
    </form>`, false, d => {
    d.querySelector('#fgCancel').onclick = () => d.close();
    d.querySelector('#fgForm').onsubmit = async e => {
      e.preventDefault(); const m = $('fgErr'); m.textContent = '';
      if ($('fgP1').value !== $('fgP2').value) { m.textContent = 'Las contraseñas no coinciden'; return; }
      try { res = await api('/api/recover', {method: 'POST', body: {code: $('fgCode').value, username: $('fgUser').value.trim(), password: $('fgP1').value}}); }
      catch (err) { m.textContent = err.message; return; }
      d.close();
    };
  });
  if (!res) return;
  await recoveryCodeDialog(res.recovery_code, res.username);
  registering = false; setAuthMode();
  $('uName').value = res.username; $('uPass').value = ''; $('uPass').focus();
  $('authErr').textContent = res.status === 'approved' ? 'Contraseña cambiada. Ya puedes entrar con la nueva.'
    : res.status === 'pending' ? 'Contraseña cambiada, pero tu cuenta aún está pendiente de aprobación' : 'Contraseña cambiada, pero tu cuenta está desactivada';
};
$('recNew').onclick = async () => {
  let res = null;
  await recDialog(`<h2 id="recTitle">Código de recuperación</h2>
    <p class="hint">Te damos un código nuevo y el anterior deja de valer. Sirve para entrar si olvidas tu usuario o tu contraseña.</p>
    <form id="rcForm"><label for="rcPw">Tu contraseña actual</label><input id="rcPw" type="password" autocomplete="current-password" required>
      <div class="err" id="rcErr" role="alert"></div>
      <div class="row" style="justify-content:flex-end"><button type="button" class="ghost" id="rcCancel">Cancelar</button><button type="submit">Crear código nuevo</button></div></form>`, false, d => {
    d.querySelector('#rcCancel').onclick = () => d.close();
    d.querySelector('#rcForm').onsubmit = async e => {
      e.preventDefault();
      try { res = await api('/api/recovery', {method: 'POST', body: {password: $('rcPw').value}}); } catch (err) { $('rcErr').textContent = err.message; return; }
      d.close();
    };
  });
  if (res) recoveryCodeDialog(res.recovery_code, me.username);
};
$('logout').onclick = async () => { await api('/api/logout', {method: 'POST'}); location.reload(); };

// ---------- arranque ----------
async function start() {
  info = await api('/api/me');
  me = info.user;
  if (!me) return showAuth();
  $('auth').hidden = true; $('app').hidden = false;
  $('usersTab').hidden = !me.is_admin; $('homeBox').hidden = !me.is_admin; $('serverBox').hidden = !me.is_admin;
  // Puerto e IP de la Raspberry para las guías de Pangolin y del proxy (si entras por la IP de casa)
  const port = location.port || '8092';
  document.querySelectorAll('.piPort').forEach(e => e.textContent = port);
  if (/^(10|172\.(1[6-9]|2\d|3[01])|192\.168)\./.test(location.hostname)) document.querySelectorAll('.piIp').forEach(e => e.textContent = location.hostname);
  $('meName').textContent = me.username; $('accName').textContent = me.username; $('accAv').textContent = String(me.username || '?')[0].toUpperCase(); $('ver').textContent = info.version;
  $('maxPages').textContent = info.max_pages; $('obBase').textContent = BASE; $('sBase').textContent = BASE;
  $('homeUrl').textContent = BASE;
  buildStatic();
  pages = await api('/api/pages');
  if (!pages.length) {
    // La primera página se crea sola con tu usuario; la dirección y el resto se cambian en Ajustes
    pages.push(await api('/api/pages', {method: 'POST', body: {auto: true}}));
    toast('Tu página ya está creada. Empieza añadiendo enlaces.');
  }
  paintVersions(); newsIfUpdated();
  const want = Number(localStorage.getItem('enlacespanel-page'));
  await openPage((pages.find(p => p.id === want) || pages[0]).id);
}
$('obForm').onsubmit = async e => {
  e.preventDefault();
  try {
    const p = await api('/api/pages', {method: 'POST', body: {slug: $('obSlug').value, name: $('obName').value}});
    pages.push(p); $('onboard').hidden = true; tab = 'links'; await openPage(p.id); toast('Página creada');
  } catch (err) { $('obErr').textContent = err.message; }
};
async function openPage(id) {
  const d = await api('/api/pages/' + id);
  links = d.links; delete d.links; P = d;
  localStorage.setItem('enlacespanel-page', id);
  $('editor').hidden = false; $('tabs').hidden = false; $('pageSel').hidden = false; $('openPage').hidden = false;
  $('pageSel').innerHTML = pages.map(p => `<option value="${p.id}" ${p.id === id ? 'selected' : ''}>/${esc(p.slug)}</option>`).join('');
  fillPage(); await loadClicks(); renderList(); refreshPreview(true); showTab(tab);
}
$('pageSel').onchange = e => openPage(Number(e.target.value));
const pageUrl = () => P.url || BASE + P.slug;
function fillPage() {
  $('pageUrl').textContent = pageUrl();
  $('sUrl').textContent = pageUrl(); $('sUrl').href = pageUrl();
  $('sDomain').value = P.domain || '';
  const srv = (!P.domain && P.url) ? P.url.slice(0, P.url.length - P.slug.length) : BASE;
  $('sBase').textContent = srv; $('obBase').textContent = srv;
  $('fName').value = P.name; $('fBio').value = P.bio; $('fLegal').value = P.legal; $('bioCount').textContent = P.bio.length;
  $('sSlug').value = P.slug; $('sPub').checked = P.published;
  renderThemes(); renderSocials(); renderQr(); paintPageLang();
  if (me.is_admin) api('/api/admin/settings').then(s => {
    $('sHome').checked = s.home === P.slug; $('sPublic').value = s.public_url || ''; $('sReg').checked = s.allow_register;
  });
}
async function savePage(fields, msg) {
  try {
    P = await api('/api/pages/' + P.id, {method: 'PUT', body: fields});
    const i = pages.findIndex(p => p.id === P.id); pages[i] = P;
    refreshPreview(); if (msg) toast(msg);
    return true;
  } catch (err) { toast(err.message); return false; }
}

// ---------- pestañas ----------
document.querySelectorAll('#tabs button').forEach(b => b.onclick = () => showTab(b.dataset.tab));
function showTab(t) {
  tab = t;
  document.querySelectorAll('#tabs button').forEach(b => b.classList.toggle('sel', b.dataset.tab === t));
  document.querySelectorAll('[data-pane]').forEach(p => p.hidden = p.dataset.pane !== t);
  if (t === 'stats') loadStats();
  if (t === 'users') loadUsers();
  setView('edit');
}
const setView = v => { document.body.dataset.view = v; $('tView').className = v === 'view' ? 'on' : 'ghost'; $('tEdit').className = v === 'edit' ? 'on' : 'ghost'; };
$('tView').onclick = () => { setView('view'); refreshPreview(true); };
$('tEdit').onclick = () => setView('edit');

// ---------- enlaces ----------
async function loadClicks() {
  try { const s = await api(`/api/pages/${P.id}/stats?days=30`); clicks = Object.fromEntries(s.links.map(l => [l.id, l.clicks])); }
  catch (e) { clicks = {}; }
}
const fmtDate = t => t ? new Date(t * 1000).toLocaleString(LANG === 'en' ? 'en-GB' : 'es-ES', {dateStyle: 'short', timeStyle: 'short'}) : '';
const toLocalInput = t => { if (!t) return ''; const d = new Date(t * 1000); d.setMinutes(d.getMinutes() - d.getTimezoneOffset()); return d.toISOString().slice(0, 16); };
const fromLocalInput = v => v ? Math.round(new Date(v).getTime() / 1000) : null;
let editing = null;
const icon = l => l.image ? `<img src="${esc(l.image)}" alt="">` : (l.emoji ? esc(l.emoji) : '');
// Recorta la foto en cuadrado y la reduce antes de subirla
function squareImage(file, S) {
  return new Promise((ok, ko) => {
    const img = new Image();
    img.onload = () => {
      const c = document.createElement('canvas'); c.width = c.height = S;
      const k = Math.max(S / img.width, S / img.height), w = img.width * k, h = img.height * k;
      c.getContext('2d').drawImage(img, (S - w) / 2, (S - h) / 2, w, h);
      URL.revokeObjectURL(img.src);
      let d = c.toDataURL('image/webp', .9);
      if (!d.startsWith('data:image/webp')) d = c.toDataURL('image/png');
      ok(d);
    };
    img.onerror = () => ko(new Error('Esa imagen no se puede leer'));
    img.src = URL.createObjectURL(file);
  });
}
let addImg = null;
$('aImg').onchange = async e => {
  const f = e.target.files[0]; if (!f) return;
  try { addImg = await squareImage(f, 160); $('aIcPrev').innerHTML = `<img src="${addImg}" alt="">`; $('aEmoji').value = ''; $('aIcClear').hidden = false; }
  catch (err) { toast(err.message); }
};
$('aEmoji').oninput = e => { if (e.target.value) { addImg = null; $('aImg').value = ''; } $('aIcPrev').textContent = e.target.value; $('aIcClear').hidden = !e.target.value; };
$('aIcClear').onclick = () => { addImg = null; $('aImg').value = ''; $('aEmoji').value = ''; $('aIcPrev').textContent = ''; $('aIcClear').hidden = true; };
function renderList() {
  const now = Date.now() / 1000;
  $('list').innerHTML = links.length ? links.map((l, i) => {
    if (editing === l.id) return `<li class="edit" data-id="${l.id}">
      <label>Título</label><input id="eT" value="${esc(l.title)}" maxlength="80">
      ${l.kind === 'link' ? `<label>Dirección</label><input id="eU" value="${esc(l.url)}" autocapitalize="off">
      <label>Icono del botón <span class="opt">(opcional)</span></label>
      <div class="icpick"><span class="icprev" id="eIcPrev" aria-hidden="true">${icon(l)}</span>
       <label class="btn ghost small filebtn">${l.image ? 'Cambiar foto o logo' : 'Subir foto o logo'}<input type="file" id="eImg" accept="image/png,image/jpeg,image/webp"></label>
       <span class="hint">o un emoji</span><input id="eE" value="${l.image ? '' : esc(l.emoji)}" maxlength="8" aria-label="Emoji" style="max-width:90px">
       <button type="button" class="ghost small" data-a="noimg" ${l.image || l.emoji ? '' : 'hidden'}>Quitar icono</button></div>
      <label class="inline"><input type="checkbox" id="eH" ${l.highlight ? 'checked' : ''}> Destacar (late suavemente para llamar la atención)</label>
      <label class="inline sw"><input type="checkbox" id="eP" ${l.start_at || l.end_at ? 'checked' : ''}> <span>Programar fechas <span class="opt">(si lo dejas apagado, el enlace se ve siempre y no caduca)</span></span></label>
      <div class="row" id="eDates" ${l.start_at || l.end_at ? '' : 'hidden'}><label style="flex:1">Se muestra desde <span class="opt">(vacío = ya)</span><input type="datetime-local" id="eS" value="${toLocalInput(l.start_at)}"></label>
      <label style="flex:1">Caduca el <span class="opt">(vacío = nunca)</span><input type="datetime-local" id="eX" value="${toLocalInput(l.end_at)}"></label></div>` : ''}
      <div class="err" id="eErr"></div>
      <div class="row"><button data-a="ok">Guardar</button><button class="ghost" data-a="cancel">Cancelar</button></div></li>`;
    const sched = (l.start_at && l.start_at > now) ? `<span class="tag">desde ${fmtDate(l.start_at)}</span>`
      : (l.end_at && l.end_at <= now) ? '<span class="tag">caducado</span>'
      : l.end_at ? `<span class="tag">hasta ${fmtDate(l.end_at)}</span>` : '';
    return `<li draggable="true" data-id="${l.id}" class="${l.enabled ? '' : 'off'} ${l.kind === 'header' ? 'hdr' : ''}">
      <span class="grip" title="Arrastra para ordenar" aria-hidden="true">⠿</span>
      <div><div class="t">${l.kind === 'link' && icon(l) ? `<span class="icprev sm" aria-hidden="true">${icon(l)}</span>` : ''}<span translate="no">${esc(l.title)}</span>${l.highlight ? '<span class="tag">destacado</span>' : ''}${sched}</div>
      <div class="u">${l.kind === 'header' ? 'Título de sección' : `<span translate="no">${esc(l.url)}</span>`}</div></div>
      <div class="c">${l.kind === 'link' ? `${clicks[l.id] || 0}<small>clics</small>` : ''}</div>
      <div class="acts">
       <button class="ghost small" data-a="up" ${i ? '' : 'disabled'} aria-label="Subir">↑</button>
       <button class="ghost small" data-a="down" ${i < links.length - 1 ? '' : 'disabled'} aria-label="Bajar">↓</button>
       <button class="ghost small" data-a="toggle">${l.enabled ? 'Ocultar' : 'Mostrar'}</button>
       <button class="ghost small" data-a="edit">Editar</button>
       <button class="ghost small" data-a="del">Borrar</button>
      </div></li>`;
  }).join('') : '<li class="empty">No tienes enlaces. Añade el primero arriba.</li>';
}
$('addForm').onsubmit = async e => {
  e.preventDefault();
  try {
    let l = await api(`/api/pages/${P.id}/links`, {method: 'POST', body: {title: $('aTitle').value, url: $('aUrl').value, emoji: addImg ? '' : $('aEmoji').value}});
    if (addImg) { try { l = await api(`/api/links/${l.id}/image`, {method: 'POST', body: {data: addImg}}); } catch (err) { toast(err.message); } }
    links.push(l); $('aTitle').value = $('aUrl').value = ''; $('aIcClear').onclick(); $('aErr').textContent = '';
    renderList(); refreshPreview(); toast('Enlace añadido');
  } catch (err) { $('aErr').textContent = err.message; }
};
$('addHeader').onclick = async () => {
  const title = $('aTitle').value.trim() || 'Sección';
  try {
    const l = await api(`/api/pages/${P.id}/links`, {method: 'POST', body: {kind: 'header', title}});
    links.push(l); $('aTitle').value = ''; renderList(); refreshPreview(); toast('Título añadido');
  } catch (err) { $('aErr').textContent = err.message; }
};
async function saveOrder() {
  await api(`/api/pages/${P.id}/order`, {method: 'POST', body: {ids: links.map(l => l.id)}});
  renderList(); refreshPreview();
}
$('list').onclick = async e => {
  const b = e.target.closest('button'); if (!b) return;
  const li = b.closest('li'), id = Number(li.dataset.id), i = links.findIndex(l => l.id === id), a = b.dataset.a, l = links[i];
  try {
    if (a === 'up' || a === 'down') { const j = i + (a === 'up' ? -1 : 1); [links[i], links[j]] = [links[j], links[i]]; return saveOrder(); }
    if (a === 'edit') { editing = id; renderList(); $('eT').focus(); return; }
    if (a === 'cancel') { editing = null; return renderList(); }
    if (a === 'toggle') { links[i] = await api('/api/links/' + id, {method: 'PUT', body: {enabled: !l.enabled}}); renderList(); refreshPreview(); return; }
    if (a === 'noimg') {
      if (l.image) links[i] = await api(`/api/links/${id}/image`, {method: 'POST', body: {data: ''}});
      $('eE').value = ''; links[i].emoji = ''; $('eIcPrev').textContent = ''; b.hidden = true; refreshPreview(); return;
    }
    if (a === 'ok') {
      const body = {title: $('eT').value}, prog = $('eP') && $('eP').checked;
      if (l.kind === 'link') Object.assign(body, {url: $('eU').value, emoji: $('eE').value, highlight: $('eH').checked,
        start_at: prog ? fromLocalInput($('eS').value) : null, end_at: prog ? fromLocalInput($('eX').value) : null});
      if (body.emoji && l.image) await api(`/api/links/${id}/image`, {method: 'POST', body: {data: ''}});
      try { links[i] = await api('/api/links/' + id, {method: 'PUT', body}); }
      catch (err) { $('eErr').textContent = err.message; return; }
      editing = null; renderList(); refreshPreview(); toast('Guardado'); return;
    }
    if (a === 'del') {
      await api('/api/links/' + id, {method: 'DELETE'});
      lastDeleted = {l, i}; links.splice(i, 1); renderList(); refreshPreview(); toast('Enlace borrado', true);
    }
  } catch (err) { toast(err.message); }
};
$('list').onchange = async e => {
  if (e.target.id === 'eP') { $('eDates').hidden = !e.target.checked; return; }
  if (e.target.id !== 'eImg' || !e.target.files[0]) return;
  const id = Number(e.target.closest('li').dataset.id), i = links.findIndex(l => l.id === id);
  try {
    const data = await squareImage(e.target.files[0], 160);
    links[i] = await api(`/api/links/${id}/image`, {method: 'POST', body: {data}});
    $('eIcPrev').innerHTML = icon(links[i]); $('eE').value = '';
    const nb = e.target.closest('li').querySelector('[data-a=noimg]'); if (nb) nb.hidden = false;
    refreshPreview(); toast('Imagen puesta');
  } catch (err) { toast(err.message); }
};
$('undo').onclick = async () => {
  if (!lastDeleted) return;
  const {l, i} = lastDeleted; lastDeleted = null;
  const n = await api(`/api/pages/${P.id}/links`, {method: 'POST', body: l});
  links.splice(i, 0, n); await saveOrder(); toast('Recuperado');
};
// arrastrar y soltar (ordenador)
let dragId = null;
$('list').addEventListener('dragstart', e => { const li = e.target.closest('li[data-id]'); if (!li) return; dragId = Number(li.dataset.id); li.classList.add('drag'); e.dataTransfer.effectAllowed = 'move'; });
$('list').addEventListener('dragend', () => { dragId = null; document.querySelectorAll('#list li').forEach(li => li.classList.remove('drag', 'over')); });
$('list').addEventListener('dragover', e => { const li = e.target.closest('li[data-id]'); if (!li || dragId === null) return; e.preventDefault(); document.querySelectorAll('#list li').forEach(x => x.classList.toggle('over', x === li)); });
$('list').addEventListener('drop', e => {
  const li = e.target.closest('li[data-id]'); if (!li || dragId === null) return; e.preventDefault();
  const to = Number(li.dataset.id); if (to === dragId) return;
  const from = links.findIndex(l => l.id === dragId), [m] = links.splice(from, 1);
  links.splice(links.findIndex(l => l.id === to), 0, m); saveOrder();
});

// ---------- perfil ----------
const debounceSave = (fields) => { clearTimeout(saveT); saveT = setTimeout(() => savePage(fields, 'Guardado'), 600); };
$('fName').oninput = e => debounceSave({name: e.target.value});
$('fBio').oninput = e => { $('bioCount').textContent = e.target.value.length; debounceSave({bio: e.target.value}); };
$('fLegal').oninput = e => debounceSave({legal: e.target.value});
$('fFoto').onchange = async e => {
  const file = e.target.files[0]; if (!file) return;
  try {
    const data = await squareImage(file, 400);
    const r = await api(`/api/pages/${P.id}/avatar`, {method: 'POST', body: {data}}); P.avatar = r.avatar; refreshPreview(true); toast('Foto actualizada');
  } catch (err) { toast(err.message); }
};
$('noFoto').onclick = async () => { await api(`/api/pages/${P.id}/avatar`, {method: 'POST', body: {data: ''}}); $('fFoto').value = ''; refreshPreview(true); toast('Foto quitada'); };

// ---------- diseño ----------
const COLOR_NAMES = {bg: 'Fondo', text: 'Texto', card: 'Botones', cardText: 'Texto de botones', accent: 'Detalles'};
const BUTTONS = {redondo: 'Redondeados', pastilla: 'Pastilla', recto: 'Rectos', borde: 'Solo borde'};
function buildStatic() {
  $('period').innerHTML = [[7, '7 días'], [30, '30 días'], [90, '90 días'], [365, '1 año']].map(([d, n]) =>
    `<button class="ghost small" data-d="${d}">${n}</button>`).join('');
}
function renderThemes() {
  const T = info.themes;
  $('themes').innerHTML = Object.entries(T).map(([id, t]) =>
    `<button class="th ${id === P.theme ? 'sel' : ''}" data-th="${id}" style="background:${t.bg};color:${t.text}" aria-pressed="${id === P.theme}">${esc(t.n)}</button>`).join('')
    + `<button class="th ${P.theme === 'propio' ? 'sel' : ''}" data-th="propio" style="background:conic-gradient(#e4002b,#f97316,#14532d,#38bdf8,#7c3aed,#e4002b);text-shadow:0 1px 2px #000" aria-pressed="${P.theme === 'propio'}">Propio</button>`;
  $('customBox').hidden = P.theme !== 'propio';
  const st = P.style || {}, def = {bg: '#ffffff', text: '#111111', card: '#111111', cardText: '#ffffff', accent: '#e4002b'};
  $('colors').innerHTML = Object.entries(COLOR_NAMES).map(([k, n]) =>
    `<label><input type="color" data-c="${k}" value="${esc(st[k] || def[k])}"> ${n}</label>`).join('');
  $('buttons').innerHTML = Object.entries(BUTTONS).map(([k, n]) =>
    `<button class="${(st.button || 'redondo') === k ? 'on' : 'ghost'} small" data-b="${k}">${n}</button>`).join('');
  $('anims').innerHTML = Object.entries(info.anims).map(([k, n]) =>
    `<button class="${(st.anim || 'suave') === k ? 'on' : 'ghost'} small" data-an="${k}">${n}</button>`).join('');
  $('socpos').innerHTML = [['arriba', 'Debajo de la bio'], ['abajo', 'Al final de la página']].map(([k, n]) =>
    `<button class="${(st.soc || 'abajo') === k ? 'on' : 'ghost'} small" data-sp="${k}">${n}</button>`).join('');
}
$('anims').onclick = async e => { const b = e.target.closest('[data-an]'); if (!b) return; if (await savePage({style: {...(P.style || {}), anim: b.dataset.an}})) renderThemes(); };
$('socpos').onclick = async e => { const b = e.target.closest('[data-sp]'); if (!b) return; if (await savePage({style: {...(P.style || {}), soc: b.dataset.sp}})) renderThemes(); };
$('themes').onclick = async e => { const b = e.target.closest('[data-th]'); if (!b) return; if (await savePage({theme: b.dataset.th})) renderThemes(); };
$('colors').oninput = e => {
  const c = e.target.dataset.c; if (!c) return;
  const style = {...(P.style || {}), [c]: e.target.value};
  P.style = style; clearTimeout(saveT); saveT = setTimeout(() => savePage({style}), 300);
};
$('buttons').onclick = async e => { const b = e.target.closest('[data-b]'); if (!b) return; if (await savePage({style: {...(P.style || {}), button: b.dataset.b}})) renderThemes(); };

// ---------- redes ----------
let socials = [];
const SOC_PH = {whatsapp: 'Tu número: +34 600 123 456', telegram: 'Tu usuario: @tunombre', email: 'tu@correo.es', phone: '+34 600 123 456',
  instagram: '@tunombre o https://…', tiktok: '@tunombre o https://…', youtube: '@tucanal o https://…', x: '@tunombre o https://…'};
function renderSocials() {
  socials = (P.socials || []).map(s => ({...s}));
  drawSocials();
}
function drawSocials() {
  const opts = Object.entries(info.socials);
  $('socList').innerHTML = socials.length ? socials.map((s, i) => `<div class="row" style="margin:8px 0" data-i="${i}">
    <select data-k="net" aria-label="Red" style="max-width:150px;flex:none">${opts.map(([k, n]) => `<option value="${k}" ${k === s.net ? 'selected' : ''}>${n}</option>`).join('')}</select>
    <input data-k="url" value="${esc(s.url)}" placeholder="${SOC_PH[s.net] || 'https://…'}" autocapitalize="off" aria-label="Dirección">
    <button type="button" class="ghost small" data-del="${i}" aria-label="Quitar">✕</button></div>`).join('')
    : '<p class="empty">Aún no has puesto redes.</p>';
}
$('socList').oninput = e => { const row = e.target.closest('[data-i]'); if (!row) return; socials[row.dataset.i][e.target.dataset.k] = e.target.value; if (e.target.dataset.k === 'net') drawSocials(); };
$('socList').onclick = e => { const b = e.target.closest('[data-del]'); if (b) { socials.splice(Number(b.dataset.del), 1); drawSocials(); } };
$('socAdd').onclick = () => { socials.push({net: 'instagram', url: ''}); drawSocials(); };
$('socSave').onclick = async () => {
  $('socErr').textContent = '';
  try { P = await api('/api/pages/' + P.id, {method: 'PUT', body: {socials: socials.filter(s => s.url.trim())}}); renderSocials(); refreshPreview(); toast('Redes guardadas'); }
  catch (err) { $('socErr').textContent = err.message; }
};

// ---------- estadísticas ----------
let days = 30;
$('period').onclick = e => { const b = e.target.closest('[data-d]'); if (b) { days = Number(b.dataset.d); loadStats(); } };
async function loadStats() {
  document.querySelectorAll('#period button').forEach(b => b.className = (Number(b.dataset.d) === days ? 'on' : 'ghost') + ' small');
  const s = await api(`/api/pages/${P.id}/stats?days=${days}`);
  $('sViews').textContent = s.views.toLocaleString('es-ES'); $('sClicks').textContent = s.clicks.toLocaleString('es-ES');
  $('sCtr').textContent = (s.views ? Math.round(s.clicks / s.views * 100) : 0) + ' %';
  const W = 600, H = 180, pad = 22, n = s.days.length, max = Math.max(1, ...s.days.map(d => Math.max(d.views, d.clicks)));
  const bw = (W - pad) / n, sc = v => (H - pad) * v / max;
  let g = `<line x1="${pad}" y1="${H - pad}" x2="${W}" y2="${H - pad}" stroke="currentColor" opacity=".25"/>
    <text x="0" y="12" font-size="11" fill="currentColor" opacity=".6">${max}</text>`;
  s.days.forEach((d, i) => {
    const x = pad + i * bw, w = Math.max(1, bw * .42);
    g += `<rect x="${x}" y="${H - pad - sc(d.views)}" width="${w}" height="${sc(d.views)}" fill="currentColor" opacity=".85"><title>${d.day}: ${d.views} visitas</title></rect>
      <rect x="${x + w}" y="${H - pad - sc(d.clicks)}" width="${w}" height="${sc(d.clicks)}" fill="#e4002b"><title>${d.day}: ${d.clicks} clics</title></rect>`;
  });
  [0, n - 1].forEach(i => { const d = s.days[i]; g += `<text x="${i ? W : pad}" y="${H - 4}" font-size="11" fill="currentColor" opacity=".6" text-anchor="${i ? 'end' : 'start'}">${d.day.slice(8)}/${d.day.slice(5, 7)}</text>`; });
  $('chart').innerHTML = g;
  $('sLinks').innerHTML = s.links.length ? s.links.sort((a, b) => b.clicks - a.clicks).map(l => `<tr><td translate="no">${esc(l.title)}</td><td class="n">${l.clicks}</td></tr>`).join('')
    : '<tr><td colspan="2" class="hint">Todavía no hay enlaces.</td></tr>';
}

// ---------- QR ----------
function renderQr() {
  const q = `color=${encodeURIComponent($('qrDark').value)}&fondo=${encodeURIComponent($('qrLight').value)}`;
  $('qrImg').src = `/qr/${P.slug}.svg?${q}`;
  $('qrPng').href = `/qr/${P.slug}.png?${q}`; $('qrPng').download = `qr-${P.slug}.png`;
  $('qrSvg').href = `/qr/${P.slug}.svg?${q}`; $('qrSvg').download = `qr-${P.slug}.svg`;
}
$('qrDark').oninput = $('qrLight').oninput = () => renderQr();

// ---------- ajustes de página ----------
$('sSlugSave').onclick = async () => {
  $('sErr').textContent = '';
  try { P = await api('/api/pages/' + P.id, {method: 'PUT', body: {slug: $('sSlug').value}}); pages[pages.findIndex(p => p.id === P.id)] = P; await openPage(P.id); toast('Dirección cambiada'); }
  catch (err) { $('sErr').textContent = err.message; }
};
$('sPub').onchange = e => savePage({published: e.target.checked}, e.target.checked ? 'Página publicada' : 'Página oculta');
$('sHome').onchange = async e => {
  try { await api('/api/admin/settings', {method: 'PUT', body: {home: e.target.checked ? P.slug : ''}}); toast(e.target.checked ? 'Ahora es la portada' : 'Portada quitada'); }
  catch (err) { toast(err.message); e.target.checked = !e.target.checked; }
};
$('sDomainSave').onclick = async () => {
  $('sDomErr').textContent = '';
  try { P = await api('/api/pages/' + P.id, {method: 'PUT', body: {domain: $('sDomain').value}}); pages[pages.findIndex(p => p.id === P.id)] = P; fillPage(); toast(P.domain ? 'Dominio guardado' : 'Dominio quitado'); }
  catch (err) { $('sDomErr').textContent = err.message; }
};
$('sPublicSave').onclick = async () => {
  $('sPubErr').textContent = '';
  try { const r = await api('/api/admin/settings', {method: 'PUT', body: {public_url: $('sPublic').value}}); $('sPublic').value = r.public_url; await openPage(P.id); toast('Dirección del servidor guardada'); }
  catch (err) { $('sPubErr').textContent = err.message; }
};
$('sReg').onchange = async e => {
  try { await api('/api/admin/settings', {method: 'PUT', body: {allow_register: e.target.checked}}); toast(e.target.checked ? 'Registro abierto' : 'Registro cerrado'); }
  catch (err) { toast(err.message); e.target.checked = !e.target.checked; }
};
$('obCancel').onclick = () => { $('onboard').hidden = true; $('editor').hidden = false; $('tabs').hidden = false; };
$('newPage').onclick = () => { $('obSlug').value = ''; $('obName').value = ''; $('obErr').textContent = ''; $('editor').hidden = true; $('onboard').hidden = false; $('tabs').hidden = true; };
$('delPage').onclick = async () => {
  const typed = prompt(t(`Para borrar la página escribe su dirección: ${P.slug}`));
  if (typed !== P.slug) return;
  await api('/api/pages/' + P.id, {method: 'DELETE'});
  localStorage.removeItem('enlacespanel-page'); location.reload();
};

// ---------- cuenta ----------
$('pwForm').onsubmit = async e => {
  e.preventDefault(); $('pwErr').textContent = '';
  try { await api('/api/password', {method: 'POST', body: {old: $('pwOld').value, new: $('pwNew').value}}); $('pwOld').value = $('pwNew').value = ''; toast('Contraseña cambiada'); }
  catch (err) { $('pwErr').textContent = err.message; }
};
$('delAccount').onclick = async () => {
  const pw = prompt(t('Esto borra tu cuenta y todas tus páginas. Escribe tu contraseña para confirmarlo:'));
  if (!pw) return;
  try { await api('/api/account/delete', {method: 'POST', body: {password: pw}}); location.reload(); }
  catch (err) { toast(err.message); }
};

// ---------- usuarios (admin) ----------
const STATUS = {approved: 'Activo', pending: 'Pendiente', disabled: 'Desactivado'};
async function loadUsers() {
  const us = await api('/api/admin/users');
  $('uList').innerHTML = us.map(u => `<tr data-id="${u.id}"><td><b translate="no">${esc(u.username)}</b>${u.is_admin ? ' <span class="hint">(admin)</span>' : ''}</td>
    <td>${STATUS[u.status] || u.status}</td><td class="n">${u.pages}</td><td><div class="row" style="justify-content:flex-end">
    ${u.status !== 'approved' ? '<button class="small" data-a="approve">Aprobar</button>' : ''}
    ${u.id !== me.id ? `${u.status === 'approved' ? '<button class="ghost small" data-a="disable">Desactivar</button>' : ''}
      <button class="ghost small" data-a="password">Cambiar contraseña</button>
      <button class="ghost small" data-a="${u.is_admin ? 'unadmin' : 'admin'}">${u.is_admin ? 'Quitar admin' : 'Hacer admin'}</button>
      <button class="danger small" data-a="delete">Borrar</button>` : ''}</div></td></tr>`).join('');
}
const genPass = () => { const c = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789', r = crypto.getRandomValues(new Uint32Array(12)); return Array.from(r, n => c[n % c.length]).join(''); };
$('nuGen').onclick = () => { $('nuPass').value = genPass(); $('nuPass').type = 'text'; };
$('nuForm').onsubmit = async e => {
  e.preventDefault(); $('nuErr').textContent = '';
  const username = $('nuName').value.trim(), password = $('nuPass').value;
  try {
    const r = await api('/api/admin/users', {method: 'POST', body: {username, password, is_admin: $('nuAdmin').checked}});
    $('nuName').value = $('nuPass').value = ''; $('nuAdmin').checked = false; loadUsers();
    toast(`Usuario ${username} creado`);
    if (r && r.recovery_code) recoveryCodeDialog(r.recovery_code, username, true);
  } catch (err) { $('nuErr').textContent = err.message; }
};
$('uList').onclick = async e => {
  const b = e.target.closest('button[data-a]'); if (!b) return;
  const id = b.closest('tr').dataset.id, a = b.dataset.a, body = {action: a};
  if (a === 'delete' && !confirm(t('¿Borrar este usuario y todas sus páginas?'))) return;
  if (a === 'password') {
    const pw = prompt(t('Nueva contraseña para este usuario (mínimo 8 caracteres):'), genPass());
    if (!pw) return; body.password = pw;
  }
  try { await api('/api/admin/users/' + id, {method: 'POST', body}); loadUsers(); toast(a === 'password' ? 'Contraseña cambiada' : 'Hecho'); }
  catch (err) { toast(err.message); }
};

// ---------- ver mi página: móvil, tablet o PC ----------
const DEVICES = {movil: [390, 844, 'Móvil · 390 × 844'], tablet: [820, 1180, 'Tablet · 820 × 1180'], pc: [1440, 900, 'PC · 1440 × 900']};
let device = localStorage.getItem('enlacespanel-dev') || 'movil';
function markDevice() {
  document.querySelectorAll('[data-dev]').forEach(b => b.classList.toggle('on', b.dataset.dev === device));
}
function fitViewer() {
  if ($('viewer').hidden) return;
  const [w, h, label] = DEVICES[device], d = $('vDev'), st = $('vStage');
  const pad = device === 'pc' ? [16, 36] : [20, 20];
  d.className = 'vdev ' + device;
  d.style.width = (w + pad[0]) + 'px'; d.style.height = (h + pad[1]) + 'px';
  const k = Math.min(1, (st.clientWidth - 32) / (w + pad[0]), (st.clientHeight - 32) / (h + pad[1]));
  d.style.transform = `translate(-50%, -50%) scale(${k})`;
  $('vSize').textContent = label + (k < 1 ? ` · al ${Math.round(k * 100)} %` : '');
}
// La vista previa de al lado del editor también cambia de tamaño
function fitPreview() {
  const [w, h, label] = DEVICES[device], d = $('pvDev'), box = $('pvBox');
  const pad = device === 'pc' ? [16, 36] : [20, 20], W = w + pad[0], H = h + pad[1];
  const maxH = Math.max(320, innerHeight - 190);
  const k = Math.min(1, box.clientWidth / W, maxH / H);
  d.className = 'pvdev ' + device;
  d.style.width = W + 'px'; d.style.height = H + 'px';
  d.style.transform = `translateX(${(box.clientWidth - W * k) / 2}px) scale(${k})`;
  box.style.height = Math.round(H * k) + 'px';
  $('pvSize').textContent = label;
}
function setDevice(dv) {
  device = dv; localStorage.setItem('enlacespanel-dev', dv); markDevice();
  $('editor').dataset.dev = dv; fitPreview(); fitViewer();
}
document.querySelectorAll('[data-dev]').forEach(b => b.onclick = () => setDevice(b.dataset.dev));
$('openPage').onclick = () => {
  $('vFrame').src = '/' + P.slug + '?vista=1&t=' + Date.now();
  $('vOpen').href = '/' + P.slug + '?vista=1';
  $('viewer').hidden = false; fitViewer();
};
$('vClose').onclick = () => { $('viewer').hidden = true; $('vFrame').src = 'about:blank'; };
addEventListener('resize', () => { fitViewer(); fitPreview(); });
new ResizeObserver(() => fitPreview()).observe($('pvBox'));
$('editor').dataset.dev = device;
addEventListener('keydown', e => { if (e.key === 'Escape' && !$('viewer').hidden) $('vClose').onclick(); });
markDevice();

// ---------- versiones y novedades ----------
const appVer = () => { try { return AND && AND.version ? AND.version() : ''; } catch (e) { return ''; } };
const md = t => esc(t).replace(/\*\*(.+?)\*\*/g, '<b>$1</b>').replace(/`(.+?)`/g, '<code>$1</code>');
const newer = (a, b) => { const x = a.split('.').map(Number), y = b.split('.').map(Number); for (let i = 0; i < 3; i++) { if ((x[i] || 0) !== (y[i] || 0)) return (x[i] || 0) > (y[i] || 0); } return false; };
function paintVersions() {
  const av = appVer();
  $('vChip').textContent = 'v' + info.version;
  $('verLine').innerHTML = `<b>Web ${esc(info.version)}</b>` + (av ? ` · <b>App ${esc(av)}</b>`
    : ' · <a href="https://github.com/iaonlineapps/enlacespanel/releases?q=android&expanded=true" target="_blank" rel="noopener">App de Android</a>');
  $('pFoot').innerHTML = `EnlacesPanel · Web ${esc(info.version)}` + (av ? ` · App Android ${esc(av)}`
    : ` · <a href="https://github.com/iaonlineapps/enlacespanel/releases?q=android&expanded=true" target="_blank" rel="noopener">App Android</a>`)
    + ` · <a href="#" id="footNews">Novedades</a> · <a href="/privacidad${LANG === 'en' ? '?lang=en' : ''}" target="_blank">Privacidad</a>`
    + `<span class="madeby">💛 <span>Proyecto sin ánimo de lucro, gratis y sin anuncios</span> · 🤖 <span>App creada con ayuda de inteligencia artificial (IA)</span> · `
    + `© 2026 <a href="https://github.com/iaonlineapps/enlacespanel" target="_blank" rel="noopener" translate="no">IA Online Apps</a> · <span>Uso personal no comercial</span></span>`;
  $('footNews').onclick = e => { e.preventDefault(); showNews(); };
  $('appNewsBtn').hidden = !(AND && AND.news); $('appCheckBtn').hidden = !(AND && AND.checkUpdate);
}
async function showNews(since) {
  const d = await api('/api/novedades?lang=' + LANG);
  const list = since ? d.novedades.filter(n => newer(n.version, since)) : d.novedades;
  if (!list.length) return;
  $('newsTitle').textContent = since ? `EnlacesPanel se ha actualizado a la ${d.version}` : 'Novedades de EnlacesPanel';
  $('newsBody').innerHTML = list.map(n => `<h3>Versión ${esc(n.version)}${n.version === d.version ? ' <span class="tag">la tuya</span>' : ''}</h3>
    <ul>${n.items.map(i => `<li>${md(i)}</li>`).join('')}</ul>`).join('');
  $('news').showModal();
}
// Tras actualizar el servidor, enseña una vez lo nuevo (en el navegador y en la app)
function newsIfUpdated() {
  const k = 'enlacespanel-visto', seen = localStorage.getItem(k);
  localStorage.setItem(k, info.version);
  if (seen && seen !== info.version && newer(info.version, seen)) showNews(seen).catch(() => {});
}
$('newsBtn').onclick = () => showNews();
$('vChip').onclick = () => showNews();
$('newsClose').onclick = () => $('news').close();
$('appNewsBtn').onclick = () => AND.news();
$('appCheckBtn').onclick = () => AND.checkUpdate();

// ---------- idioma ----------
const ANDL = window.EnlacesPanelAndroid;  // la app de Android usa el mismo idioma que el panel
document.querySelectorAll('[data-lang]').forEach(b => {
  b.classList.toggle('on', b.dataset.lang === LANG);
  b.onclick = () => { if (ANDL && ANDL.setLang) try { ANDL.setLang(b.dataset.lang); } catch (e) {} setLang(b.dataset.lang); };
});
if (ANDL && ANDL.setLang) try { ANDL.setLang(LANG); } catch (e) {}
function paintPageLang() {
  const pl = (P.style && P.style.lang) || 'es';
  document.querySelectorAll('[data-pl]').forEach(b => b.className = (b.dataset.pl === pl ? 'on' : 'ghost') + ' small');
}
$('pLang').onclick = async e => { const b = e.target.closest('[data-pl]'); if (!b) return; if (await savePage({style: {...(P.style || {}), lang: b.dataset.pl}}, 'Guardado')) paintPageLang(); };

// ---------- compartir ----------
const AND = window.EnlacesPanelAndroid;  // dentro de la app de Android
$('copyUrl').onclick = async () => {
  if (AND) return AND.copy(pageUrl());
  try { await navigator.clipboard.writeText(pageUrl()); toast('Enlace copiado'); } catch (e) { toast(pageUrl()); }
};
if (AND) { $('shareUrl').hidden = false; $('shareUrl').onclick = () => AND.share(pageUrl(), P.name); }
else if (navigator.share) { $('shareUrl').hidden = false; $('shareUrl').onclick = () => navigator.share({title: P.name, url: pageUrl()}).catch(() => {}); }

start().catch(err => { document.body.textContent = t('No se puede conectar con el servidor') + ': ' + err.message; });
})();
