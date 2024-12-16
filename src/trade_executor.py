import json
import os
import time
from math import floor
from web3 import Web3
from web3.exceptions import TimeExhausted, Web3RPCError

class TradeExecutor:
    def __init__(self, rpc_endpoint, private_key, router_address, logger, slippage_tolerance_percent):
        self.w3 = Web3(Web3.HTTPProvider(rpc_endpoint))
        self.account = self.w3.eth.account.from_key(private_key)
        self.address = self.account.address
        self.router_address = Web3.to_checksum_address(router_address)
        self.logger = logger
        self.slippage_tolerance_percent = slippage_tolerance_percent

        # Load router ABI
        router_abi_path = os.path.join(os.path.dirname(__file__), "router_abi.json")
        with open(router_abi_path, "r") as f:
            self.router_abi = json.load(f)
        self.router_contract = self.w3.eth.contract(address=self.router_address, abi=self.router_abi)

        # Load ERC20 ABI
        erc20_abi_path = os.path.join(os.path.dirname(__file__), "erc20_abi.json")
        with open(erc20_abi_path, "r") as f:
            self.erc20_abi = json.load(f)

    def to_wei(self, value, unit='ether'):
        return self.w3.to_wei(value, unit)

    def get_token_balance(self, token_address):
        token_contract = self.w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=self.erc20_abi)
        balance = token_contract.functions.balanceOf(self.address).call()
        return balance

    def get_eth_balance(self):
        return self.w3.eth.get_balance(self.address)

    def approve_token(self, token_address, spender_address, amount_in_wei, attempts=3):
        """Approve the Uniswap router to spend `amount_in_wei` of `token_address`.
           Retries the transaction with higher fees if stuck or "already known".
        """
        token_contract = self.w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=self.erc20_abi)

        # Start fee strategy: Note we must use camelCase keys here as required by Web3:
        base_fee = self.w3.eth.gas_price
        max_fee_per_gas = int(base_fee * 1.5)
        max_priority_fee_per_gas = self.to_wei(2, 'gwei')

        for attempt in range(attempts):
            nonce = self.w3.eth.get_transaction_count(self.address, 'pending')

            self.logger.info(
                f"Attempting approval (Attempt {attempt+1}/{attempts}) "
                f"with nonce {nonce}, maxFeePerGas={max_fee_per_gas}, maxPriorityFeePerGas={max_priority_fee_per_gas}"
            )

            tx = token_contract.functions.approve(
                Web3.to_checksum_address(spender_address),
                amount_in_wei
            ).build_transaction({
                'from': self.address,
                'gas': 100000,
                'maxFeePerGas': max_fee_per_gas,           # must remain camelCase
                'maxPriorityFeePerGas': max_priority_fee_per_gas,  # must remain camelCase
                'nonce': nonce,
                'chainId': 1
            })

            signed_tx = self.account.sign_transaction(tx)
            raw_transaction = signed_tx.raw_transaction  # Store in snake_case variable
            try:
                tx_hash = self.w3.eth.send_raw_transaction(raw_transaction)
                self.logger.info(f"Approval TX sent: {tx_hash.hex()}")

                # Wait for receipt
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300, poll_latency=5)
                if receipt.status == 1:
                    self.logger.info("Approval transaction confirmed.")
                    return True
                else:
                    self.logger.error("Approval failed on-chain.")
                    return False

            except TimeExhausted:
                self.logger.warning("Transaction timed out waiting for confirmation. Will retry with higher fees.")
                # Increase fees and try again
                max_fee_per_gas = int(max_fee_per_gas * 1.2)
                max_priority_fee_per_gas = int(max_priority_fee_per_gas * 1.5)

            except Web3RPCError as e:
                err_msg = e.args[0] if e.args else str(e)
                self.logger.error(f"RPC Error: {err_msg}")
                if 'already known' in err_msg:
                    # Means the transaction is already in the mempool
                    # Increase fees and try again with the same nonce to replace the tx
                    self.logger.warning("Transaction already known. Increasing fees and retrying with same nonce.")
                    max_fee_per_gas = int(max_fee_per_gas * 1.2)
                    max_priority_fee_per_gas = int(max_priority_fee_per_gas * 1.5)
                    time.sleep(10)  # wait before retry
                else:
                    # Some other RPC error not handled specifically
                    return False

            except Exception as ex:
                self.logger.error(f"Unexpected error: {str(ex)}")
                return False

        self.logger.error("Exceeded maximum attempts to approve token. Giving up.")
        return False

    def build_exact_input_single(self, token_in, token_out, fee, recipient, amount_in_wei, amount_out_min):
        deadline = int(time.time()) + 300
        params = (
            Web3.to_checksum_address(token_in),
            Web3.to_checksum_address(token_out),
            fee,
            Web3.to_checksum_address(recipient),
            deadline,
            amount_in_wei,
            amount_out_min,
            0
        )
        return self.router_contract.functions.exactInputSingle(params)

    def get_amount_out_min(self, amount_in_wei, token_in_price, token_in_decimals=18, token_out_decimals=6):
        # Convert amount_in_wei to units of token_in
        amount_in_units = amount_in_wei / (10 ** token_in_decimals)

        # Calculate expected amount out based on token_in_price (token_out per token_in)
        amount_out_expected = amount_in_units * token_in_price
        amount_out_wei = int(amount_out_expected * (10 ** token_out_decimals))

        slippage_factor = (100 - self.slippage_tolerance_percent) / 100.0
        amount_out_min = int(floor(amount_out_wei * slippage_factor))
        return amount_out_min

    def execute_buy(self, token_in, token_out, amount_in_wei, token_in_price):
        balance = self.get_token_balance(token_in)
        print(balance, "<-- this is balance")
        if balance < amount_in_wei:
            self.logger.error("Insufficient token_in balance to execute buy.")
            return None

        amount_out_min = self.get_amount_out_min(amount_in_wei, token_in_price)
        nonce = self.w3.eth.get_transaction_count(self.address, 'pending')
        gas_price = self.w3.eth.gas_price

        # Using a simpler fee strategy here; you could also use EIP-1559 parameters:
        tx = self.build_exact_input_single(token_in, token_out, 3000, self.address, amount_in_wei, amount_out_min)
        built_tx = tx.build_transaction({
            'from': self.address,
            'gas': 300000,
            'gasPrice': gas_price,
            'nonce': nonce,
            'chainId': 1,
            'value': 0
        })

        signed_tx = self.account.sign_transaction(built_tx)
        raw_transaction = signed_tx.raw_transaction
        self.logger.info("Sending buy transaction...")
        tx_hash = self.w3.eth.send_raw_transaction(raw_transaction)
        self.logger.info(f"Buy TX sent: {tx_hash.hex()}")
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            self.logger.info("Buy transaction confirmed.")
            return True
        else:
            self.logger.error("Buy transaction failed.")
            return False

    def execute_sell(self, token_in, token_out, amount_in_wei, token_in_price):
        # Similar to execute_buy but reversed tokens if needed.
        # For simplicity, call the same logic as execute_buy.
        return self.execute_buy(token_in, token_out, amount_in_wei, token_in_price)
