#!/usr/bin/env python3
import logging
import os
import sys
from typing import Optional

import typer

from dotenv import load_dotenv

from utils.kraken import KrakenClient

load_dotenv()

app = typer.Typer(help="Simple Kraken DCA CLI for placing buy limit orders on Kraken")

# --- Logs Configuration: send to stdout ---
logger = logging.getLogger("crypto_trading_rpi")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)  # logs to stdout
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
handler.setFormatter(formatter)
logger.handlers = [handler]


def _get_client():
    public_key = os.getenv("PUBLIC_KEY", "")
    private_key = os.getenv("PRIVATE_KEY", "")
    if not public_key or not private_key:
        logger.warning(
            "PUBLIC_KEY or PRIVATE_KEY not found in environment. Make sure .env is loaded."
        )
    return KrakenClient(public_key, private_key)


@app.command()
def buy(
    symbol: Optional[str] = typer.Option(
        None,
        "--symbol",
        "-s",
        help="Kraken trading pair symbol (e.g. XXBTZEUR, SOLEUR). If omitted you'll be prompted.",
    ),
    amount: Optional[float] = typer.Option(
        None,
        "--amount",
        "-a",
        help="Amount to spend in fiat (flat amount) OR number of units when used with --units flag.",
    ),
    units: bool = typer.Option(
        False,
        "--units",
        help="Interpret --amount as asset units (volume) instead of fiat flat amount.",
    ),
    buffer: float = typer.Option(
        0.002,
        "--buffer",
        "-b",
        help="Limit price buffer as a decimal fraction (default 0.002 = 0.2%).",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="If set, don't place the order; just show what would be done.",
    ),
):
    """
    Place a buy limit order on Kraken.

    Examples:
      main.py buy --symbol XXBTZEUR --amount 10        # spend 10 EUR (flat_amount)
      main.py buy --symbol XXBTZEUR --amount 0.001 --units  # buy 0.001 BTC
    """
    # Default known symbols to prompt if user didn't pass one
    known_symbols = ["XXBTZEUR", "SOLEUR", "XETHZEUR", "XLTCZEUR"]

    if not symbol:
        # prompt the user to choose a symbol
        choices_text = ", ".join(known_symbols)
        symbol = typer.prompt(
            f"Symbol (example: {choices_text}). Enter the exact Kraken pair symbol"
        )

    if amount is None:
        amount = typer.prompt(
            "Amount to use (fiat amount or units depending on --units). Enter a number",
            type=float,
        )

    client = _get_client()

    try:
        ask_price = client.get_ticker_ask_price(symbol)
    except Exception as e:
        logger.error(f"Failed to fetch ask price for {symbol}: {e}", exc_info=False)
        raise typer.Exit(code=1)

    # Calculate limit price using buffer: place limit slightly above ask for buy
    limit_price = ask_price * (1 + buffer)

    logger.info(f"Symbol: {symbol}")
    logger.info(f"Current ask price: {ask_price}")
    logger.info(f"Using buffer: {buffer} -> limit price: {limit_price}")

    if dry_run:
        logger.info(
            f"[DRY RUN] Would place buy limit order for {symbol} at price {limit_price} with "
            f"{'units' if units else 'flat amount'} = {amount}"
        )
        raise typer.Exit()

    # Prepare kwargs for the KrakenClient buy method.
    # Original code used flat_amount=..., so prefer that. If user passed --units we try volume=...
    order_kwargs = {"buffer": buffer}
    if units:
        # try volume param (common name) — if KrakenClient doesn't accept it, we'll catch error and suggest flat_amount
        order_kwargs["volume"] = amount
    else:
        order_kwargs["flat_amount"] = amount

    try:
        order = client.buy_limit_order(symbol, **order_kwargs)
        logger.info(f"Order placed: {order}")
    except TypeError as te:
        # likely wrong kwarg for volume/flat_amount — give a helpful message
        logger.error(
            f"Failed to call buy_limit_order with arguments {order_kwargs}: {te}"
        )
        logger.error(
            "If your KrakenClient uses a different parameter name, try the CLI with/without --units "
            "or update KrakenClient.buy_limit_order to accept 'flat_amount' or 'volume'."
        )
        raise typer.Exit(code=2)
    except Exception as e:
        logger.error(f"Error placing order: {e}", exc_info=False)
        raise typer.Exit(code=3)


if __name__ == "__main__":
    app()
