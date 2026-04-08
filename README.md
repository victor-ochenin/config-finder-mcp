# Config Finder MCP Server

MCP-сервер для быстрого поиска конфигурационных файлов приложений.

---

<!-- ==================== РУССКАЯ ВЕРСИЯ ==================== -->

## Оглавление

- [🇷🇺 Русская версия](#русская-версия)
  - [Зачем MCP-сервер вместо обычных инструментов агента](#зачем-mcp-сервер-вместо-обычных-инструментов-агента)
  - [Установка](#установка)
  - [Подключение к MCP-клиенту](#подключение-к-mcp-клиенту)
  - [Доступные инструменты](#доступные-инструменты)
  - [Поддерживаемые типы конфигов](#поддерживаемые-типы-конфигов)
- [🇬🇧 English version](#english-version)
  - [Why an MCP server instead of regular agent tools](#why-an-mcp-server-instead-of-regular-agent-tools)
  - [Installation](#installation-1)
  - [Connecting to an MCP client](#connecting-to-an-mcp-client)
  - [Available tools](#available-tools)
  - [Supported config types](#supported-config-types)

---

## Русская версия

### Зачем MCP-сервер вместо обычных инструментов агента

#### Проблема обычного поиска

Когда LLM-агент ищет конфигурационные файлы с помощью стандартных инструментов (`list_directory`, `read_file`, `glob`), он вынужден:

1. **Вызывать обход директорий для каждой папки** — рекурсивный поиск требует десятков или сотен отдельных вызовов инструментов
2. **Получать все файлы без фильтрации** — агент не может заранее отфильтровать только конфигурационные файлы
3. **Тратить ресурсы на каждый вызов** — каждый вызов инструмента — это отдельный цикл «запрос → модель → ответ → парсинг»

На проекте с глубокой структурой каталогов (`node_modules`, `vendor`, `__pycache__`, `.venv` и т. д.) это занимает значительное время и расходует токены контекста на обработку нерелевантных файлов.

#### Решение через MCP

`config-finder-mcp` устраняет эти проблемы:

| Параметр | MCP `find_configs` | Обычный поиск агента |
|---|---|---|
| Вызовов инструментов | **1** | **10–100+** |
| Циклов «запрос → ответ» | **1** | **10–100+** |
| Фильтрация | На стороне сервера (мгновенно) | На стороне агента (после получения всех файлов) |
| Передача данных | Только найденные конфиги | Все файлы + ручная фильтрация |
| Расход контекстных токенов | Минимальный | Значительный |

**Результат:** ускорение в **2–10x** на проектах с глубокой структурой каталогов.

#### Когда использовать

- **`find_configs`** — нужно быстро найти все конфиги в проекте или файлы по паттерну (например, все `docker`-файлы)
- **`find_config_by_name`** — точный путь неизвестен, но известно имя приложения или часть имени файла
- **`read_config`** — прочитать содержимое уже найденного конфигурационного файла
- **Стандартные инструменты агента** — изучение произвольных файлов, не являющихся конфигурационными

---

### Установка

#### Шаг 1: Клонируйте репозиторий

```bash
git clone https://github.com/<your-org>/config-finder-mcp.git
cd config-finder-mcp
```

#### Шаг 2: Установите зависимости

```bash
pip install -e .
```

### Подключение к MCP-клиенту

Добавьте сервер в конфигурацию вашего MCP-клиента.

#### Шаг 1: Откройте настройки MCP-клиента

#### Шаг 2: Добавьте секцию `mcpServers`
```json
{
  "mcpServers": {
    "config-finder": {
      "command": "python",
      "args": [
        "-m",
        "config_finder_mcp.server"
      ],
      "cwd": "C:\\Users\\user\\Desktop\\LocalMcp\\config-finder-mcp"
    }
  }
}
```

**Вариант с `uv`:**
```json
{
  "mcpServers": {
    "config-finder": {
      "command": "uv",
      "args": [
        "run",
        "-m",
        "config_finder_mcp.server"
      ],
      "cwd": "C:\\Users\\user\\Desktop\\LocalMcp\\config-finder-mcp"
    }
  }
}
```

> **Примечание:** замените путь в `cwd` на абсолютный путь к директории `config-finder-mcp` на вашей системе. На Linux/macOS используйте прямые слеши: `/home/user/projects/config-finder-mcp`.

#### Шаг 3: Перезапустите MCP-клиент

После добавления конфигурации перезапустите клиент. Сервер `config-finder` станет доступен как источник инструментов для LLM-агента.

---

### Доступные инструменты

| Инструмент | Описание |
|---|---|
| `find_configs` | Найти все конфигурационные файлы в указанной директории за **один вызов** |
| `read_config` | Прочитать содержимое конфигурационного файла с ограничением количества строк |
| `find_config_by_name` | Найти конфигурационные файлы по имени приложения в стандартных директориях |

#### Примеры использования

```
# Найти все конфиги в проекте
find_configs(root_path="C:\\Users\\user\\Desktop\\MyProject")

# Найти Docker-файлы
find_configs(root_path="C:\\Users\\user\\Desktop\\MyProject", file_name_filter="docker")

# Ограничить глубину поиска
find_configs(root_path="C:\\Users\\user\\Desktop\\MyProject", max_depth=3)

# Найти по имени приложения
find_config_by_name(app_name="myapp")

# Прочитать конкретный конфиг
read_config(file_path="C:\\Users\\user\\Desktop\\MyProject\\pyproject.toml", max_lines=100)
```

---

### Поддерживаемые типы конфигов

- **Python:** pyproject.toml, setup.py, requirements*.txt, Pipfile, poetry.lock
- **JS/TS:** package.json, tsconfig.json, webpack/vite/rollup/babel конфиги, eslint, prettier, jest, tailwind, next, nuxt
- **Java:** pom.xml, build.gradle, application.yml/properties
- **Go:** go.mod, go.sum, .golangci
- **Rust:** Cargo.toml, Cargo.lock
- **Ruby:** Gemfile, Rakefile, .rubocop.yml
- **PHP:** composer.json, phpunit.xml
- **DevOps:** Dockerfile, docker-compose, .github, .gitlab-ci.yml, Jenkinsfile
- **Инфраструктура:** *.tf, *.yaml, *.yml, nginx.conf
- **Общие:** .env, config.*, settings.*, *.ini, *.cfg, *.toml, *.conf

Сервер автоматически пропускает «тяжёлые» директории (`node_modules`, `.venv`, `__pycache__`, `dist`, `build`, `.git`, `target`, `vendor`) и пропускает скрытые директории, кроме `.github`, `.config`, `.vscode`, `.idea`.

---
---

## English version

### Why an MCP server instead of regular agent tools

#### The problem with regular search

When an LLM agent searches for configuration files using built-in tools (`list_directory`, `read_file`, `glob`), it must:

1. **Call directory traversal for every folder** — recursive search requires dozens or hundreds of separate tool calls
2. **Receive all files indiscriminately** — the agent can't pre-filter only configuration files
3. **Spend resources on each call** — every tool invocation is a separate "request → model → response → parsing" cycle

On a project with deep directory structures (`node_modules`, `vendor`, `__pycache__`, `.venv`, etc.) this takes significant time and burns context tokens processing irrelevant files.

#### The MCP solution

`config-finder-mcp` eliminates these issues:

| Parameter | MCP `find_configs` | Regular agent search |
|---|---|---|
| Tool calls | **1** | **10–100+** |
| Request → response cycles | **1** | **10–100+** |
| Filtering | Server-side (instant) | Agent-side (after receiving all files) |
| Data transfer | Only found configs | All files + manual filtering |
| Context token usage | Minimal | Significant |

**Result:** **2–10x** faster on projects with deep directory structures.

#### When to use

- **`find_configs`** — quickly find all configs in a project or files by pattern (e.g. all `docker` files)
- **`find_config_by_name`** — exact path is unknown, but the application name or partial filename is known
- **`read_config`** — read the contents of an already discovered config file
- **Built-in agent tools** — exploring arbitrary non-config files

---

### Installation

```bash
cd config-finder-mcp
pip install -e .
```

### Connecting to an MCP client

#### Step 1: Install dependencies

```bash
cd config-finder-mcp
pip install -e .
```

#### Step 2: Add the server to your MCP client configuration

Open your MCP client's settings file (e.g. `settings.json`) and add the `mcpServers` section:

**With `python`:**
```json
{
  "mcpServers": {
    "config-finder": {
      "command": "python",
      "args": [
        "-m",
        "config_finder_mcp.server"
      ],
      "cwd": "C:\\Users\\user\\Desktop\\LocalMcp\\config-finder-mcp"
    }
  }
}
```

**With `uv`:**
```json
{
  "mcpServers": {
    "config-finder": {
      "command": "uv",
      "args": [
        "run",
        "-m",
        "config_finder_mcp.server"
      ],
      "cwd": "C:\\Users\\user\\Desktop\\LocalMcp\\config-finder-mcp"
    }
  }
}
```

> **Note:** replace the `cwd` path with the absolute path to the `config-finder-mcp` directory on your system. On Linux/macOS use forward slashes: `/home/user/projects/config-finder-mcp`.

#### Step 3: Restart the MCP client

After adding the configuration, restart your MCP client. The `config-finder` server will become available as a tool source for the LLM agent.

---

### Available tools

| Tool | Description |
|---|---|
| `find_configs` | Find all configuration files in a directory in a **single call** |
| `read_config` | Read a configuration file with a configurable line limit |
| `find_config_by_name` | Find configuration files by application name in standard directories |

#### Usage examples

```
# Find all configs in a project
find_configs(root_path="/path/to/MyProject")

# Find Docker files
find_configs(root_path="/path/to/MyProject", file_name_filter="docker")

# Limit search depth
find_configs(root_path="/path/to/MyProject", max_depth=3)

# Search by app name
find_config_by_name(app_name="myapp")

# Read a specific config
read_config(file_path="/path/to/MyProject/pyproject.toml", max_lines=100)
```

---

### Supported config types

- **Python:** pyproject.toml, setup.py, requirements*.txt, Pipfile, poetry.lock
- **JS/TS:** package.json, tsconfig.json, webpack/vite/rollup/babel configs, eslint, prettier, jest, tailwind, next, nuxt
- **Java:** pom.xml, build.gradle, application.yml/properties
- **Go:** go.mod, go.sum, .golangci
- **Rust:** Cargo.toml, Cargo.lock
- **Ruby:** Gemfile, Rakefile, .rubocop.yml
- **PHP:** composer.json, phpunit.xml
- **DevOps:** Dockerfile, docker-compose, .github, .gitlab-ci.yml, Jenkinsfile
- **Infrastructure:** *.tf, *.yaml, *.yml, nginx.conf
- **General:** .env, config.*, settings.*, *.ini, *.cfg, *.toml, *.conf

The server automatically skips "heavy" directories (`node_modules`, `.venv`, `__pycache__`, `dist`, `build`, `.git`, `target`, `vendor`) and skips hidden directories except `.github`, `.config`, `.vscode`, `.idea`.
