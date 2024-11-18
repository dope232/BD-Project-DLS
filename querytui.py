
from elasticsearch import Elasticsearch
import datetime 
from datetime import timedelta  
import os 
import time 
import json

class LogQueryTUI:
    def __init__(self):
        self.es = Elasticsearch(['http://localhost:9200'])
        self.index_pattern = 'fitness-logs-*' 

    def get_available_indices(self):
        try:
            indices = self.es.indices.get_alias(index=self.index_pattern)
            return list(indices.body.keys())
        except Exception as e:
            print(f"Error getting indices: {str(e)}")
            return []

    def check_connection(self):
        try:
            if self.es.ping():
                indices = self.get_available_indices()
                if indices:
                    return True
                else:
                    print("No fitness log indices found. Please ensure the log consumer is running.")
                    return False
            else:
                print("Connection failed")
                return False
        except Exception as e:
            print(f"Error connecting to elasticsearch: {str(e)}")
            return False 

    def format_timestamp(self, timestamp_str):
            try:
                if isinstance(timestamp_str, (int, float)) or timestamp_str.replace('.', '').isdigit():
                    timestamp = float(timestamp_str)
                    dt = datetime.datetime.fromtimestamp(timestamp)
                    return dt.strftime('%Y-%m-%d %H:%M:%S')
                
                dt = datetime.datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                return timestamp_str


    def format_log_entry(self, log_entry):
        try:
            source = log_entry['_source']
            return {
                'timestamp': self.format_timestamp(source.get('timestamp', 'N/A')),
                'log_level': source.get('log_level', 'N/A'),
                'message': source.get('message', 'N/A'),
                'service': source.get('service_name', 'N/A'),
                'node_id': source.get('node_id', 'N/A')
            }
        except Exception as e:
            return {
                'timestamp': 'ERROR',
                'log_level': 'ERROR',
                'message': f'Error formatting log: {str(e)}',
                'service': 'ERROR',
                'node_id': 'ERROR'
            }

    def display_logs(self, logs):
            if not logs:
                print("\nNo logs found or error getting logs")
                return

            print("\n{:<20} {:<10} {:<20} {:<36} {:<50}".format(
                'Timestamp', 'Log Level', 'Service', 'Node ID', 'Message'))
            print("-" * 136)
            
            for log in logs:
                formatted_log = self.format_log_entry(log)
                try:
                    print("{:<20} {:<10} {:<20} {:<36} {:<50}".format(
                        formatted_log['timestamp'],
                        formatted_log['log_level'],
                        formatted_log['service'],
                        formatted_log['node_id'],
                        formatted_log['message']
                    ))
                except Exception as e:
                    print(f"Error displaying log entry: {str(e)}")
            print("\n")


    def get_all_service_logs(self):
        try:
            body = {
                "query": {
                    "match_all": {}
                },
                "sort": [{"timestamp": {"order": "desc"}}],
                "size": 100
            }

            results = self.es.search(index=self.index_pattern, body=body)
            return results.body['hits']['hits']
        except Exception as e:
            print(f"Error getting all service logs: {str(e)}")
            return []
        
    def get_registration_logs(self):
        try:
            body = {
                "query": {
                    "match": {
                        "message_type": "REGISTRATION"
                    }
                },
                "sort": [{"timestamp": {"order": "desc"}}],
                "size": 100
            }

            results = self.es.search(index=self.index_pattern, body=body)
            return results.body['hits']['hits']
        except Exception as e:
            print(f"Error getting registration logs: {str(e)}")
            return []

        

    def get_service_logs(self, service):
        try:
            body = {
                "query": {
                    "match": {
                        "service_name": service
                    }
                },
                "sort": [{"timestamp": {"order": "desc"}}],
                "size": 100
            }

            results = self.es.search(index=self.index_pattern, body=body)
            return results.body['hits']['hits']
        except Exception as e:
            print(f"Error getting service logs: {str(e)}")
            return []

    def get_service_errors(self, service):
        try:
            body = {
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"service_name": service}},
                            {"match": {"log_level": "ERROR"}}
                        ]
                    }
                },
                "sort": [{"timestamp": {"order": "desc"}}],
                "size": 100
            }

            results = self.es.search(index=self.index_pattern, body=body)
            return results.body['hits']['hits']
        except Exception as e:
            print(f"Error getting service errors: {str(e)}")
            return []

    

    def display_menu(self):
        print("\nFitness Log Query")
        print("-" * 80)
        print("1. View Service Logs")
        print("2. View Service Errors")
        print("3. List Available Indices")
        print("4. Exit")
        print("5- Get all logs")
        print("6. View Registration Logs")
        print("-" * 80)

    def wait_for_input(self):
        input("\nPress Enter to continue...")

    def main_menu(self):
        while True:
            self.clear_screen()
            self.display_menu()
            choice = input("Enter choice: ")

            if choice == '1':
                self.clear_screen()
                service = input("Enter service name: ")
                service_logs = self.get_service_logs(service)
                self.display_logs(service_logs)
                self.wait_for_input()
            
            elif choice == '2':
                self.clear_screen()
                service = input("Enter service name: ")
                service_errors = self.get_service_errors(service)
                self.display_logs(service_errors)
                self.wait_for_input()

            elif choice == '3':
                self.clear_screen()
                print("\nAvailable Indices:")
                indices = self.get_available_indices()
                for idx in sorted(indices):
                    print(f"- {idx}")
                self.wait_for_input()

            elif choice == '4':
                break
            elif choice == '5':
                self.clear_screen()
                all_service_logs = self.get_all_service_logs()
                self.display_logs(all_service_logs)
                self.wait_for_input()

            if choice == '6':
                self.clear_screen()
                registration_logs = self.get_registration_logs()
                self.display_logs(registration_logs)
                self.wait_for_input()

            else:
                print("Invalid choice")
                self.wait_for_input()

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

def main():
    tui = LogQueryTUI()
    if not tui.check_connection():
        return
    tui.main_menu()

if __name__ == "__main__":
    main()
