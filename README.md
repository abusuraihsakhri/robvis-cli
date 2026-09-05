# robvis-cli

> **Domain:** Clinical Decision Support & Biomedical Computing
> **Standards:** Cochrane Risk of Bias 2 (RoB 2), ROBINS-I, QUADAS-2

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**robvis-cli** is a publication-ready Cochrane Risk of Bias visualization tool that generates SVG figures for systematic reviews. It supports:

- **RoB 2** (Risk of Bias 2) for randomized trials
- **ROBINS-I** (Risk Of Bias In Non-randomized Studies - of Interventions)
- **QUADAS-2** (Quality Assessment of Diagnostic Accuracy Studies)
- **Custom** risk of bias assessment tools

The tool generates two types of publication-ready SVG figures:
1. **Traffic Light Matrices** - Per-study domain judgments with color-coded circles
2. **Summary Bar Charts** - Domain risk proportions (weighted or unweighted)

Additionally, robvis-cli includes an enterprise-grade analytical suite with:
- Zero-PHI outbound guard for HIPAA compliance
- HMAC-SHA256 tamper-evident audit trail
- FastAPI REST API server
- Multi-worker evaluation system

---

## ⚙️ Key Capabilities

- **Deterministic Calculation Engine**: Strict compliance with standard reference formulations and thresholds
- **Risk & Urgency Classification**: Multi-tier categorization with automated clinical/operational action recommendations
- **Validation & Guardrails**: Rigorous input bounds checking and anomaly detection
- **Zero-Dependency SVG Generation**: Pure Python SVG rendering (no external dependencies for core visualization)

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/robvis-cli.git
cd robvis-cli

# Install with dependencies
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

---

## 🛡️ Security Configuration

The audit trail requires a secret key to be set via environment variable:

```bash
# Generate a secure key
python -c "import secrets; print(secrets.token_hex(32))"

# Set the environment variable
export AUDIT_SECRET_KEY="your-secure-key-here"
```

**Important:** Never commit your audit secret key to version control. Use environment variables or a secure secrets manager.

---

## 💻 CLI Quickstart & Usage

### SVG Visualization Commands

#### 1. Generate Traffic Light Matrix
```bash
python -m robvis_cli.cli traffic-light -i sample_rob2.csv -o traffic_light.svg
```

#### 2. Generate Summary Bar Chart
```bash
python -m robvis_cli.cli summary -i sample_rob2.csv -o summary_bar.svg --weighted
```

#### 3. Validate a Risk of Bias CSV
```bash
python -m robvis_cli.cli validate -i sample_rob2.csv
```

#### 4. Generate Sample CSV
```bash
# RoB 2 sample
python -m robvis_cli.cli sample-csv --tool rob2 -o my_rob2.csv

# ROBINS-I sample
python -m robvis_cli.cli sample-csv --tool robins-i -o my_robins_i.csv
```

### Analytical Suite Commands

#### 5. Run Single Task Evaluation
```bash
python cli.py audit --task-id TASK-001 --target KEY-01 --primary 28.5 --secondary 14.2
```

#### 6. Batch Process CSV Records
```bash
python cli.py batch -i input.csv -o results.csv
```

#### 7. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

#### 8. Launch FastAPI REST Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### Parameter Reference

**Visualization Commands:**
| Parameter | Description | Required |
|:----------|:------------|:---------|
| `-i, --input` | Path to Risk of Bias CSV file | Yes |
| `-o, --output` | Output file path (.svg) | No (default: `traffic_light.svg` or `summary_bar.svg`) |
| `-t, --title` | Chart title | No |
| `--tool` | Force tool type (ROB2, ROBINS_I, QUADAS_2, CUSTOM) | No |
| `--weighted` | Weight bars by study sample size (summary only) | No |
| `--no-symbols` | Hide +/-/? symbols inside circles (traffic-light only) | No |
| `--no-tooltips` | Omit hover tooltips (traffic-light only) | No |

**Analytical Commands:**
| Parameter | Description | Required |
|:----------|:------------|:---------|
| `--task-id` | Unique task/case identifier | No (default: `TASK-2026-001`) |
| `--target` | Entity or target identifier | No (default: `KEY-TARGET-01`) |
| `--primary` | Primary measurement or score | No (default: `28.5`) |
| `--secondary` | Secondary measurement or score | No (default: `14.2`) |
| `--critical` | Flag as critical priority | No |
| `--status` | Status descriptor | No (default: `DISCORDANT`) |

### Input Data Schema

**Risk of Bias CSV Format:**

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Study` | Study identifier (Author Year) | Required |
| `D1`, `D2`, ... | Domain judgments (Low/Some concerns/High/Critical) | Required |
| `Overall` | Overall judgment (auto-calculated if missing) | Optional |
| `Weight` | Study sample size or weight for weighted analysis | Optional |
| `Subgroup` | Subgroup classification | Optional |

**Judgment Values:**
- **Low risk**: `Low`, `L`, `+`, `green`
- **Some concerns**: `Some concerns`, `SC`, `Moderate`, `?`, `yellow`
- **High risk**: `High`, `H`, `-`, `red`, `serious`
- **Critical risk**: `Critical`, `Crit`, `X`, `purple`
- **No information**: `No info`, `NI`, `N/A`, `missing`

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`)
* **Input Validation:** Path traversal protection and file validation for all CLI inputs

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t robvis-cli .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY="your-secret-key" robvis-cli
```

---

## 📁 Project Structure

```
robvis-cli/
├── robvis_cli/           # Core visualization package (zero dependencies)
│   ├── cli.py            # CLI entry point for visualization
│   ├── models.py         # Data models and enums
│   ├── parser.py         # CSV parser with auto-detection
│   └── renderer_svg.py   # SVG rendering engine
├── agents/               # Enterprise analytical suite
│   ├── api.py            # FastAPI REST server
│   ├── base.py           # Security, PHI guard, audit trail
│   ├── supervisor.py     # Multi-worker orchestrator
│   ├── workers.py        # Specialized evaluation workers
│   └── models.py         # Pydantic data schemas
├── tests/                # Test suite
├── cli.py                # Analytical CLI entry point
├── robvis.py             # Visualization CLI entry point
├── simulator.py          # High-throughput stress testing
├── enrichment.py         # Feature enrichment suite
├── sample_rob2.csv       # Sample RoB 2 dataset
├── sample_robins_i.csv   # Sample ROBINS-I dataset
└── Dockerfile            # Container configuration
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
