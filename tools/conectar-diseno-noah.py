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
