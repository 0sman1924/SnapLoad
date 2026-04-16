# Contributing to SnapLoad (yt-dlp GUI)

Thank you for your interest in contributing! Here's how to get started.

## 🛠 Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/0sman1924/SnapLoad.git
   cd yt-dlp-gui
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # macOS/Linux
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -e .              # Install in editable mode
   ```

4. **Run the app:**
   ```bash
   python -m ytdlp_gui.main
   ```

## 📐 Code Standards

- **PEP 8** compliant code (enforced via `ruff`)
- **Type hints** on all function signatures
- **Docstrings** on all public modules, classes, and functions
- **Meaningful variable names** — no single-letter variables outside loops

## 🧪 Running Tests

```bash
python -m pytest tests/ -v
```

## 📁 Project Structure

- `src/ytdlp_gui/core/` — Business logic (no UI imports)
- `src/ytdlp_gui/ui/` — CustomTkinter views and widgets
- `src/ytdlp_gui/utils/` — Shared helper utilities
- `tests/` — Unit and integration tests

## 🔀 Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes with clear, descriptive commits
4. Run tests and linting before submitting
5. Open a PR with a clear description of what you changed and why

## 🐛 Reporting Issues

Use the GitHub Issue templates to report bugs or suggest features.
Include:
- Python version
- OS version
- Steps to reproduce
- Error logs (from the Log panel or terminal)

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.
