# Conecta el diseño exportado de Claude Design (invitación de Noah) con Yo Organizo.
# Uso: python3 tools/conectar-diseno-noah.py <diseño-exportado.html> invitaciones/noah-diseno.html
import json, re, sys
src, out = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()

# ---- 1) Plantilla del diseño: conectar respuestas ----
m = re.search(r'(<script type="__bundler/template"[^>]*>)(.*?)(</script>)', s, re.S)
t = json.loads(m.group(2))
def rep(a, b):
    global t
    assert t.count(a) == 1, (t.count(a), a[:80])
    t = t.replace(a, b)

rep('<meta name="viewport" content="width=device-width, initial-scale=1">',
    '<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>Baby shower de Noah · Invitación</title>')

# Mensaje personal antes del texto principal
rep('<div style="font-style:italic;font-size:31px;line-height:1.25;color:#2f4f73;text-wrap:balance;max-width:470px;">Acompañanos a celebrar esta dulce espera.</div>',
    '<sc-if value="{{ hasMsg }}" hint-placeholder-val="{{ false }}"><div style="max-width:470px;padding:18px 26px;border-radius:18px;background:rgba(234,242,248,.8);border:1px solid #d6e4ef;font-style:italic;font-size:25px;line-height:1.4;color:#2f4f73;text-wrap:balance;">“{{ msg }}”</div></sc-if>\n'
    '    <div style="font-style:italic;font-size:31px;line-height:1.25;color:#2f4f73;text-wrap:balance;max-width:470px;">Acompañanos a celebrar esta dulce espera.</div>')

# Aviso si no se pudo guardar la respuesta
rep('<div style="font-style:italic;font-size:36px;color:#2f4f73;line-height:1.1;">{{ replyTitle }}</div>',
    '<div style="font-style:italic;font-size:36px;color:#2f4f73;line-height:1.1;">{{ replyTitle }}</div>\n'
    '        <sc-if value="{{ hasErr }}" hint-placeholder-val="{{ false }}"><div style="font-size:20px;color:#a2482a;max-width:440px;">{{ err }}</div></sc-if>')

# Textos que no van en la invitación
rep('<div style="font-size:23px;font-style:italic;line-height:1.25;color:#3f5f82;">Es en una quinta: ¡vengan cómodos!</div>', '')
rep('<div style="font-size:21px;font-style:italic;line-height:1.3;color:#52667d;margin-top:-6px;">*El horario de la invitación es el establecido.</div>', '')
rep('<div style="font-size:24px;line-height:1.4;color:#3f5f82;text-wrap:balance;max-width:500px;">Nos encantaría saber si nos {{ acompanas }}. Si podés, contanos antes del miércoles 2 de diciembre.</div>', '')
rep('De 12:00 a 16:00 h*</div>', 'De 12:00 a 16:00 h</div>')

# La carta del sobre muestra la invitación real (copia en miniatura de la tarjeta)
rep("""padding-top:9%;box-sizing:border-box;">
      <div style="font-size:15px;letter-spacing:.3em;text-transform:uppercase;color:#85652f;">Baby shower</div>
      <div style="font-family:'Gloock',serif;font-size:46px;line-height:1.1;color:#2f4f73;">Noah</div>
    </div>""", """box-sizing:border-box;overflow:hidden;"></div>""")
rep("  componentWillUnmount() {",
    "  fillLetter() {\n"
    "    const L = this.letterRef.current, C = this.cardRef.current;\n"
    "    if (!L || !C || !this.state.sealed || this.opening) return;\n"
    "    const k = C.cloneNode(true);\n"
    "    Object.assign(k.style, { zoom: 1, margin: 0, position: 'absolute', left: 0, top: 0, transformOrigin: '0 0', transform: 'scale(' + (L.clientWidth / 600) + ')', boxShadow: 'none', pointerEvents: 'none' });\n"
    "    k.setAttribute('aria-hidden', 'true');\n"
    "    L.replaceChildren(k);\n"
    "  }\n"
    "  componentDidUpdate() { this.fillLetter(); }\n"
    "  componentWillUnmount() {")
rep("    this.fit(); window.addEventListener('resize', this.onResize);\n",
    "    this.fit(); window.addEventListener('resize', this.onResize); this.fillLetter();\n"
    "    window.addEventListener('resize', () => this.fillLetter()); document.fonts?.ready.then(() => this.fillLetter());\n")

# La carta sube sin dejar hueco abajo: crece hacia arriba con la base escondida en el sobre
rep("letter.animate([{transform:'translateY(0)'},{transform:'translateY(-64%)'}]",
    "letter.animate([{top:'5%',height:'88%'},{top:'-51%',height:'144%'}]")

# Itinerario del día (mismo contenido e iconos que el itinerario impreso)
BOTTLE = "data:image/webp;base64,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"
ITIN = [
  ("12:00", "8937021e-bfaa-477a-acc2-2976147b8a4b", "Bienvenida y Libro de Visitas", "¡Los recibimos con mucha alegría! Dejen sus regalitos en el rinconcito de regalos y, al lado, pasen a dejarle una notita a Noah en el libro de visitas para recordar este día."),
  ("13:00", "0147d0bc-08fd-454c-969b-a80e0ff639ec", "Picada y Bebidas", "Momento de compartir algo rico para comer, tomar y charlar un rato juntos."),
  ("13:30", "c54540d8-5035-4aa3-b6e5-08913a096144", "Dinámicas y Juegos", "¡Llegó el momento más divertido! Erica, nuestra animadora, lo va a dar todo para que la pasemos genial. ¡Anímense a jugar, que sin ustedes no es lo mismo!"),
  ("15:30", BOTTLE, "Torta, Brindis y Fotos", "Palabras para los futuros mamás y papás, brindis por Noah y la gran foto grupal de recuerdo."),
  ("16:00", "72e4bb10-538c-4411-93a1-dab1573f05f5", "Despedida", "¡Gracias por venir! No te olvides de llevarte tu recuerdito hecho con mucho amor."),
]
rows = ''.join(
  '<div style="position:relative;display:flex;align-items:flex-start;gap:16px;text-align:left;padding:0 0 22px;">'
  + ('<div style="position:absolute;left:132px;top:62px;bottom:0;width:2px;background:#c6dbeb;"></div>' if i < len(ITIN) - 1 else '') +
  '<div style="width:86px;flex:none;text-align:right;font-family:\'Gloock\',serif;font-size:29px;line-height:62px;color:' + ('#7fb3c4' if i % 2 == 0 else '#2f4f73') + ';">' + h + '</div>'
  '<div style="position:relative;z-index:1;width:62px;height:62px;flex:none;border-radius:50%;background:#ffffff;border:2px solid #c6dbeb;box-shadow:0 0 0 5px #f1f6fa;display:flex;align-items:center;justify-content:center;">'
  '<img src="' + src + '" alt="" style="max-width:' + ('22' if src == BOTTLE else '38') + 'px;max-height:40px;display:block;"></div>'
  '<div style="flex:1;min-width:0;padding-top:12px;"><div style="font-family:\'Gloock\',serif;font-size:25px;line-height:1.15;color:#2f4f73;">' + t + '</div>'
  '<div style="font-size:20px;line-height:1.4;color:#3f5f82;margin-top:6px;">' + d + '</div></div></div>'
  for i, (h, src, t, d) in enumerate(ITIN))
rep('<div style="font-size:26px;line-height:1.4;color:#2f4f73;text-wrap:balance;max-width:500px;">{{ estes }} con nosotros',
    '<div style="width:100%;max-width:500px;margin-top:6px;">'
    '<div style="display:flex;align-items:center;gap:14px;justify-content:center;margin-bottom:6px;"><span style="flex:1;height:1px;background:#c6dbeb;"></span>'
    '<span style="font-size:17px;letter-spacing:.3em;text-transform:uppercase;color:#85652f;">Itinerario</span><span style="flex:1;height:1px;background:#c6dbeb;"></span></div>'
    '<div style="font-style:italic;font-size:24px;color:#3f5f82;margin-bottom:20px;">Así va a ser el día</div>'
    '<div style="position:relative;">'
    + rows + '</div></div>\n    '
    '<div style="font-size:26px;line-height:1.4;color:#2f4f73;text-wrap:balance;max-width:500px;">{{ estes }} con nosotros')

# Lógica: estado, carga por token, guardado
rep("state = { rsvp: null, sealed: true, zoom: Math.min(1, window.innerWidth / 600) };",
    "state = { rsvp: null, sealed: true, zoom: Math.min(1, window.innerWidth / 600), para: '', nene: '', msg: '', total: 0, note: '', saved: false, err: '' };")
rep("letterRef = React.createRef();", "letterRef = React.createRef(); noteRef = React.createRef();")
rep("  componentDidMount() {\n",
    "  token() { return new URLSearchParams(location.search).get('t') || ''; }\n"
    "  countNames(para, nene) { const n = String(para || '').split(/,|\\s+y\\s+|&/).map(x => x.trim()).filter(Boolean).length; return Math.max(1, n + (nene ? 1 : 0)); }\n"
    "  send(r, extra) {\n"
    "    const t = this.token(); if (!t || !window.YO_INVITE) return;\n"
    "    const total = this.state.total || 1;\n"
    "    const note = this.noteRef.current ? this.noteRef.current.value : this.state.note;\n"
    "    this.setState({ err: '' });\n"
    "    window.YO_INVITE.respond(t, r, r === 'si' ? Math.max(0, total - 1) : 0, r === 'si' ? note : '')\n"
    "      .then(ok => { if (!ok) throw new Error('no'); if (extra) this.setState({ saved: true, note }); })\n"
    "      .catch(() => this.setState({ err: 'No pudimos guardar tu respuesta. Revisá tu conexión y probá de nuevo.' }));\n"
    "  }\n"
    "  componentDidMount() {\n"
    "    const tk = this.token();\n"
    "    if (tk && window.YO_INVITE) window.YO_INVITE.load(tk).then(d => {\n"
    "      if (!d) return;\n"
    "      const answered = d.rsvp === 'si' || d.rsvp === 'no';\n"
    "      this.setState({ para: d.para || '', nene: d.nene || '', msg: d.mensaje || '', rsvp: answered ? d.rsvp : null, note: d.note || '',\n"
    "        total: d.rsvp === 'si' ? (Number(d.plus) || 0) + 1 : this.countNames(d.para, d.nene) });\n"
    "    }).catch(() => {});\n")
rep("const para = (q.get('para') || this.props.para || '').trim();",
    "const own = !!q.get('t');\n    const para = (this.state.para || q.get('para') || (own ? '' : this.props.para) || '').trim();")
rep("const nene = (q.get('nene') || this.props.nene || '').trim();",
    "const nene = (this.state.nene || q.get('nene') || (own ? '' : this.props.nene) || '').trim();")
rep("pending: r === null, answered: r !== null,",
    "pending: r === null, answered: r !== null, yesAnswered: r === 'si',\n"
    "      hasMsg: !!this.state.msg, msg: this.state.msg, noteRef: this.noteRef, note: this.state.note,\n"
    "      total: this.state.total || this.countNames(para, nene), savedOk: this.state.saved, hasErr: !!this.state.err, err: this.state.err,\n"
    "      minus: () => this.setState(st => ({ total: Math.max(1, (st.total || this.countNames(para, nene)) - 1), saved: false })),\n"
    "      plusOne: () => this.setState(st => ({ total: Math.min(21, (st.total || this.countNames(para, nene)) + 1), saved: false })),\n"
    "      saveExtra: () => this.send('si', true),")
rep("yes: () => { this.setState({ rsvp: 'si' }); this.props.onRsvp?.('si', who); },",
    "yes: () => { this.setState(st => ({ rsvp: 'si', saved: false, total: st.total || this.countNames(para, nene) }), () => this.send('si')); this.props.onRsvp?.('si', who); },")
rep("no: () => { this.setState({ rsvp: 'no' }); this.props.onRsvp?.('no', who); },",
    "no: () => { this.setState({ rsvp: 'no', saved: false }); this.send('no'); this.props.onRsvp?.('no', who); },")
rep("reset: () => this.setState({ rsvp: null })", "reset: () => this.setState({ rsvp: null, saved: false })")

enc = json.dumps(t, ensure_ascii=False).replace('</', '<\\u002F')
s = s[:m.start(2)] + enc + s[m.end(2):]

# ---- 2) Cáscara: título, vista previa para WhatsApp y conexión ----
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt4Y2p2cXNrcnNqZWZtcWZiaHBhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTI1MjI2MDEsImV4cCI6MjEwODA5ODYwMX0.4JJpwNF2pwqecmMsM2QgF9qsHJlruwYyy-JRhpzpmyI"
head = '''<title>Baby shower de Noah · Invitación</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Tenés una invitación al baby shower de Noah. Abrila para confirmar si venís.">
  <meta property="og:title" content="Baby shower de Noah 🩵">
  <meta property="og:description" content="Tenés una invitación. Abrila para confirmar si venís.">
  <meta property="og:image" content="https://yoorganizo.vercel.app/invitaciones/noah-og.jpg">
  <meta property="og:type" content="website">
  <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.js"></script>
  <script>
  // Conexión de Yo Organizo: el invitado solo lee y responde SU invitación (por su token)
  (function () {
    var URL = "https://kxcjvqskrsjefmqfbhpa.supabase.co", KEY = "''' + KEY + '''";
    var sb = null;
    function client() { if (!sb && window.supabase) sb = window.supabase.createClient(URL, KEY, { auth: { persistSession: false } }); return sb; }
    window.YO_INVITE = {
      load: function (t) { var c = client(); if (!c) return Promise.resolve(null); return c.rpc("get_invite", { p_token: t }).then(function (r) { return r.error ? null : r.data; }); },
      respond: function (t, r, plus, note) { var c = client(); if (!c) return Promise.resolve(false); return c.rpc("respond_invite", { p_token: t, p_rsvp: r, p_plus: plus || 0, p_note: note || "" }).then(function (x) { return !x.error && x.data === true; }); }
    };
  })();
  </script>'''
assert s.count('<title>Bundled Page</title>') == 1
s = s.replace('<title>Bundled Page</title>', head)
# Pantalla de carga amigable (en vez del sobre genérico del exportador)
thumb = re.search(r'<div id="__bundler_thumbnail">.*?</div>', s, re.S)
assert thumb
loader = """<div id="__bundler_thumbnail"><div class="yo-load">
    <svg class="yo-boat" viewBox="0 0 120 100" aria-hidden="true">
      <path d="M58 12 L58 70" stroke="#8a6a4a" stroke-width="2.5"/>
      <path d="M60 16 C80 30 88 50 90 66 L60 66 Z" fill="#fff" stroke="#9fb9d1" stroke-width="2"/>
      <path d="M60 30 L86 42 M60 44 L89 54 M60 57 L90 63" stroke="#7d9fc0" stroke-width="5" opacity=".75"/>
      <path d="M56 22 C42 36 36 52 34 66 L56 66 Z" fill="#fff" stroke="#9fb9d1" stroke-width="2"/>
      <path d="M26 70 L96 70 L88 82 L34 82 Z" fill="#b98a5e"/>
    </svg>
    <svg class="yo-waves" viewBox="0 0 240 24" preserveAspectRatio="none" aria-hidden="true">
      <path d="M0 12 Q15 2 30 12 T60 12 T90 12 T120 12 T150 12 T180 12 T210 12 T240 12 V24 H0Z" fill="#a9c8e2"/>
    </svg>
    <p>Preparando tu invitación…</p>
  </div></div>"""
s = s[:thumb.start()] + loader + s[thumb.end():]
css_old = '#__bundler_thumbnail svg { width: 100%; height: 100%; object-fit: contain; }'
assert s.count(css_old) == 1
s = s.replace(css_old, """#__bundler_loading { display: none !important; }
    #__bundler_thumbnail { background: linear-gradient(180deg, #f4f9fd 0%, #e3eff8 100%); }
    .yo-load { display: flex; flex-direction: column; align-items: center; gap: 0; }
    .yo-boat { width: 120px; height: 100px; animation: yo-bob 2.4s ease-in-out infinite; transform-origin: 50% 80%; }
    .yo-waves { width: 160px; height: 16px; margin-top: -14px; animation: yo-wave 2.4s linear infinite; }
    .yo-load p { margin-top: 22px; font: italic 20px/1.3 Georgia, "Times New Roman", serif; color: #3f5f82; animation: yo-fade 1.8s ease-in-out infinite; }
    @keyframes yo-bob { 0%,100% { transform: translateY(0) rotate(-3deg); } 50% { transform: translateY(-6px) rotate(3deg); } }
    @keyframes yo-wave { from { transform: translateX(-10px); } 50% { transform: translateX(10px); } to { transform: translateX(-10px); } }
    @keyframes yo-fade { 0%,100% { opacity: .55; } 50% { opacity: 1; } }
    @media (prefers-reduced-motion: reduce) { .yo-boat, .yo-waves, .yo-load p { animation: none; } }""")

s = s.replace('This page requires JavaScript to display.', 'Para ver la invitación, activá JavaScript en tu navegador.')
open(out, 'w', encoding='utf-8').write(s)
print('ok', len(s))
