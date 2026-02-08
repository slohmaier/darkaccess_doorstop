#!/usr/bin/env python3
"""Post-process Doorstop HTML output for requirements documentation.

Transforms generated HTML files:
- Replace local Bootstrap/MathJax assets with CDN links (with SRI)
- Add dark mode support (Bootstrap 5.3 data-bs-theme)
- Add accessibility features (lang, skip-nav, captions)
- Replace Doorstop branding with project-specific navbar

Usage:
    python postprocess_html.py <output_dir> [--project-name "MyProject"]
"""

import argparse
import os
import re
import sys


# Bootstrap 5.3.3 CDN with SRI integrity hashes
BOOTSTRAP_CSS_CDN = (
    '<link rel="stylesheet" '
    'href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" '
    'integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YcnS/S7cOl+1QRLI0jaPJSKyIp6s0GOuQ24p" '
    'crossorigin="anonymous">'
)

BOOTSTRAP_JS_CDN = (
    '<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js" '
    'integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz" '
    'crossorigin="anonymous"></script>'
)

# Inline CSS that replaces general.css + doorstop.css + dark mode refinements
INLINE_CSS = """\
<style>
  /* Section indentation (from general.css) */
  section > * { margin-left: 30px; }
  section > :first-child { margin-left: 0; }

  /* Caption styling (from doorstop.css) */
  .caption { text-align: center; font-size: 15px; }
  #img { width: 100%; }

  /* Dark mode refinements */
  [data-bs-theme="dark"] .table { --bs-table-bg: transparent; }
  [data-bs-theme="dark"] a { color: #6ea8fe; }
  [data-bs-theme="dark"] a:hover { color: #9ec5fe; }
  [data-bs-theme="dark"] .navbar { border-bottom: 1px solid rgba(255,255,255,0.1); }
  [data-bs-theme="dark"] section { border-color: rgba(255,255,255,0.1); }
  [data-bs-theme="dark"] .dropdown-menu { --bs-dropdown-bg: #2b3035; }

  /* Skip nav (Bootstrap visually-hidden-focusable handles show-on-focus) */
</style>"""

# Dark mode JS snippet
DARK_MODE_JS = """\
<script>
(function() {
  var mq = window.matchMedia('(prefers-color-scheme: dark)');
  function apply(e) {
    document.documentElement.setAttribute('data-bs-theme', e.matches ? 'dark' : 'light');
  }
  apply(mq);
  mq.addEventListener('change', apply);
})();
</script>"""

SKIP_NAV_LINK = (
    '<a href="#main-content" '
    'class="visually-hidden-focusable position-absolute top-0 start-0 p-2 m-1 bg-primary text-white rounded">'
    'Skip to main content</a>'
)


def compute_nav_prefix(html):
    """Determine the relative path prefix for navigation links.

    Files in output/ root use '' prefix; files in output/documents/ use '../'.
    We detect this by checking existing href patterns in the original HTML.
    """
    if '../template/' in html or '../index.html' in html:
        return '../'
    return ''


def build_navbar(title, nav_prefix, has_contents_dropdown, contents_html, project_name=""):
    """Build the project-branded navbar HTML."""
    # Brand text
    if project_name:
        brand = f'{project_name} Requirements'
    else:
        brand = 'Requirements'

    # Documents and Traceability links
    docs_href = f'{nav_prefix}index.html'
    trace_href = f'{nav_prefix}traceability.html'

    contents_section = ''
    if has_contents_dropdown and contents_html:
        contents_section = f"""\
          <li class="nav-item dropdown">
            <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false">
              Contents
            </a>
            <ul class="dropdown-menu">
{contents_html}
            </ul>
          </li>"""

    return f"""\
<header>
  <nav class="navbar navbar-expand-lg sticky-top bg-body-tertiary" aria-label="Main navigation">
    <div class="container-xxl">
      <a class="navbar-brand fw-bold" href="{docs_href}">{brand}</a>
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav">
          <li class="nav-item">
            <a class="nav-link" href="{docs_href}">Documents</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="{trace_href}">Traceability</a>
          </li>
{contents_section}
        </ul>
      </div>
    </div>
  </nav>
</header>"""


def extract_contents_dropdown(html):
    """Extract the Contents dropdown menu items from the original navbar."""
    # Look for the Contents dropdown UL content
    m = re.search(
        r'<a class="nav-link dropdown-toggle"[^>]*>\s*Contents\s*</a>\s*<ul class="dropdown-menu">(.*?)</ul>\s*</li>',
        html,
        re.DOTALL
    )
    if m:
        return m.group(1).strip()
    return None


def extract_title(html):
    """Extract the page title from <title> tag."""
    m = re.search(r'<title>(.*?)</title>', html)
    if m:
        return m.group(1)
    return 'Document'


def process_html(filepath, project_name=""):
    """Process a single HTML file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    nav_prefix = compute_nav_prefix(html)
    title = extract_title(html)

    # --- Heading text ---
    if project_name:
        index_heading = f'{project_name} Requirements'
        trace_heading = f'{project_name} Traceability Matrix'
    else:
        index_heading = 'Requirements'
        trace_heading = 'Traceability Matrix'

    # --- <head> replacements ---

    # Add lang to <html> (data-bs-theme set by dark mode JS in <head>)
    html = re.sub(r'<html\b[^>]*>', '<html lang="en">', html)

    # Add viewport meta if not present
    if 'name="viewport"' not in html:
        html = html.replace(
            '<meta charset="utf-8" />',
            '<meta charset="utf-8" />\n  <meta name="viewport" content="width=device-width, initial-scale=1">'
        )

    # Replace local Bootstrap CSS with CDN
    html = re.sub(
        r'<link[^>]*href="[^"]*bootstrap\.min\.css"[^>]*/?>',
        BOOTSTRAP_CSS_CDN,
        html
    )

    # Remove general.css and doorstop.css links, replace with inline styles
    html = re.sub(r'<link[^>]*href="[^"]*general\.css"[^>]*/?>[\r\n]*', '', html)
    html = re.sub(r'<link[^>]*href="[^"]*doorstop\.css"[^>]*/?>[\r\n]*', '', html)

    # Insert inline CSS and dark mode JS after Bootstrap CDN link
    # Dark mode JS must be in <head> to apply before first paint
    html = html.replace(BOOTSTRAP_CSS_CDN, BOOTSTRAP_CSS_CDN + '\n  ' + INLINE_CSS + '\n  ' + DARK_MODE_JS)

    # Remove MathJax script tags
    html = re.sub(
        r'<script[^>]*id="MathJax-script"[^>]*></script>[\r\n]*',
        '',
        html
    )
    html = re.sub(
        r'<script type="text/x-mathjax-config">.*?</script>[\r\n]*',
        '',
        html,
        flags=re.DOTALL
    )

    # --- Navbar replacement ---

    # Extract Contents dropdown before replacing the header
    contents_html = extract_contents_dropdown(html)
    has_contents = contents_html is not None

    # Replace entire <header>...</header> with branded navbar
    new_navbar = build_navbar(title, nav_prefix, has_contents, contents_html, project_name)
    html = re.sub(r'<header\b[^>]*>.*?</header>', new_navbar, html, flags=re.DOTALL)

    # --- <body> accessibility ---

    # Add skip-nav link as first child of <body>
    html = html.replace('<body>', '<body>\n' + SKIP_NAV_LINK)

    # Add id="main-content" to <main> element
    html = re.sub(r'<main\b([^>]*)>', r'<main id="main-content"\1>', html)

    # --- Replace Doorstop headings ---

    html = html.replace('<H1>Doorstop index</H1>', f'<h1>{index_heading}</h1>')
    html = html.replace(
        '<H1>Doorstop traceability matrix</H1>',
        f'<h1>{trace_heading}</h1>'
    )

    # --- Traceability table caption ---

    # Add <caption> to the traceability table if present
    html = re.sub(
        r'(<table class="table">\s*<thead>)',
        r'<table class="table">\n<caption>Requirements traceability matrix</caption>\n<thead>',
        html
    )

    # --- Replace local Bootstrap JS with CDN ---

    html = re.sub(
        r'<script[^>]*src="[^"]*bootstrap\.bundle\.min\.js"[^>]*></script>',
        BOOTSTRAP_JS_CDN,
        html
    )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)


def postprocess_directory(output_dir, project_name=""):
    """Post-process all HTML files in a directory tree.

    Args:
        output_dir: Path to the directory containing Doorstop HTML output.
        project_name: Project name for branding (e.g., "ControlNav").
                      If empty, generic "Requirements" branding is used.

    Returns:
        Number of files processed.
    """
    count = 0
    for root, dirs, files in os.walk(output_dir):
        for fname in files:
            if fname.endswith('.html'):
                filepath = os.path.join(root, fname)
                print(f'  Processing: {os.path.relpath(filepath, output_dir)}')
                process_html(filepath, project_name)
                count += 1

    print(f'  Post-processed {count} HTML file(s)')
    return count


def main():
    parser = argparse.ArgumentParser(
        description='Post-process Doorstop HTML output with CDN assets, dark mode, and branding.'
    )
    parser.add_argument('output_dir', help='Directory containing Doorstop HTML output')
    parser.add_argument('--project-name', default='', help='Project name for branding (e.g., "ControlNav")')

    args = parser.parse_args()

    if not os.path.isdir(args.output_dir):
        print(f'ERROR: Directory not found: {args.output_dir}')
        sys.exit(1)

    postprocess_directory(args.output_dir, args.project_name)


if __name__ == '__main__':
    main()
