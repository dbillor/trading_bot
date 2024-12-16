import time
from collections import deque

class MomentumAnalyzer:
    def __init__(self, window_seconds, threshold_percent):
        self.window_seconds = window_seconds
        self.threshold_percent = threshold_percent
        self.prices = deque()  # store (timestamp, price)

    def add_price(self, price):
        now = time.time()
        self.prices.append((now, price))
        # Remove old prices outside of the window
        while self.prices and (now - self.prices[0][0] > self.window_seconds):
            self.prices.popleft()

    def should_buy(self):
        # If price increased by threshold_percent or more in the last window
        if len(self.prices) < 2:
            return False
        oldest_price = self.prices[0][1]
        latest_price = self.prices[-1][1]
        increase = (latest_price - oldest_price) / oldest_price * 100.0
        return increase >= self.threshold_percent

    def should_sell(self):
        # If price decreased by half the threshold, we sell
        if len(self.prices) < 2:
            return False
        oldest_price = self.prices[0][1]
        latest_price = self.prices[-1][1]
        decrease = (oldest_price - latest_price) / oldest_price * 100.0
        return decrease >= (self.threshold_percent / 2)
