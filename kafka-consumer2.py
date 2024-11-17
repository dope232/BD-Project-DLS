# service_monitor.py
from kafka import KafkaConsumer
from elasticsearch import Elasticsearch
import json
from datetime import datetime, timedelta
import time
import warnings
import threading
import os
from collections import defaultdict
warnings.filterwarnings("ignore")

class ServiceMonitor:
    def __init__(self, kafka_servers='localhost:9092', 
                 elastic_host='http://localhost:9200',
                 kafka_topic='fitness_logs'):
        
        
        self.services = {}
        self.heartbeat_threshold = 30  
        self.lock = threading.Lock()
        
        #  consumer 
        self.consumer = KafkaConsumer(
            kafka_topic,
            bootstrap_servers=kafka_servers,
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='service_monitor_group',  
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        
        #  client
        self.es = Elasticsearch(
            hosts=[elastic_host],
            verify_certs=False,
            ssl_show_warn=False,
            request_timeout=30
        )
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self.check_services, daemon=True)
        self.monitor_thread.start()

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def display_service_status(self):
        self.clear_screen()
        current_time = datetime.now()
        
        print("\n=== Service Status Monitor ===")
        print(f"Last Updated: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)

        if not self.services:
            print("\nNo services registered yet...")
            return

        for service_name, info in sorted(self.services.items()):
            last_heartbeat = info['last_heartbeat']
            time_since_heartbeat = (current_time - last_heartbeat).total_seconds()
            status = "UP" if time_since_heartbeat <= self.heartbeat_threshold else "DOWN"
            status_color = "\033[92m" if status == "UP" else "\033[91m"
            
            print(f"\nService: {service_name}")
            print(f"Status: {status_color}{status}\033[0m")
            print(f"Last Heartbeat: {time_since_heartbeat:.1f} seconds ago")
            print(f"Node ID: {info['node_id'][:8]}...")
            print("-" * 30)

    def check_services(self):
        while True:
            current_time = datetime.now()
            with self.lock:
                for service_name, info in list(self.services.items()):
                    time_since_heartbeat = (current_time - info['last_heartbeat']).total_seconds()
                    
                    if time_since_heartbeat > self.heartbeat_threshold:
                        if info.get('status') != 'DOWN':
                            print(f"\n⚠️  ALERT: Service {service_name} is DOWN!")
                            print(f"Last heartbeat was {time_since_heartbeat:.1f} seconds ago")
                            print(f"Node ID: {info['node_id']}")
                            print("-" * 50)
                            info['status'] = 'DOWN'
                            
                        
                            alert_doc = {
                                "timestamp": datetime.now().isoformat(),
                                "service_name": service_name,
                                "node_id": info['node_id'],
                                "message_type": "ALERT",
                                "alert_type": "SERVICE_DOWN",
                                "message": f"Service {service_name} is down",
                                "downtime_seconds": time_since_heartbeat
                            }
                            
                            try:
                                self.es.index(index=f"fitness-logs-{datetime.now():%Y.%m.%d}", 
                                            document=alert_doc)
                            except Exception as e:
                                print(f"Error storing alert: {e}")
                    else:
                        info['status'] = 'UP'

            self.display_service_status()
            time.sleep(5)

    def process_message(self, message):
        try:
            record = message.value
            if 'record' in record:
                record = record['record']

            # Only  heartbeat 
            if record.get('message_type') == 'HEARTBEAT':
                service_name = record.get('service_name')
                node_id = record.get('node_id')
                
                if service_name and node_id:
                    with self.lock:
                        self.services[service_name] = {
                            'node_id': node_id,
                            'last_heartbeat': datetime.now(),
                            'status': 'UP'
                        }

        except Exception as e:
            print(f"Error processing message: {e}")

    def start_monitoring(self):
        print("Service monitor started - monitoring service health...")
        try:
            for message in self.consumer:
                self.process_message(message)
        except KeyboardInterrupt:
            print("\nStopping service monitor...")
        finally:
            self.consumer.close()

def main():
    monitor = ServiceMonitor(
        kafka_servers='localhost:9092',
        elastic_host='http://localhost:9200',
        kafka_topic='fitness_logs'
    )
    monitor.start_monitoring()

if __name__ == "__main__":
    main()
