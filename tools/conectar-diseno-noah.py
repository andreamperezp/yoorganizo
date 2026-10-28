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
  <meta property="og:title" content="Baby shower de Noah 💙">
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
open(out, 'w', encoding='utf-8').write(s)
print('ok', len(s))
