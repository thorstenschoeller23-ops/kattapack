#!/usr/bin/env python3
"""Baut die KattaPack-Website.

   python3 build.py ausgabe
       legt die fertige Website zum Hochladen im Ordner "ausgabe" an
       (vollständige HTML-Seiten, Schriften lokal, Browser-Symbole).

   python3 build.py vorschau hosting vorschau-index.html
       baut zusätzlich die Vorschau-Variante für Claude.

Aufbau: einfacher Einstieg, Tiefe auf Abruf.
   Start · Leistungen · Preise · So starten Sie · Fragen  (+ Über uns, Kontakt, Impressum, Datenschutz)
Alle Texte stehen in diesem Skript. Design: site.css, Funktionen: site.js.
"""
import os, re, sys, shutil, hashlib

SRC = os.path.dirname(os.path.abspath(__file__))
ARGS = sys.argv[1:]
if len(ARGS) == 3:
    OUT_A, OUT_H, INDEX_A = ARGS
else:
    OUT_A, INDEX_A = None, None
    OUT_H = ARGS[0] if ARGS else os.path.join(os.getcwd(), "ausgabe")

# Platzhalter: hier die echte Adresse eintragen. Sie steht zusätzlich in site.js (EMAIL).
EMAIL = "info@kattapack.de"

GOOGLE_FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
                '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
                '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,100..900'
                '&family=IBM+Plex+Mono:wght@400;500;600&display=swap">')
LOCAL_FONTS = '<link rel="stylesheet" href="fonts/fonts.css">'

# Versionsnummer aus dem Inhalt: Browser dürfen site.css und site.js lange zwischenspeichern
# und laden sie nach jeder Änderung trotzdem neu (spart Datenvolumen beim Hoster).
def _ver(name):
    with open(os.path.join(SRC, name), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:10]
CSS_HREF = "site.css?v=" + _ver("site.css")
JS_SRC = "site.js?v=" + _ver("site.js")

# ---------------------------------------------------------------- Logo
# Das Logo liegt als Vektorgrafik in assets/ (logo-mark.svg: Katta mit Paket, logo-word.svg: Schriftzug,
# logo-tag.svg: Unterzeile). Schwarz wird auf der Website zur Textfarbe, damit es auch im dunklen Modus passt.
def _logo(name):
    t = open(os.path.join(SRC, "assets", name), encoding="utf-8").read()
    vb = re.search(r'viewBox="([^"]+)"', t).group(1)
    inner = t[t.index(">") + 1:t.rindex("</svg>")].replace('fill="#171614"', 'fill="currentColor"')
    w, h = [float(v) for v in vb.split()[2:]]
    return vb, inner, w / h

LOGO = {k: _logo("logo-%s.svg" % k) for k in ("mark", "word", "tag")}

def sprite(with_tag=False):
    names = ("mark", "word", "tag") if with_tag else ("mark", "word")
    return ('<svg class="sprite" aria-hidden="true" focusable="false">' +
            ''.join('<symbol id="kp-%s" viewBox="%s">%s</symbol>' % (k, LOGO[k][0], LOGO[k][1]) for k in names) + '</svg>')

def logo(part, cls, height):
    vb, _, ratio = LOGO[part]
    w, h = vb.split()[2:]
    # Das Symbol bringt seinen eigenen Ausschnitt mit, außen deshalb ab 0,0
    return ('<svg class="%s" viewBox="0 0 %s %s" width="%d" height="%d" aria-hidden="true" focusable="false"><use href="#kp-%s"/></svg>'
            % (cls, w, h, round(height * ratio), height, part))

def brand(size="sm"):
    big = size == "lg"
    return ('<a class="brand%s" href="index.html" aria-label="KattaPack, zur Startseite">' % (' brand-lg' if big else '') +
            logo("mark", "lm", 64 if big else 44) + logo("word", "lw", 26 if big else 20) + '</a>')

NAV = [("leistungen", "Leistungen"), ("preise", "Preise"), ("ablauf", "So starten Sie"), ("fragen", "Fragen")]

# Abschnitte je Seite: Anker, kurzer Name (Leiste), Beschreibung (Menü)
SECTIONS = {
    "leistungen": [
        ("bestellablauf", "Bestellablauf", "So läuft jede Bestellung"),
        ("stationen", "Stationen", "Wareneingang, Lager, Kommissionierung, Verpackung, Versand"),
        ("retouren", "Retouren", "Annahme, Prüfung, Wiedereinlagerung"),
        ("sonderwuensche", "Sonderwünsche", "Beilagen, Sets, Verpackung mit Ihrer Marke"),
        ("weitere", "Weitere Leistungen", "Händler, Marktplätze, Anbindung"),
    ],
    "preise": [
        ("rechner", "Stellplatz-Rechner", "Passt Ihre Ware in die kostenfreien Plätze?"),
        ("platz", "So zählen wir", "Was ein Palettenstellplatz ist"),
        ("kosten", "Kostenbausteine", "Woraus sich Ihre Kosten zusammensetzen"),
        ("mehr-platz", "Mehr Platz", "Wenn Ihr Bestand wächst"),
        ("kostenfragen", "Fragen zu Kosten", "Kurze Antworten"),
    ],
    "ablauf": [
        ("schritte", "Sechs Schritte", "Vom Gespräch bis zum ersten Paket"),
        ("anlieferung", "Anlieferung", "So kommt Ihre Ware gut bei uns an"),
        ("bekommen", "Was Sie bekommen", "Ansprechpartner, Bestand, Berichte"),
    ],
    "fragen": [
        ("haeufige-fragen", "Häufige Fragen", "Kosten, Lager, Versand, Retouren, Start"),
        ("lohnt", "Lohnt es sich?", "Wann sich Fulfillment rechnet"),
        ("vergleich", "Vergleich", "Selbst versenden oder auslagern"),
        ("pflichten", "Pflichten für Shops", "Verpackung, Elektrogeräte, Batterien"),
    ],
}
PAGE_NAMES = {"leistungen": "Leistungen", "preise": "Preise", "ablauf": "So starten Sie", "fragen": "Fragen"}

# Am Ende jeder Hauptseite: Hinweis auf die nächste Seite in Menü-Reihenfolge
NEXT = {
    "leistungen": ("preise", "Stellplatz-Rechner und alle Kostenbausteine"),
    "preise": ("ablauf", "Sechs Schritte vom Gespräch bis zum ersten Paket"),
    "ablauf": ("fragen", "Häufige Fragen, Vergleich und Pflichten für Shops"),
}

MARK_UP = ('<svg aria-hidden="true" focusable="false" viewBox="0 0 28 28" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="square">'
           '<path d="M8 21V6M4 10l4-4 4 4M20 21V6M16 10l4-4 4 4M3 25h22"/></svg>')
MARK_GLASS = ('<svg aria-hidden="true" focusable="false" viewBox="0 0 28 28" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round">'
              '<path d="M8 3h12l-1 8.5a5 5 0 0 1-10 0Z"/><path d="M14 16.5V24M9.5 25h9"/>'
              '<path d="M13 4.5l1.8 3-2 2.4 1.4 2" stroke-width="1.6"/></svg>')
MARK_DRY = ('<svg aria-hidden="true" focusable="false" viewBox="0 0 28 28" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M3 17a11 11 0 0 1 22 0Z"/><path d="M14 17v6a2.5 2.5 0 0 1-5 0"/>'
            '<path d="M7 2.5v2M14 1v2M21 2.5v2"/></svg>')


def header(active):
    parts = []
    for slug, label in NAV:
        cur = ' aria-current="page"' if slug == active else ''
        sub = ''.join('<li><a href="%s.html#%s"><b>%s</b><span>%s</span></a></li>' % (slug, sid, short, desc)
                      for sid, short, desc in SECTIONS[slug])
        parts.append('<div class="nav-item">'
                     '<a class="nav-link" href="%s.html"%s>%s</a>'
                     '<button class="nav-more" type="button" aria-expanded="false" aria-controls="m-%s" aria-label="Bereiche von %s anzeigen"><i aria-hidden="true"></i></button>'
                     '<div class="nav-menu" id="m-%s"><ul>%s</ul></div>'
                     '</div>' % (slug, cur, label, slug, label, slug, sub))
    cur = ' aria-current="page"' if active == "ueber-uns" else ''
    parts.append('<a class="nav-link solo" href="ueber-uns.html"%s>Über uns</a>' % cur)
    return ('<header class="site-header"><div class="wrap header-inner">'
            + brand() +
            '<button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav">'
            '<span class="bars" aria-hidden="true"></span><span class="label">Menü</span></button>'
            '<nav class="site-nav" id="site-nav" aria-label="Hauptnavigation">' + ''.join(parts) +
            '<a class="btn btn-small" href="kontakt.html">Angebot anfragen</a></nav>'
            '</div></header>')


def pagebar(slug):
    items = ''.join('<li><a href="#%s">%s</a></li>' % (sid, short) for sid, short, _ in SECTIONS[slug])
    return ('<nav class="pagebar" aria-label="Auf dieser Seite"><div class="wrap pagebar-inner">'
            '<span class="pagebar-title">' + PAGE_NAMES[slug] + '</span>'
            '<div class="pagebar-scroll"><ol class="pagebar-list">' + items + '</ol></div>'
            '</div></nav>')


def page_next(slug):
    if slug not in NEXT:
        return ''
    to, desc = NEXT[slug]
    return ('<nav class="page-next" aria-label="Nächste Seite"><div class="wrap">'
            '<a class="next-link" href="' + to + '.html">'
            '<span class="next-label">Weiter mit</span>'
            '<span class="next-title">' + PAGE_NAMES[to] + '</span>'
            '<span class="next-desc">' + desc + '</span>'
            '<span class="next-arr" aria-hidden="true">→</span></a></div></nav>')


def footer():
    return ('<footer class="site-footer"><div class="wrap"><div class="footer-grid">'
            '<div class="footer-col footer-brand">' + brand("lg") +
            '<p class="muted">Fulfillment für wachsende Onlineshops. Lagerung, Versand, Retouren und Sonderwünsche aus einer Hand.</p>'
            '<span class="mailline">' + EMAIL + '</span></div>'
            '<nav class="footer-col" aria-label="Seiten"><span class="kicker">Seiten</span>'
            '<a href="leistungen.html">Leistungen</a><a href="preise.html">Preise</a><a href="ablauf.html">So starten Sie</a>'
            '<a href="fragen.html">Fragen</a><a href="ueber-uns.html">Über uns</a><a href="kontakt.html">Kontakt</a></nav>'
            '<nav class="footer-col" aria-label="Direkt zu"><span class="kicker">Direkt zu</span>'
            '<a href="preise.html#rechner">Stellplatz-Rechner</a><a href="leistungen.html#retouren">Retouren</a>'
            '<a href="leistungen.html#sonderwuensche">Sonderwünsche</a><a href="ablauf.html#anlieferung">Anlieferung</a>'
            '<a href="fragen.html#haeufige-fragen">Häufige Fragen</a><a href="fragen.html#pflichten">Pflichten für Shops</a></nav>'
            '</div><div class="footer-bottom"><span>© <span data-year>2026</span> KattaPack</span>'
            '<nav aria-label="Rechtliches"><a href="impressum.html">Impressum</a><a href="datenschutz.html">Datenschutz</a><a href="barrierefreiheit.html">Barrierefreiheit</a></nav>'
            '</div></div></footer>')


def cta():
    return ('<section class="cta" aria-labelledby="cta-title">'
            '<div class="tape-strip" aria-hidden="true"><span>' + " · ".join(["KattaPack"] * 40) + '</span></div>'
            '<div class="wrap cta-inner">'
            '<h2 class="cta-title" id="cta-title">Erzählen Sie uns von Ihrem Shop<span class="dot">.</span></h2>'
            '<div class="cta-side"><p>Mit ein paar Angaben zu Ihrem Shop machen wir Ihnen ein passendes Angebot.</p>'
            '<a class="btn" href="kontakt.html">Angebot anfragen <span class="arr" aria-hidden="true">→</span></a><span class="mailline">' + EMAIL + '</span></div>'
            '</div></section>')


def hero(crumb, title, lead, visual="", actions=""):
    vis = '<div class="page-hero-visual">' + visual + '</div>' if visual else ''
    cls = 'page-hero-grid' + ('' if visual else ' single')
    return ('<section class="page-hero"><div class="wrap ' + cls + '"><div class="page-hero-copy">'
            '<nav class="crumbs" aria-label="Brotkrumen"><a href="index.html">Start</a><span aria-hidden="true">/</span>'
            '<span aria-current="page">' + crumb + '</span></nav>'
            '<h1 class="page-title">' + title + '</h1><p class="lead">' + lead + '</p>' + actions +
            '</div>' + vis + '</div></section>')


def ul(items, cls="sq"):
    return '<ul class="' + cls + '">' + ''.join('<li>' + i + '</li>' for i in items) + '</ul>'


def faq(items):
    out = []
    for q, a in items:
        out.append('<details><summary>' + q + '</summary><div class="answer"><p>' + a + '</p></div></details>')
    return '<div class="faq">' + ''.join(out) + '</div>'


def acc(id_, title, summary, panel, code=None):
    idattr = ' id="' + id_ + '"' if id_ else ''
    if code:
        head = '<span class="bin">' + code + '</span>'
        cls = 'acc'
    else:
        head = ''
        cls = 'acc plain'
    return ('<details class="' + cls + '"' + idattr + '><summary>' + head +
            '<span class="acc-title">' + title + '</span><span class="acc-sum">' + summary + '</span>'
            '<span class="acc-icon" aria-hidden="true"></span></summary><div class="acc-panel">' + panel + '</div></details>')


def svc_panel(intro, items, note_label, note, link=""):
    return ('<p class="svc-intro">' + intro + '</p><div class="svc-cols">'
            '<div><h3 class="mini">Das gehört dazu</h3>' + ul(items) + '</div>'
            '<div class="note"><span class="kicker">' + note_label + '</span><p>' + note + '</p>' + link + '</div></div>')




CHECK_ICON = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="square" aria-hidden="true">'
              '<path d="M3 8.5 6.5 12 13 4.5"/></svg>')

SLIP_IN = ('<div class="slip-in">'
           '<div class="slip-top"><span class="slip-brand">' + logo("mark", "lm", 30) + logo("word", "lw", 14) + '</span><span>Lieferschein</span></div>'
           '<div class="slip-row"><span>1×</span><span>Ihre Bestellung</span></div>'
           '<div class="slip-row"><span>' + CHECK_ICON + '</span><span>Geprüft und sorgfältig verpackt</span></div>'
           '<div class="slip-lines"><i></i><i></i><i></i></div>'
           '</div>')

TAPE_TEXT = " · ".join(["KattaPack"] * 14)

WALLS = ('<svg class="walls" viewBox="0 0 500 400" preserveAspectRatio="none" aria-hidden="true">'
         '<rect class="w-floor" x="80" y="64" width="340" height="272"/>'
         '<polygon class="w-top" points="0,0 500,0 420,64 80,64"/>'
         '<polygon class="w-left" points="0,0 80,64 80,336 0,400"/>'
         '<polygon class="w-right" points="500,0 500,400 420,336 420,64"/>'
         '<polygon class="w-bottom" points="0,400 80,336 420,336 500,400"/>'
         '<polygon class="w-shadow" points="80,64 420,64 420,82 102,82 102,336 80,336"/>'
         '</svg>')

ARROW_LEFT = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="square" aria-hidden="true">'
              '<path d="M13 8H3.5M7.5 4 3.5 8l4 4"/></svg>')

BOX = (
  '<div class="box-wrap"><div class="box" aria-hidden="true">'
  '<div class="box-inside">' + WALLS + SLIP_IN + '</div>'
  '<div class="iflap iflap-t"><div class="face f"></div><div class="face b"></div></div>'
  '<div class="iflap iflap-b"><div class="face f"></div><div class="face b"></div></div>'
  '<div class="flap flap-l"><div class="face f">'
    '<div class="print"><div class="print-logo">' + logo("mark", "lm", 120) + logo("word", "lw", 30) + logo("tag", "lt", 8) + '</div>'
    '<div class="print-marks">' + MARK_UP + MARK_GLASS + MARK_DRY + '</div></div>'
    '<div class="tape-half"><div class="tape-full"><span>' + TAPE_TEXT + '</span></div></div>'
  '</div><div class="face b"></div></div>'
  '<div class="flap flap-r"><div class="face f">'
    '<div class="tape-half"><div class="tape-full"><span>' + TAPE_TEXT + '</span></div></div>'
    '<div class="ship">'
      '<div><span class="k">Von</span><span class="v">Ihr Shop</span></div>'
      '<div class="big"><span class="k">An</span><span class="v">Ihre Kunden</span></div>'
      '<div class="ship-code"><svg class="barcode" data-barcode="26102104" viewBox="0 0 300 60" preserveAspectRatio="none" aria-hidden="true" focusable="false"></svg><span>KP 2610 2104 8270</span></div>'
      '<div class="ship-foot"><span class="k">Lagerkosten</span><span class="v">0,00&nbsp;€</span></div>'
    '</div>'
    '<span class="open-here">' + ARROW_LEFT + 'Hier öffnen</span>'
  '</div><div class="face b"></div></div>'
  '<div class="blade"><i class="blade-line"></i><i class="blade-tip"></i></div>'
  '</div></div>')


def tapeband(items):
    one = ''.join('<span>' + it + '<i></i></span>' for it in items)
    return ('<div class="tapeband" aria-hidden="true"><div class="tape-roll"><div class="tape-track">'
            + one + one + '</div></div></div>')

# ---------------------------------------------------------------- Bausteine

RACK = '''<figure class="rack" aria-label="Regalgang mit sechs Stellplätzen. Die ersten drei sind mit Ihrer Ware belegt und kostenfrei.">
<figcaption class="rack-head"><span>Gang A · Ebene 1</span><span>Stellplatz 1.200 × 800 mm</span></figcaption>
<div class="slots">
<div class="slot used"><span class="slot-id">A-01</span><span class="slot-tag">Ihre Ware</span></div>
<div class="slot used"><span class="slot-id">A-02</span><span class="slot-tag">Ihre Ware</span></div>
<div class="slot used"><span class="slot-id">A-03</span><span class="slot-tag">Ihre Ware</span></div>
<div class="rack-brace"><span>kostenfrei</span></div>
<div class="slot free"><span class="slot-id">A-04</span><span class="slot-tag">frei</span></div>
<div class="slot free"><span class="slot-id">A-05</span><span class="slot-tag">frei</span></div>
<div class="slot free"><span class="slot-id">A-06</span><span class="slot-tag">frei</span></div>
</div>
<p class="rack-note">Beispiel: 3 belegte Stellplätze ergeben <strong>0,00&nbsp;€ Lagerkosten</strong> im Monat. Ab A-04 gilt der Preis aus Ihrem Angebot.</p>
</figure>'''

RETURN_DOC = '''<figure class="doc" aria-label="Beispiel für einen Retourenschein">
<div class="doc-head"><span>Retourenschein</span><span>Beispiel</span></div>
<dl class="doc-rows">
<dt>Bestellung</dt><dd>#10482</dd>
<dt>Artikel</dt><dd>Leinenhemd, Größe M</dd>
<dt>Grund</dt><dd>Größe passt nicht</dd>
<dt>Zustand</dt><dd>Originalverpackt, ungetragen</dd>
<dt>Ergebnis</dt><dd>Zurück in den Bestand</dd>
</dl>
</figure>'''

SLIP = '''<figure class="doc" aria-label="Packhinweis mit Beispielen für Sonderwünsche">
<div class="doc-head"><span>Packhinweis · Bestellung #10482</span><span>Beispiele</span></div>
<ul class="doc-list">
<li class="done">Grußkarte mit persönlichem Text beilegen</li>
<li class="done">Geschenkverpackung, Lieferschein ohne Preise</li>
<li>Produktprobe ab einem bestimmten Bestellwert</li>
<li class="done">Artikel zu einem Set zusammenstellen</li>
<li>Versand im Karton mit Ihrem Logo</li>
<li>Seidenpapier und Sticker in Ihrer Markenfarbe</li>
<li>Vorbestellungen gesammelt zum Erscheinungstag verschicken</li>
</ul>
<div class="doc-foot"><span>Packanweisung gilt für jedes Paket</span><span>KattaPack</span></div>
</figure>'''

ROUTE = '''<div class="route" role="list">
<div class="route-step" role="listitem"><a class="station" href="#wareneingang"><span class="bin">WE</span><span class="st-name">Wareneingang</span><span class="st-text">Annahme, Zählung und Einbuchung</span></a></div>
<div class="route-step" role="listitem"><a class="station" href="#lagerung"><span class="bin">LAG</span><span class="st-name">Lagerung</span><span class="st-text">Trocken, sauber, eindeutig verortet</span></a></div>
<div class="route-step" role="listitem"><a class="station" href="#kommissionierung"><span class="bin">KOMM</span><span class="st-name">Kommissio&shy;nierung</span><span class="st-text">Bestellung zusammenstellen und prüfen</span></a></div>
<div class="route-step" role="listitem"><a class="station" href="#verpackung"><span class="bin">VP</span><span class="st-name">Verpackung</span><span class="st-text">Passender Karton, sauber verschlossen</span></a></div>
<div class="route-step" role="listitem"><a class="station" href="#versand"><span class="bin">WA</span><span class="st-name">Versand</span><span class="st-text">Übergabe an den Paketdienst</span></a></div>
<div class="route-step" role="listitem"><a class="station" href="#retouren"><span class="bin">RET</span><span class="st-name">Retouren</span><span class="st-text">Prüfen und zurück in den Bestand</span></a></div>
<div class="route-return" aria-hidden="true"><svg aria-hidden="true" focusable="false" viewBox="0 0 100 100" preserveAspectRatio="none"><path d="M100 0 V100 H0 V0" vector-effect="non-scaling-stroke"/></svg><span>Verkaufsfähige Retouren gehen zurück ins Lager</span></div>
</div>'''

COND_TABLE = '''<div class="table-wrap" tabindex="0" role="region" aria-label="Tabelle: Zustandsklassen bei Retouren"><table class="tbl">
<thead><tr><th scope="col">Klasse</th><th scope="col">Zustand</th><th scope="col">Was passiert</th></tr></thead>
<tbody>
<tr><td class="grade">A</td><td>Originalverpackt oder ungenutzt</td><td>Zurück in den Bestand</td></tr>
<tr><td class="grade">B</td><td>Geöffnet, ohne erkennbare Mängel</td><td>Nach Ihrer Vorgabe, zum Beispiel aufbereiten oder als B-Ware verkaufen</td></tr>
<tr><td class="grade">C</td><td>Beschädigt, verschmutzt oder unvollständig</td><td>Gesondert gelagert, Sie entscheiden</td></tr>
</tbody></table></div>'''

FAQ_CORE = [
    ("Was bedeutet „keine Lagerkosten“ genau?",
     "Solange Ihr Bestand auf bis zu drei Palettenstellplätze passt, berechnen wir für die Lagerung nichts. "
     "Kosten entstehen für die Arbeit an Ihren Bestellungen, zum Beispiel für Wareneingang, Pick &amp; Pack, "
     "Verpackungsmaterial, Versand und Retouren. Was genau anfällt, steht in Ihrem Angebot."),
    ("Was passiert, wenn mein Bestand größer wird?",
     "Dann wachsen wir mit. Für zusätzliche Stellplätze gilt ein fester Preis pro Stellplatz und Monat aus Ihrem Angebot. "
     "Den Platz planen wir mit Ihnen, bevor die Ware kommt."),
    ("Meine Produkte sind klein. Wie wird der Platz gezählt?",
     "Kleine Artikel lagern wir in Fachregalen. Wir schätzen mit Ihnen gemeinsam ab, wie vielen Palettenstellplätzen "
     "Ihr Bestand entspricht. Einen ersten Richtwert liefert unser <a href=\"preise.html#rechner\">Stellplatz-Rechner</a>."),
    ("Wie schnell gehen Bestellungen raus?",
     "Das hängt davon ab, wann eine Bestellung bei uns eingeht. Bis zu welcher Uhrzeit wir am selben Werktag versenden, "
     "legen wir im Angebot mit Ihnen fest."),
    ("Kann ich eigene Kartons und Beilagen verwenden?",
     "Ja. Sie schicken uns Ihr Verpackungsmaterial, und wir verwenden es für Ihre Pakete. Wird es knapp, sagen wir Ihnen rechtzeitig Bescheid."),
]

PAGES = {}

# ================================================================ Start
PAGES["index"] = ("KattaPack Fulfillment",
  "KattaPack lagert, packt und versendet Ware für Onlineshops. Keine Lagerkosten bis 3 Palettenstellplätze, Retouren und Sonderwünsche.",
  '''<section class="intro" id="intro" aria-labelledby="hero-title"><div class="intro-stage">
<div class="wrap intro-grid">
  <div class="intro-copy">
    <span class="kicker">Fulfillment für Onlineshops</span>
    <h1 class="hero-title" id="hero-title">Wir packen das<span class="dot">.</span></h1>
    <p class="hero-lead">Wir lagern Ihre Ware, packen jede Bestellung und schicken sie an Ihre Kunden.</p>
    <ul class="chips">
      <li><b>0&nbsp;€</b> Lagerkosten bis 3 Paletten</li>
      <li>Retouren nehmen wir an</li>
      <li>Sonderwünsche willkommen</li>
    </ul>
    <div class="actions"><a class="btn" href="kontakt.html">Angebot anfragen <span class="arr" aria-hidden="true">→</span></a><a class="btn btn-ghost" href="#so-gehts" data-open>Paket öffnen <span class="arr down" aria-hidden="true">→</span></a></div>
  </div>
  ''' + BOX + '''
</div>
<a class="scroll-hint" href="#so-gehts" data-open><i aria-hidden="true"></i>Zum Auspacken scrollen</a>
</div></section>

<section class="section" id="so-gehts" aria-labelledby="how-title"><div class="wrap">
<div class="section-head"><h2 id="how-title">So einfach funktioniert’s</h2></div>
<ol class="how">
<li><h3>Sie schicken uns Ihre Ware</h3><p>Per Paket oder auf Paletten. Wir zählen nach und lagern alles ordentlich ein.</p></li>
<li><h3>Wir packen jede Bestellung</h3><p>Sobald jemand in Ihrem Shop bestellt, packen wir das Paket und übergeben es dem Paketdienst.</p></li>
<li><h3>Retouren kommen zu uns</h3><p>Wir prüfen jede Rücksendung und lagern verkaufsfähige Ware wieder ein.</p></li>
</ol>
<div class="how-foot"><p>Sie kümmern sich um Ihren Shop. Den Rest erledigen wir.</p><a class="text-link" href="leistungen.html">Alle Leistungen im Detail</a></div>
</div></section>

''' + tapeband(["0 € Lagerkosten bis 3 Paletten", "Retouren nehmen wir an", "Sonderwünsche willkommen", "Sendungsnummer für jedes Paket", "Ein fester Ansprechpartner"]) + '''

<section class="section band" aria-labelledby="lager-title"><div class="wrap split">
<div class="split-text">
<h2 id="lager-title">0&nbsp;€ Lagerkosten bis drei Paletten</h2>
<p>Solange Ihre Ware auf bis zu drei Palettenstellplätze passt, zahlen Sie für die Lagerung nichts. Sie zahlen für die Arbeit an Ihren Bestellungen.</p>
<p>Mehr Ware? Kein Problem. Für jeden weiteren Stellplatz gilt ein fester Preis aus Ihrem Angebot. Den Platz planen wir rechtzeitig mit Ihnen.</p>
<div class="links"><a class="text-link" href="preise.html#rechner">Ausrechnen, ob Ihre Ware passt</a><a class="text-link" href="preise.html">Alle Preise</a></div>
</div>
<div class="split-visual">''' + RACK + '''</div>
</div></section>

<section class="section" aria-labelledby="detail-title"><div class="wrap">
<div class="section-head"><h2 id="detail-title">Alles im Detail</h2><p>Für alle, die es genau wissen möchten.</p></div>
<div class="doors">
<a class="door" href="leistungen.html"><span class="kicker">Leistungen</span><h3>Jede Station erklärt</h3><p>Vom Wareneingang über Verpackung und Versand bis zu Retouren und Sonderwünschen.</p><span class="go">Leistungen ansehen</span></a>
<a class="door" href="preise.html"><span class="kicker">Preise</span><h3>Was es kostet</h3><p>Alle Kostenbausteine und der Stellplatz-Rechner.</p><span class="go">Preise ansehen</span></a>
<a class="door" href="ablauf.html"><span class="kicker">So starten Sie</span><h3>Der Weg zum ersten Paket</h3><p>Sechs Schritte, eine Checkliste und Hinweise zur Anlieferung.</p><span class="go">Ablauf ansehen</span></a>
<a class="door" href="fragen.html"><span class="kicker">Fragen</span><h3>Antworten und Wissen</h3><p>Häufige Fragen, Vergleich und Pflichten für Shops.</p><span class="go">Fragen ansehen</span></a>
</div>
</div></section>
''')

# ================================================================ Leistungen
def group(title, items):
    return '<div class="item"><h3>' + title + '</h3>' + ul(items) + '</div>'

STATIONS = ''.join([
  acc("wareneingang", "Wareneingang", "Annahme, Zählung und Einbuchung Ihrer Ware", svc_panel(
      "Ihre Ware kommt per Paket oder auf Paletten bei uns an. Wir gleichen die Lieferung mit Ihrer Ankündigung ab, zählen nach und buchen sie in den Bestand. Abweichungen melden wir Ihnen, bevor sie zum Problem werden.",
      ["Annahme von Paketen und Paletten", "Abgleich mit Avis und Lieferschein", "Zählung nach Artikel und Variante",
       "Sichtprüfung auf Transportschäden", "Fotos bei Schäden oder Abweichungen", "Bestandsmeldung an Sie nach der Einlagerung"],
      "Gut zu wissen",
      "Je besser eine Lieferung vorbereitet ist, desto schneller ist sie verkaufsbereit. Was dazu gehört, steht in unseren Anlieferhinweisen.",
      '<a class="text-link" href="ablauf.html#anlieferung">Zu den Anlieferhinweisen</a>'), "WE"),
  acc("lagerung", "Lagerung", "Trocken, sauber und bis 3 Palettenstellplätze ohne Lagerkosten", svc_panel(
      "Ihre Ware liegt trocken, sauber und geordnet. Jeder Artikel bekommt einen eindeutigen Lagerplatz, damit beim Packen nichts gesucht werden muss. Bis drei Palettenstellplätze kostet die Lagerung nichts.",
      ["Palettenstellplätze für größere Mengen", "Fachregale für kleine Artikel", "Lagerung nach Artikel und Variante",
       "Mindesthaltbarkeit und Chargen auf Wunsch (FEFO)", "Bestandsübersicht in festen Abständen", "Inventur nach Absprache"],
      "Gut zu wissen",
      "Ware mit besonderen Anforderungen, etwa Lebensmittel, Kosmetik oder Produkte mit Akkus, besprechen wir vorab. So wissen Sie vor dem Start, was zu beachten ist.",
      '<a class="text-link" href="preise.html#rechner">Stellplatzbedarf berechnen</a>'), "LAG"),
  acc("kommissionierung", "Kommissio&shy;nierung", "Jede Bestellung zusammenstellen und vor dem Verpacken prüfen", svc_panel(
      "Sobald eine Bestellung bei uns eingeht, stellen wir sie zusammen. Artikel, Variante und Menge werden vor dem Verpacken mit der Bestellung abgeglichen. So kommt bei Ihrem Kunden an, was er bestellt hat.",
      ["Einzel- und Mehrfachbestellungen", "Sets und Bundles aus mehreren Artikeln", "Abgleich von Artikel, Variante und Menge",
       "Vorziehen von Expressbestellungen", "Teillieferungen nach Ihrer Vorgabe", "Vorbestellungen gesammelt zum Stichtag"],
      "Versandschluss",
      "Bis zu welcher Uhrzeit eine Bestellung noch am selben Werktag rausgeht, legen wir im Angebot mit Ihnen fest."), "KOMM"),
  acc("verpackung", "Verpackung", "Passender Karton, ordentlich gepolstert, sauber verschlossen", svc_panel(
      "Wir wählen den Karton passend zur Bestellung, polstern nach Bedarf und verschließen sauber. Ihr Kunde bekommt ein Paket, das ordentlich aussieht und heil ankommt.",
      ["Kartons und Versandtaschen in passender Größe", "Polsterung je nach Produkt", "Lieferschein oder Rechnung im Paket",
       "Beilagen wie Flyer, Proben oder Karten", "Ihre eigenen Kartons und Materialien", "Geschenkverpackung auf Wunsch"],
      "Weniger Luft im Karton",
      "Die EU-Verpackungsverordnung sieht ab 2030 höchstens 50&nbsp;% Leerraum in Versandverpackungen vor. Passende Kartons sparen schon heute Füllmaterial und oft auch Versandkosten.",
      '<a class="text-link" href="fragen.html#pflichten">Pflichten für Shops</a>'), "VP"),
  acc("versand", "Versand", "Übergabe an den Paketdienst, Sendungsnummer für Ihre Kunden", svc_panel(
      "Wir erstellen das Versandlabel, übergeben das Paket an den Paketdienst und geben die Sendungsnummer an Ihren Shop weiter. So kann Ihr Kunde sein Paket verfolgen.",
      ["Versand mit gängigen Paketdiensten", "Sendungsnummern für Ihre Kunden", "Versand innerhalb Deutschlands",
       "Versand ins Ausland auf Anfrage", "Expressversand auf Anfrage", "Palettenversand für größere Lieferungen"],
      "Gut zu wissen",
      "Welche Paketdienste für Ihren Shop passen, hängt von Größe, Gewicht und Zielländern Ihrer Pakete ab. Das klären wir im Angebot."), "WA"),
])

RETOUR_ACCS = ''.join([
  acc("zustandsklassen", "Drei Zustandsklassen", "Damit bei jeder Rücksendung klar ist, was mit ihr passiert",
      '<p>Was mit Ware der Klassen B und C geschieht, legen Sie fest. Möglich sind zum Beispiel Aufbereitung, Verkauf als B-Ware, Rücksendung an Sie oder Entsorgung.</p>' + COND_TABLE),
  acc("aufbereitung", "Aufbereitung", "Fast neue Retouren wieder verkaufsfähig machen",
      '<p>Viele Retouren sind fast neu. Mit wenig Aufwand werden sie wieder verkaufsfähig. Was wir aufbereiten, legen Sie fest. Wir rechnen es nach Aufwand ab.</p>' +
      ul(["Neu falten und verpacken", "Polybeutel oder Etiketten erneuern", "Vollständigkeit prüfen: Zubehör, Anleitung, Etiketten",
          "Leichte Verschmutzungen entfernen, wenn das Material es zulässt", "Fotos von Mängeln als Grundlage für Ihre Entscheidung"])),
  acc("tempo", "Warum Tempo bei Retouren zählt", "14 Tage Erstattungsfrist nach einem Widerruf",
      '<p>Nach einem Widerruf müssen Onlinehändler den Kaufpreis innerhalb von 14 Tagen erstatten. Die Frist beginnt, sobald der Widerruf bei Ihnen eingeht (§&nbsp;357 Abs.&nbsp;1 BGB).</p>'
      '<p>Sie dürfen die Erstattung zurückhalten, bis die Ware wieder da ist oder der Kunde den Versand nachweist (§&nbsp;357 Abs.&nbsp;4 BGB). Je schneller eine Retoure geprüft ist, desto früher wissen Sie, ob alles vollständig zurückkam. Verkaufsfähige Ware steht schneller wieder im Shop.</p>'
      '<p class="muted">Allgemeine Information, keine Rechtsberatung. Stand: Oktober 2026.</p>'),
  acc("retourenregeln", "Ihre Retourenregeln", "Was wir vor dem Start von Ihnen wissen sollten",
      ul(["Welche Artikel wieder in den Bestand dürfen", "Ab wann Ware als B-Ware gilt", "Was mit beschädigter oder unvollständiger Ware passiert",
          "Ob Sie Fotos von Mängeln möchten", "Wie und wie oft Sie benachrichtigt werden möchten", "Unsere Adresse als Retourenadresse in Ihrem Shop"]) +
      '<p>Wenn Ihre Kunden einen Rücksendegrund angeben, erfassen wir ihn auf Wunsch. Häufen sich Gründe wie „fällt klein aus“, wissen Sie, wo Sie bei Größentabellen, Fotos oder Beschreibungen nachbessern können.</p>'),
])

WISH_ACCS = ''.join([
  acc("moeglichkeiten", "Was alles möglich ist", "Unboxing, Beilagen, Geschenke, Sets, Launches und Marktplätze",
      '<div class="grid-3">' +
      group("Auspacken mit Wirkung", ["Kartons und Versandtaschen mit Ihrem Logo", "Seidenpapier, Sticker und Siegel", "Füllmaterial in Ihrer Farbe", "Anordnung im Karton nach Ihrer Fotovorlage"]) +
      group("Beilagen", ["Flyer, Gutscheine und Dankeskarten", "Produktproben ab einem Bestellwert oder für Neukunden", "Handgeschriebene Karten", "Beilagen nur für bestimmte Artikel oder Aktionen"]) +
      group("Geschenke", ["Geschenkverpackung", "Grußkarte mit Text aus der Bestellung", "Lieferschein ohne Preise", "Versand direkt an die beschenkte Person"]) +
      group("Sets und Konfektionierung", ["Artikel zu Sets zusammenstellen", "Geschenk- und Probierboxen bestücken", "Großgebinde in Einzelverpackungen umpacken", "Etikettieren mit EAN, Hinweisen oder Übersetzungen"]) +
      group("Launches und Aktionen", ["Vorbestellungen sammeln und zum Stichtag versenden", "Crowdfunding-Belohnungen verschicken", "Abo-Boxen in festen Abständen packen", "Saisonbeilagen, etwa im Weihnachtsgeschäft"]) +
      group("Händler und Marktplätze", ["Vorbereitung für Amazon-Lager: FNSKU, Beutel, Sets", "Lieferungen nach Händlervorgaben", "Umetikettieren von Ware", "Musterpakete für Ihren Vertrieb"]) +
      '</div>'),
  acc("standard", "So wird aus einem Wunsch ein Standard", "Damit Paket Nummer 500 genauso aussieht wie Paket Nummer 1",
      '<ol class="vsteps">'
      '<li><b>Beschreiben</b><span>Ein Foto, eine Skizze oder ein Musterpaket von Ihnen genügt.</span></li>'
      '<li><b>Musterpaket</b><span>Wir packen ein Muster und schicken Ihnen Fotos oder das Paket selbst. Sie geben es frei.</span></li>'
      '<li><b>Packanweisung</b><span>Wir halten alles schriftlich fest: Karton, Polster, Beilagen, Reihenfolge.</span></li>'
      '<li><b>Umsetzung</b><span>Jede passende Bestellung wird danach gepackt. Änderungen sind jederzeit möglich.</span></li>'
      '</ol>'),
  acc("wunsch-kosten", "Was Sonderwünsche kosten", "Nach Aufwand, vorher vereinbart",
      '<p>Sonderwünsche rechnen wir nach Aufwand ab. Den Preis kennen Sie, bevor wir starten. Material wie Karten, Sticker oder Kartons stellen Sie oft selbst. Wir lagern es zusammen mit Ihrer Ware.</p>'
      '<p>Wenn ein Wunsch die Ware gefährdet oder wir ihn nicht in gleichbleibender Qualität umsetzen können, sagen wir Ihnen das vorher und schlagen eine Lösung vor.</p>'),
])

MORE_ACCS = ''.join([
  acc("b2b", "Händler und Marktplätze", "Belieferung von Läden, Händlern und Marktplatz-Lagern", svc_panel(
      "Neben Paketen an Endkunden beliefern wir auf Wunsch auch Läden, Händler und Marktplatz-Lager. Dabei halten wir uns an deren Vorgaben für Lieferscheine, Etiketten und Verpackung.",
      ["Belieferung von Händlern und Concept Stores", "Lieferscheine und Etiketten nach Händlervorgabe", "Palettenversand per Spedition",
       "Vorbereitung für Amazon-Lager: FNSKU-Etiketten, Beutel, Sets", "Bestellungen aus Marktplätzen wie Amazon, eBay oder Etsy", "Umetikettieren von Ware"],
      "Gut zu wissen",
      "Marktplätze und Händler haben eigene Vorgaben. Schicken Sie uns diese vorab, dann bereiten wir jede Lieferung passend vor."), "B2B"),
  acc("anbindung", "Anbindung und Übersicht", "Bestellungen, Sendungsnummern und Bestand zwischen Ihrem Shop und uns", svc_panel(
      "Wie Ihre Bestellungen zu uns kommen, hängt von Ihrem Shopsystem ab. Wir klären das vor dem Start, richten die Übertragung ein und testen sie mit Ihnen. Danach laufen Bestellungen und Sendungsnummern zuverlässig zwischen Ihrem Shop und uns.",
      ["Übertragung der Bestellungen aus Ihrem Shop", "Rückmeldung von Versandstatus und Sendungsnummern", "Bestandslisten in festen Abständen",
       "Auswertung von Retouren und Rücksendegründen", "Ein persönlicher Ansprechpartner", "Abrechnung nach den Preisen aus Ihrem Angebot"],
      "Ihr Shopsystem",
      "Sie arbeiten mit Shopify, WooCommerce, Shopware, JTL oder einem anderen System? Sagen Sie uns, womit Sie arbeiten. Wir prüfen die Anbindung, bevor Sie ein Angebot bekommen."), "IT"),
  acc("nachweise", "Nachweise vor dem Start", "Registrierungen, die wir gesetzlich prüfen müssen",
      '<p>Fulfillment-Dienstleister müssen vor dem Start prüfen, ob ihre Auftraggeber bestimmte Registrierungen haben. Sonst dürfen sie für diese Ware nicht tätig werden. Wir fragen deshalb nach:</p>' +
      ul(["Registrierungsnummer im Verpackungsregister LUCID", "Bei Elektro- und Elektronikgeräten: WEEE-Registrierung der stiftung ear",
          "Bei Batterien, auch eingebauten: Registrierung nach dem Batterierecht", "Bei Unternehmen außerhalb der EU: verantwortlicher Wirtschaftsakteur nach der Produktsicherheitsverordnung"]) +
      '<div><a class="text-link" href="fragen.html#pflichten">Pflichten für Shops erklärt</a></div>', "§"),
])

PAGES["leistungen"] = ("Leistungen · KattaPack",
  "Wareneingang, Lagerung, Kommissionierung, Verpackung, Versand, Retouren, Sonderwünsche und B2B: alle Fulfillment-Leistungen von KattaPack.",
  hero("Leistungen", "Leistungen",
       "Alles, was wir für Ihren Shop erledigen, vom Wareneingang bis zur Retoure. Öffnen Sie einen Punkt, wenn Sie die Details wissen möchten.",
       "", '<div class="actions"><a class="btn" href="kontakt.html">Angebot anfragen</a><a class="text-link" href="preise.html">Preise ansehen</a></div>') +
  '''<section class="section" id="bestellablauf" aria-labelledby="flow-title"><div class="wrap">
<div class="section-head row"><h2 id="flow-title">So läuft jede Bestellung</h2><p>Sechs Stationen, ein Ansprechpartner. Tippen Sie auf eine Station, um zu den Details zu springen.</p></div>
''' + ROUTE + '''
</div></section>

<section class="section band" id="stationen" aria-labelledby="stationen-title"><div class="wrap">
<div class="section-head"><h2 id="stationen-title">Die Stationen im Detail</h2></div>
<div class="acc-list">''' + STATIONS + '''</div>
</div></section>

<section class="section" id="retouren" aria-labelledby="ret-title"><div class="wrap">
<div class="split top">
<div class="split-text">
<span class="bin">RET</span>
<h2 id="ret-title">Retouren nehmen wir Ihnen ab</h2>
<p>Rücksendungen Ihrer Kunden kommen direkt zu uns. Wir prüfen jede Retoure, lagern verkaufsfähige Ware wieder ein und melden Ihnen, was zurückkam. So können Sie schnell erstatten und schnell wieder verkaufen.</p>
<ol class="vsteps">
<li><b>Rücksendung</b><span>Ihr Kunde schickt das Paket an unsere Retourenadresse.</span></li>
<li><b>Eingang</b><span>Wir ordnen das Paket der ursprünglichen Bestellung zu.</span></li>
<li><b>Prüfung</b><span>Jeder Artikel wird auf Zustand und Vollständigkeit geprüft.</span></li>
<li><b>Einordnung</b><span>Verkaufsfähige Ware geht zurück in den Bestand.</span></li>
<li><b>Rückmeldung</b><span>Sie erfahren, was zurückkam, und lösen die Erstattung aus.</span></li>
</ol>
</div>
<div class="split-visual">''' + RETURN_DOC + '''</div>
</div>
<div class="acc-list after-split">''' + RETOUR_ACCS + '''</div>
</div></section>

<section class="section band" id="sonderwuensche" aria-labelledby="wish-title"><div class="wrap">
<div class="split">
<div class="split-text">
<span class="bin">VP+</span>
<h2 id="wish-title">Sonderwünsche gehören bei uns dazu</h2>
<p>Ihr Paket ist oft der erste echte Kontakt mit Ihrer Marke. Sagen Sie uns, wie es aussehen soll. Wir halten es in einer Packanweisung fest und setzen es bei jeder Bestellung gleich um.</p>
<p>Bei uns sprechen Sie direkt mit den Leuten, die Ihre Pakete packen. Deshalb ist so etwas schnell geklärt.</p>
</div>
<div class="split-visual">''' + SLIP + '''</div>
</div>
<div class="acc-list after-split">''' + WISH_ACCS + '''</div>
</div></section>

<section class="section" id="weitere" aria-labelledby="mehr-title"><div class="wrap">
<div class="section-head"><h2 id="mehr-title">Weitere Leistungen</h2></div>
<div class="acc-list">''' + MORE_ACCS + '''</div>
</div></section>''')

# ================================================================ Preise
CALC = '''<div class="calc" id="calc">
<form class="calc-in" aria-labelledby="rechner-title">
<div class="field"><label for="c-count">Anzahl Kartons</label><div class="unit-wrap"><input id="c-count" type="number" inputmode="numeric" min="1" step="1" value="100"><span class="unit">Stk.</span></div></div>
<div class="row-3">
<div class="field"><label for="c-l">Länge</label><div class="unit-wrap"><input id="c-l" type="number" inputmode="decimal" min="1" step="1" value="40"><span class="unit">cm</span></div></div>
<div class="field"><label for="c-b">Breite</label><div class="unit-wrap"><input id="c-b" type="number" inputmode="decimal" min="1" step="1" value="30"><span class="unit">cm</span></div></div>
<div class="field"><label for="c-h">Höhe</label><div class="unit-wrap"><input id="c-h" type="number" inputmode="decimal" min="1" step="1" value="30"><span class="unit">cm</span></div></div>
</div>
<p class="calc-note">Voreingestellt ist ein Beispiel. Tragen Sie die Maße Ihrer Versandkartons ein, so wie die Ware bei uns ankommt.</p>
</form>
<div class="calc-out" aria-live="polite">
<div class="calc-num"><strong id="c-num">3</strong><span id="c-unit">Palettenstellplätze</span></div>
<p class="calc-status ok" id="c-status">Passt in die kostenfreien Stellplätze. Lagerkosten: 0,00 € im Monat.</p>
<div class="pal-viz" id="c-viz" aria-hidden="true"></div>
<p class="calc-break" id="c-break">8 Kartons pro Lage × 5 Lagen = 40 Kartons pro Stellplatz</p>
<p class="calc-note">Grundlage: Europalette mit 120 × 80 cm Grundfläche, Ladehöhe bis 1,50 m, Kartons stehen aufrecht. Das Ergebnis ist eine Schätzung. Den genauen Platzbedarf klären wir mit Ihnen.</p>
</div>
</div>'''

PRICE_DOC = '''<figure class="doc" aria-label="Preise auf einen Blick">
<div class="doc-head"><span>Auf einen Blick</span><span>Preise</span></div>
<dl class="doc-rows">
<dt>Lagerung</dt><dd><span class="zero">0,00&nbsp;€</span> bis 3 Palettenstellplätze</dd>
<dt>Mehr Platz</dt><dd>Fester Preis pro Stellplatz und Monat</dd>
<dt>Bestellungen</dt><dd>Nach Bausteinen, zum Beispiel Pick &amp; Pack und Versand</dd>
<dt>Angebot</dt><dd>Schriftlich, vor dem Start</dd>
</dl>
</figure>'''

PAGES["preise"] = ("Preise · KattaPack",
  "Keine Lagerkosten bis 3 Palettenstellplätze. Stellplatz-Rechner und alle Kostenbausteine im Fulfillment bei KattaPack.",
  hero("Preise", "Preise",
       "Bis drei Palettenstellplätze zahlen Sie keine Lagerkosten. Alles andere rechnen wir nach Bausteinen ab. Alle Preise stehen vorher in Ihrem schriftlichen Angebot.",
       PRICE_DOC,
       '<div class="actions"><a class="btn" href="#rechner">Bedarf berechnen</a><a class="text-link" href="#kosten">Kostenbausteine ansehen</a></div>') +
  '''<section class="section" id="rechner" aria-labelledby="rechner-title"><div class="wrap">
<div class="section-head row"><h2 id="rechner-title">Passt Ihre Ware in die kostenfreien Stellplätze?</h2><p>Geben Sie Anzahl und Maße Ihrer Kartons ein. Der Rechner schätzt, wie viele Palettenstellplätze Sie brauchen.</p></div>
''' + CALC + '''
</div></section>

<section class="section band" id="platz" aria-labelledby="regal-title"><div class="wrap split">
<div class="split-text"><h2 id="regal-title">So zählen wir den Platz</h2>
<p>Ein Palettenstellplatz ist der Platz, den eine Europalette mit 1.200 × 800&nbsp;mm im Regal einnimmt. Solange Ihr Bestand auf bis zu drei solcher Plätze passt, berechnen wir für die Lagerung nichts.</p>
<p>Kleine Artikel lagern wir in Fachregalen. Wie viel Stellplatz das entspricht, schätzen wir vorab mit Ihnen ab.</p></div>
<div class="split-visual">''' + RACK + '''</div>
</div></section>

<section class="section" id="kosten" aria-labelledby="kosten-title"><div class="wrap">
<div class="section-head"><h2 id="kosten-title">Woraus sich Ihre Kosten zusammensetzen</h2><p>Fulfillment wird meist nach Bausteinen abgerechnet. So zahlen Sie für das, was tatsächlich anfällt.</p></div>
<div class="table-wrap" tabindex="0" role="region" aria-label="Tabelle: Kostenbausteine"><table class="tbl">
<thead><tr><th scope="col">Baustein</th><th scope="col">Was dazugehört</th><th scope="col">Abrechnung</th></tr></thead>
<tbody>
<tr><th scope="row">Lagerung</th><td>Platz im Regal für Ihre Ware</td><td><span class="hi">0,00&nbsp;€ bis 3 Palettenstellplätze</span>, darüber pro Stellplatz und Monat</td></tr>
<tr><th scope="row">Wareneingang</th><td>Annahme, Zählung, Einlagerung</td><td>pro Palette oder Karton</td></tr>
<tr><th scope="row">Pick &amp; Pack</th><td>Bestellung zusammenstellen und verpacken</td><td>pro Bestellung, weitere Artikel je Stück</td></tr>
<tr><th scope="row">Verpackungsmaterial</th><td>Kartons, Polster, Klebeband</td><td>nach Verbrauch, oder Sie stellen eigenes Material</td></tr>
<tr><th scope="row">Versand</th><td>Übergabe an den Paketdienst</td><td>je nach Paketdienst, Gewicht, Größe und Ziel</td></tr>
<tr><th scope="row">Retouren</th><td>Annahme, Prüfung, Einordnung, Rückmeldung</td><td>pro Retoure</td></tr>
<tr><th scope="row">Sonderwünsche</th><td>Beilagen, Sets, Geschenkverpackung, Aufbereitung</td><td>nach Aufwand, vorher vereinbart</td></tr>
</tbody></table></div>
<p class="table-note">Alle Bausteine und Preise stehen in Ihrem schriftlichen Angebot.</p>

</div></section>

<section class="section inverse" id="mehr-platz" aria-labelledby="mehrplatz-title"><div class="wrap grow">
<h2 class="grow-title" id="mehrplatz-title">Mehr als drei Stellplätze<span class="dot">?</span></h2>
<div class="grow-body">
<p class="lead">Kein Problem. Für zusätzliche Plätze gilt ein fester Preis pro Stellplatz und Monat aus Ihrem Angebot. Wir planen den Platz mit Ihnen, bevor die Ware kommt.</p>
<dl class="facts">
<div><dt>Die ersten drei</dt><dd>Bleiben Teil Ihres Angebots mit 0,00&nbsp;€ Lagerkosten.</dd></div>
<div><dt>Jeder weitere</dt><dd>Fester Preis pro Stellplatz und Monat, schriftlich vereinbart.</dd></div>
<div><dt>Planung</dt><dd>Saisonware und große Lieferungen stimmen wir vorab mit Ihnen ab.</dd></div>
</dl>
</div>
</div></section>

<section class="section" id="kostenfragen" aria-labelledby="pfaq-title"><div class="wrap split top">
<div class="split-text"><h2 id="pfaq-title">Fragen zu Kosten</h2><div class="links"><a class="text-link" href="fragen.html#kosten">Alle Fragen zu Kosten</a></div></div>
<div class="split-visual">''' + faq([FAQ_CORE[0], FAQ_CORE[1], FAQ_CORE[2],
    ("Kosten Sonderwünsche extra?", "Ja, nach Aufwand. Den Preis vereinbaren wir, bevor wir starten.")]) + '''</div>
</div></section>''')

# ================================================================ So starten Sie
CHECK_DOC = '''<figure class="doc" aria-label="Checkliste: Was Sie für den Start bereithalten sollten">
<div class="doc-head"><span>Für den Start bereithalten</span><span>Checkliste</span></div>
<ul class="doc-list">
<li>Artikelliste mit SKU, Bezeichnung und EAN</li>
<li>Maße und Gewicht je Artikel</li>
<li>Ungefähre Bestellmengen pro Monat</li>
<li>Wünsche zu Verpackung und Beilagen</li>
<li>Ihre Retourenregeln</li>
<li>LUCID-Nummer, gegebenenfalls WEEE- und Batterie-Registrierung</li>
<li>Ansprechpartner für Ihr Shopsystem</li>
</ul></figure>'''

CARTON_DOC = '''<figure class="doc" aria-label="Beispiel für ein Kartonetikett bei der Anlieferung">
<div class="doc-head"><span>Kartonetikett</span><span>Beispiel</span></div>
<dl class="doc-rows">
<dt>Artikel</dt><dd>Leinenhemd, blau</dd>
<dt>Variante</dt><dd>Größe M</dd>
<dt>SKU</dt><dd>LH-BL-M</dd>
<dt>Menge</dt><dd>24 Stück</dd>
<dt>Karton</dt><dd>3 von 12</dd>
<dt>MHD / Charge</dt><dd>entfällt</dd>
</dl>
<div class="doc-code"><svg class="barcode" data-barcode="8817" viewBox="0 0 300 60" preserveAspectRatio="none" aria-hidden="true"></svg><span>LH-BL-M · 24</span></div>
</figure>'''

PAGES["ablauf"] = ("So starten Sie · KattaPack",
  "So starten Sie mit KattaPack: sechs Schritte vom Gespräch bis zum ersten Paket, Checkliste und Anlieferhinweise.",
  hero("So starten Sie", "So starten Sie",
       "Vom ersten Gespräch bis zum ersten versendeten Paket in sechs Schritten. Sie haben dabei einen festen Ansprechpartner.",
       CHECK_DOC,
       '<div class="actions"><a class="btn" href="kontakt.html">Gespräch anfragen</a><a class="text-link" href="#anlieferung">Zu den Anlieferhinweisen</a></div>') +
  '''<section class="section" id="schritte" aria-labelledby="schritte-title"><div class="wrap">
<div class="section-head"><h2 id="schritte-title">Sechs Schritte</h2><p>Was wir tun und was wir dafür von Ihnen brauchen.</p></div>
<ol class="steps">
<li><h3>Gespräch</h3><p>Sie erzählen uns, was Sie verkaufen, wie viele Bestellungen Sie haben und was Ihnen bei Verpackung und Retouren wichtig ist. Wir sagen Ihnen ehrlich, ob und wie wir helfen können.</p><p class="yours"><b>Ihr Teil</b>Eckdaten zu Shop, Produkten und Mengen</p></li>
<li><h3>Angebot</h3><p>Sie bekommen ein schriftliches Angebot mit allen Kostenbausteinen. Lagerung bis drei Palettenstellplätze ist darin mit 0,00&nbsp;€ ausgewiesen.</p><p class="yours"><b>Ihr Teil</b>Angebot prüfen, Fragen stellen</p></li>
<li><h3>Einrichtung</h3><p>Wir legen Ihre Artikel mit Maßen, Gewicht und Barcodes an, schreiben mit Ihnen die Packanweisung und richten die Übertragung der Bestellungen ein.</p><p class="yours"><b>Ihr Teil</b>Artikelliste, Registrierungen, Zugang zum Shopsystem</p></li>
<li><h3>Testlauf</h3><p>Wir spielen Testbestellungen durch, prüfen die Rückmeldung der Sendungsnummern und packen auf Wunsch ein Musterpaket.</p><p class="yours"><b>Ihr Teil</b>Musterpaket freigeben</p></li>
<li><h3>Anlieferung</h3><p>Ihre Ware kommt zu uns. Wir zählen sie, prüfen sie auf Schäden, lagern sie ein und melden Ihnen den Bestand.</p><p class="yours"><b>Ihr Teil</b>Anlieferung ankündigen, Lieferschein beilegen</p></li>
<li><h3>Start</h3><p>Ab jetzt gehen Ihre Bestellungen bei uns ein und raus an Ihre Kunden. Retouren kommen direkt zu uns. Ihr Ansprechpartner bleibt derselbe.</p><p class="yours"><b>Ihr Teil</b>Sich um Ihren Shop kümmern</p></li>
</ol>
</div></section>

<section class="section band" id="anlieferung" aria-labelledby="anl-title"><div class="wrap">
<div class="section-head"><h2 id="anl-title">So kommt Ihre Ware gut bei uns an</h2><p>Je besser eine Lieferung vorbereitet ist, desto schneller steht sie zum Verkauf bereit. Anlieferzeiten stimmen wir mit Ihnen ab.</p></div>
<div class="split top">
<div class="split-visual"><figure class="doc" aria-label="Anlieferhinweise">
<div class="doc-head"><span>Anlieferhinweise</span><span>KattaPack</span></div>
<ul class="doc-list">
<li>Anlieferung vorher ankündigen: Datum, Anzahl Pakete oder Paletten, Artikel und Mengen</li>
<li>Lieferschein mit Artikelnummern und Mengen beilegen</li>
<li>Kartons außen beschriften: Artikelnummer, Bezeichnung, Stückzahl</li>
<li>Möglichst ein Artikel pro Karton, gemischte Kartons deutlich kennzeichnen</li>
<li>Paletten sauber stapeln und sichern, bevorzugt auf Europaletten</li>
<li>Barcodes (EAN) auf den Artikeln, falls vorhanden</li>
<li>Bei Ware mit MHD oder Charge: Angaben auf Karton und Lieferschein</li>
</ul></figure></div>
<div class="split-visual">''' + CARTON_DOC + '''<p class="muted after-note">Sichtbare Transportschäden halten wir bei der Annahme fest und melden sie Ihnen mit Fotos.</p></div>
</div>
</div></section>

<section class="section" id="bekommen" aria-labelledby="bekommen-title"><div class="wrap">
<div class="section-head"><h2 id="bekommen-title">Was Sie von uns bekommen</h2></div>
<div class="grid-3">
<div class="item"><h3>Einen festen Ansprechpartner</h3><p>Der Ihre Artikel, Ihre Packanweisung und Ihre Besonderheiten kennt.</p></div>
<div class="item"><h3>Bestandsmeldung</h3><p>Nach jeder Anlieferung erfahren Sie, was eingelagert wurde.</p></div>
<div class="item"><h3>Bestandsübersicht</h3><p>In festen Abständen und jederzeit auf Anfrage.</p></div>
<div class="item"><h3>Meldung bei Abweichungen</h3><p>Fehlmengen, Schäden oder Unklarheiten erfahren Sie direkt von uns.</p></div>
<div class="item"><h3>Retourenberichte</h3><p>Was zurückkam, in welchem Zustand und auf Wunsch mit Rücksendegrund.</p></div>
<div class="item"><h3>Klare Abrechnung</h3><p>Nach den Preisen aus Ihrem Angebot, nachvollziehbar nach Bausteinen.</p></div>
</div>
</div></section>''')

# ================================================================ Fragen und Wissen
FAQ_GROUPS = [
    ("allgemein", "Allgemein", [
        ("Was ist Fulfillment überhaupt?", "Fulfillment umfasst alle Schritte zwischen Bestellung und Lieferung: Ware annehmen und lagern, Bestellungen zusammenstellen, verpacken, versenden und Retouren bearbeiten. Wer Fulfillment auslagert, übergibt diese Arbeit einem Dienstleister. Shop, Sortiment, Marketing und Kundenkontakt bleiben bei Ihnen."),
        ("Was macht KattaPack genau?", "Wir lagern die Ware von Onlineshops, packen ihre Bestellungen und verschicken sie an deren Kunden. Dazu kommen Retouren, Sonderwünsche bei der Verpackung und auf Wunsch die Belieferung von Händlern."),
        ("Für welche Shops ist KattaPack gedacht?", "Für Onlineshops, die wachsen und das Packen abgeben möchten. Besonders gut passen Marken, die Wert auf ihre Verpackung legen, und Shops mit vielen Retouren."),
        ("Steht KattaPack auf meinen Paketen?", "Auf Wunsch versenden wir unter dem Namen Ihres Shops. Ihre Kunden sehen dann Ihre Marke."),
    ]),
    ("kosten", "Kosten", [
        FAQ_CORE[0], FAQ_CORE[1],
        ("Welche Kosten entstehen insgesamt?", "Kosten entstehen für die Arbeit an Ihren Bestellungen, etwa Wareneingang, Pick &amp; Pack, Verpackungsmaterial, Versand und Retouren. Alle Bausteine stehen mit Preisen in Ihrem Angebot. Eine Übersicht finden Sie unter <a href=\"preise.html#kosten\">Preise</a>."),
        ("Kosten Sonderwünsche extra?", "Ja, nach Aufwand. Den Preis vereinbaren wir, bevor wir starten."),
    ]),
    ("lager", "Lager und Ware", [
        FAQ_CORE[2],
        ("Welche Produkte lagern Sie?", "Die meisten Produkte, die per Paket verschickt werden. Ware mit besonderen Anforderungen, etwa Lebensmittel mit Mindesthaltbarkeit, Kosmetik, zerbrechliche Artikel oder Produkte mit Akkus, besprechen wir vorab."),
        ("Ist meine Ware versichert?", "Wie Ihre Ware im Lager und auf dem Versandweg abgesichert ist, regeln wir im Angebot. Fragen Sie gern gezielt danach."),
        ("Wie behalte ich den Überblick über meinen Bestand?", "Nach jeder Anlieferung melden wir Ihnen, was eingelagert wurde. Dazu bekommen Sie in festen Abständen und auf Anfrage eine aktuelle Bestandsliste."),
        ("Kann ich mir das Lager ansehen?", "Nach Absprache gern."),
    ]),
    ("versand", "Versand", [
        ("Mit welchen Paketdiensten versenden Sie?", "Mit gängigen Paketdiensten. Welcher für Ihre Pakete passt, hängt von Größe, Gewicht und Zielland ab. Das klären wir im Angebot."),
        FAQ_CORE[3],
        ("Versenden Sie ins Ausland?", "Auf Anfrage. Wir prüfen Zielländer, Kosten und gegebenenfalls Zollformalitäten für Ihr Angebot."),
        ("Bekommen meine Kunden eine Sendungsnummer?", "Ja. Wir geben die Sendungsnummer an Ihren Shop weiter. Je nach Shopsystem geht sie von dort automatisch an Ihre Kunden."),
        FAQ_CORE[4],
    ]),
    ("retouren-fragen", "Retouren", [
        ("Wer bezahlt die Rücksendung?", "Das regeln Sie in Ihren Shop-Bedingungen. Wichtig ist, dass Rücksendungen ausreichend frankiert sind oder mit Ihrem Retourenlabel bei uns ankommen."),
        ("Wie schnell werden Retouren geprüft?", "Zeitnah nach Eingang. Den genauen Rahmen halten wir in Ihrem Angebot fest."),
        ("Was passiert mit beschädigter Ware?", "Sie wird gesondert gelagert. Sie entscheiden, ob wir sie aufbereiten, an Sie zurückschicken oder entsorgen."),
        ("Was passiert mit Retouren, die sich nicht zuordnen lassen?", "Wir lagern sie gesondert, dokumentieren den Inhalt und klären mit Ihnen, wohin sie gehören."),
    ]),
    ("technik", "Technik", [
        ("Welche Shopsysteme können angebunden werden?", "Sagen Sie uns, womit Sie arbeiten, etwa Shopify, WooCommerce, Shopware oder JTL. Wir prüfen vor dem Angebot, wie die Anbindung funktioniert."),
        ("Muss ich Bestellungen von Hand weitergeben?", "Das hängt von Ihrem Shopsystem ab. Wo eine Anbindung möglich ist, laufen Bestellungen automatisch zu uns. Wir klären das vor dem Start."),
        ("Bekomme ich Auswertungen?", "Ja. Sie bekommen Bestandslisten und Retourenberichte, auf Wunsch mit Rücksendegründen."),
    ]),
    ("start", "Start", [
        ("Wie lange dauert der Start?", "Das hängt vor allem von der Anbindung und der Anlieferung ab. Wir nennen Ihnen im Angebot einen realistischen Termin."),
        ("Was muss ich vorbereiten?", "Eine Artikelliste mit Maßen und Gewichten, Ihre Wünsche zur Verpackung und Ihre Registrierungsnummern. Die vollständige Checkliste steht unter <a href=\"ablauf.html\">So starten Sie</a>."),
        ("Welche Registrierungen brauchen Sie von mir?", "Ihre LUCID-Registrierungsnummer, bei Elektrogeräten die WEEE-Registrierung und bei Batterien die Registrierung nach dem Batterierecht. Mehr dazu weiter unten unter <a href=\"#pflichten\">Pflichten für Shops</a>."),
        ("Wie lange bin ich gebunden?", "Laufzeit und Kündigungsfristen stehen in Ihrem Angebot."),
        ("Was passiert, wenn mein Shop stark wächst?", "Dann wachsen wir mit. Zusätzliche Stellplätze und Kapazität planen wir rechtzeitig mit Ihnen, damit der Versand auch bei deutlich mehr Bestellungen zuverlässig läuft."),
    ]),
]

def faq_block():
    navl = ''.join('<a href="#' + gid + '">' + title + '</a>' for gid, title, _ in FAQ_GROUPS)
    groups = ''.join('<section class="faq-group" id="' + gid + '" aria-labelledby="h-' + gid + '"><h3 class="h-sm" id="h-' + gid + '">' + title + '</h3>' + faq(items) + '</section>'
                     for gid, title, items in FAQ_GROUPS)
    return '<div class="faq-layout"><nav class="faq-nav" aria-label="Themen">' + navl + '</nav><div>' + groups + '</div></div>'

FRAGEN_DOC = '''<nav class="doc doc-index" aria-label="Inhalt dieser Seite">
<div class="doc-head"><span>Inhalt</span><span>Stand Oktober 2026</span></div>
<a href="#haeufige-fragen"><span class="ix-code">FAQ</span><span class="ix-name">Häufige Fragen</span><span class="ix-go" aria-hidden="true">↓</span></a>
<a href="#lohnt"><span class="ix-code">TIPP</span><span class="ix-name">Wann sich Fulfillment lohnt</span><span class="ix-go" aria-hidden="true">↓</span></a>
<a href="#vergleich"><span class="ix-code">VGL</span><span class="ix-name">Selbst versenden oder auslagern</span><span class="ix-go" aria-hidden="true">↓</span></a>
<a href="#pflichten"><span class="ix-code">§</span><span class="ix-name">Pflichten für Shops</span><span class="ix-go" aria-hidden="true">↓</span></a>
</nav>'''

PAGES["fragen"] = ("Fragen · KattaPack",
  "Häufige Fragen zu Kosten, Lager, Versand und Retouren, dazu Wissen zu Fulfillment und den Pflichten für Shops.",
  hero("Fragen", "Fragen und Antworten",
       "Oben finden Sie schnelle Antworten. Weiter unten steht Hintergrundwissen für alle, die es genau wissen möchten.",
       FRAGEN_DOC) +
  '''<section class="section" id="haeufige-fragen" aria-labelledby="hf-title"><div class="wrap">
<div class="section-head"><h2 id="hf-title">Häufige Fragen</h2><p>Ihre Frage ist nicht dabei? Schreiben Sie uns, wir antworten persönlich.</p></div>
''' + faq_block() + '''
</div></section>

<section class="section band" id="lohnt" aria-labelledby="lohnt-title"><div class="wrap">
<div class="section-head"><h2 id="lohnt-title">Wann sich Fulfillment lohnt</h2><p>Eine feste Grenze gibt es nicht. Diese Anzeichen sprechen aber dafür, sich das genauer anzusehen.</p></div>
<div class="grid-2">
<div class="item"><h3>Gute Gründe</h3>''' + ul(["Sie packen regelmäßig mehrere Stunden pro Woche.", "Ihre Ware nimmt zu Hause oder im Büro zu viel Platz ein.",
    "Bei Aktionen oder vor Weihnachten wird der Versand zum Engpass.", "Retouren bleiben liegen, Erstattungen verzögern sich.",
    "Sie möchten wachsen, ohne gleich Lager und Personal aufzubauen.", "Sie planen den Verkauf an Händler oder über Marktplätze."]) + '''</div>
<div class="item"><h3>Eher noch nicht, wenn</h3>''' + ul(["Sie nur wenige Pakete im Monat verschicken und gern selbst packen.",
    "Ihre Produkte erst nach der Bestellung einzeln gefertigt werden.", "Sie jedes Paket persönlich gestalten möchten, ohne festen Ablauf."]) + '''
<p>In diesen Fällen ist eigener Versand oft günstiger. Das sagen wir Ihnen auch im Gespräch.</p></div>
</div>
</div></section>

<section class="section" id="vergleich" aria-labelledby="vgl-title"><div class="wrap">
<div class="section-head"><h2 id="vgl-title">Selbst versenden oder auslagern?</h2><p>Beides hat Vorteile. Die Tabelle zeigt, worin sich die Wege unterscheiden.</p></div>
<div class="table-wrap" tabindex="0" role="region" aria-label="Tabelle: Selbst versenden oder auslagern"><table class="tbl">
<thead><tr><th scope="col">Thema</th><th scope="col">Selbst versenden</th><th scope="col">Mit KattaPack</th></tr></thead>
<tbody>
<tr><th scope="row">Zeit</th><td>Packen, Etiketten, Abholung und Retouren kosten jeden Tag Zeit.</td><td>Bestellungen laufen zu uns. Sie kümmern sich um Ihren Shop.</td></tr>
<tr><th scope="row">Platz</th><td>Ware lagert in Wohnung, Keller, Büro oder Mietlager.</td><td>Bis 3 Palettenstellplätze ohne Lagerkosten.</td></tr>
<tr><th scope="row">Spitzen</th><td>Mehr Bestellungen bedeuten mehr Arbeit für Sie.</td><td>Aktionen und Saisonspitzen planen wir vorab mit Ihnen ein.</td></tr>
<tr><th scope="row">Retouren</th><td>Prüfen, einsortieren, erstatten.</td><td>Wir prüfen, sortieren und melden. Sie erstatten.</td></tr>
<tr><th scope="row">Verpackung</th><td>Volle Kontrolle über jedes Paket.</td><td>Kontrolle über Ihre Packanweisung, die wir bei jeder Bestellung umsetzen.</td></tr>
<tr><th scope="row">Kosten</th><td>Material, Versand, Platz und Ihre Arbeitszeit.</td><td>Preise pro Bestellung, Material und Versand. Lagerkosten erst ab dem vierten Stellplatz.</td></tr>
</tbody></table></div>
</div></section>

<section class="section band" id="pflichten" aria-labelledby="pfl-title"><div class="wrap">
<div class="section-head"><h2 id="pfl-title">Pflichten für Shops beim Versand</h2><p>Einige Pflichten bleiben bei Ihrem Shop, auch wenn wir lagern und versenden. Fulfillment-Dienstleister müssen vor dem Start prüfen, ob sie erfüllt sind.</p></div>
<div class="laws">
<article class="law"><span class="law-tag">VerpackG · LUCID</span><h3>Verpackungen registrieren</h3><p>Wer verpackte Ware an private Endkunden in Deutschland verschickt, muss sich vor dem ersten Verkauf im Verpackungsregister LUCID registrieren und seine Verpackungen bei einem dualen System beteiligen. Das gilt auch für Versandkartons und Füllmaterial. Seit dem 1. Juli 2022 müssen Fulfillment-Dienstleister sicherstellen, dass ihre Auftraggeber diese Pflichten erfüllen. Andernfalls dürfen sie für sie nicht tätig werden.</p></article>
<article class="law"><span class="law-tag">PPWR · seit 12. August 2026</span><h3>EU-Verpackungsverordnung</h3><p>Seit dem 12. August 2026 gilt die EU-Verpackungsverordnung direkt in allen EU-Staaten. Sie nennt Fulfillment-Dienstleister ausdrücklich und bringt schrittweise neue Vorgaben, etwa zu Kennzeichnung, Stoffbeschränkungen und Leerraum. Ab 2030 sollen Versandverpackungen höchstens 50&nbsp;% Leerraum haben. Viele Einzelheiten werden noch in Durchführungsrechtsakten festgelegt.</p></article>
<article class="law"><span class="law-tag">ElektroG § 6</span><h3>Elektro- und Elektronikgeräte</h3><p>Hersteller von Elektro- und Elektronikgeräten brauchen eine Registrierung bei der stiftung ear (WEEE-Reg.-Nr.). Fulfillment-Dienstleister dürfen Geräte nicht registrierter Hersteller weder lagern noch verpacken, adressieren oder versenden.</p></article>
<article class="law"><span class="law-tag">BattDG § 4</span><h3>Batterien</h3><p>Für Batterien gilt Ähnliches. Nach dem Batterierecht-Durchführungsgesetz, in Kraft seit Oktober 2025, dürfen Fulfillment-Dienstleister Batterien nicht registrierter Hersteller nicht lagern, verpacken, adressieren oder versenden. Das kann auch Batterien betreffen, die in Geräten verbaut oder beigelegt sind.</p></article>
<article class="law"><span class="law-tag">GPSR · seit 13. Dezember 2024</span><h3>Produktsicherheit</h3><p>Die EU-Produktsicherheitsverordnung verlangt für Verbraucherprodukte einen verantwortlichen Wirtschaftsakteur mit Sitz in der EU, etwa den Hersteller, Importeur oder einen Bevollmächtigten. Gibt es keinen, kann diese Rolle auf den Fulfillment-Dienstleister fallen. Für Shops außerhalb der EU klären wir das deshalb vor dem Start.</p></article>
<article class="law"><span class="law-tag">BGB § 357</span><h3>Widerruf und Erstattung</h3><p>Nach einem Widerruf muss der Kaufpreis innerhalb von 14 Tagen erstattet werden. Händler dürfen die Erstattung zurückhalten, bis die Ware zurück ist oder der Kunde den Versand nachweist. Schnell geprüfte Retouren helfen, diese Frist entspannt einzuhalten.</p></article>
</div>
<p class="disclaimer">Stand: Oktober 2026. Diese Übersicht ist eine allgemeine Information und ersetzt keine Rechtsberatung. Verbindlich sind die Gesetzestexte und die Auskünfte der zuständigen Stellen, etwa der Zentralen Stelle Verpackungsregister oder der stiftung ear.</p>
</div></section>''')

# ================================================================ Über uns
RULES_DOC = '''<figure class="doc" aria-label="Packregeln bei KattaPack">
<div class="doc-head"><span>Packregeln</span><span>KattaPack</span></div>
<ol class="doc-list numbered">
<li>Jede Bestellung wird vor dem Verschließen geprüft.</li>
<li>Der Karton wird passend zur Ware gewählt.</li>
<li>Ihre Packanweisung gilt für jedes Paket.</li>
<li>Auffälligkeiten melden wir Ihnen sofort.</li>
<li>Was wir zusagen, steht schriftlich im Angebot.</li>
</ol>
<div class="doc-foot"><span>Gilt für jeden Shop</span><span>Lager A</span></div>
</figure>'''

PAGES["ueber-uns"] = ("Über uns · KattaPack",
  "KattaPack ist ein junges Fulfillment-Unternehmen für wachsende Onlineshops. Wofür wir stehen und wie wir arbeiten.",
  hero("Über uns", "Über uns",
       "KattaPack ist ein junges Fulfillment-Unternehmen. Wir lagern, packen und versenden für Onlineshops, die wachsen, und behandeln jede Bestellung, als wäre es unsere eigene.",
       RULES_DOC) +
  '''<section class="section" aria-labelledby="werte-title"><div class="wrap">
<div class="section-head"><h2 id="werte-title">Wofür wir stehen</h2></div>
<div class="grid-2">
<div class="item"><h3>Sorgfalt</h3><p>Jede Bestellung wird vor dem Verschließen geprüft. Ein Fehler beim Packen landet direkt bei Ihrem Kunden. Deshalb nehmen wir das ernst.</p></div>
<div class="item"><h3>Erreichbarkeit</h3><p>Sie sprechen mit Menschen, die Ihre Artikel und Ihre Packanweisung kennen. Fragen klären wir direkt.</p></div>
<div class="item"><h3>Ehrlichkeit</h3><p>Wir sagen vorher, was geht und was nicht. Preise und Zusagen stehen schriftlich im Angebot.</p></div>
<div class="item"><h3>Beweglichkeit</h3><p>Sonderwünsche, Aktionen und Änderungen gehören bei uns zum Alltag.</p></div>
</div>
</div></section>

<section class="section band" aria-labelledby="warum-title"><div class="wrap split top">
<div class="split-text"><h2 id="warum-title">Warum keine Lagerkosten<span class="dot">?</span></h2></div>
<div class="split-text">
<p class="lead">Am Anfang ist der Bestand klein und jeder Euro zählt. Lagerkosten fallen jeden Monat an, auch wenn wenig verkauft wird.</p>
<p>Wir möchten mit Shops zusammenarbeiten, die wachsen, und verdienen an der Arbeit, die wir für sie erledigen. Deshalb kostet der Platz im Regal bis drei Palettenstellplätze nichts.</p>
<div class="links"><a class="text-link" href="preise.html">Preise ansehen</a></div>
</div>
</div></section>

<section class="section inverse" aria-labelledby="mit-title"><div class="wrap grow">
<h2 class="grow-title" id="mit-title">Wir wachsen mit Ihnen<span class="dot">.</span></h2>
<div class="grow-body">
<p class="lead">Unser Lager ist so organisiert, dass wir mit unseren Kunden wachsen können. Steigt Ihr Volumen, planen wir zusätzliche Fläche und Kapazität rechtzeitig und gemeinsam mit Ihnen.</p>
<dl class="facts">
<div><dt>Heute</dt><dd>Persönliche Betreuung, kurze Wege, schnelle Absprachen.</dd></div>
<div><dt>Morgen</dt><dd>Mehr Stellplätze und mehr Bestellungen, ohne dass sich an der Betreuung etwas ändert.</dd></div>
</dl>
</div>
</div></section>''')

# ================================================================ Kontakt
def opt(values, selected=None):
    return ''.join('<option' + (' selected' if v == selected else '') + '>' + v + '</option>' for v in values)

def choose(values):
    return '<option value="" disabled selected>Bitte auswählen</option>' + ''.join('<option>' + v + '</option>' for v in values)

def check(value):
    return '<label class="check"><input type="checkbox" name="needs" value="' + value + '">' + value + '</label>'

PAGES["kontakt"] = ("Angebot anfragen · KattaPack",
  "Angebot für Fulfillment bei KattaPack anfragen: Lagerung, Versand, Retouren und Sonderwünsche für Ihren Onlineshop.",
  hero("Kontakt", "Angebot anfragen",
       "Erzählen Sie uns von Ihrem Shop. Mit diesen Angaben können wir Ihnen ein passendes Angebot machen.") +
  '''<section class="section"><div class="wrap contact-grid">
<div>
<form class="form" id="contact-form" novalidate>
<fieldset><legend>Ihre Angaben</legend>
<div class="row-2">
<div class="field"><label for="f-name">Name</label><input id="f-name" name="name" type="text" autocomplete="name" required data-error="Bitte geben Sie Ihren Namen an."></div>
<div class="field"><label for="f-mail">E-Mail</label><input id="f-mail" name="email" type="email" autocomplete="email" required data-error="Bitte geben Sie Ihre E-Mail-Adresse an."></div>
</div>
<div class="row-2">
<div class="field"><label for="f-shop">Shop oder Firma</label><input id="f-shop" name="shop" type="text" autocomplete="organization" required data-error="Bitte geben Sie Ihren Shop oder Ihre Firma an."></div>
<div class="field"><label for="f-phone">Telefon</label><input id="f-phone" name="phone" type="tel" autocomplete="tel"></div>
</div>
<div class="field"><label for="f-web">Website</label><input id="f-web" name="website" type="text" inputmode="url" autocomplete="url" placeholder="z. B. www.ihr-shop.de"></div>
</fieldset>
<fieldset><legend>Ihr Shop</legend>
<div class="row-2">
<div class="field"><label for="f-system">Shopsystem</label><select id="f-system" name="system" required data-error="Bitte wählen Sie Ihr Shopsystem aus.">''' + choose(["Shopify", "WooCommerce", "Shopware", "JTL", "plentymarkets", "Nur Marktplätze", "Anderes", "Weiß ich nicht"]) + '''</select></div>
<div class="field"><label for="f-volume">Bestellungen pro Monat</label><select id="f-volume" name="volume" required data-error="Bitte wählen Sie aus, wie viele Bestellungen Sie pro Monat haben.">''' + choose(["unter 100", "100 bis 500", "500 bis 2.000", "über 2.000", "noch unklar"]) + '''</select></div>
</div>
<div class="row-2">
<div class="field"><label for="f-skus">Anzahl Artikel und Varianten</label><select id="f-skus" name="skus" required data-error="Bitte wählen Sie aus, wie viele Artikel Sie haben.">''' + choose(["bis 20", "21 bis 100", "101 bis 500", "mehr als 500", "noch unklar"]) + '''</select></div>
<div class="field"><label for="f-stock">Bestand heute</label><select id="f-stock" name="stock" required data-error="Bitte wählen Sie aus, wie groß Ihr Bestand heute ist.">''' + choose(["unter 1 Palette", "1 bis 3 Paletten", "4 bis 10 Paletten", "mehr als 10 Paletten", "weiß ich nicht"]) + '''</select></div>
</div>
<div class="row-2">
<div class="field"><label for="f-products">Was verkaufen Sie?</label><input id="f-products" name="products" type="text" placeholder="z. B. Naturkosmetik, Kleidung, Ersatzteile" required data-error="Bitte sagen Sie uns, was Sie verkaufen."></div>
<div class="field"><label for="f-start">Wann möchten Sie starten?</label><select id="f-start" name="start" required data-error="Bitte wählen Sie aus, wann Sie starten möchten.">''' + choose(["So bald wie möglich", "In 1 bis 3 Monaten", "Später", "Noch offen"]) + '''</select></div>
</div>
</fieldset>
<fieldset><legend>Was brauchen Sie?</legend>
<div class="checks">''' + ''.join(check(v) for v in ["Lagerung und Versand", "Retourenabwicklung", "Sonderwünsche und Branding", "Belieferung von Händlern", "Vorbereitung für Amazon-Lager", "Versand ins Ausland"]) + '''</div>
</fieldset>
<fieldset><legend>Ihre Nachricht</legend>
<div class="field"><label for="f-msg">Was ist Ihnen wichtig?</label><textarea id="f-msg" name="message" placeholder="Sonderwünsche, Retourenquote, offene Fragen"></textarea></div>
</fieldset>
<div class="form-foot"><button class="btn" type="submit">Anfrage vorbereiten</button><p class="status" id="form-note" aria-live="polite">Ihre Angaben werden zu einer E-Mail an uns zusammengefasst.</p></div>
</form>
<div class="result" id="result" hidden>
<h2 id="result-title" tabindex="-1">Ihre Anfrage ist vorbereitet</h2>
<p class="muted">Senden Sie den Text an <strong>''' + EMAIL + '''</strong>. Der erste Button öffnet Ihr E-Mail-Programm, falls eines eingerichtet ist.</p>
<pre id="result-text"></pre>
<div class="result-actions"><a class="btn" id="result-mailto" href="mailto:''' + EMAIL + '''">E-Mail öffnen</a><button class="btn btn-ghost" type="button" id="copy-result">Text kopieren</button><button class="btn btn-ghost" type="button" id="edit-result">Angaben ändern</button><span class="status" id="result-status" aria-live="polite"></span></div>
</div>
</div>
<aside class="aside" aria-label="Weitere Kontaktwege">
<div class="aside-box"><h2 class="h-sm">Was danach passiert</h2>
<ol><li>Wir melden uns per E-Mail mit Rückfragen oder einem Terminvorschlag.</li><li>Wir sprechen über Produkte, Mengen und Abläufe, persönlich, per Telefon oder per Video.</li><li>Sie bekommen ein schriftliches Angebot.</li></ol></div>
<div class="aside-box"><h2 class="h-sm">Lieber direkt schreiben</h2>
<span class="addr" id="mail-addr">''' + EMAIL + '''</span>
<div><button class="btn btn-ghost btn-small" type="button" data-copy="mail-addr" data-status="mail-status">Adresse kopieren</button> <span class="status" id="mail-status" aria-live="polite"></span></div></div>
</aside>
</div></section>''')

# ================================================================ Impressum
PAGES["impressum"] = ("Impressum · KattaPack", "Impressum von KattaPack.",
  hero("Impressum", "Impressum", "Angaben gemäß § 5 Digitale-Dienste-Gesetz (DDG).") +
  '''<section class="section"><div class="wrap legal-body">
<p class="legal-note">Vorlage: Die markierten Felder müssen vor der Veröffentlichung mit Ihren Angaben gefüllt werden.</p>
<section><h2>Anbieter</h2><p><span class="ph">Firmenname und Rechtsform</span><br><span class="ph">Straße und Hausnummer</span><br><span class="ph">PLZ und Ort</span><br>Deutschland</p></section>
<section><h2>Vertreten durch</h2><p><span class="ph">Name der Geschäftsführung oder Inhaberin / Inhaber</span></p></section>
<section><h2>Kontakt</h2><p>E-Mail: ''' + EMAIL + '''<br>Telefon: <span class="ph">Telefonnummer</span></p></section>
<section><h2>Registereintrag</h2><p>Registergericht: <span class="ph">Amtsgericht</span><br>Registernummer: <span class="ph">HRB / HRA</span><br>Nur ausfüllen, wenn ein Handelsregistereintrag besteht.</p></section>
<section><h2>Umsatzsteuer-Identifikationsnummer</h2><p>gemäß § 27a Umsatzsteuergesetz: <span class="ph">DE…</span></p></section>
<section><h2>Verantwortlich für redaktionelle Inhalte</h2><p>nach § 18 Abs. 2 Medienstaatsvertrag: <span class="ph">Name, Anschrift</span><br>Nötig bei journalistisch-redaktionellen Inhalten wie den Erklärtexten auf der Seite „Fragen“. Im Zweifel ausfüllen.</p></section>
</div></section>''')

# ================================================================ Datenschutz
PAGES["datenschutz"] = ("Datenschutz · KattaPack", "Datenschutzerklärung von KattaPack.",
  hero("Datenschutz", "Datenschutz&shy;erklärung", "Wie wir mit Ihren Daten umgehen, wenn Sie diese Website besuchen oder uns schreiben.") +
  '''<section class="section"><div class="wrap legal-body">
<p class="legal-note">Vorlage: Bitte vor der Veröffentlichung ergänzen und von einer fachkundigen Stelle prüfen lassen, etwa mit Blick auf Ihren Hosting-Anbieter.</p>
<section><h2>1. Verantwortlicher</h2><p><span class="ph">Firmenname und Rechtsform</span>, <span class="ph">Anschrift</span><br>E-Mail: ''' + EMAIL + '''</p></section>
<section><h2>2. Aufruf der Website</h2><p>Diese Website wird bei <span class="ph">Hosting-Anbieter mit Anschrift</span> betrieben. Beim Aufruf verarbeitet der Server technisch notwendige Daten wie IP-Adresse, Datum und Uhrzeit des Abrufs, aufgerufene Seite und Browsertyp. Das ist erforderlich, um die Website sicher bereitzustellen und Angriffe abzuwehren. Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO. Unser berechtigtes Interesse ist ein sicherer und stabiler Betrieb der Website. Wie lange diese Daten gespeichert werden: <span class="ph">Speicherdauer laut Hoster</span>.</p>
<p>Der Hosting-Anbieter verarbeitet die Daten in unserem Auftrag. Mit ihm besteht ein Vertrag zur Auftragsverarbeitung nach Art. 28 DSGVO. Die Verbindung zur Website ist verschlüsselt (HTTPS).</p></section>
<section><h2>3. Anfragen per E-Mail, Telefon und Anfrageformular</h2><p>Das Anfrageformular auf dieser Website überträgt keine Daten an uns. Es fasst Ihre Angaben in Ihrem Browser zu einem E-Mail-Text zusammen, den Sie selbst abschicken. Wenn Sie uns schreiben oder anrufen, verarbeiten wir Ihre Angaben, um Ihre Anfrage zu beantworten und ein Angebot zu erstellen. Rechtsgrundlage ist Art. 6 Abs. 1 lit. b DSGVO. Wir löschen die Daten, wenn sie dafür nicht mehr nötig sind und keine gesetzlichen Aufbewahrungspflichten bestehen.</p>
<p>Ihre Angaben sind freiwillig. Ohne sie können wir Ihre Anfrage aber nicht beantworten. E-Mails liegen bei unserem E-Mail-Anbieter <span class="ph">E-Mail-Anbieter, oft derselbe wie der Hoster</span>, der sie in unserem Auftrag speichert.</p></section>
<section><h2>4. Schriftarten</h2><p>Die Schriftarten dieser Website liegen auf demselben Server wie die Website. Dabei werden keine Daten an Dritte übertragen.</p></section>
<section><h2>5. Cookies und Analyse</h2><p>Diese Website setzt keine Cookies und verwendet keine Analyse- oder Tracking-Dienste. Eine automatisierte Entscheidungsfindung oder Profilbildung findet nicht statt.</p></section>
<section><h2>6. Ihre Rechte</h2><p>Sie haben das Recht auf</p><ul><li>Auskunft über Ihre gespeicherten Daten (Art. 15 DSGVO)</li><li>Berichtigung unrichtiger Daten (Art. 16 DSGVO)</li><li>Löschung (Art. 17 DSGVO)</li><li>Einschränkung der Verarbeitung (Art. 18 DSGVO)</li><li>Datenübertragbarkeit (Art. 20 DSGVO)</li></ul><p>Außerdem können Sie sich bei einer Datenschutz-Aufsichtsbehörde beschweren (Art. 77 DSGVO).</p></section>
<section class="legal-box"><h2>7. Widerspruchsrecht</h2><p>Wenn wir Daten auf Grundlage von Art. 6 Abs. 1 lit. f DSGVO verarbeiten, also wegen eines berechtigten Interesses, können Sie dem jederzeit widersprechen (Art. 21 DSGVO). Gründe dafür müssen sich aus Ihrer besonderen Situation ergeben. Wir verarbeiten die Daten dann nicht mehr, es sei denn, wir können zwingende schutzwürdige Gründe nachweisen, die Ihre Interessen überwiegen, oder die Verarbeitung dient der Geltendmachung, Ausübung oder Verteidigung von Rechtsansprüchen. Eine E-Mail an ''' + EMAIL + ''' genügt.</p></section>
<section><h2>8. Stand</h2><p><span class="ph">Datum</span></p></section>
</div></section>''')

# ================================================================ Barrierefreiheit
PAGES["barrierefreiheit"] = ("Barrierefreiheit · KattaPack", "Erklärung zur Barrierefreiheit der Website von KattaPack.",
  hero("Barrierefreiheit", "Barriere&shy;freiheit", "Diese Website soll für alle gut nutzbar sein, auch mit Tastatur, Screenreader, Vergrößerung oder ohne Animationen.") +
  '''<section class="section"><div class="wrap legal-body">
<section><h2>Stand der Barrierefreiheit</h2><p>Wir haben die Website nach den Web Content Accessibility Guidelines (WCAG) 2.2, Stufe AA, gestaltet und geprüft. Nach unserem Prüfstand erfüllt sie diese Anforderungen. Geprüft haben wir alle Seiten mit dem Prüfwerkzeug axe-core, im hellen und dunklen Modus, am Handy und am Computer, und zusätzlich von Hand: Bedienung nur mit der Tastatur, Darstellung bei 320 Pixel Breite und Fehlermeldungen im Anfrageformular.</p></section>
<section><h2>Was die Website bietet</h2><ul><li>Alle Funktionen lassen sich mit der Tastatur bedienen. Der Fokus ist immer sichtbar.</li><li>Ein Link „Zum Inhalt springen“ führt an der Navigation vorbei.</li><li>Texte haben ausreichend Kontrast, auch im dunklen Modus.</li><li>Die Seiten lassen sich bis 400&nbsp;% vergrößern, ohne dass Inhalte abgeschnitten werden.</li><li>Wer auf seinem Gerät „Bewegung reduzieren“ eingestellt hat, sieht die Seite ohne Animationen.</li><li>Grafiken, die nur schmücken, sind für Screenreader ausgeblendet. Alle Inhalte stehen zusätzlich als Text auf der Seite.</li><li>Pflichtfelder im Anfrageformular sind gekennzeichnet. Fehlt eine Angabe, erscheint eine Meldung direkt am Feld.</li></ul></section>
<section><h2>Bekannte Einschränkungen</h2><p>Das Paket auf der Startseite ist eine Animation zum Schmücken. Was es zeigt, steht auch im Text daneben.</p></section>
<section><h2>Barriere gefunden?</h2><p>Wenn Sie auf ein Problem stoßen oder Inhalte in einer anderen Form brauchen, schreiben Sie uns an ''' + EMAIL + '''. Wir antworten persönlich und suchen eine Lösung.</p></section>
<section><h2>Stand</h2><p>Erstellt am 5. November 2026. Bitte nach größeren Änderungen an der Website erneut prüfen.</p></section>
</div></section>''')


# ---------------------------------------------------------------- Ausgabe

def render(slug, mode):
    title, desc, body = PAGES[slug]
    if slug in SECTIONS:
        body = body.replace('</section>', '</section>' + pagebar(slug), 1)
    cls = 'site page-' + slug + (' has-pagebar' if slug in SECTIONS else '')
    chrome = (sprite(slug == "index") + '<a class="skip" href="#main">Zum Inhalt springen</a>' + header(slug) +
              '<main id="main">' + body + page_next(slug) +
              ('' if slug in ("kontakt", "impressum", "datenschutz", "barrierefreiheit") else cta()) + '</main>' + footer())
    meta = '<meta name="description" content="' + desc + '">'
    if mode == "artifact" and slug == "index":
        return ('<title>' + title + '</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n' + meta + '\n' +
                GOOGLE_FONTS + '\n<link rel="stylesheet" href="' + CSS_HREF + '">\n<div class="' + cls + '" lang="de">' + chrome +
                '</div>\n<script src="' + JS_SRC + '"></script>\n')
    fonts = GOOGLE_FONTS if mode == "artifact" else LOCAL_FONTS
    extra = ''
    if mode == "hosting":
        extra = ('<meta property="og:type" content="website">\n'
                 '<meta property="og:locale" content="de_DE">\n'
                 '<meta property="og:site_name" content="KattaPack">\n'
                 '<meta property="og:title" content="' + title + '">\n'
                 '<meta property="og:description" content="' + desc + '">\n'
                 '<meta name="theme-color" content="#F5F5F2" media="(prefers-color-scheme: light)">\n'
                 '<meta name="theme-color" content="#111213" media="(prefers-color-scheme: dark)">\n'
                 '<link rel="icon" href="favicon.ico" sizes="32x32">\n'
                 '<link rel="icon" href="favicon.svg" type="image/svg+xml">\n'
                 '<link rel="apple-touch-icon" href="apple-touch-icon.png">\n')
    return ('<!doctype html>\n<html lang="de">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<title>' + title + '</title>\n' + meta + '\n' + extra + fonts + '\n<link rel="stylesheet" href="' + CSS_HREF + '">\n</head>\n'
            '<body>\n<div class="' + cls + '">' + chrome + '</div>\n<script src="' + JS_SRC + '"></script>\n</body>\n</html>\n')


def main():
    os.makedirs(OUT_H, exist_ok=True)
    if OUT_A:
        os.makedirs(OUT_A, exist_ok=True)
    for slug in PAGES:
        if OUT_A:
            target = INDEX_A if slug == "index" else os.path.join(OUT_A, slug + ".html")
            with open(target, "w", encoding="utf-8") as f:
                f.write(render(slug, "artifact"))
        with open(os.path.join(OUT_H, slug + ".html"), "w", encoding="utf-8") as f:
            f.write(render(slug, "hosting"))
    for name in ("site.css", "site.js"):
        if OUT_A:
            shutil.copy(os.path.join(SRC, name), os.path.join(OUT_A, name))
        shutil.copy(os.path.join(SRC, name), os.path.join(OUT_H, name))
    # Server-Einstellungen: Zwischenspeichern, Komprimieren, Sicherheits-Header
    # (.htaccess für Apache-Hoster, _headers für Netlify und Cloudflare Pages)
    shutil.copy(os.path.join(SRC, "server", "htaccess"), os.path.join(OUT_H, ".htaccess"))
    shutil.copy(os.path.join(SRC, "server", "_headers"), os.path.join(OUT_H, "_headers"))
    # Symbole für Browser-Tab und Handy-Startbildschirm
    for name in ("favicon.svg", "favicon.ico", "apple-touch-icon.png"):
        shutil.copy(os.path.join(SRC, "assets", name), os.path.join(OUT_H, name))
    # Schriften lokal einbinden, damit keine Daten an Google gehen
    fdir = os.path.join(OUT_H, "fonts")
    os.makedirs(fdir, exist_ok=True)
    files = {
        "archivo-latin-wdth-normal.woff2": "fonts/archivo-latin-wdth-normal.woff2",
        "archivo-latin-ext-wdth-normal.woff2": "fonts/archivo-latin-ext-wdth-normal.woff2",
        "ibm-plex-mono-latin-400-normal.woff2": "fonts/ibm-plex-mono-latin-400-normal.woff2",
        "ibm-plex-mono-latin-500-normal.woff2": "fonts/ibm-plex-mono-latin-500-normal.woff2",
        "ibm-plex-mono-latin-600-normal.woff2": "fonts/ibm-plex-mono-latin-600-normal.woff2",
    }
    for dst, srcf in files.items():
        shutil.copy(os.path.join(SRC, srcf), os.path.join(fdir, dst))
    latin = "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"
    latin_ext = "U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF"
    css = [
        "@font-face{font-family:'Archivo';font-style:normal;font-display:swap;font-weight:100 900;font-stretch:62% 125%;"
        "src:url(archivo-latin-ext-wdth-normal.woff2) format('woff2-variations'),url(archivo-latin-ext-wdth-normal.woff2) format('woff2');unicode-range:" + latin_ext + "}",
        "@font-face{font-family:'Archivo';font-style:normal;font-display:swap;font-weight:100 900;font-stretch:62% 125%;"
        "src:url(archivo-latin-wdth-normal.woff2) format('woff2-variations'),url(archivo-latin-wdth-normal.woff2) format('woff2');unicode-range:" + latin + "}",
    ]
    for w in (400, 500, 600):
        css.append("@font-face{font-family:'IBM Plex Mono';font-style:normal;font-display:swap;font-weight:" + str(w) + ";"
                   "src:url(ibm-plex-mono-latin-" + str(w) + "-normal.woff2) format('woff2');unicode-range:" + latin + "}")
    with open(os.path.join(fdir, "fonts.css"), "w", encoding="utf-8") as f:
        f.write("/* Archivo und IBM Plex Mono (beide SIL Open Font License), lokal eingebunden */\n" + "\n".join(css) + "\n")
    for lic in ("LICENSE-Archivo.txt", "LICENSE-IBM-Plex-Mono.txt"):
        shutil.copy(os.path.join(SRC, "fonts", lic), os.path.join(fdir, lic))
    print("Seiten:", len(PAGES), "->", OUT_H)


if __name__ == "__main__":
    main()
