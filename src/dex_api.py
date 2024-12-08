import requests

def get_uniswap_pool_data(uniswap_url, pool_address):
    # Example GraphQL query to fetch pool data (liquidity, volume, etc.)
    query = """
    {
      pool(id: "%s") {
        id
        token0Price
        token1Price
        volumeUSD
        liquidity
      }
    }
    """ % pool_address.lower()

    response = requests.post(uniswap_url, json={"query": query})
    if response.status_code == 200:
        return response.json()
    else:
        return None
