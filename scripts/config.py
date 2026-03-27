"""Shared configuration for profile README generators."""

import os

USERNAME = "scorpio-99"

# All paths relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_DIR = os.path.join(PROJECT_ROOT, "assets", "logos")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "assets", "generated")
OUTPUT_CONTRIBUTION_GRAPH = os.path.join(OUTPUT_DIR, "github-contribution-graph.svg")
OUTPUT_TECH_STACK = os.path.join(OUTPUT_DIR, "github-tech-stack.svg")

# GitHub dark theme
THEME = {
    "bg": "#0d1117",
    "text": "#e6edf3",
    "text_secondary": "#848d97",
    "border": "#21262d",
    "font": '-apple-system, "Segoe UI", Helvetica, Arial, sans-serif',
    "contribution_levels": {
        0: "#161b22",
        1: "#0e4429",
        2: "#006d32",
        3: "#26a641",
        4: "#39d353",
    },
}

# Tech stack: (display_name, folder, [(logo_file, label), ...])
TECH_STACK = [
    ("Languages", "languages", [
        ("python.svg", "Python"),
        ("javascript.svg", "JavaScript"),
        ("typescript.svg", "TypeScript"),
        ("swift.svg", "Swift"),
        ("csharp.svg", "C#"),
        ("bash.svg", "Bash"),
    ]),
    ("Frontend", "frontend", [
        ("react.svg", "React"),
        ("nextjs.svg", "Next.js"),
        ("redux.svg", "Redux"),
        ("tailwindcss.svg", "TailwindCSS"),
        ("html5.svg", "HTML5"),
        ("css3.svg", "CSS3"),
        ("sass.svg", "Sass"),
        ("less.svg", "Less"),
    ]),
    ("Mobile", "mobile", [
        ("frontend/react.svg", "React Native"),
        ("xcode.svg", "Xcode"),
        ("expo.svg", "Expo"),
    ]),
    ("Backend & Databases", "backend", [
        ("nodejs.svg", "Node.js"),
        ("fastapi.svg", "FastAPI"),
        ("payloadcms.svg", "Payload"),
        ("directus.svg", "Directus"),
        ("postgresql.svg", "Postgres"),
        ("mysql.svg", "MySQL"),
        ("mongodb.svg", "MongoDB"),
        ("sqlite.svg", "SQLite"),
        ("solr.svg", "Solr"),
    ]),
    ("Infrastructure & DevOps", "infrastructure", [
        ("linux.svg", "Linux"),
        ("nginx.svg", "Nginx"),
        ("docker.svg", "Docker"),
        ("tools/gitlab.svg", "GitLab CI/CD"),
        ("tools/github.svg", "GitHub Actions"),
    ]),
    ("Tools", "tools", [
        ("git.svg", "Git"),
        ("github.svg", "GitHub"),
        ("gitlab.svg", "GitLab"),
        ("vscode.svg", "VS Code"),
        ("pycharm.svg", "PyCharm"),
        ("npm.svg", "npm"),
        ("pnpm.svg", "pnpm"),
        ("postman.svg", "Postman"),
        ("jest.svg", "Jest"),
        ("playwright.svg", "Playwright"),
        ("claude.svg", "Claude"),
    ]),
]
