from utils import load_config, setup_logger
from dex_api import get_uniswap_pool_data

def main():
    config = load_config()
    logger = setup_logger(config.get("log_level", "INFO"))
    logger.info("Starting Day 1 test...")

    uniswap_url = config["uniswap_subgraph_url"]
    # WETH/USDC pool address (just for testing data pull)
    pool_address = "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8"

    data = get_uniswap_pool_data(uniswap_url, pool_address)
    if data:
        pool = data.get("data", {}).get("pool", {})
        logger.info(f"Pool Data: {pool}")
    else:
        logger.error("Failed to fetch pool data")

if __name__ == "__main__":
    main()
