#!/bin/bash

# Exit on error
set -e

# Function for error handling
handle_error() {
    echo "Error occurred in script at line: ${1}"
    exit 1
}
trap 'handle_error ${LINENO}' ERR

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

# Get VM2 IP address
read -p "Enter this VM's (VM2) IP address: " VM2_IP

echo "Installing dependencies..."
apt-get update
apt-get install -y openjdk-11-jdk wget gpg apt-transport-https

# Create directories
mkdir -p /data/kafka /data/zookeeper
chown -R $USER:$USER /data/kafka /data/zookeeper

echo "Downloading and setting up Kafka..."
cd /opt
wget https://downloads.apache.org/kafka/3.6.0/kafka_2.13-3.6.0.tgz
tar xzf kafka_2.13-3.6.0.tgz
mv kafka_2.13-3.6.0 kafka
chown -R $USER:$USER /opt/kafka

# Create systemd service for Zookeeper
cat > /etc/systemd/system/zookeeper.service <<EOF
[Unit]
Description=Apache Zookeeper server
Documentation=http://zookeeper.apache.org
Requires=network.target remote-fs.target
After=network.target remote-fs.target

[Service]
Type=simple
ExecStart=/opt/kafka/bin/zookeeper-server-start.sh /opt/kafka/config/zookeeper.properties
ExecStop=/opt/kafka/bin/zookeeper-server-stop.sh
Restart=on-abnormal
User=$USER

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for Kafka
cat > /etc/systemd/system/kafka.service <<EOF
[Unit]
Description=Apache Kafka Server
Documentation=http://kafka.apache.org/documentation.html
Requires=zookeeper.service
After=zookeeper.service

[Service]
Type=simple
Environment="JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64"
ExecStart=/opt/kafka/bin/kafka-server-start.sh /opt/kafka/config/server.properties
ExecStop=/opt/kafka/bin/kafka-server-stop.sh
Restart=on-abnormal
User=$USER

[Install]
WantedBy=multi-user.target
EOF

echo "Configuring Kafka and Zookeeper..."
# Configure Zookeeper
cat > /opt/kafka/config/zookeeper.properties <<EOF
dataDir=/data/zookeeper
clientPort=2181
maxClientCnxns=0
admin.enableServer=false
EOF

# Configure Kafka
cat > /opt/kafka/config/server.properties <<EOF
broker.id=0
listeners=PLAINTEXT://:9092
advertised.listeners=PLAINTEXT://${VM2_IP}:9092
delete.topic.enable=true
log.dirs=/data/kafka
num.partitions=1
offsets.topic.replication.factor=1
transaction.state.log.replication.factor=1
transaction.state.log.min.isr=1
log.retention.hours=168
zookeeper.connect=localhost:2181
EOF

echo "Installing Elasticsearch..."
curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | gpg --dearmor -o /usr/share/keyrings/elastic.gpg
echo "deb [signed-by=/usr/share/keyrings/elastic.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | tee /etc/apt/sources.list.d/elastic-8.x.list
apt-get update
apt-get install -y elasticsearch

# Configure Elasticsearch
cat > /etc/elasticsearch/elasticsearch.yml <<EOF
cluster.name: fitness-cluster
network.host: 0.0.0.0
discovery.type: single-node
xpack.security.enabled: false
EOF

# Configure JVM heap size for Elasticsearch
cat > /etc/elasticsearch/jvm.options.d/heap.options <<EOF
-Xms512m
-Xmx512m
EOF

echo "Starting services..."
systemctl daemon-reload
systemctl enable zookeeper
systemctl enable kafka
systemctl enable elasticsearch

systemctl start zookeeper
sleep 10
systemctl start kafka
sleep 10
systemctl start elasticsearch
sleep 10

echo "Creating Kafka topic..."
/opt/kafka/bin/kafka-topics.sh --create --topic fitness_logs --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

echo "Installing Python dependencies..."
apt-get install -y python3-pip
pip3 install kafka-python elasticsearch

echo "VM2 setup completed successfully"
echo "Verifying services..."
systemctl status zookeeper --no-pager
systemctl status kafka --no-pager
systemctl status elasticsearch --no-pager

exit 0
