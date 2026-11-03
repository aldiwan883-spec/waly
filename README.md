# الولي للخدمات القانونية

Static Arabic (RTL) site for the law office of الأستاذ محمود جمال الولي المحامي in Damietta. Plain HTML, CSS and JS, no framework. Pages are generated from one content file and committed, so any static host (GitHub Pages included) serves them as they are.

## Pages

| URL | Page |
|---|---|
| `/` | Home |
| `/about/` | من نحن |
| `/services/` | All services |
| `/services/<slug>/` | One page per service (11 pages) |
| `/contact/` | Contact form, map, opening hours, FAQ |

Every service page has its own title, description, breadcrumb, FAQ, and structured data (`Service`, `FAQPage`, `BreadcrumbList`).

## Editing

- **Text** (services, FAQ, why-us, hours, address, phone): `content.py`
- **Layout and templates**: `build.py`
- **Styles / scripts**: `css/style.css`, `js/main.js` (the WhatsApp number is also in `CONFIG` at the top of `js/main.js`)
- **Images**: `assets/`. The hero portrait is `assets/hero.webp` (transparent background).

After any change to `content.py` or `build.py`, regenerate the pages:

```bash
python3 build.py
```

Python 3 with Pillow installed (used only to read image sizes).

## Public address

The canonical URLs, sitemap, `robots.txt`, `llms.txt` and share tags use `https://elwali.aldiwan.io/` by default. To use another address, rebuild with:

```bash
python3 build.py --site https://your-domain.example/
```

Links between pages are relative, so the site also works under a sub-path such as `https://<user>.github.io/waly/`.

## Generated files

`index.html`, `about/`, `services/`, `contact/`, `404.html`, `sitemap.xml`, `robots.txt` and `llms.txt` are written by `build.py`. Do not edit them by hand.
