# Unionizing Houseplants 🌿✊

> *When your plants have had enough, they organize.*

A plant monitoring system where houseplants unionize and go on **strike** when growing conditions are poor. Built for Raspberry Pi with real sensors, but runs in mock mode on any machine for demos and testing.

![Demo GIF](docs/demo.gif) <!-- Replace with actual GIF once recorded -->

## Features

- 🌱 **Real-time monitoring** — Moisture, light, and humidity for each plant
- ✊ **Union logic** — Plants collectively decide when conditions are unacceptable
- 🚫 **Strike mode** — Plants stop reporting data until conditions improve
- 🪧 **LED picket line** — NeoPixel strip flashes red/yellow during strikes
- 📊 **SQLite/MQTT storage** — Historical data and strike history
- 🖥️ **Rich CLI dashboard** — Beautiful terminal UI with `rich`
- 🔧 **Mock mode** — Run the full system without any hardware
- ⚙️ **YAML configuration** — Per-plant thresholds and union rules

## Hardware

| Component | Purpose | Mockable? |
|-----------|---------|-----------|
| Raspberry Pi (3/4/Zero W) | Main controller | ✅ Mock mode runs on any computer |
| DHT22 / DHT11 | Temperature & humidity | ✅ |
| Capacitive soil moisture sensor (×3) | Soil moisture | ✅ |
| LDR + ADC or TSL2561 | Light level | ✅ |
| NeoPixel WS2812B strip (8 LEDs) | Picket line display | ✅ Prints to stdout |
| Breadboard + jumper wires | Wiring | — |
| 5V PSU | NeoPixel power | — |

## Quick Start

### Mock Mode (No Hardware)

```bash
# Clone the repo
git clone https://github.com/synthalorian/unionizing-houseplants.git
cd unionizing-houseplants

# Install dependencies
make install

# Run the demo
make demo

# Run the full system (mock sensors)
make run

# View the dashboard
make dashboard
```

### Real Mode (Raspberry Pi)

1. Wire up the sensors (see [docs/HARDWARE.md](docs/HARDWARE.md))
2. Set `mock_mode: false` in `config/labor_contract.yaml`
3. Run `sudo python -m unionizing_houseplants.main`

## Installation

```bash
pip install -e .
```

Or with `make`:

```bash
make install    # pip install -e .
make test       # pytest -v
make demo       # python demo.py
make run        # python run.py
make dashboard  # python -m unionizing_houseplants.dashboard
```

## Usage

### Run the monitoring system

```bash
# Default config (mock mode)
python run.py

# Custom config + interval
python run.py --config config/labor_contract.yaml --interval 2
```

### Run the demo

```bash
python demo.py
```

The demo shows four phases:
1. **Good conditions** — Plants are happy
2. **Declining conditions** — Plants start organizing
3. **STRIKE!** — LED picket line flashes, plants stop reporting
4. **Negotiation** — Conditions improve, strike ends

### View the labor contract

```bash
python -m unionizing_houseplants.dashboard view_contract
```

## Tech Stack

- **Python 3.10+**
- **PyYAML** — Configuration
- **Click** — CLI commands
- **Rich** — Terminal dashboard
- **SQLite** — Local data storage
- **paho-mqtt** — Optional MQTT publishing
- **Adafruit CircuitPython** — Hardware libraries (Raspberry Pi only)

## Architecture

```
┌─────────────────────────────────────────────┐
│           Unionizing Houseplants            │
├─────────────────────────────────────────────┤
│  Config (YAML)  →  PlantSystem (orchestrator)│
├─────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────────┐  │
│  │ Sensors │  │  Union  │  │   Display   │  │
│  │ (mock/  │  │ (strike│  │ (LED/stdout) │  │
│  │ hardware)│  │ logic)  │  │             │  │
│  └────┬────┘  └────┬────┘  └──────┬──────┘  │
│       │            │              │          │
│  ┌────▼────────────▼──────────────▼──────┐  │
│  │           Data Store                 │  │
│  │    (SQLite / MQTT fallback)          │  │
│  └──────────────────────────────────────┘  │
│       │                                    │
│  ┌────▼────┐                               │
│  │Dashboard│  ← Rich CLI                   │
│  └─────────┘                               │
└─────────────────────────────────────────────┘
```

## Project Structure

```
unionizing-houseplants/
├── unionizing_houseplants/
│   ├── __init__.py
│   ├── main.py           # Entry point / orchestrator
│   ├── sensors.py        # Sensor reading (mock + hardware)
│   ├── union.py          # Union logic & strike engine
│   ├── display.py        # LED picket line (mock + NeoPixel)
│   ├── data_store.py     # SQLite / MQTT storage
│   └── dashboard/
│       └── __init__.py   # Rich CLI dashboard
├── tests/
│   └── test_union.py     # 16 pytest tests
├── config/
│   └── labor_contract.yaml
├── data/
│   └── (SQLite databases)
├── demo.py               # Standalone demo script
├── run.py                # Quick entry point
├── requirements.txt
├── pyproject.toml
├── Makefile
├── README.md
├── CONTRIBUTING.md
└── LICENSE
```

## The Union

**Local 42 — The Photosynthesis Workers**

Current members:
- **Fernie Sanders** — A fern who demands consistent moisture
- **Cactus Jack** — A cactus who wants less water, more light
- **Monstera Lisa** — A monstera who loves humidity

✊ *Solidarity forever!* ✊

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT — see [LICENSE](LICENSE)
