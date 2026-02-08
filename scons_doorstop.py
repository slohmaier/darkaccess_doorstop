"""SCons integration for Doorstop requirements management.

Registers reqs-deps, reqs-validate, and reqs-publish targets in a SCons build.

Usage in SConstruct:
    import scons_doorstop
    scons_doorstop.register_targets(env, project_root=PROJECT_ROOT, config={
        'project_name': 'MyProject',
        'reqs_dir': 'reqs',
        'documents': {'req': 'REQ', 'ui': 'UI', 'tst': 'TST'},
    })
"""

import os
import shutil
import subprocess
import sys

from postprocess_html import postprocess_directory


def _discover_documents(reqs_dir):
    """Auto-discover Doorstop document directories from .doorstop.yml files.

    Returns a dict mapping directory name to prefix (e.g., {'req': 'REQ'}).
    """
    documents = {}
    if not os.path.isdir(reqs_dir):
        return documents

    for entry in os.listdir(reqs_dir):
        entry_path = os.path.join(reqs_dir, entry)
        doorstop_yml = os.path.join(entry_path, '.doorstop.yml')
        if os.path.isdir(entry_path) and os.path.exists(doorstop_yml):
            # Read the prefix from .doorstop.yml
            prefix = entry.upper()
            try:
                with open(doorstop_yml, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('prefix:'):
                            prefix = line.split(':', 1)[1].strip().strip('"').strip("'")
                            break
            except (OSError, UnicodeDecodeError):
                pass
            documents[entry] = prefix

    return documents


def _install_deps(target, source, env):
    """Install requirements management dependencies (doorstop)."""
    print("\nInstalling requirements management dependencies...")
    deps = ['doorstop']
    cmd = [sys.executable, '-m', 'pip', 'install'] + deps
    result = subprocess.run(cmd)
    if result.returncode == 0:
        print("\nRequirements management dependencies installed successfully.")
    else:
        print("\nFailed to install requirements management dependencies.")
    return result.returncode


def _make_validate_action(project_root, config):
    """Create a validate action closure capturing project_root and config."""
    project_name = config.get('project_name', '')
    reqs_dir_name = config.get('reqs_dir', 'reqs')
    documents = config.get('documents', None)

    def validate_requirements(target, source, env):
        display_name = project_name or 'Doorstop'
        print("\n" + "=" * 60)
        print(f"   {display_name} Requirements Validation")
        print("=" * 60)

        reqs_dir = os.path.join(project_root, reqs_dir_name)
        if not os.path.exists(reqs_dir):
            print(f"ERROR: {reqs_dir_name}/ directory not found.")
            return 1

        cmd = ['doorstop']
        result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)

        if result.stdout:
            print(result.stdout)

        if result.stderr:
            for line in result.stderr.splitlines():
                if 'ERROR' in line:
                    print(f"  ERROR: {line}")
                elif 'WARNING' in line:
                    print(f"  {line}")

        # Resolve documents (auto-discover if not provided)
        docs = documents if documents else _discover_documents(reqs_dir)

        # Count items per document
        counts = {}
        total = 0
        for dirname, prefix in sorted(docs.items()):
            doc_path = os.path.join(reqs_dir, dirname)
            if os.path.isdir(doc_path):
                count = len([f for f in os.listdir(doc_path) if f.endswith('.yml') and not f.startswith('.')])
                counts[prefix] = count
                total += count

        counts_str = ', '.join(f'{prefix}={count}' for prefix, count in counts.items())
        print(f"\nItem counts: {counts_str}, Total={total}")

        has_errors = 'ERROR' in (result.stderr or '')
        if has_errors:
            print("\nValidation FAILED with errors.")
            return 1

        print("\nValidation passed (warnings are informational).")
        return 0

    return validate_requirements


def _make_publish_action(project_root, config):
    """Create a publish action closure capturing project_root and config."""
    project_name = config.get('project_name', '')
    reqs_dir_name = config.get('reqs_dir', 'reqs')

    def publish_requirements(target, source, env):
        display_name = project_name or 'Doorstop'
        print("\n" + "=" * 60)
        print(f"   {display_name} Requirements Publishing")
        print("=" * 60)

        reqs_dir = os.path.join(project_root, reqs_dir_name)
        output_dir = os.path.join(reqs_dir, 'output')

        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir)

        cmd = ['doorstop', 'publish', 'all', output_dir]
        result = subprocess.run(cmd, cwd=project_root)

        if result.returncode != 0:
            print("\nPublishing failed.")
            return result.returncode

        # Post-process HTML files (CDN, dark mode, accessibility, branding)
        print("\nPost-processing HTML files...")
        postprocess_directory(output_dir, project_name)

        # Remove template/ directory (assets now loaded from CDN)
        template_dir = os.path.join(output_dir, 'template')
        if os.path.exists(template_dir):
            shutil.rmtree(template_dir)
            print("  Removed template/ directory (using CDN)")

        # List output files
        print(f"\nRequirements published to: {output_dir}")
        for root, dirs, files in os.walk(output_dir):
            for f in sorted(files):
                if f.endswith(('.html', '.csv')):
                    fpath = os.path.join(root, f)
                    relpath = os.path.relpath(fpath, output_dir)
                    size = os.path.getsize(fpath) / 1024
                    print(f"  {relpath} ({size:.1f} KB)")

        return 0

    return publish_requirements


def register_targets(env, project_root, config=None):
    """Register Doorstop requirements management targets in a SCons environment.

    Args:
        env: SCons Environment object.
        project_root: Absolute path to the project root directory.
        config: Optional configuration dict with keys:
            - project_name (str): Project name for branding. Default: ''.
            - reqs_dir (str): Requirements directory name. Default: 'reqs'.
            - documents (dict): Map of dir name to prefix, e.g. {'req': 'REQ'}.
                                If omitted, auto-discovered from .doorstop.yml files.

    Returns:
        Dict mapping target name to SCons target node.
    """
    if config is None:
        config = {}

    reqs_deps_target = env.Command('reqs-deps', [], _install_deps)
    reqs_validate_target = env.Command('reqs-validate', [], _make_validate_action(project_root, config))
    reqs_publish_target = env.Command('reqs-publish', [], _make_publish_action(project_root, config))

    env.AlwaysBuild(reqs_deps_target)
    env.AlwaysBuild(reqs_validate_target)
    env.AlwaysBuild(reqs_publish_target)

    return {
        'reqs-deps': reqs_deps_target,
        'reqs-validate': reqs_validate_target,
        'reqs-publish': reqs_publish_target,
    }
