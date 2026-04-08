"""Core functions for finding configuration files."""

import os
from pathlib import Path
from typing import Optional

# Распространённые имена конфигурационных файлов
CONFIG_PATTERNS = [
    # Общие
    "config.*",
    "configuration.*",
    "settings.*",
    "conf.*",
    "app.*",
    ".env",
    ".env.*",
    # Python
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements*.txt",
    "Pipfile",
    "poetry.lock",
    # JavaScript/TypeScript
    "package.json",
    "package-lock.json",
    "yarn.lock",
    "tsconfig.json",
    "webpack.config.*",
    "vite.config.*",
    "rollup.config.*",
    "babel.config.*",
    ".babelrc",
    "eslintrc.*",
    ".eslintrc",
    "prettier.config.*",
    ".prettierrc",
    "jest.config.*",
    "tailwind.config.*",
    "next.config.*",
    "nuxt.config.*",
    # Java
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "settings.gradle",
    "application.properties",
    "application.yml",
    "application.yaml",
    # Go
    "go.mod",
    "go.sum",
    ".golangci.*",
    # Rust
    "Cargo.toml",
    "Cargo.lock",
    # Ruby
    "Gemfile",
    "Gemfile.lock",
    "Rakefile",
    ".rubocop.yml",
    # PHP
    "composer.json",
    "composer.lock",
    "phpunit.xml",
    ".php-cs-fixer.*",
    # Docker
    "Dockerfile",
    "docker-compose.*",
    ".dockerignore",
    # CI/CD
    ".github",
    ".gitlab-ci.yml",
    ".travis.yml",
    "Jenkinsfile",
    "bitbucket-pipelines.yml",
    # Kubernetes
    "*.yaml",
    "*.yml",
    # Terraform
    "*.tf",
    "terraform.tfvars",
    # Nginx
    "nginx.conf",
    # Database
    "*.sql",
    # Other
    ".editorconfig",
    ".gitignore",
    ".gitattributes",
    "Makefile",
    "CMakeLists.txt",
    "*.ini",
    "*.cfg",
    "*.toml",
    "*.conf",
]

# Расширения файлов конфигов
CONFIG_EXTENSIONS = {
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".conf", ".env", ".properties", ".xml", ".sql", ".tf",
}

# Имена файлов, которые точно являются конфигами
CONFIG_NAMES = {
    "config", "configuration", "settings", "conf", "app",
    ".env", "pyproject", "package", "tsconfig", "webpack.config",
    "vite.config", "docker-compose", "nginx", "application",
    "go.mod", "cargo", "gemfile", "composer", "makefile",
    "dockerfile", ".gitignore", ".editorconfig",
}


def is_config_file(filename: str) -> bool:
    """Проверить, является ли файл конфигурационным."""
    name_lower = filename.lower()

    # Проверка по имени
    name_without_ext = Path(filename).stem.lower()
    if name_without_ext in CONFIG_NAMES or name_lower in CONFIG_NAMES:
        return True

    # Проверка по расширению
    ext = Path(filename).suffix.lower()
    if ext in CONFIG_EXTENSIONS:
        return True

    # Проверка по паттернам
    import fnmatch
    for pattern in CONFIG_PATTERNS:
        if fnmatch.fnmatch(name_lower, pattern.lower()):
            return True

    return False


def find_configs(
    root_path: str,
    max_depth: int = 5,
    file_name_filter: Optional[str] = None,
) -> list[dict]:
    """
    Найти все конфигурационные файлы в директории.

    Args:
        root_path: Корневая директория для поиска.
        max_depth: Максимальная глубина поиска.
        file_name_filter: Опциональный фильтр по имени файла (например, 'docker' найдёт Dockerfile, docker-compose и т.д.)

    Returns:
        Список словарей с информацией о найденных файлах.
    """
    root = Path(root_path).resolve()
    if not root.exists():
        return [{"error": f"Path not found: {root_path}"}]

    if not root.is_dir():
        return [{"error": f"Path is not a directory: {root_path}"}]

    results = []
    root_depth = len(root.parts)

    for dirpath, dirnames, filenames in os.walk(root):
        current_depth = len(Path(dirpath).parts) - root_depth
        if current_depth > max_depth:
            dirnames.clear()
            continue

        # Пропускаем скрытые директории (кроме .github, .config и т.п.)
        allowed_hidden = {".github", ".config", ".vscode", ".idea"}
        dirnames[:] = [
            d for d in dirnames
            if not d.startswith(".") or d in allowed_hidden
        ]
        # Пропускаем node_modules, .venv, __pycache__, dist, build
        skip_dirs = {"node_modules", ".venv", "venv", "__pycache__",
                     "dist", "build", ".git", "target", "vendor"}
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]

        for fname in filenames:
            if not is_config_file(fname):
                continue

            # Фильтр по имени
            if file_name_filter:
                if file_name_filter.lower() not in fname.lower():
                    continue

            full_path = Path(dirpath) / fname
            try:
                stat = full_path.stat()
                results.append({
                    "path": str(full_path),
                    "filename": fname,
                    "relative_path": str(full_path.relative_to(root)),
                    "size_bytes": stat.st_size,
                    "modified": stat.st_mtime,
                })
            except OSError:
                continue

    results.sort(key=lambda x: x["relative_path"])
    return results


def read_config(file_path: str, max_lines: int = 200) -> dict:
    """
    Прочитать содержимое конфигурационного файла.

    Args:
        file_path: Путь к файлу.
        max_lines: Максимальное количество строк для чтения.

    Returns:
        Словарь с содержимым файла и метаданными.
    """
    path = Path(file_path).resolve()
    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    if not path.is_file():
        return {"error": f"Path is not a file: {file_path}"}

    try:
        stat = path.stat()
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = []
            for i, line in enumerate(f):
                if i >= max_lines:
                    lines.append(f"... (truncated, showing first {max_lines} lines)")
                    break
                lines.append(line.rstrip("\n"))

        return {
            "path": str(path),
            "filename": path.name,
            "size_bytes": stat.st_size,
            "total_lines": "unknown" if len(lines) >= max_lines else len(lines),
            "truncated": len(lines) >= max_lines,
            "content": "\n".join(lines),
        }
    except Exception as e:
        return {"error": f"Error reading file: {str(e)}"}


def find_config_by_name(app_name: str, search_roots: list[str] | None = None) -> list[dict]:
    """
    Найти конфигурационные файлы по имени приложения.

    Args:
        app_name: Имя приложения или часть имени.
        search_roots: Список корневых директорий для поиска. По умолчанию — Desktop и текущая директория.

    Returns:
        Список найденных конфигурационных файлов.
    """
    if search_roots is None:
        desktop = Path.home() / "Desktop"
        search_roots = [str(desktop), str(Path.cwd())]

    all_results = []
    for root in search_roots:
        root_path = Path(root)
        if root_path.exists():
            results = find_configs(str(root_path), file_name_filter=app_name)
            all_results.extend(results)

    # Убираем дубликаты
    seen = set()
    unique = []
    for item in all_results:
        if item["path"] not in seen:
            seen.add(item["path"])
            unique.append(item)

    return unique
