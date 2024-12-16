import requests

def get_uniswap_pool_data(uniswap_url, pool_address):
    query = """
    {
      pool(id: "%s") {
        token0Price
        token1Price
      }
    }
    """ % pool_address.lower()

    response = requests.post(uniswap_url, json={"query": query})
    if response.status_code == 200:
        return response.json()
    return None

def get_current_price(uniswap_url, pool_address):
    # For WETH/USDC pool, token0 is often WETH and token1 is USDC. token0Price = price of token0 in token1 terms.
    data = get_uniswap_pool_data(uniswap_url, pool_address)
    if data:
        pool = data.get("data", {}).get("pool", {})
        if pool and "token0Price" in pool:
            return float(pool["token0Price"])
    return None
