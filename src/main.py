import time
import sys
from utils import load_config, setup_logger, RiskManager
from dex_api import get_current_price
from momentum_logic import MomentumAnalyzer
from trade_executor import TradeExecutor
from web3 import Web3

def main():
    config = load_config()
    logger = setup_logger(config.get("log_level", "INFO"))

    logger.info("Starting complete prototype with real trading capabilities...")

    # Initialize classes
    momentum = MomentumAnalyzer(config["momentum_window_seconds"], config["momentum_threshold_percent"])
    risk_manager = RiskManager(initial_balance=1.0, max_daily_loss_limit=config["max_daily_loss_limit"])
    executor = TradeExecutor(
        config["rpc_endpoint"], 
        config["private_key"], 
        config["uniswap_router"], 
        logger,
        config["slippage_tolerance_percent"]
    )

    uniswap_url = config["uniswap_subgraph_url"]
    pool_address = config["pool_address"]
    token_in = Web3.to_checksum_address(config["trade_token_in"])
    token_out = Web3.to_checksum_address(config["trade_token_out"])
    amount_in_wei = int(config["base_position_size_wei"])
    poll_interval = config["poll_interval_seconds"]

    # Approve tokens once before trading
    logger.info("Approving token_in for the Uniswap router...")
    if not executor.approve_token(token_in, config["uniswap_router"], int(1e23)):
        logger.error("Token approval failed, cannot proceed with trading.")
        sys.exit(1)
    else:
        logger.info("Token approval successful. Ready to trade.")

    # Trading loop
    while True:
        price = get_current_price(uniswap_url, pool_address)
        if price is not None:
            # Add price to momentum analyzer
            momentum.add_price(price)
            logger.info(f"Current price: {price}")

            if risk_manager.should_stop():
                logger.warning("Daily loss limit reached. Stopping trades.")
                break

            if momentum.should_buy():
                logger.info("Momentum suggests a BUY.")
                # Execute a buy (e.g., WETH -> USDC)
                success = executor.execute_buy(token_in, token_out, amount_in_wei, price)
                if success:
                    # Simulate portfolio increase or pull real balances to update risk_manager
                    # For now, just simulate a small profit
                    risk_manager.update_balance(risk_manager.current_balance * 1.01)
                else:
                    logger.error("Buy failed. Check logs and Etherscan for details.")

            elif momentum.should_sell():
                logger.info("Momentum suggests a SELL.")
                # Execute a sell (e.g., USDC -> WETH), reverse the direction and token_in/out
                # Note: If you actually hold USDC now, swap token_out/token_in here
                # For demonstration: token_out -> token_in (USDC -> WETH)
                success = executor.execute_sell(token_out, token_in, amount_in_wei, 1.0/price if price != 0 else 0)
                if success:
                    # Simulate a small loss after selling
                    risk_manager.update_balance(risk_manager.current_balance * 0.99)
                else:
                    logger.error("Sell failed. Check logs and Etherscan for details.")

            else:
                logger.info("No trade signal at the moment.")

        else:
            logger.error("Failed to fetch price data.")

        time.sleep(poll_interval)

if __name__ == "__main__":
    main()
