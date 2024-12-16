import json
import logging
import os

def load_config(path="config/config.json"):
    with open(path, "r") as f:
        return json.load(f)

def setup_logger(log_level="INFO"):
    logger = logging.getLogger("trading_bot")
    logger.setLevel(log_level)
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger

class RiskManager:
    def __init__(self, initial_balance, max_daily_loss_limit):
        self.initial_balance = initial_balance
        self.max_daily_loss_limit = max_daily_loss_limit
        self.current_balance = initial_balance

    def update_balance(self, new_balance):
        self.current_balance = new_balance

    def should_stop(self):
        loss = (self.initial_balance - self.current_balance) / self.initial_balance
        return loss >= self.max_daily_loss_limit
