# Publishing to PyPI

## Prerequisites

1. Install build tools:
```bash
pip install build twine
```

2. Create accounts:
   - PyPI: https://pypi.org/account/register/
   - TestPyPI (optional): https://test.pypi.org/account/register/

## Build the Package

From the project root directory:

```bash
# Clean previous builds
rm -rf dist/ build/ src/*.egg-info

# Build the package
python -m build
```

This creates:
- `dist/strayl_mcp_server-0.1.0.tar.gz` (source distribution)
- `dist/strayl_mcp_server-0.1.0-py3-none-any.whl` (wheel)

## Test on TestPyPI (Recommended)

First, upload to TestPyPI to verify everything works:

```bash
python -m twine upload --repository testpypi dist/*
```

You'll be prompted for your TestPyPI credentials.

Test installation:
```bash
pipx install --index-url https://test.pypi.org/simple/ strayl-mcp-server
```

## Publish to PyPI

Once tested, publish to the real PyPI:

```bash
python -m twine upload dist/*
```

You'll be prompted for your PyPI credentials.

## Verify Installation

Test the published package:

```bash
pipx install strayl-mcp-server
```

## Using API Tokens (Recommended)

Instead of username/password, use API tokens:

1. Go to PyPI Account Settings → API tokens
2. Create a new API token with appropriate scope
3. Create `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_TOKEN_HERE

[testpypi]
username = __token__
password = pypi-YOUR_TESTPYPI_TOKEN_HERE
```

Now you can upload without entering credentials:

```bash
python -m twine upload dist/*
```

## Automated Publishing with GitHub Actions

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build twine

      - name: Build package
        run: python -m build

      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

Add your PyPI token to GitHub Secrets as `PYPI_API_TOKEN`.

## Version Updates

When releasing a new version:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` (if you have one)
3. Commit changes
4. Create a git tag:
   ```bash
   git tag v0.1.1
   git push origin v0.1.1
   ```
5. Build and publish as described above

## Troubleshooting

### "File already exists" error

If you get this error, you're trying to upload a version that already exists on PyPI. You must increment the version number in `pyproject.toml`.

### Import errors

Make sure your package structure is correct:
```
strayl-mcp-server/
├── src/
│   └── strayl_mcp_server/
│       ├── __init__.py
│       ├── __main__.py
│       ├── server.py
│       └── utils.py
└── pyproject.toml
```

### Missing dependencies

Ensure all dependencies are listed in `pyproject.toml` under `dependencies`.
