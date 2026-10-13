# robvis-cli

Generate reproducible SVG risk-of-bias figures for systematic reviews from CSV assessments. This repository contains a **Python command-line visualizer** and a **browser interface using Pyodide**; it also retains an optional, independent FastAPI audit service.

## Features

- Traffic-light study-by-domain SVG matrix, with optional symbols and tooltips.
- Unweighted or explicitly weighted domain percentage summary SVGs.
- RoB 2 (five domains), original ROBINS-I (seven domains), QUADAS-2 (four risk-of-bias domains), and custom layouts.
- CSV validation with actionable errors; no imputation of malformed weights or invalid overall judgments.
- Browser CSV upload/edit, immediate SVG preview, and SVG download. Browser calculations use the same Python modules as the CLI.
- MIT-licensed, dependency-free Python visualization core. API functionality has additional dependencies installed through the default package installation.

**Scientific scope:** This is a visualization program, *not* an automated risk-of-bias assessment instrument. Overall judgments inferred from domains are simplified defaults. RoB 2 may require a high overall judgment when multiple domains have some concerns; this requires reviewer judgment. For QUADAS-2 no overall judgment is displayed unless an explicit Overall column is supplied. ROBINS-I category names (Low, Moderate, Serious, Critical, No information) follow the original seven-domain instrument; the revised six-domain ROBINS-I instrument is not implemented as a separate preset.

## Local installation

Requires Python 3.9 or later.

```bash
git clone https://github.com/abusuraihsakhri/robvis-cli.git
cd robvis-cli
python -m pip install -e ".[dev]"
pytest -q
```

## CLI quickstart

```bash
robvis validate -i sample_rob2.csv
robvis traffic-light -i sample_rob2.csv -o traffic.svg -t "RoB 2 assessment"
robvis summary -i sample_rob2.csv -o summary.svg --weighted
robvis sample-csv --tool robins-i -o robins-example.csv
```

Useful options: `--tool ROB2|ROBINS_I|QUADAS_2|CUSTOM` overrides tool detection; `--no-symbols` and `--no-tooltips` customize traffic-light plots; `--weighted` uses the positive finite numeric Weight values in the dataset. The default tool detection is based on the number of domain columns; **explicitly select CUSTOM** for similarly sized custom assessments.

CSV columns: `Study,D1,D2,...` with optional `Overall,Weight,Subgroup`. Domain judgments are specific to the assessment tool. For ROBINS-I use `Low`, `Moderate`, `Serious`, `Critical`, or `No information`; for RoB 2 use `Low`, `Some concerns`, or `High`. See `sample_rob2.csv` and `sample_robins_i.csv`.

## Browser usage and privacy

The browser source is `web/index.html`. Deploy with `.github/workflows/pages.yml` after enabling GitHub Pages with **GitHub Actions** as the build/deployment source. Open the published application, load or edit CSV, choose the instrument, then generate and download SVG.

The web interface fetches the Pyodide runtime from the jsDelivr CDN on first generation; it does **not** send CSV data to a server. External network access is required to initialize Python. The visualization CLI also works offline after installation. Do not put patient identifiers or other sensitive information in demonstration CSVs.

## Optional audit API

An independent sample audit service remains available at `python cli.py serve` or via Docker. It is not required for SVG generation and is **not a validated clinical decision support system**. Set `AUDIT_SECRET_KEY` to a cryptographically random private value of at least 16 characters before starting the service. The audit-log endpoint additionally requires `AUDIT_ADMIN_TOKEN`, supplied in the `X-Admin-Token` HTTP header. Copy `.env.example` for the list of environment variables; never commit filled secrets.

```bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export AUDIT_ADMIN_TOKEN="$(python -c 'import secrets; print(secrets.token_hex(32))')"
docker compose up --build
```

The included identifier guard uses pattern matching and must not be regarded as comprehensive PHI detection or HIPAA compliance.

## Testing and technology

`pytest -q` runs unit and regression tests. GitHub Actions also checks Python compilation, the CLI, SVG XML validity, and browser script syntax. Technology: Python standard-library CSV/SVG generator, Pydantic/FastAPI for the optional service, and HTML/CSS/JavaScript with Pyodide for the browser interface.

Modern desktop and mobile browsers supporting WebAssembly and the File API are expected to work; platform-specific browser tests and end-to-end Pages deployment must be verified separately.

## License

MIT; see [LICENSE](LICENSE).
