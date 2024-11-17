# log_consumer.py
from kafka import KafkaConsumer
from elasticsearch import Elasticsearch
import json
from datetime import datetime
import time
import warnings
import os
warnings.filterwarnings("ignore")

class LogConsumer:
    def __init__(self, kafka_servers='localhost:9092', 
                 elastic_host='http://localhost:9200',
                 kafka_topic='fitness_logs'):
        print(f"trying to connect to kafka ")
        print("-" * 50)
        
        self.consumer = KafkaConsumer(
            kafka_topic,
            bootstrap_servers=kafka_servers,
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='fitness_log_group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        
        self.es = Elasticsearch(
            hosts=[elastic_host],
            verify_certs=False,
            ssl_show_warn=False,
            request_timeout=30
        )
        
        if not self.es.ping():
            raise ConnectionError("Could not connect to Elasticsearch")
        
        
            
        print(" connected to Elasticsearch")
        print("-" * 50)
        self.clear_screen()
        print(f"waiting for messages on : {kafka_topic}")
        print("\n=== Service Logs (WARN/ERROR) ===")
        print("-" * 50)
        


    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

        
        

    def process_and_store_log(self, log_data):
        try:
            record = log_data
            #print(f"record: {record}")
            tag = record.pop('tag', None)
            if 'record' in record:
                record = record['record']

            # skip heartbeat 
            if record.get('message_type') == 'HEARTBEAT':
                return

            if tag and 'log_level' not in record:
                tag_parts = tag.split('.')
                if len(tag_parts) > 2:
                    record['log_level'] = tag_parts[-1].upper()

            timestamp = record.get('timestamp', datetime.now().isoformat())
            index_name = f"fitness-logs-{datetime.now():%Y.%m.%d}"

            document = {
                "timestamp": timestamp,
                "service_name": record.get('service_name'),
                "log_level": record.get('log_level'),
                "message_type": record.get('message_type'),
                "message": record.get('message'),
                "node_id": record.get('node_id'),
                "log_id": record.get('log_id')
            }

            if 'error_details' in record:
                document['error_details'] = record['error_details']

            
            response = self.es.index(index=index_name, document=document)

            #  WARN and ERROR logs
            if document.get('log_level', '').upper() in ['ERROR', 'WARN']:
                loglevel_colour = "\033[91m" if document['log_level'] == 'ERROR' else "\033[93m"
                print(f"\nTimestamp: {document.get('timestamp')}")
                print(f"Service: {document.get('service_name', 'unknown')}")
                print(f"Level: {loglevel_colour}{document.get('log_level', 'unknown')}")
                print(f"Message: {document.get('message', 'N/A')}")
                if 'error_details' in document:
                    print(f"Error Details: {document['error_details']}")
                print("-" * 50)

        except Exception as e:
            print(f"Error processing log: {e}")
            print(f"Problematic log_data: {log_data}")

    def start_consuming(self):
        print("Log consumer started - monitoring for WARN/ERROR logs...")
        try:
            for message in self.consumer:
                try:
                    log_data = message.value
                    self.process_and_store_log(log_data)
                except json.JSONDecodeError as e:
                    print(f"Error decoding message: {message.value}")
                except Exception as e:
                    print(f"Error processing message: {e}")
                    
        except KeyboardInterrupt:
            print("\nStopping consumer...")
        finally:
            self.consumer.close()
            print("Consumer closed")

def main():
    consumer = LogConsumer(
        kafka_servers='localhost:9092',
        elastic_host='http://localhost:9200',
        kafka_topic='fitness_logs'
    )
    consumer.start_consuming()

if __name__ == "__main__":
    main()
