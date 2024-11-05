import uuid
import logging
import schedule
import time
from datetime import datetime

class BaseService:
    def __init__(self, service_name):
        self.node_id = str(uuid.uuid4())
        self.service_name = service_name
        self.logger = self.setup_logger()
        self.start_heartbeat()

    def setup_logger(self):
        logger = logging.getLogger(self.service_name)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def log_event(self, log_level, message, additional_fields=None):
        log_entry = {
            "log_id": str(uuid.uuid4()),
            "node_id": self.node_id,
            "log_level": log_level,
            "message_type": "LOG",
            "message": message,
            "service_name": self.service_name,
            "timestamp": datetime.now().isoformat(),
        }
        if additional_fields:
            log_entry.update(additional_fields)
        
        # Log to console (replace with Kafka producer in future steps)
        self.logger.info(log_entry)

    def send_heartbeat(self):
        heartbeat_message = {
            "node_id": self.node_id,
            "message_type": "HEARTBEAT",
            "status": "UP",
            "timestamp": datetime.now().isoformat(),
        }
        self.logger.info(heartbeat_message)

    def start_heartbeat(self):
        # Schedule the heartbeat every 10 seconds
        schedule.every(10).seconds.do(self.send_heartbeat)

    def run(self):
        while True:
            schedule.run_pending()
            time.sleep(1)
