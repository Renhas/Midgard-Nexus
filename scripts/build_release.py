#!/usr/bin/env python3
"""Сборка production-архива Midgard-Nexus.

Базовая фильтрация — через `git ls-files` (уважает .gitignore).
Поверх неё — чёрный список dev/test-артефактов, которые
трекаются в git, но в prod-архив не нужны.
docker-compose.prod.yml переименовывается в docker-compose.yml.
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "dist"
DEFAULT_BASENAME = "midgard-nexus"

# --- Второй проход: что выкидываем даже если оно в git ---------------------

EXCLUDED_DIR_NAMES = {
    "tests",  # любые tests/ внутри apps
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".nox",
    "htmlcov",
    "node_modules",
    "venv",
    ".venv",
    "env",
    ".idea",
    ".vscode",
    ".github",
}

EXCLUDED_FILE_NAMES = {
    # dev-инфра
    ".gitignore",
    ".gitattributes",
    ".gitmodules",
    ".editorconfig",
    ".pre-commit-config.yaml",
    # dev-compose (prod-версия придёт через RENAMES)
    "docker-compose.yml",
    # test-хелперы
    "conftest.py",
    "factories.py",
    # локальное
    ".DS_Store",
    "Thumbs.db",
    "db.sqlite3",
    ".env",
    "pyproject.toml",
}

EXCLUDED_FILE_PATTERNS = [
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.sqlite3",
    "*.log",
    ".env.*",
]

# Точечные относительные пути (файл или каталог).
EXCLUDED_REL_PATHS = {
    "scripts",  # сам скрипт и dev-хелперы
    "requirements/development.txt",
    "src/config/settings/development.py",
    "src/config/settings/test.py",
}

# Что вернуть, даже если паттерн выше это поймал.
KEEP_OVERRIDES = {
    ".env.example",
    ".env.sample",
    ".env.template",
    "scripts/manage.ps1",
    "scripts/init-env.ps1",
    "scripts/reset.ps1",
    "scripts/run.ps1",
    "scripts/manage.sh",
    "scripts/init-env.sh",
    "scripts/reset.sh",
    "scripts/run.sh",
}

RENAMES = {
    "docker-compose.prod.yml": "docker-compose.yml",
}

EXECUTABLE_FILES = {
    "docker/web/entrypoint.sh",
    "docker/web/download_static.sh",
    "scripts/manage.sh",
    "scripts/init-env.sh",
    "scripts/reset.sh",
    "scripts/run.sh",
}


# --- Список файлов проекта -------------------------------------------------


def _git_ls_files(root: Path) -> list[Path] | None:
    """Трекнутые файлы (уже отфильтрованные .gitignore). None, если не git-репо."""
    try:
        res = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            check=True,
            capture_output=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return [Path(p) for p in res.stdout.decode("utf-8").split("\0") if p]


def _walk_all(root: Path) -> list[Path]:
    result: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {".git"}]
        for name in filenames:
            result.append(Path(dirpath, name).relative_to(root))
    return result


# --- Второй проход: какие пути оставить ------------------------------------


def _is_keep_override(posix: str, name: str) -> bool:
    if name in KEEP_OVERRIDES:
        return True
    return any(fnmatch.fnmatch(posix, ov) for ov in KEEP_OVERRIDES)


def should_keep(rel: Path) -> bool:
    posix = rel.as_posix()
    name = rel.name
    parts = rel.parts

    if _is_keep_override(posix, name):
        return True

    if any(p in EXCLUDED_DIR_NAMES for p in parts[:-1]):
        return False
    if name in EXCLUDED_DIR_NAMES:
        return False

    for excl in EXCLUDED_REL_PATHS:
        if posix == excl or posix.startswith(excl + "/"):
            return False

    if name in EXCLUDED_FILE_NAMES:
        return False

    for pattern in EXCLUDED_FILE_PATTERNS:
        if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(posix, pattern):
            return False

    return True


def collect_files(root: Path) -> list[Path]:
    base = _git_ls_files(root)
    source = "git ls-files" if base is not None else "filesystem walk"
    if base is None:
        base = _walk_all(root)
    kept = [p for p in base if should_keep(p)]
    print(
        f"[build] source: {source}; "
        f"{len(base)} candidates -> {len(kept)} files after filter"
    )
    return kept


# --- Копирование / переименования / права ----------------------------------


def copy_project(root: Path, staging: Path, files: list[Path]) -> None:
    for rel in files:
        src = root / rel
        if not src.is_file():
            continue  # трекнутый, но отсутствующий (например, удалён, но не закоммичен)
        dst = staging / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def apply_renames(staging: Path) -> None:
    for src_rel, dst_rel in RENAMES.items():
        src = staging / src_rel
        if not src.exists():
            print(f"[build] warning: не найден {src_rel}", file=sys.stderr)
            continue
        dst = staging / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            dst.unlink()
        src.replace(dst)


def fix_permissions(staging: Path) -> None:
    for rel in EXECUTABLE_FILES:
        p = staging / rel
        if p.exists():
            try:
                p.chmod(0o755)
            except OSError:
                pass


# --- Архивы ----------------------------------------------------------------


def make_zip(source_root: Path, archive_path: Path) -> None:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(source_root.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(source_root).as_posix())


def make_tar(source_root: Path, archive_path: Path) -> None:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "w:gz") as tf:
        for path in sorted(source_root.rglob("*")):
            tf.add(
                path, arcname=path.relative_to(source_root).as_posix(), recursive=False
            )


# --- Версия ----------------------------------------------------------------


def _read_version_via_import(py: Path) -> str | None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("_midgard_version", py)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        print(f"[build] warning: не удалось импортировать {py}: {exc}", file=sys.stderr)
        return None
    v = getattr(module, "__version__", None)
    return str(v) if v else None


def read_version(root: Path) -> str:
    py = root / "src" / "config" / "version.py"
    if py.exists():
        # 1. Пробуем импортировать файл напрямую (без config/__init__.py).
        v = _read_version_via_import(py)
        if v:
            return v
        # 2. Fallback: парсинг. Тот же результат, но без выполнения кода.
        m = re.search(
            r'(?m)^__version__\s*(?::\s*\w+)?\s*=\s*["\']([^"\']+)["\']',
            py.read_text(encoding="utf-8"),
        )
        if m:
            return m.group(1)
        print(f"[build] warning: __version__ не найден в {py}", file=sys.stderr)

    # 2. pyproject.toml [project].version (на будущее)
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        text = pyproject.read_text(encoding="utf-8")
        try:
            import tomllib

            v = tomllib.loads(text).get("project", {}).get("version")
            if v:
                return str(v)
        except Exception:
            m = re.search(r'(?m)^\s*version\s*=\s*"([^"]+)"', text)
            if m:
                return m.group(1)

    # 3. VERSION / version.txt
    for candidate in ("VERSION", "version.txt"):
        p = root / candidate
        if p.exists():
            v = p.read_text(encoding="utf-8").strip()
            if v:
                return v

    # 4. ближайший git-тег — но только если теги вообще есть
    try:
        res = subprocess.run(
            ["git", "-C", str(root), "describe", "--tags", "--abbrev=0"],
            check=True,
            capture_output=True,
            text=True,
        )
        v = res.stdout.strip()
        if v:
            return v.lstrip("v")
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    # 5. крайний случай — короткий SHA, помечаем как dev-сборку
    try:
        res = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        sha = res.stdout.strip()
        if sha:
            return f"0.0.0+{sha}"
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    return "0.0.0"


# --- Точка входа -----------------------------------------------------------


def build(output_dir: Path, basename: str, fmt: str) -> list[Path]:
    version = read_version(PROJECT_ROOT)
    name = f"{basename}-{version}"
    print(f"[build] version={version}")
    output_dir.mkdir(parents=True, exist_ok=True)

    files = collect_files(PROJECT_ROOT)

    created: list[Path] = []
    with tempfile.TemporaryDirectory(prefix="midgard-build-") as tmp:
        tmp_path = Path(tmp)
        staging = tmp_path / name
        staging.mkdir()

        copy_project(PROJECT_ROOT, staging, files)
        apply_renames(staging)
        fix_permissions(staging)

        if fmt in ("zip", "both"):
            p = output_dir / f"{name}.zip"
            make_zip(tmp_path, p)
            created.append(p)
        if fmt in ("tar", "both"):
            p = output_dir / f"{name}.tar.gz"
            make_tar(tmp_path, p)
            created.append(p)

    return created


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Сборка prod-архива Midgard-Nexus.")
    parser.add_argument("--format", choices=("zip", "tar", "both"), default="both")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--name", default=DEFAULT_BASENAME)
    args = parser.parse_args(argv)

    for f in build(args.output_dir.resolve(), args.name, args.format):
        print(f"Created {f} ({f.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
