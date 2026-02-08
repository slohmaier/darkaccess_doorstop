# darkaccess_doorstop - AI Agent Instructions

## Architecture Overview

This module provides two components for Doorstop requirements management:

1. **`postprocess_html.py`** - HTML transformer (both CLI and importable)
2. **`scons_doorstop.py`** - SCons target registration

### postprocess_html.py

The core transformation engine. Key functions:

- `process_html(filepath, project_name="")` - Transform a single HTML file
- `postprocess_directory(output_dir, project_name="")` - Walk directory, transform all `.html` files
- `main()` - CLI entry point with argparse

The `project_name` parameter controls branding:
- Non-empty: `"MyProject Requirements"`, `"MyProject Traceability Matrix"`
- Empty: `"Requirements"`, `"Traceability Matrix"`

All CSS/JS constants are module-level (`BOOTSTRAP_CSS_CDN`, `INLINE_CSS`, `DARK_MODE_JS`, etc.).

### scons_doorstop.py

Single public function: `register_targets(env, project_root, config)`.

Internally uses closures (`_make_validate_action`, `_make_publish_action`) to capture config. The publish action calls `postprocess_directory()` directly (no subprocess).

Document auto-discovery: `_discover_documents()` scans for `.doorstop.yml` files and reads the `prefix:` field.

## Key Design Decisions

- **No subprocess for post-processing**: `scons_doorstop.py` imports `postprocess_directory` directly, avoiding a Python subprocess call.
- **Closures over config**: Validate/publish actions are factory functions that return closures, since SCons action signatures are fixed `(target, source, env)`.
- **Auto-discovery**: If `documents` config is omitted, document prefixes are discovered from `.doorstop.yml` files at runtime.
- **CDN with SRI**: Bootstrap assets use Subresource Integrity hashes for security.

## How to Modify

### Adding a new SCons target
1. Write a new action function or factory in `scons_doorstop.py`
2. Add `env.Command()` + `env.AlwaysBuild()` in `register_targets()`
3. Return the target in the dict

### Changing HTML transformations
1. Modify `process_html()` in `postprocess_html.py`
2. Ensure `project_name` parameter is threaded through if branding-related
3. Test with `python postprocess_html.py <dir> --project-name "Test"`

### Updating Bootstrap version
1. Update `BOOTSTRAP_CSS_CDN` and `BOOTSTRAP_JS_CDN` constants
2. Generate new SRI hashes from the CDN provider

## How to Test

```bash
# Standalone post-processing
python postprocess_html.py /path/to/doorstop/output --project-name "TestProject"

# Via SCons (from consuming project)
scons reqs-validate
scons reqs-publish

# Verify: open output HTML, check navbar brand, headings, dark mode toggle
```
