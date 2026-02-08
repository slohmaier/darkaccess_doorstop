# darkaccess_doorstop

SCons integration and HTML post-processing for [Doorstop](https://doorstop.readthedocs.io/) requirements management. Transforms Doorstop's default HTML output into accessible, dark-mode-ready documentation with project branding.

## Features

- **CDN assets**: Replaces local Bootstrap/MathJax with CDN links (with SRI integrity hashes)
- **Dark mode**: Automatic dark/light theme via `prefers-color-scheme`
- **Accessibility**: Skip-nav link, `lang` attribute, table captions
- **Project branding**: Replaces Doorstop branding with your project name
- **SCons targets**: `reqs-deps`, `reqs-validate`, `reqs-publish`

## Installation

Add as a git submodule to your project:

```bash
git submodule add -b main git@github.com:slohmaier/darkaccess_doorstop.git tools/darkaccess_doorstop
```

When cloning a project that uses this submodule, initialize it with:

```bash
git clone --recurse-submodules <your-project-url>

# Or if already cloned without submodules:
git submodule update --init --recursive
```

To update the submodule to the latest version:

```bash
git submodule update --remote tools/darkaccess_doorstop
git add tools/darkaccess_doorstop
git commit -m "Update darkaccess_doorstop submodule"
```

## SCons Integration

In your `SConstruct`:

```python
import sys, os
sys.path.insert(0, os.path.join(Dir('.').abspath, 'tools', 'darkaccess_doorstop'))
import scons_doorstop

# After creating your SCons Environment:
scons_doorstop.register_targets(env, project_root=PROJECT_ROOT, config={
    'project_name': 'MyProject',
    'reqs_dir': 'reqs',                                    # optional, default 'reqs'
    'documents': {'req': 'REQ', 'ui': 'UI', 'tst': 'TST'}, # optional, auto-discovered
})
```

This registers three targets:

| Target | Description |
|--------|-------------|
| `scons reqs-deps` | Install Doorstop via pip |
| `scons reqs-validate` | Run `doorstop` validation, count items per document |
| `scons reqs-publish` | Publish HTML, post-process, remove template/ |

### Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `project_name` | str | `''` | Project name for navbar branding and headings |
| `reqs_dir` | str | `'reqs'` | Directory containing Doorstop documents |
| `documents` | dict | auto | Map of dir name to prefix (e.g., `{'req': 'REQ'}`) |

If `documents` is omitted, document directories are auto-discovered by scanning for `.doorstop.yml` files.

## CLI Usage

The post-processor can also be used standalone:

```bash
python tools/darkaccess_doorstop/postprocess_html.py <output_dir> --project-name "MyProject"
```

Without `--project-name`, generic "Requirements" branding is used.

## What the Post-Processor Does

1. Replaces local Bootstrap CSS/JS with CDN links (SRI hashes included)
2. Removes local `general.css`, `doorstop.css`, and MathJax
3. Injects inline CSS for section indentation, captions, and dark mode refinements
4. Adds `<html lang="en" data-bs-theme="light">` attributes
5. Adds viewport meta tag for responsive layout
6. Replaces the Doorstop navbar with a project-branded navbar
7. Adds skip-navigation link for accessibility
8. Replaces "Doorstop index" / "Doorstop traceability matrix" headings
9. Adds `<caption>` to the traceability table
10. Injects dark mode JavaScript that follows system preference

## License

MIT
