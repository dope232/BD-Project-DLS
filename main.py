# main.py
import uuid
import logging
import schedule
import time
from datetime import datetime
from fluent import sender
from fluent import event
import threading

class BaseService:
    def __init__(self, service_name):
        self.node_id = str(uuid.uuid4())
        self.service_name = service_name
        self.logger = self.setup_logger()
        self.fluent_sender = self.setup_fluent()
        self.start_heartbeat()
        # Start heartbeat in a separate thread
        self.start_heartbeat_thread()

    def setup_logger(self):
        logger = logging.getLogger(self.service_name)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def setup_fluent(self):
        return sender.FluentSender('fitness', host='localhost', port=24224)

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

        self.logger.info(log_entry)
        try:
            self.fluent_sender.emit(f'logs.{log_level.lower()}', log_entry)
        except Exception as e:
            self.logger.error(f"Error emitting log event: {e}")

    def send_heartbeat(self):
        heartbeat_message = {
            "node_id": self.node_id,
            "service_name": self.service_name,
            "message_type": "HEARTBEAT",
            "status": "UP",
            "timestamp": datetime.now().isoformat(),
        }
        self.logger.info(heartbeat_message)
        try:
            self.fluent_sender.emit('heartbeat', heartbeat_message)
        except Exception as e:
            self.logger.error(f"Error emitting heartbeat: {e}")

    def start_heartbeat(self):
        schedule.every(10).seconds.do(self.send_heartbeat)
        self.send_heartbeat()

    def heartbeat_thread(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

    def start_heartbeat_thread(self):
        thread = threading.Thread(target=self.heartbeat_thread, daemon=True)
        thread.start()

    def __del__(self):
        if hasattr(self, 'fluent_sender'):
            self.fluent_sender.close()