// Idioma del panel: español (el texto original) o inglés.
// Traduce los textos de la página y los que el panel va añadiendo (avisos, listas, errores),
// sin tocar lo que escribe el usuario (lo que va dentro de translate="no").
(() => {
const KEY = 'enlacespanel-lang';
const guess = () => ((navigator.language || 'es').toLowerCase().startsWith('es') ? 'es' : 'en');
const lang = ['es', 'en'].includes(localStorage.getItem(KEY)) ? localStorage.getItem(KEY) : guess();
document.documentElement.lang = lang;

const EN = {
  // entrar
  'EnlacesPanel · Panel': 'EnlacesPanel · Panel',
  'Tu página de enlaces, en tu propio servidor.': 'Your link page, on your own server.',
  'Bienvenido. Crea la primera cuenta: será la del administrador.': 'Welcome. Create the first account: it will be the administrator.',
  'Usuario': 'Username', 'Contraseña': 'Password', 'Entrar': 'Sign in', 'Crear cuenta': 'Create account',
  'Ya tengo cuenta': 'I already have an account',
  'Cuenta creada. El administrador tiene que aprobarla antes de que puedas entrar.': 'Account created. The administrator has to approve it before you can sign in.',
  // cabecera y pestañas
  'Página que editas': 'Page you are editing', 'Ver como': 'View as',
  'Ver como en un móvil': 'View as on a phone', 'Ver como en una tablet': 'View as on a tablet', 'Ver como en un ordenador': 'View as on a computer',
  'Móvil': 'Phone', 'Tablet': 'Tablet', 'PC': 'Desktop', 'Ver mi página': 'View my page', 'Ver novedades': "See what's new", 'Salir': 'Sign out',
  'Secciones': 'Sections', 'Enlaces': 'Links', 'Perfil': 'Profile', 'Diseño': 'Design', 'Redes': 'Socials', 'Estadísticas': 'Stats',
  'QR': 'QR', 'Ajustes': 'Settings', 'Cuenta': 'Account', 'Usuarios': 'Users', 'Vista': 'View', 'Editar': 'Edit', 'Vista previa': 'Preview',
  // otra página
  'Dirección': 'Address', 'tu-nombre': 'your-name', 'Nombre que se ve': 'Display name', 'Crear página': 'Create page', 'Cancelar': 'Cancel',
  // enlaces
  'Añadir enlace': 'Add link', 'Título': 'Title', 'Mi canal de YouTube': 'My YouTube channel',
  'Icono del botón': 'Button icon', '(opcional)': '(optional)', 'Subir foto o logo': 'Upload photo or logo', 'Cambiar foto o logo': 'Change photo or logo',
  'o un emoji': 'or an emoji', 'Emoji': 'Emoji', 'Quitar': 'Remove', 'Quitar icono': 'Remove icon',
  'Sale a la izquierda del botón. La foto se recorta en cuadrado.': 'It shows on the left of the button. The photo is cropped square.',
  'Añadir título de sección': 'Add section title', 'Tus enlaces': 'Your links',
  'Arrastra ⠿ para ordenarlos (o usa ↑ ↓). Los clics son de los últimos 30 días.': 'Drag ⠿ to reorder them (or use ↑ ↓). Clicks are from the last 30 days.',
  'No tienes enlaces. Añade el primero arriba.': 'You have no links yet. Add the first one above.',
  'Destacar (late suavemente para llamar la atención)': 'Highlight (gently pulses to catch the eye)',
  'Programar fechas': 'Schedule dates', '(si lo dejas apagado, el enlace se ve siempre y no caduca)': '(if it is off, the link always shows and never expires)',
  'Se muestra desde': 'Shows from', '(vacío = ya)': '(empty = now)', 'Caduca el': 'Expires on', '(vacío = nunca)': '(empty = never)',
  'Guardar': 'Save', 'Subir': 'Move up', 'Bajar': 'Move down', 'Ocultar': 'Hide', 'Mostrar': 'Show', 'Borrar': 'Delete',
  'clics': 'clicks', 'destacado': 'highlighted', 'caducado': 'expired', 'Título de sección': 'Section title', 'Sección': 'Section',
  'Arrastra para ordenar': 'Drag to reorder',
  // perfil
  'Nombre': 'Name', 'Bio': 'Bio', 'Foto': 'Photo', 'Quitar foto': 'Remove photo',
  'La foto se guarda en tu servidor: ninguna web externa ve quién visita tu página.': 'The photo is stored on your server: no outside website sees who visits your page.',
  'Aviso legal': 'Legal notice', '(opcional; obligatorio si la usas para un negocio)': '(optional; required in Spain if you use it for a business)',
  'Titular, NIF, domicilio, correo de contacto…': 'Owner, tax ID, address, contact email…',
  'Sale como «Aviso legal» al pie de tu página. La política de privacidad ya la pone EnlacesPanel.': 'It shows as "Legal notice" at the bottom of your page. EnlacesPanel already adds the privacy policy.',
  // diseño
  'Tema': 'Theme', 'Tus colores': 'Your colours', 'Botones': 'Buttons', 'Animación': 'Animation', 'Iconos de redes': 'Social icons',
  'Cómo aparecen los botones al abrir la página. Quien tenga activado «reducir movimiento» en su móvil la verá quieta.': 'How the buttons appear when the page opens. Visitors with "reduce motion" turned on see it still.',
  'Noche': 'Night', 'Papel': 'Paper', 'Bosque': 'Forest', 'Atardecer': 'Sunset', 'Arena': 'Sand', 'Mar': 'Sea', 'Lavanda': 'Lavender',
  'Aurora': 'Aurora', 'Neón': 'Neon', 'Carbón': 'Charcoal', 'Propio': 'Custom',
  'Fondo': 'Background', 'Texto': 'Text', 'Texto de botones': 'Button text', 'Detalles': 'Accents',
  'Redondeados': 'Rounded', 'Pastilla': 'Pill', 'Rectos': 'Square', 'Solo borde': 'Outline',
  'Suave': 'Soft', 'Viva': 'Lively', 'Sin animación': 'No animation',
  'Debajo de la bio': 'Below the bio', 'Al final de la página': 'At the bottom of the page',
  // redes
  'Redes sociales': 'Social networks', '+ Añadir red': '+ Add network', 'Guardar redes': 'Save networks', 'Aún no has puesto redes.': 'No networks added yet.',
  'Salen como iconos redondos (puedes elegir arriba o abajo en Diseño). Para WhatsApp pon tu número, para Telegram tu @usuario y para Correo tu email: al tocarlos se abre la app directamente.':
    'They show as round icons (choose top or bottom in Design). For WhatsApp enter your number, for Telegram your @username and for Email your address: tapping them opens the app directly.',
  'Correo': 'Email', 'Teléfono': 'Phone', 'Web': 'Website', 'Red': 'Network',
  'Tu número: +34 600 123 456': 'Your number: +34 600 123 456', 'Tu usuario: @tunombre': 'Your username: @yourname', 'tu@correo.es': 'you@example.com',
  '@tunombre o https://…': '@yourname or https://…', '@tucanal o https://…': '@yourchannel or https://…',
  // estadísticas
  'visitas': 'visits', 'clics por visita': 'clicks per visit', 'Visitas y clics por día': 'Visits and clicks per day', 'Visitas': 'Visits', 'Clics': 'Clicks',
  'Clics por enlace': 'Clicks per link', 'Enlace': 'Link', '7 días': '7 days', '30 días': '30 days', '90 días': '90 days', '1 año': '1 year',
  'Sin cookies y sin guardar IPs: solo se cuenta cuántas visitas y clics hay cada día.': 'No cookies and no IPs stored: only how many visits and clicks there are each day.',
  'Todavía no hay enlaces.': 'No links yet.',
  // QR
  'Código QR': 'QR code', 'Código QR de tu página': 'QR code of your page',
  'Imprímelo en tarjetas, carteles o en el mostrador: al escanearlo se abre tu página.': 'Print it on cards, posters or at the counter: scanning it opens your page.',
  'Color': 'Colour', 'Descargar PNG': 'Download PNG', 'Descargar SVG': 'Download SVG',
  'Si cambias la dirección de la página, vuelve a descargar el QR.': 'If you change the page address, download the QR again.',
  // ajustes
  'Esta página': 'This page', 'Dirección dentro del servidor': 'Address on the server', 'Cambiar': 'Change',
  'Publicada (si la desactivas, solo tú la ves en la vista previa)': 'Published (if you turn it off, only you see it in the preview)',
  'Idioma de la página': 'Page language', 'Español': 'Español', 'English': 'English',
  'Los textos fijos de tu página (pie, privacidad, aviso legal) salen en este idioma.': 'The fixed texts of your page (footer, privacy, legal notice) use this language.',
  'Dominio propio': 'Custom domain', 'Dominio': 'Domain',
  'Con Pangolin (dominio por tu VPS)': 'With Pangolin (domain through your VPS)',
  'Con otro proxy (Nginx Proxy Manager, Caddy, Cloudflare Tunnel…)': 'With another proxy (Nginx Proxy Manager, Caddy, Cloudflare Tunnel…)',
  'Si publicas tus apps con Pangolin en un VPS y Newt en esta Raspberry:': 'If you publish your apps with Pangolin on a VPS and Newt on this Raspberry Pi:',
  'Escribe el dominio aquí y pulsa Guardar. El enlace, el botón Compartir y el código QR usarán tu dominio.': 'Type the domain here and press Save. The link, the Share button and the QR code will use your domain.',
  'Servidor': 'Server', '(administrador)': '(administrator)', 'Dirección pública del servidor': 'Public server address',
  'Permitir que otras personas pidan cuenta (tú las apruebas en Usuarios)': 'Let other people request an account (you approve them in Users)',
  'Otra página': 'Another page', '+ Crear otra página': '+ Create another page', 'Borrar esta página para siempre': 'Delete this page forever',
  // cuenta
  'Tu cuenta': 'Your account', 'Has entrado como': 'Signed in as', 'Cambiar contraseña': 'Change password',
  'Contraseña actual': 'Current password', 'Contraseña nueva': 'New password', '(mínimo 8 caracteres)': '(at least 8 characters)',
  'Tus datos': 'Your data', 'Descarga todo lo que tienes guardado (páginas y enlaces) en un archivo.': 'Download everything you have stored (pages and links) as a file.',
  'Descargar mis datos': 'Download my data', 'Borrar cuenta': 'Delete account',
  'Se borran tu cuenta, tus páginas, tus fotos y tus estadísticas. No se puede deshacer.': 'Your account, pages, photos and stats are deleted. It cannot be undone.',
  'Borrar mi cuenta': 'Delete my account', 'Acerca de': 'About', 'Idioma': 'Language',
  'Novedades de la web': "What's new in the web", 'Novedades de la app': "What's new in the app", 'Buscar versión nueva de la app': 'Check for a new app version',
  'Privacidad': 'Privacy', 'App de Android': 'Android app', 'App Android': 'Android app',
  // usuarios
  'Crear usuario': 'Create user', 'Generar contraseña': 'Generate password', 'Administrador': 'Administrator',
  'La cuenta queda activa al momento. Pásale el usuario y la contraseña a esa persona; puede cambiarla en Cuenta.': 'The account is active right away. Give that person the username and password; they can change it in Account.',
  'Estado': 'Status', 'Páginas': 'Pages', 'Activo': 'Active', 'Pendiente': 'Pending', 'Desactivado': 'Disabled', '(admin)': '(admin)',
  'Aprobar': 'Approve', 'Desactivar': 'Disable', 'Quitar admin': 'Remove admin', 'Hacer admin': 'Make admin',
  // vista previa y visor
  'Vista previa de tu página': 'Preview of your page', 'Copiar enlace': 'Copy link', 'Compartir': 'Share', 'Tu página': 'Your page',
  'Abrir en otra pestaña ↗': 'Open in a new tab ↗', 'Cerrar': 'Close', 'Novedades': "What's new", 'Novedades de EnlacesPanel': "What's new in EnlacesPanel",
  'Entendido': 'Got it', 'Deshacer': 'Undo', 'la tuya': 'yours',
  // avisos
  'Tu página ya está creada. Empieza añadiendo enlaces.': 'Your page is ready. Start by adding links.',
  'Página creada': 'Page created', 'Enlace añadido': 'Link added', 'Título añadido': 'Title added', 'Guardado': 'Saved', 'Enlace borrado': 'Link deleted',
  'Recuperado': 'Restored', 'Imagen puesta': 'Image set', 'Foto actualizada': 'Photo updated', 'Foto quitada': 'Photo removed', 'Redes guardadas': 'Networks saved',
  'Dirección cambiada': 'Address changed', 'Página publicada': 'Page published', 'Página oculta': 'Page hidden', 'Ahora es la portada': 'It is now the home page',
  'Portada quitada': 'Home page removed', 'Dominio guardado': 'Domain saved', 'Dominio quitado': 'Domain removed', 'Dirección del servidor guardada': 'Server address saved',
  'Registro abierto': 'Sign-up open', 'Registro cerrado': 'Sign-up closed', 'Contraseña cambiada': 'Password changed', 'Hecho': 'Done', 'Enlace copiado': 'Link copied',
  'No se puede conectar con el servidor': 'Cannot connect to the server',
  'Esa imagen no se puede leer': 'That image cannot be read', 'Datos no válidos': 'Invalid data',
  '¿Borrar este usuario y todas sus páginas?': 'Delete this user and all their pages?',
  'Esto borra tu cuenta y todas tus páginas. Escribe tu contraseña para confirmarlo:': 'This deletes your account and all your pages. Type your password to confirm:',
  'Nueva contraseña para este usuario (mínimo 8 caracteres):': 'New password for this user (at least 8 characters):',
  // errores del servidor
  'Acción desconocida': 'Unknown action', 'Demasiados intentos. Espera unos minutos.': 'Too many attempts. Wait a few minutes.',
  'El registro está cerrado': 'Sign-up is closed', 'El usuario debe tener de 3 a 32 letras, números, puntos, guiones o _': 'The username must have 3 to 32 letters, numbers, dots, hyphens or _',
  'Enlace no encontrado': 'Link not found', 'Eres el único administrador: nombra antes a otro': 'You are the only administrator: make someone else admin first',
  'Esa dirección no parece válida': "That address doesn't look valid", 'Esa dirección ya está cogida': 'That address is already taken',
  'Escribe solo la dirección, por ejemplo https://enlaces.midominio.com': 'Type only the address, for example https://links.mydomain.com',
  'Ese correo no parece válido': "That email doesn't look valid", 'Ese dominio no parece válido. Escríbelo así: laura.com o enlaces.laura.com': "That domain doesn't look valid. Write it like this: laura.com or links.laura.com",
  'Ese dominio ya lo usa otra página': 'Another page already uses that domain', 'Ese teléfono no parece válido': "That phone number doesn't look valid",
  'Ese usuario ya existe': 'That username already exists', 'Falta la dirección': 'The address is missing', 'Imagen no válida': 'Invalid image',
  'La contraseña actual no es correcta': 'The current password is wrong', 'La contraseña debe tener al menos 8 caracteres': 'The password must have at least 8 characters',
  'La contraseña no es correcta': 'The password is wrong', 'La contraseña nueva debe tener al menos 8 caracteres': 'The new password must have at least 8 characters',
  'La dirección debe tener de 2 a 32 letras minúsculas, números, - o _ (y no ser una palabra reservada)': 'The address must have 2 to 32 lowercase letters, numbers, - or _ (and not be a reserved word)',
  'La dirección es demasiado larga': 'The address is too long', 'La imagen debe ser JPG, PNG o WebP': 'The image must be JPG, PNG or WebP',
  'La imagen es demasiado grande': 'The image is too large', 'No encontrado': 'Not found', 'No hay ninguna página con esa dirección': 'There is no page with that address',
  'No puedes hacerte eso a ti mismo': "You can't do that to yourself",
  'Pon el número de WhatsApp con prefijo, por ejemplo +34 600 123 456': 'Enter the WhatsApp number with country code, for example +44 7700 900123',
  'Pon tu usuario de Telegram, por ejemplo @tunombre': 'Enter your Telegram username, for example @yourname', 'Ponle un título': 'Give it a title',
  'Página no encontrada': 'Page not found', 'Solo para el administrador': 'Administrator only',
  'Solo se permiten direcciones web, correos (mailto:) o teléfonos (tel:)': 'Only web addresses, emails (mailto:) or phone numbers (tel:) are allowed',
  'Tema desconocido': 'Unknown theme', 'Tienes que aceptar la política de privacidad': 'You have to accept the privacy policy', 'Tienes que entrar': 'You have to sign in',
  'Tu cuenta está pendiente de que el administrador la apruebe': 'Your account is waiting for the administrator to approve it',
  'Usuario no encontrado': 'User not found', 'Usuario o contraseña incorrectos': 'Wrong username or password',
};
// Textos con partes que cambian
const PAT = [
  [/^Usuario (.+) creado$/, 'User $1 created'],
  [/^desde (.+)$/, 'from $1'], [/^hasta (.+)$/, 'until $1'],
  [/^(.+): (\d+) visitas$/, '$1: $2 visits'], [/^(.+): (\d+) clics$/, '$1: $2 clicks'],
  [/^EnlacesPanel se ha actualizado a la (.+)$/, 'EnlacesPanel has been updated to $1'],
  [/^Versión (.+)$/, 'Version $1'],
  [/^(Móvil|Tablet|PC) · (\d+ × \d+)(?: · al (\d+) %)?$/, (m, d, s, k) => ({'Móvil': 'Phone', 'Tablet': 'Tablet', 'PC': 'Desktop'}[d]) + ' · ' + s + (k ? ` · at ${k}%` : '')],
  [/^Para borrar la página escribe su dirección: (.+)$/, 'To delete the page, type its address: $1'],
  [/^Puedes tener como mucho (\d+) enlaces por página$/, 'You can have at most $1 links per page'],
  [/^Puedes tener como mucho (\d+) páginas$/, 'You can have at most $1 pages'],
  [/^Error (\d+)$/, 'Error $1'],
];
// Párrafos con negritas o datos dentro (data-i18n="clave" en index.html)
const ENH = {
  accept: 'I have read the <a href="/privacidad?lang=en" target="_blank">privacy policy</a>',
  obTitle: 'Another <b>page</b>',
  obHint: 'Choose the address. For example, if you type <b>shop</b>, the page will be <span id="obBase"></span>shop',
  seenAt: 'Your page is at: <a id="sUrl" target="_blank" rel="noopener"></a>',
  home: '<input type="checkbox" id="sHome"> Show this page on the server home page (<span id="homeUrl"></span>)',
  domHint: 'If you have a domain for this page (for example <b>laura.com</b> or <b>links.laura.com</b>), type it here and your page will open directly on it, with nothing after it.',
  pg1: 'In Pangolin, go to <b>Resources → Add Resource</b>, type <b>HTTP</b>. Name <b>EnlacesPanel</b> and a subdomain, for example <b>links</b> (you get <b>links.yourdomain.com</b>).',
  pg2: 'Pick the <b>Site</b> of this Raspberry Pi and set the target to <b>http</b>, the Raspberry Pi IP (<b class="piIp">192.168.1.50</b>) and port <b class="piPort"></b>. Save: Pangolin adds the https certificate by itself.',
  pg3: 'In that resource, under <b>Authentication</b>, <b>turn off Pangolin authentication</b> (Use Platform SSO off): link pages are public and the panel already has its own username and password.',
  pg4: 'The administrator enters <b>https://links.yourdomain.com</b> in <b>Public server address</b> (below).',
  pg5: 'For a page\'s <b>custom domain</b> (for example <b>laura.com</b>): add it in Pangolin under <b>Domains</b> (with the DNS records it shows you), create another resource with that domain and the same target (Raspberry Pi IP and port <b class="piPort"></b>), and type it above in Custom domain.',
  px1: 'Where you bought the domain, create an <b>A</b> record pointing to your home public IP (or a <b>CNAME</b> to your dynamic DNS).',
  px2: 'In your HTTPS proxy (Nginx Proxy Manager, Caddy, Cloudflare Tunnel…) add that domain and send it to this Raspberry Pi, port <b class="piPort"></b>.',
  pubHint: 'The address used to reach the server from the Internet, for example <b>https://links.mydomain.com</b>. It is used for the links you share and for the QR codes of every page without a custom domain. Leave it empty to use the browser address.',
  maxPages: 'You can have several: a personal one, another for your business… (up to <span id="maxPages"></span>).',
  upd: 'To update the server: <code>git pull && ./install.sh</code> in the EnlacesPanel folder.',
};

function tr(s) {
  if (lang !== 'en' || !s) return s;
  const m = /^(\s*)([\s\S]*?)(\s*)$/.exec(s), core = m[2];
  if (!core) return s;
  let r = EN[core];
  if (r === undefined) for (const [re, rep] of PAT) if (re.test(core)) { r = core.replace(re, rep); break; }
  return r === undefined ? s : m[1] + r + m[3];
}
const ATTRS = ['placeholder', 'title', 'aria-label', 'alt'];
const skip = n => n.closest && n.closest('[translate="no"],script,style,textarea,code');
function walk(n) {
  if (n.nodeType === 3) {
    if (n.parentElement && skip(n.parentElement)) return;
    const v = tr(n.nodeValue); if (v !== n.nodeValue) n.nodeValue = v; return;
  }
  if (n.nodeType !== 1 || skip(n)) return;
  for (const a of ATTRS) if (n.hasAttribute(a)) { const v = tr(n.getAttribute(a)); if (v !== n.getAttribute(a)) n.setAttribute(a, v); }
  for (const c of [...n.childNodes]) walk(c);
}
window.t = tr;
window.LANG = lang;
window.setLang = l => { localStorage.setItem(KEY, l); location.reload(); };
if (lang === 'en') {
  document.querySelectorAll('[data-i18n]').forEach(e => { if (ENH[e.dataset.i18n]) e.innerHTML = ENH[e.dataset.i18n]; });
  walk(document.documentElement);
  document.title = tr(document.title);
  new MutationObserver(ms => {
    for (const m of ms) {
      if (m.type === 'characterData') walk(m.target);
      else if (m.type === 'attributes') walk(m.target);
      else m.addedNodes.forEach(walk);
    }
  }).observe(document.documentElement, {subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ATTRS});
}
})();
