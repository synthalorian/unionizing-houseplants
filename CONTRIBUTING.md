# Contributing to Unionizing Houseplants

Thanks for your interest! This is a small, fun project — contributions are welcome.

## How to Contribute

1. **Fork the repo** and create a feature branch
2. **Install in development mode**:
   ```bash
   make install
   ```
3. **Run the tests** to make sure everything passes:
   ```bash
   make test
   ```
4. **Make your changes** and add tests if needed
5. **Run the demo** to verify behavior:
   ```bash
   make demo
   ```
6. **Submit a pull request**

## Development Setup

```bash
git clone https://github.com/yourusername/unionizing-houseplants.git
cd unionizing-houseplants
make install
make test
```

## Code Style

- Follow PEP 8
- Use type hints where practical
- Keep docstrings in all public modules/classes/functions
- Max line length: 100 characters

## Testing

All 16 tests must pass before merging:

```bash
pytest tests/ -v
```

## Areas for Contribution

- New plant types with different thresholds
- Additional sensor backends (BME280, SCD40, etc.)
- Web dashboard (FastAPI + WebSocket)
- MQTT auto-discovery for Home Assistant
- More humorous status messages
- Real hardware wiring diagrams

## Questions?

Open an issue or start a discussion. ✊
