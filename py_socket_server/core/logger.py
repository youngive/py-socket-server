import datetime
import logging

class NoExcInfoFilter(logging.Filter):
    def filter(self, record):
        record.exc_info = None
        return True
    
log_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')