#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static site generator for the Elwali law-office site.

    python3 build.py                              write the site into this folder
    python3 build.py --site https://example.com/  use another public address
    python3 build.py --preview OUTDIR             flat .html build for artifact previews

The text lives in content.py. The generated pages are committed, so GitHub Pages
(or any static host) serves them as they are.
"""
import argparse
import datetime
import html
import json
import os
import posixpath
import re
import shutil

import content as C

DEFAULT_SITE = "https://elwali.aldiwan.io/"
ROOT = os.path.dirname(os.path.abspath(__file__))
esc = html.escape

# --------------------------------------------------------------------- icons
ICONS = {
    "house": "M3 11 12 4l9 7v9H3v-9Zm6 9v-6h6v6",
    "document": "M6 3h9l4 4v14H6V3Zm9 0v4h4M9 12h7M9 16h7",
    "building": "M4 21V5h10v16M14 9h6v12M8 9h2M8 13h2M8 17h2",
    "tag": "M3 12V4h8l10 10-8 8L3 12Zm5-5h.01",
    "clipboard": "M8 4h8v3H8V4Zm-3 2h3M16 6h3v15H5V6h3M9 14l2 2 4-4",
    "bulb": "M9 18h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3Z",
    "shield": "M12 3 4 6v6c0 4.5 3.2 7.8 8 9 4.8-1.2 8-4.5 8-9V6l-8-3Zm-3 9 2.2 2.2L15.5 10",
    "heart": "M12 21s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 11c0 5.6-7 10-7 10Z",
    "columns": "M3 10 12 4l9 6M5 10v8M9 10v8M15 10v8M19 10v8M3 20h18",
    "scales": "M12 3v18M5 7h14M5 7l-3 7a3.5 3.5 0 0 0 6 0L5 7Zm14 0-3 7a3.5 3.5 0 0 0 6 0l-3-7ZM8 21h8",
    "users": "M16 20v-1.5a3.5 3.5 0 0 0-3.5-3.5h-5A3.5 3.5 0 0 0 4 18.5V20M10 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Zm9 9v-1.5a3.5 3.5 0 0 0-2.5-3.3M15.5 4.2a3.5 3.5 0 0 1 0 6.6",
    "calendar": "M4 7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7Zm0 3h16M9 3v4M15 3v4",
    "clock": "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm0 4v5l3 2",
    "pin": "M12 21s-7-5-7-11a7 7 0 0 1 14 0c0 6-7 11-7 11Zm0-8.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z",
    "arrow": "M17 17 7 7M7 16V7h9",
    "chevron": "m6 9 6 6 6-6",
    "info": "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm0 8v5m0-8.5v.01",
    "phone": "M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2Z",
}
WA_PATH = ("M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm5.8 14.1c-.2.7-1.3 1.3-1.8 1.3-.5.1-1 .2-3.3-.7-2.8-1.2-4.6-4-4.7-4.2-.1-.2-1.1-1.5-1.1-2.8"
           "s.7-2 1-2.3c.2-.3.5-.3.7-.3h.5c.2 0 .4 0 .6.5l.9 2.1c.1.2.1.4 0 .5l-.4.6-.3.4c-.1.1-.3.3-.1.6.2.3.8 1.3 1.7 2.1 1.2 1 2.2 1.4 2.5 1.5.3.1.4.1.6-.1"
           "l.8-1c.2-.3.4-.2.6-.1l2 1c.3.1.5.2.5.4.1.1.1.7-.1 1.4Z")


def icon(name, cls=""):
    c = f' class="{cls}"' if cls else ""
    return f'<svg viewBox="0 0 24 24" aria-hidden="true"{c}><path d="{ICONS[name]}"/></svg>'


# ------------------------------------------------------------------- config
class Cfg:
    site = DEFAULT_SITE
    preview = False
    today = datetime.date.today().isoformat()


SVC = {s["slug"]: s for s in C.SERVICES}
FOCUS = [s for s in C.SERVICES if s["group"] == "focus"]
OTHERS = [s for s in C.SERVICES if s["group"] != "focus"]


def image_size(rel):
    try:
        from PIL import Image
        with Image.open(os.path.join(ROOT, rel)) as im:
            return im.size
    except Exception:
        return (960, 644)


# ------------------------------------------------------------------- paths
def out_file(path):
    """File written for a page. path: '' | 'about/' | 'services/' | 'services/<slug>/'."""
    if not Cfg.preview:
        return posixpath.join(path, "index.html") if path else "index.html"
    return "index.html" if not path else path.rstrip("/") + ".html"


def href(src, dst, anchor=""):
    src_dir = posixpath.dirname(out_file(src)) or "."
    if not Cfg.preview:
        rel = posixpath.relpath(dst.rstrip("/") or ".", src_dir)
        rel = "./" if rel == "." else rel + "/"
    else:
        rel = posixpath.relpath(out_file(dst), src_dir)
    return rel + anchor


def asset(src, f):
    return posixpath.relpath(f, posixpath.dirname(out_file(src)) or ".")


def url(path):
    return Cfg.site + path


def svc_path(slug):
    return f"services/{slug}/"


# --------------------------------------------------------------- components
def wa_icon():
    return f'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="{WA_PATH}"/></svg>'


def pill(label, *, wa=None, link=None, gold=False, block=False, tel=None, extra=""):
    cls = "pill-cta" + (" pill-gold" if gold else "") + (" btn-block" if block else "") + (f" {extra}" if extra else "")
    arrow = f'<span class="pill-arrow" aria-hidden="true">{icon("arrow")}</span>'
    inner = f"<span>{esc(label)}</span>{arrow}"
    if wa is not None:
        return f'<a class="{cls}" data-wa data-msg="{esc(wa, quote=True)}">{inner}</a>'
    if tel:
        return f'<a class="{cls}" href="tel:{tel}">{inner}</a>'
    return f'<a class="{cls}" href="{link}">{inner}</a>'


def blocks_html(blocks):
    out = []
    ar = "٠١٢٣٤٥٦٧٨٩"
    for b in blocks:
        kind = b[0]
        if kind == "p":
            out.append(f"<p>{esc(b[1])}</p>")
        elif kind == "ul":
            out.append('<ul class="check">' + "".join(f"<li>{esc(t)}</li>" for t in b[1]) + "</ul>")
        elif kind == "ol":
            items = []
            for i, (t, d) in enumerate(b[1], 1):
                n = "".join(ar[int(ch)] for ch in str(i))
                items.append(f'<li><span class="n">{n}</span><div><h3>{esc(t)}</h3><p>{esc(d)}</p></div></li>')
            out.append('<ol class="steps-list">' + "".join(items) + "</ol>")
        elif kind == "table":
            head = "".join(f"<th scope=\"col\">{esc(h)}</th>" for h in b[1])
            rows = "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>" for r in b[2])
            out.append(f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>')
        elif kind == "callout":
            out.append(f'<div class="callout">{icon("info")}<p>{esc(b[1])}</p></div>')
    return "\n".join(out)


def faq_html(items, first_open=True):
    out = []
    for i, (q, a) in enumerate(items):
        op = " open" if (i == 0 and first_open) else ""
        out.append(f"<details{op}><summary>{esc(q)}</summary><p>{esc(a)}</p></details>")
    return '<div class="faq">' + "".join(out) + "</div>"


def media_html(s, src, cls="media"):
    """Photo when the service has one, otherwise an icon panel."""
    if s.get("img"):
        w, h = image_size("assets/" + s["img"])
        return (f'<div class="{cls}"><img src="{asset(src, "assets/" + s["img"])}" alt="{esc(s["img_alt"], quote=True)}" '
                f'width="{w}" height="{h}" loading="lazy" style="object-position: {s["img_pos"]}"></div>')
    return f'<div class="{cls} media-art" aria-hidden="true">{icon(s["icon"])}</div>'


def mini_card(s, src):
    return (f'<a class="mini-card" href="{href(src, svc_path(s["slug"]))}">'
            f'<span class="ic">{icon(s["icon"])}</span>'
            f'<h3>{esc(s["menu"])}</h3>'
            f'<span class="go" aria-hidden="true">{icon("arrow")}</span>'
            f'<p>{esc(s["card"])}</p></a>')


def hub_card(s, src):
    return (f'<a class="hub-card" href="{href(src, svc_path(s["slug"]))}">{media_html(s, src, "ph")}'
            f'<div class="bd"><span class="chip">{esc(s["chip"])}</span><h3>{esc(s["menu"])}</h3>'
            f'<p>{esc(s["card"])}</p><span class="more">اقرأ المزيد<span class="go" aria-hidden="true">{icon("arrow")}</span></span></div></a>')


def focus_card(s, src):
    teasers = "".join(f"<li>{esc(t)}</li>" for t in s["teasers"])
    return (f'<article class="focus-card">{media_html(s, src, "ph")}<div class="bd">'
            f'<span class="chip">{esc(s["chip"])}</span><h3>{esc(s["menu"])}</h3><p>{esc(s["card"])}</p>'
            f'<ul class="check">{teasers}</ul>'
            f'<div class="focus-actions">{pill("اقرأ التفاصيل", link=href(src, svc_path(s["slug"])), gold=True)}'
            f'{pill("اسأل على واتساب", wa=s["wa"])}</div></div></article>')


# ------------------------------------------------------------------ layout
def org_graph():
    lat, lng = C.GEO
    return [
        {
            "@type": ["LegalService", "Attorney"],
            "@id": url("#office"),
            "name": C.OFFICE,
            "alternateName": ["Elwali for legal services", "الولي للمحاماة", "مكتب الأستاذ محمود جمال الولي المحامي"],
            "url": Cfg.site,
            "logo": url("assets/logo.png"),
            "image": url("assets/og-image.jpg"),
            "description": "مكتب محاماة وخدمات قانونية في دمياط: مراجعة عقود الملكية قبل الشراء، وصياغة العقود، وتأسيس الشركات، والعلامات التجارية، والتراخيص، والقضايا الجنائية والأحوال الشخصية.",
            "telephone": C.PHONE_TEL,
            "address": {"@type": "PostalAddress", "streetAddress": "الشعراء بجانب مدرسة سعد الأسمر، عبده سعد",
                        "addressLocality": "دمياط", "addressRegion": "محافظة دمياط", "postalCode": "34511", "addressCountry": "EG"},
            "geo": {"@type": "GeoCoordinates", "latitude": lat, "longitude": lng},
            "hasMap": f"https://www.google.com/maps?cid={C.MAPS_CID}",
            "sameAs": [f"https://www.google.com/maps?cid={C.MAPS_CID}"],
            "areaServed": [{"@type": "City", "name": "دمياط"}, {"@type": "AdministrativeArea", "name": "محافظة دمياط"}],
            "knowsLanguage": "ar",
            "knowsAbout": [s["menu"] for s in C.SERVICES],
            "founder": {"@id": url("#lawyer")},
            "employee": {"@id": url("#lawyer")},
            "openingHoursSpecification": [{
                "@type": "OpeningHoursSpecification",
                "dayOfWeek": ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"],
                "opens": "20:00", "closes": "23:30"}],
            "contactPoint": {"@type": "ContactPoint", "telephone": C.PHONE_TEL, "contactType": "customer service", "availableLanguage": "ar"},
            "hasOfferCatalog": {
                "@type": "OfferCatalog", "name": "الخدمات القانونية",
                "itemListElement": [{"@type": "Offer", "itemOffered": {
                    "@type": "Service", "name": s["menu"], "url": url(svc_path(s["slug"])), "areaServed": "دمياط"}} for s in C.SERVICES]},
        },
        {
            "@type": "Person", "@id": url("#lawyer"), "name": C.LAWYER_SHORT,
            "alternateName": ["الأستاذ محمود جمال الولي", C.LAWYER, "Mahmoud Gamal Elwali"],
            "jobTitle": "محامٍ", "worksFor": {"@id": url("#office")},
            "workLocation": {"@type": "Place", "name": "دمياط"},
            "knowsAbout": [s["menu"] for s in C.SERVICES], "url": Cfg.site, "image": url("assets/hero.webp"),
        },
        {"@type": "WebSite", "@id": url("#website"), "url": Cfg.site, "name": C.OFFICE, "inLanguage": "ar",
         "publisher": {"@id": url("#office")}},
    ]


def breadcrumb(items):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i, "name": n, "item": u} for i, (n, u) in enumerate(items, 1)]}


def faq_graph(path, items):
    return {"@type": "FAQPage", "@id": url(path) + "#faq", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items]}


def head(path, title, desc, graph_extra, kind="website"):
    src = path
    canonical = url(path)
    graph = org_graph() + [
        {"@type": "WebPage", "@id": canonical + "#webpage", "url": canonical, "name": title, "description": desc,
         "inLanguage": "ar", "isPartOf": {"@id": url("#website")}, "about": {"@id": url("#office")},
         "primaryImageOfPage": {"@type": "ImageObject", "url": url("assets/og-image.jpg"), "width": 1200, "height": 630},
         "dateModified": Cfg.today},
    ] + graph_extra
    ld = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=2)
    lat, lng = C.GEO
    og_desc = desc if len(desc) < 200 else desc[:197] + "…"
    return f"""<meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(desc, quote=True)}">
  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
  <link rel="canonical" href="{canonical}">
  <link rel="alternate" hreflang="ar-EG" href="{canonical}">
  <link rel="alternate" hreflang="x-default" href="{canonical}">
  <meta name="author" content="{esc(C.LAWYER, quote=True)}">
  <meta name="geo.region" content="EG-DT">
  <meta name="geo.placename" content="دمياط">
  <meta name="geo.position" content="{lat};{lng}">
  <meta name="ICBM" content="{lat}, {lng}">
  <meta name="theme-color" content="#13242b">
  <meta property="og:type" content="{kind}">
  <meta property="og:locale" content="ar_EG">
  <meta property="og:site_name" content="{esc(C.OFFICE, quote=True)}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:title" content="{esc(title, quote=True)}">
  <meta property="og:description" content="{esc(og_desc, quote=True)}">
  <meta property="og:image" content="{url('assets/og-image.jpg')}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="{esc(C.LAWYER + ' - ' + C.OFFICE, quote=True)}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(title, quote=True)}">
  <meta name="twitter:description" content="{esc(og_desc, quote=True)}">
  <meta name="twitter:image" content="{url('assets/og-image.jpg')}">
  <link rel="icon" type="image/png" href="{asset(src, 'assets/favicon.png')}">
  <link rel="apple-touch-icon" href="{asset(src, 'assets/apple-touch-icon.png')}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&family=Noto+Kufi+Arabic:wght@500;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{asset(src, 'css/style.css')}">
  <script type="application/ld+json">
  {ld.replace(chr(10), chr(10) + '  ')}
  </script>"""


def header(src, current):
    def a(label, path, key):
        cur = ' aria-current="page"' if current == key else ""
        return f'<a href="{href(src, path)}"{cur}>{label}</a>'

    def dd_link(s):
        cur = ' aria-current="page"' if current == s["slug"] else ""
        return f'<a href="{href(src, svc_path(s["slug"]))}"{cur}><span class="ic">{icon(s["icon"])}</span>{esc(s["menu"])}</a>'

    half = (len(OTHERS) + 1) // 2
    dd_current = " is-current" if (current == "services" or current in SVC) else ""
    panel = (f'<div class="dd-panel" id="ddPanel" hidden>'
             f'<div class="dd-col"><p class="dd-title">الأكثر طلبًا</p>{"".join(dd_link(s) for s in FOCUS)}'
             f'<a class="dd-all" href="{href(src, "services/")}">كل الخدمات {icon("arrow")}</a></div>'
             f'<div class="dd-col"><p class="dd-title">باقي الخدمات</p>{"".join(dd_link(s) for s in OTHERS[:half])}</div>'
             f'<div class="dd-col"><p class="dd-title" aria-hidden="true">&nbsp;</p>{"".join(dd_link(s) for s in OTHERS[half:])}</div></div>')
    return f"""<header class="site-header">
    <a class="brand" href="{href(src, '')}" aria-label="{esc(C.OFFICE, quote=True)} - الرئيسية">
      <img src="{asset(src, 'assets/logo.png')}" alt="شعار {esc(C.OFFICE, quote=True)}" width="48" height="48">
      <span class="brand-text"><strong>الولي</strong> <span>للخدمات القانونية</span></span>
    </a>
    <nav class="nav" id="nav" aria-label="القائمة الرئيسية">
      {a('الرئيسية', '', 'home')}
      {a('من نحن', 'about/', 'about')}
      <div class="nav-dd">
        <button type="button" class="nav-dd-btn{dd_current}" id="ddBtn" aria-expanded="false" aria-controls="ddPanel">خدماتنا {icon('chevron')}</button>
        {panel}
      </div>
      {a('تواصل معنا', 'contact/', 'contact')}
    </nav>
    {pill('احجز استشارة', wa='السلام عليكم، أرغب في حجز استشارة قانونية.', extra='head-cta')}
    <button class="menu-toggle" id="menuToggle" aria-label="فتح القائمة" aria-expanded="false" aria-controls="nav"><span></span><span></span><span></span></button>
  </header>"""


def footer(src):
    others = "".join(f'<a href="{href(src, svc_path(s["slug"]))}">{esc(s["menu"])}</a>' for s in OTHERS)
    focus = "".join(f'<a href="{href(src, svc_path(s["slug"]))}">{esc(s["menu"])}</a>' for s in FOCUS)
    return f"""<footer class="site-footer">
  <div class="container">
    <div class="foot-grid">
      <div class="foot-brand">
        <img src="{asset(src, 'assets/logo.png')}" alt="" width="64" height="64" loading="lazy">
        <p><strong>{esc(C.LAWYER)}</strong><br>{esc(C.OFFICE)}<br>{esc(C.ADDRESS_SHORT)}</p>
      </div>
      <nav class="foot-links" aria-label="الأكثر طلبًا"><b>الأكثر طلبًا</b>{focus}
        <a href="{href(src, 'about/')}">من نحن</a><a href="{href(src, 'services/')}">كل الخدمات</a><a href="{href(src, 'contact/')}">تواصل معنا</a></nav>
      <nav class="foot-links" aria-label="الخدمات"><b>خدماتنا</b>{others}</nav>
      <address class="foot-contact"><b>تواصل</b>
        <a href="tel:{C.PHONE_TEL}" dir="ltr">{C.PHONE_DISPLAY}</a>
        <span>{esc(C.HOURS_TEXT)}</span>
        <span>{esc(C.ADDRESS_SHORT)}</span></address>
    </div>
    <p class="disclaimer">المحتوى المعروض في هذا الموقع لأغراض التعريف والمعلومات العامة فقط، ولا يُعد استشارة قانونية ولا يُنشئ علاقة وكالة بين المحامي والزائر.</p>
    <p class="copy">© <span id="year">{datetime.date.today().year}</span> {esc(C.OFFICE)}. جميع الحقوق محفوظة.</p>
    <div class="wordmark" aria-hidden="true">الولي</div>
  </div>
</footer>
<a class="wa-float" data-wa aria-label="تواصل عبر واتساب" href="#">{wa_icon()}</a>"""


def page_shell(src, title, desc, graph_extra, current, frame_html, main_html, kind="website"):
    return f"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
  {head(src, title, desc, graph_extra, kind)}
</head>
<body>
<div class="frame" id="top">
  {header(src, current)}
  {frame_html}
</div>
<main>
{main_html}
</main>
{footer(src)}
<script src="{asset(src, 'js/main.js')}" defer></script>
</body>
</html>
"""


def crumbs_html(src, trail):
    """trail: list of (label, path|None)."""
    items = []
    for label, path in trail:
        if path is None:
            items.append(f'<li aria-current="page">{esc(label)}</li>')
        else:
            items.append(f'<li><a href="{href(src, path)}">{esc(label)}</a></li>')
    return '<nav aria-label="مسار التنقل"><ol class="crumbs">' + "".join(items) + "</ol></nav>"


def page_hero(src, trail, h1, lead, actions, media):
    return f"""<section class="page-hero">
    <div class="page-hero-grid">
      <div class="ph-copy">
        {crumbs_html(src, trail)}
        <h1>{esc(h1)}</h1>
        <p class="lead">{esc(lead)}</p>
        <div class="hero-actions">{actions}</div>
      </div>
      {media}
    </div>
  </section>"""


def cta_band(src, heading, text, msg):
    return f"""<section class="cta-band">
  <div class="container cta-inner">
    <div>
      <h2>{esc(heading)}</h2>
      <p>{esc(text)}</p>
      <p class="cta-hours">{icon('clock')}{esc(C.HOURS_TEXT)}</p>
    </div>
    <div class="cta-actions">
      {pill('تواصل على واتساب', wa=msg, gold=True)}
      {pill('اتصل بالمكتب', tel=C.PHONE_TEL)}
    </div>
  </div>
</section>"""


def hours_rows():
    rows = [("السبت", 6, True), ("الأحد", 0, True), ("الإثنين", 1, True), ("الثلاثاء", 2, True),
            ("الأربعاء", 3, True), ("الخميس", 4, True), ("الجمعة", 5, False)]
    out = []
    for name, d, is_open in rows:
        if is_open:
            out.append(f'<li data-day="{d}"><span class="d">{name}</span><span class="h">٨:٠٠ – ١١:٣٠ م</span><span class="s">مفتوح</span></li>')
        else:
            out.append(f'<li data-day="{d}" class="off"><span class="d">{name}</span><span class="h">مغلق</span><span class="s">إجازة</span></li>')
    return "".join(out)


# ------------------------------------------------------------------- pages
def build_home():
    src = ""
    title = f"{C.LAWYER} | {C.OFFICE} في دمياط"
    desc = f"{C.LAWYER}: مراجعة عقود الملكية قبل الشراء وصياغة العقود وتأسيس الشركات في دمياط. {C.OFFICE}. تواصل واتساب 01140118038."
    hw, hh = image_size("assets/hero.webp")
    prop = SVC["property-contract-review"]
    stats = [("building", str(len(C.SERVICES)).translate(str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")), "خدمة قانونية"),
             ("calendar", "٦", "أيام استقبال أسبوعيًا"),
             ("clock", "٨ – ١١:٣٠", "مساءً"),
             ("pin", "دمياط", "بجانب مدرسة سعد الأسمر")]
    stats_html = "".join(f'<li>{icon(i)}<b>{b}</b><span>{esc(t)}</span></li>' for i, b, t in stats)
    frame = f"""<section class="hero" id="hero">
    <div class="hero-bg" aria-hidden="true"><img class="watermark" src="{asset(src, 'assets/logo.png')}" alt="" width="640" height="640"></div>
    <div class="hero-grid">
      <div class="hero-copy">
        <p class="badge">{icon('scales')}{esc(C.OFFICE)} · دمياط</p>
        <h1>حلولك القانونية<br>في أيدٍ <em>أمينة</em></h1>
        <p class="lawyer-name"><b>{esc(C.LAWYER)}</b></p>
        <p class="lead">نراجع عقود الملكية قبل أن تشتري، ونصوغ عقودك، ونؤسس شركتك، ونتولى قضاياك بوضوح وسرية.</p>
        <div class="hero-actions">
          {pill('احجز استشارة', wa='السلام عليكم، أرغب في حجز استشارة قانونية.', gold=True)}
          {pill('مراجعة عقد ملكية', link=href(src, svc_path(prop['slug'])))}
        </div>
      </div>
      <div class="hero-portrait">
        <img id="heroPhoto" src="{asset(src, 'assets/hero.webp')}" alt="{esc(C.LAWYER, quote=True)}، {esc(C.OFFICE, quote=True)} في دمياط" width="{hw}" height="{hh}" hidden fetchpriority="high">
      </div>
      <aside class="hours-card" aria-label="مواعيد الاستقبال">
        <strong class="hc-time">٨:٠٠ – ١١:٣٠ مساءً</strong>
        <p>كل يوم ما عدا الجمعة.</p>
        {pill('احجز موعدك', wa='السلام عليكم، أرغب في حجز موعد للاستشارة.', gold=True)}
      </aside>
    </div>
    <ul class="stats" aria-label="معلومات سريعة">{stats_html}</ul>
  </section>"""

    why_titles = "".join(
        f'<li><span class="n">{"١٢٣٤٥"[i]}-</span><span>{esc(t)}</span></li>' for i, (t, _) in enumerate(C.WHY))
    main = f"""<section class="section light" id="focus">
  <div class="container">
    <div class="sec-head">
      <p class="tag">الأكثر طلبًا</p>
      <h2>قبل أن تشتري أو توقّع، <em>راجع أوراقك</em></h2>
      <p class="sec-lead">أغلب النزاعات تبدأ من عقد لم يُراجع أو عقار لم تُفحص ملكيته. هاتان الخدمتان هما الأكثر طلبًا لدينا.</p>
    </div>
    <div class="focus-grid">{"".join(focus_card(s, src) for s in FOCUS)}</div>
  </div>
</section>

<section class="panel" id="why">
  <div class="container why-wrap">
    <div class="why-head">
      <p class="tag tag-dark">لماذا نحن</p>
      <h2>لماذا <em>{esc(C.OFFICE)}</em>؟</h2>
      <p class="sec-lead">{esc(C.WHY_QUOTE)}</p>
      {pill('اعرف المزيد عنا', link=href(src, 'about/'), gold=True)}
    </div>
    <ol class="why-titles">{why_titles}</ol>
  </div>
</section>

<section class="section light" id="services">
  <div class="container">
    <div class="sec-head">
      <p class="tag">خدماتنا</p>
      <h2>كل ما تحتاجه قانونيًا، <em>في مكان واحد</em></h2>
    </div>
    <div class="mini-grid">{"".join(mini_card(s, src) for s in OTHERS)}</div>
    <div class="center-cta">{pill('عرض كل الخدمات', link=href(src, 'services/'), gold=True)}</div>
  </div>
</section>

{cta_band(src, 'جاهز لتبدأ؟', 'أرسل لنا موقفك على واتساب باختصار، ونرد عليك لتحديد موعد الاستشارة.', 'السلام عليكم، أرغب في الاستفسار عن خدمات المكتب.')}"""
    return src, page_shell(src, title, desc, [], "home", frame, main)


def build_about():
    src = "about/"
    title = f"من نحن | {C.OFFICE} في دمياط"
    desc = "نعمل كشركاء استراتيجيين لحماية استثماراتك وتأمين مسارك القانوني: خبرة متخصصة، وقاية قانونية قبل النزاع، سرعة ودقة إجرائية، وشفافية وسرية."
    hw, hh = image_size("assets/hero.webp")
    media = (f'<div class="ph-media person"><img src="{asset(src, "assets/hero.webp")}" alt="{esc(C.LAWYER, quote=True)}" '
             f'width="{hw}" height="{hh}"></div>')
    frame = page_hero(src, [("الرئيسية", ""), ("من نحن", None)], "من نحن", C.WHY_QUOTE,
                      pill("احجز استشارة", wa="السلام عليكم، أرغب في حجز استشارة قانونية.", gold=True) +
                      pill("خدماتنا", link=href(src, "services/")), media)
    why = "".join(
        f'<li><span class="n">{"١٢٣٤٥"[i]}-</span><div><h3>{esc(t)}</h3><p>{esc(d)}</p></div></li>' for i, (t, d) in enumerate(C.WHY))
    steps = "".join(f'<li><span class="num">{"١٢٣٤"[i]}</span><h3>{esc(t)}</h3><p>{esc(d)}</p></li>' for i, (t, d) in enumerate(C.PROCESS))
    main = f"""<section class="section light">
  <div class="container">
    <div class="sec-head">
      <p class="tag">لماذا نحن</p>
      <h2>لماذا <em>{esc(C.OFFICE)}</em>؟</h2>
    </div>
    <ol class="why-list">{why}</ol>
  </div>
</section>

<section class="panel">
  <div class="container">
    <div class="panel-head"><div>
      <p class="tag tag-dark">كيف نعمل</p>
      <h2>خطوات <em>واضحة</em> وبسيطة</h2>
    </div></div>
    <ol class="steps">{steps}</ol>
  </div>
</section>

<section class="section light">
  <div class="container">
    <div class="sec-head">
      <p class="tag">خدماتنا</p>
      <h2>مجالات <em>عملنا</em></h2>
    </div>
    <div class="mini-grid">{"".join(mini_card(s, src) for s in C.SERVICES)}</div>
  </div>
</section>

{cta_band(src, 'لنبدأ بمناقشة موقفك', 'أرسل لنا موقفك على واتساب، ونرد عليك لتحديد موعد الاستشارة.', 'السلام عليكم، أرغب في الاستفسار عن خدمات المكتب.')}"""
    graph = [breadcrumb([("الرئيسية", url("")), ("من نحن", url(src))])]
    return src, page_shell(src, title, desc, graph, "about", frame, main)


def build_services_hub():
    src = "services/"
    title = f"خدماتنا القانونية في دمياط | {C.OFFICE}"
    desc = "مراجعة عقود الملكية قبل الشراء، صياغة العقود، تأسيس الشركات، العلامات التجارية، التراخيص، الملكية الفكرية، والقضايا الجنائية والأسرية والإدارية والمدنية والعمالية."
    frame = page_hero(src, [("الرئيسية", ""), ("خدماتنا", None)], "خدماتنا القانونية",
                      "اختر الخدمة التي تهمك لتقرأ تفاصيلها وخطواتها والمستندات المطلوبة، ثم تواصل معنا على واتساب.",
                      pill("احجز استشارة", wa="السلام عليكم، أرغب في حجز استشارة قانونية.", gold=True),
                      '<div class="ph-media media-art" aria-hidden="true">' + icon("scales") + "</div>")
    main = f"""<section class="section light">
  <div class="container">
    <div class="sec-head">
      <p class="tag">الأكثر طلبًا</p>
      <h2>قبل أن تشتري أو توقّع، <em>راجع أوراقك</em></h2>
    </div>
    <div class="focus-grid">{"".join(focus_card(s, src) for s in FOCUS)}</div>
    <div class="sec-head second">
      <p class="tag">باقي الخدمات</p>
      <h2>خبرة <em>تثق بها</em> في كل ملف</h2>
    </div>
    <div class="hub-grid">{"".join(hub_card(s, src) for s in OTHERS)}</div>
  </div>
</section>

{cta_band(src, 'لم تجد ما تبحث عنه؟', 'أرسل لنا موقفك على واتساب، وسنخبرك إن كان من اختصاصنا وكيف نساعدك.', 'السلام عليكم، لدي استفسار قانوني.')}"""
    graph = [breadcrumb([("الرئيسية", url("")), ("خدماتنا", url(src))]),
             {"@type": "CollectionPage", "@id": url(src) + "#collection", "url": url(src), "name": "خدماتنا القانونية",
              "mainEntity": {"@type": "ItemList", "itemListElement": [
                  {"@type": "ListItem", "position": i, "url": url(svc_path(s["slug"])), "name": s["menu"]}
                  for i, s in enumerate(C.SERVICES, 1)]}}]
    return src, page_shell(src, title, desc, graph, "services", frame, main)


def build_contact():
    src = "contact/"
    title = f"تواصل معنا ومواعيد العمل | {C.OFFICE} في دمياط"
    desc = f"احجز استشارتك عبر واتساب 01140118038. المكتب في الشعراء بجانب مدرسة سعد الأسمر بدمياط، والاستقبال مساءً من ٨ إلى ١١:٣٠ كل يوم ما عدا الجمعة."
    frame = page_hero(src, [("الرئيسية", ""), ("تواصل معنا", None)], "تواصل معنا",
                      "أرسل لنا موقفك باختصار على واتساب وسنرد عليك لتحديد موعد الاستشارة، أو اتصل بنا في مواعيد الاستقبال.",
                      pill("تواصل على واتساب", wa="السلام عليكم، أرغب في حجز استشارة قانونية.", gold=True) +
                      pill("اتصل بالمكتب", tel=C.PHONE_TEL),
                      '<div class="ph-media media-art" aria-hidden="true">' + icon("phone") + "</div>")
    lat, lng = C.GEO
    types = ["استشارة قانونية", "مراجعة عقد ملكية قبل الشراء", "صياغة أو مراجعة عقد", "تأسيس شركة", "تسجيل علامة تجارية",
             "ترخيص محل أو مصنع", "ملكية فكرية", "قضية جنائية", "أسرة وأحوال شخصية ومواريث", "قرار إداري",
             "تعويض مدني", "مسألة عمالية", "أخرى"]
    options = "".join(f'<option value="{esc(t, quote=True)}">{esc(t)}</option>' for t in types)
    if Cfg.preview:
        map_html = (f'<a class="map-link" target="_blank" rel="noopener" href="https://www.google.com/maps/search/?api=1&query={lat},{lng}">'
                    'عرض موقع المكتب على خريطة جوجل ↗</a>')
    else:
        map_html = (f'<div class="map"><iframe title="موقع المكتب على الخريطة" loading="lazy" referrerpolicy="no-referrer-when-downgrade" '
                    f'src="https://maps.google.com/maps?q={lat},{lng}&z=16&output=embed"></iframe></div>')
    main = f"""<section class="panel" id="contact">
  <div class="container">
    <div class="contact-grid">
      <form class="wa-form" id="waForm" novalidate>
        <label for="name">الاسم</label>
        <input id="name" name="name" type="text" autocomplete="name" placeholder="اسمك الكريم" required>
        <label for="type">موضوع الاستشارة</label>
        <select id="type" name="type">{options}</select>
        <label for="msg">نبذة مختصرة عن موقفك</label>
        <textarea id="msg" name="msg" rows="4" placeholder="اكتب باختصار ما تحتاجه (اختياري)"></textarea>
        <button class="pill-cta pill-gold btn-block" type="submit"><span>إرسال عبر واتساب</span><span class="pill-arrow" aria-hidden="true">{icon('arrow')}</span></button>
        <p class="form-note">بياناتك لا تُحفظ على هذا الموقع، وتُرسل مباشرة إلى المكتب عبر واتساب.</p>
      </form>
      <div class="contact-info">
        <ul class="info-list">
          <li><span class="info-label">العنوان</span><span>{esc(C.ADDRESS)}<br><small>كود الموقع: CQ3V+3Q</small></span></li>
          <li><span class="info-label">الهاتف وواتساب</span><a href="tel:{C.PHONE_TEL}" dir="ltr">{C.PHONE_DISPLAY}</a></li>
          <li><span class="info-label">المواعيد</span><span>{esc(C.HOURS_TEXT)}</span></li>
        </ul>
        {map_html}
        {pill('احصل على الاتجاهات', link=f'https://www.google.com/maps/dir/?api=1&destination={lat},{lng}', block=True)}
      </div>
    </div>
  </div>
</section>

<section class="section light" id="hours">
  <div class="container hours">
    <div class="hours-head">
      <p class="tag">المواعيد</p>
      <h2>مواعيد <em>الاستقبال</em></h2>
      <p class="hours-note">الاستقبال مساءً. يُفضّل التواصل على واتساب قبل الحضور لتحديد موعدك.</p>
    </div>
    <ul class="hours-list" id="hoursList">{hours_rows()}</ul>
  </div>
</section>

<section class="section light faq-section" id="faq">
  <div class="container faq-wrap">
    <div class="faq-head">
      <p class="tag">أسئلة شائعة</p>
      <h2>إجابات <em>سريعة</em></h2>
    </div>
    {faq_html(C.GENERAL_FAQ)}
  </div>
</section>"""
    graph = [breadcrumb([("الرئيسية", url("")), ("تواصل معنا", url(src))]), faq_graph(src, C.GENERAL_FAQ)]
    return src, page_shell(src, title, desc, graph, "contact", frame, main)


def build_service(s):
    path = svc_path(s["slug"])
    src = path
    title = f"{s['title']} | {C.OFFICE}"
    if len(title) > 72:          # keep search-result titles short enough to show in full
        title = s["title"]
    trail = [("الرئيسية", ""), ("خدماتنا", "services/"), (s["menu"], None)]
    media = media_html(s, src, "ph-media")
    frame = page_hero(src, trail, s["h1"], s["lead"],
                      pill("اسأل على واتساب", wa=s["wa"], gold=True) + pill("اتصل بالمكتب", tel=C.PHONE_TEL), media)
    secs = []
    for i, (h2, blocks) in enumerate(s["sections"], 1):
        secs.append(f'<section class="art-sec" id="s{i}"><h2>{esc(h2)}</h2>\n{blocks_html(blocks)}</section>')
    secs.append(f'<section class="art-sec" id="faq"><h2>أسئلة شائعة</h2>\n{faq_html(s["faq"])}</section>')
    def side_link(o):
        cur = ' aria-current="page"' if o["slug"] == s["slug"] else ""
        return f'<li><a href="{href(src, svc_path(o["slug"]))}"{cur}>{icon(o["icon"])}{esc(o["menu"])}</a></li>'
    other_links = "".join(side_link(o) for o in C.SERVICES)
    aside = f"""<aside class="aside">
        <div class="aside-card contact-card">
          <h2>تحدث معنا الآن</h2>
          <p>أرسل موقفك باختصار وسنرد عليك لتحديد موعد الاستشارة.</p>
          {pill('تواصل على واتساب', wa=s['wa'], gold=True, block=True)}
          <a class="aside-phone" href="tel:{C.PHONE_TEL}" dir="ltr">{icon('phone')}{C.PHONE_DISPLAY}</a>
          <p class="aside-hours">{icon('clock')}{esc(C.HOURS_TEXT)}</p>
        </div>
        <nav class="aside-card links-card" aria-label="الخدمات"><h2>خدماتنا</h2><ul>{other_links}</ul></nav>
      </aside>"""
    related = "".join(mini_card(SVC[r], src) for r in s["related"])
    main = f"""<section class="page">
  <div class="container page-layout">
    <article class="article">
      {chr(10).join(secs)}
    </article>
    {aside}
  </div>
</section>

<section class="section light related">
  <div class="container">
    <div class="sec-head"><p class="tag">اقرأ أيضًا</p><h2>خدمات <em>ذات صلة</em></h2></div>
    <div class="mini-grid">{related}</div>
  </div>
</section>

{cta_band(src, f'هل تحتاج إلى مساعدة في: {s["menu"]}؟', 'أرسل لنا موقفك على واتساب باختصار، ونرد عليك لتحديد موعد الاستشارة.', s['wa'])}"""
    graph = [
        breadcrumb([("الرئيسية", url("")), ("خدماتنا", url("services/")), (s["menu"], url(path))]),
        {"@type": "Service", "@id": url(path) + "#service", "name": s["menu"], "serviceType": s["menu"],
         "description": s["desc"], "url": url(path), "provider": {"@id": url("#office")},
         "areaServed": {"@type": "City", "name": "دمياط"}},
        faq_graph(path, s["faq"]),
    ]
    return src, page_shell(src, title, s["desc"], graph, s["slug"], frame, main)


def build_404():
    return f"""<!doctype html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex"><title>الصفحة غير موجودة | {esc(C.OFFICE)}</title>
<style>body{{margin:0;min-height:100vh;display:grid;place-items:center;background:#13242b;color:#f2f6f6;font-family:Cairo,Tajawal,system-ui,sans-serif;text-align:center;padding:24px}}
h1{{font-size:2rem;margin:0 0 8px}}p{{color:#9fb0b5}}a{{display:inline-block;margin-top:12px;padding:10px 24px;border-radius:999px;background:#cdb06a;color:#13242b;font-weight:700;text-decoration:none}}</style></head>
<body><main><h1>الصفحة غير موجودة</h1><p>الرابط الذي فتحته غير صحيح أو تم نقله.</p><a href="{Cfg.site}">العودة إلى الرئيسية</a></main></body></html>
"""


# ----------------------------------------------------------- text/seo files
def build_robots():
    bots = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User", "PerplexityBot",
            "Perplexity-User", "Google-Extended", "Applebot-Extended", "Bingbot", "Googlebot", "CCBot", "Bytespider",
            "Meta-ExternalAgent", "Amazonbot", "DuckDuckBot"]
    return ("User-agent: *\nAllow: /\n\n" + "".join(f"User-agent: {b}\nAllow: /\n\n" for b in bots)
            + f"Sitemap: {url('sitemap.xml')}\n")


def build_sitemap(paths):
    prio = {"": "1.0", "services/": "0.9"}
    rows = []
    for p in paths:
        pr = prio.get(p, "0.9" if p.startswith("services/") and any(p == svc_path(s["slug"]) for s in FOCUS) else "0.8")
        rows.append(f"  <url>\n    <loc>{url(p)}</loc>\n    <lastmod>{Cfg.today}</lastmod>\n    <changefreq>monthly</changefreq>\n"
                    f"    <priority>{pr}</priority>\n    <xhtml:link rel=\"alternate\" hreflang=\"ar-EG\" href=\"{url(p)}\"/>\n  </url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(rows) + "\n</urlset>\n")


def build_llms():
    svc = "\n".join(f"- [{s['menu']}]({url(svc_path(s['slug']))}): {s['desc']}" for s in C.SERVICES)
    return f"""# {C.OFFICE}

> مكتب {C.LAWYER} في دمياط (مصر). يتولى مراجعة عقود الملكية قبل شراء العقار، وصياغة ومراجعة العقود، وتأسيس الشركات، وتسجيل العلامات التجارية، واستخراج التراخيص، والملكية الفكرية، والقضايا الجنائية والأحوال الشخصية والمواريث، والطعن على القرارات الإدارية، والتعويضات المدنية، والمسائل العمالية. الاستقبال مساءً من ٨:٠٠ إلى ١١:٣٠ كل يوم ما عدا الجمعة.

## بيانات المكتب
- الاسم: {C.OFFICE} (Elwali for legal services)
- المحامي: {C.LAWYER} (Mahmoud Gamal Elwali)
- المدينة: دمياط، مصر
- العنوان: {C.ADDRESS}
- الهاتف وواتساب: +20 114 011 8038 (01140118038)
- الخريطة: https://www.google.com/maps?cid={C.MAPS_CID}
- مواعيد العمل: كل يوم ما عدا الجمعة، من ٨:٠٠ مساءً إلى ١١:٣٠ مساءً
- اللغة: العربية

## الصفحات
- [الرئيسية]({url('')}): التعريف بالمكتب وأهم الخدمات
- [من نحن]({url('about/')}): لماذا نحن وكيف نعمل
- [خدماتنا]({url('services/')}): كل الخدمات القانونية
- [تواصل معنا]({url('contact/')}): العنوان والمواعيد والأسئلة الشائعة

## الخدمات
{svc}

## ملاحظة
المحتوى للتعريف والمعلومات العامة وليس استشارة قانونية.

# English summary
{C.OFFICE} (Elwali for legal services) is a law office in Damietta, Egypt, run by lawyer Mahmoud Gamal Elwali. Main services: pre-purchase review of property ownership documents and contracts, contract drafting and review, company formation, trademark registration, shop and factory licensing, intellectual property, criminal defence, personal status and inheritance, administrative-court challenges, civil compensation, and labour matters. Hours: every day except Friday, 8:00-11:30 PM. Address: next to Saad El-Asmar School, El-Shuaraa, Abdo Saad, Damietta. Phone and WhatsApp: +20 114 011 8038. Website: {Cfg.site}
"""


# --------------------------------------------------------------------- main
def write(rel, text):
    full = os.path.join(Cfg.outdir, rel)
    os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)


def as_fragment(doc):
    """Artifact previews wrap the main page in their own document skeleton: keep only head tags and body."""
    h = re.search(r"<head>(.*?)</head>", doc, re.S).group(1)
    h = re.sub(r'\s*<meta charset="utf-8">|\s*<meta name="viewport"[^>]*>', "", h)
    b = re.search(r"<body>(.*?)</body>", doc, re.S).group(1)
    return f"{h}\n<style>html{{direction:rtl}}</style>\n{b}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default=DEFAULT_SITE, help="public address, e.g. https://example.com/")
    ap.add_argument("--preview", metavar="OUTDIR", help="flat .html build (for artifact previews)")
    args = ap.parse_args()
    Cfg.site = args.site if args.site.endswith("/") else args.site + "/"
    Cfg.preview = bool(args.preview)
    Cfg.outdir = os.path.abspath(args.preview) if args.preview else ROOT

    pages = [build_home(), build_about(), build_services_hub(), build_contact()] + [build_service(s) for s in C.SERVICES]
    for path, doc in pages:
        if Cfg.preview and path == "":
            doc = as_fragment(doc)
        write(out_file(path), doc)
    if Cfg.preview:
        for sub in ("css", "js", "assets"):
            dst = os.path.join(Cfg.outdir, sub)
            shutil.rmtree(dst, ignore_errors=True)
            shutil.copytree(os.path.join(ROOT, sub), dst)
    else:
        write("404.html", build_404())
        write("robots.txt", build_robots())
        write("sitemap.xml", build_sitemap([p for p, _ in pages]))
        write("llms.txt", build_llms())
    print(f"{len(pages)} pages -> {Cfg.outdir} ({'preview' if Cfg.preview else Cfg.site})")


if __name__ == "__main__":
    main()
