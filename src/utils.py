import json
import logging
import os

def load_config(config_path="config/config.json"):
    with open(config_path, "r") as f:
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
