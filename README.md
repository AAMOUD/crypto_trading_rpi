# crypto_trading_rpi

A simple command-line interface for placing buy limit orders on Kraken exchange. This tool is designed for dollar-cost averaging (DCA) strategies and automated cryptocurrency purchases.

## Features

-  Place buy limit orders on Kraken exchange
-  Support for both fiat amount and crypto volume purchases
-  Configurable price buffer for limit orders
-  Secure API key management via environment variables
-  Dry-run mode for testing without placing actual orders
-  Interactive prompts for symbol and amount selection
-  Docker support for containerized deployment

## Prerequisites

- Python 3.11 or higher (3.13 recommended)
- Kraken API keys (public and private)
- pipenv (for dependency management)

## Installation

### Local Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd crypto_trading_rpi
```

2. Install dependencies using pipenv:
```bash
pipenv install
```

3. Create a `.env` file in the project root:
```bash
touch .env
```

4. Add your Kraken API credentials to the `.env` file:
```env
PUBLIC_KEY=your_kraken_public_key
PRIVATE_KEY=your_kraken_private_key
```

### Docker Setup

Build the Docker image:
```bash
docker build -t crypto_trading_rpi .
```

## Usage

### Basic Commands

Activate the virtual environment:
```bash
pipenv shell
```

#### Interactive Mode
Run without parameters to be prompted for symbol and amount:
```bash
python main.py buy
```

#### Specify Symbol and Fiat Amount
Spend a fixed fiat amount (e.g., 10 EUR):
```bash
python main.py buy --symbol XXBTZEUR --amount 10
```

#### Buy Specific Crypto Volume
Purchase a specific amount of cryptocurrency:
```bash
python main.py buy --symbol XXBTZEUR --amount 0.001 --units
```

#### Dry Run Mode
Test your order without actually placing it:
```bash
python main.py buy --symbol SOLEUR --amount 50 --dry-run
```

#### Custom Price Buffer
Adjust the limit price buffer (default is 0.2%):
```bash
python main.py buy --symbol XETHZEUR --amount 100 --buffer 0.005
```

### Command Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--symbol` | `-s` | Kraken trading pair (e.g., XXBTZEUR, SOLEUR) | Interactive prompt |
| `--amount` | `-a` | Amount to spend (fiat) or volume (with --units) | Interactive prompt |
| `--units` | - | Interpret amount as crypto units instead of fiat | `False` |
| `--buffer` | `-b` | Limit price buffer as decimal (0.002 = 0.2%) | `0.002` |
| `--dry-run` | - | Show what would be done without placing order | `False` |

### Supported Trading Pairs

Common trading pairs include:
- `XXBTZEUR` - Bitcoin/EUR
- `SOLEUR` - Solana/EUR
- `XETHZEUR` - Ethereum/EUR
- `XLTCZEUR` - Litecoin/EUR

For a complete list, check the [Kraken API documentation](https://docs.kraken.com/api/docs/rest-api/get-tradable-asset-pairs).

## Docker Usage

Run the CLI in a Docker container:

```bash
docker run --env-file .env crypto_trading_rpi python main.py buy --symbol XXBTZEUR --amount 10
```

## How It Works

1. **Fetch Current Price**: The CLI retrieves the current ask price for the specified trading pair
2. **Calculate Limit Price**: Applies a buffer to the ask price to create a competitive limit order
3. **Place Order**: Submits a buy limit order to Kraken with calculated volume and price
4. **Confirmation**: Returns order details upon successful placement

### Price Buffer Logic

The buffer ensures your limit order is competitive:
- Buy orders: `limit_price = ask_price × (1 + buffer)`
- Default buffer of 0.002 means your limit is 0.2% above the current ask price

## Project Structure

```
crypto_trading_rpi/
├── main.py              # CLI entry point with Typer commands
├── utils/
│   ├── __init__.py
│   └── kraken.py        # Kraken API client implementation
├── Pipfile              # Python dependencies
├── Pipfile.lock         # Locked dependency versions
├── Dockerfile           # Docker container configuration
├── .env                 # API credentials (not in repo)
└── README.md            # This file
```

## API Client

The `KrakenClient` class in `utils/kraken.py` provides:
- `get_ticker_ask_price(pair)` - Fetch current ask price
- `buy_limit_order(pair, flat_amount, buffer)` - Place buy limit order
- `place_order(...)` - Generic order placement
- `get_account_balance()` - Check account balances
- `get_asset_pairs()` - List available trading pairs

## Security Notes

**Important Security Considerations:**

- Store API keys securely and limit their permissions
- Consider using read-only API keys for balance checks
- Review Kraken's API key permissions and set appropriate restrictions

## Logging

Logs are output to stdout with the following format:
```
2025-10-10 12:34:56 | INFO | Symbol: XXBTZEUR
2025-10-10 12:34:56 | INFO | Current ask price: 55000.0
2025-10-10 12:34:56 | INFO | Order placed: {...}
```

## Troubleshooting

### "PUBLIC_KEY or PRIVATE_KEY not found"
- Ensure your `.env` file exists and contains valid credentials
- Check that `python-dotenv` is installed

### "Error fetching ticker ask price"
- Verify the trading pair symbol is correct (use exact Kraken format)
- Check your internet connection
- Ensure Kraken API is accessible

### "Error placing order"
- Verify you have sufficient balance
- Check API key has trading permissions
- Review Kraken's order requirements for the specific pair


## Disclaimer

This tool is for educational and personal use. Cryptocurrency trading carries risk. Always:
- Test with small amounts first
- Use the `--dry-run` flag to verify orders
- Understand the market and trading pair before placing orders
- Never invest more than you can afford to lose

## Resources

- [Kraken API Documentation](https://docs.kraken.com/api/)
- [Typer Documentation](https://typer.tiangolo.com/)
