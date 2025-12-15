# Scripts

This directory contains utility scripts for managing and running the trading algorithm.

## Available Scripts

### Trading Operations

- **run_trader.sh** - Main script to run the trading algorithm
  ```bash
  ./scripts/run_trader.sh
  ```

### Maintenance

- **rotate_logs.sh** - Rotates log files to prevent them from growing too large
  ```bash
  ./scripts/rotate_logs.sh
  ```

- **setup_monitoring.sh** - Sets up monitoring for the trading system
  ```bash
  ./scripts/setup_monitoring.sh
  ```

## Usage

Make scripts executable:
```bash
chmod +x scripts/*.sh
```

Run from project root:
```bash
./scripts/run_trader.sh
```

## Notes

- All scripts should be run from the project root directory
- Ensure environment variables are set in `.env` before running
- Log files will be saved to the `logs/` directory
