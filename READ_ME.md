
# Distributed Logging System Setup Guide

 how to set up a distributed logging system using Fluentd, Kafka, and Python services across two Virtual Machines.

## System Overview

- **VM1**: runs Python microservices and Fluentd
- **VM2**: uns  Kafka (message broker)

## VM1 Setup (Fluentd & Python Services)

### 1. Install Required Dependencies

First, we need to install `libssl1.1` which is a prerequisite for td-agent (Fluentd):

```bash
# Add the old ubuntu repository that has libssl1.1
echo "deb <http://security.ubuntu.com/ubuntu> focal-security main" | sudo tee /etc/apt/sources.list.d/focal-security.list

# Update package lists
sudo apt-get update

# Install libssl1.1
sudo apt-get install libssl1.1

# Remove the focal-security repository as we don't need it anymore
sudo rm /etc/apt/sources.list.d/focal-security.list
sudo apt-get update

```

### 2. Install td-agent (Fluentd)

```bash
# Install curl if not already installed
sudo apt-get install -y curl

# Install td-agent
curl -fsSL <https://toolbelt.treasuredata.com/sh/install-ubuntu-jammy-td-agent4.sh> | sudo sh

# Install the Kafka plugin for Fluentd
sudo /opt/td-agent/bin/fluent-gem install fluent-plugin-kafka

```

### 3. Configure td-agent

Edit the td-agent configuration file:

```bash
sudo nano /etc/td-agent/td-agent.conf

```

Add this configuration (replace VM2_IP with your second VM's IP address):

```

# Input source using forward protocol
<source>
  @type forward
  port 24224
  bind 0.0.0.0
</source>

# Match all service logs and heartbeats
<match fitness.**>
  @type kafka2
  brokers 192.168.238.129:9092
  default_topic fitness_logs
 
  # Kafka producer configurations
  required_acks -1
  compression_codec gzip
  max_send_retries 5
  retry_wait 1

  # Use record_accessor to modify the record structure
  <inject>
    tag_key tag
    time_key timestamp
  </inject>

  <format>
    @type json
  </format>

  <buffer>
    @type memory
    chunk_limit_size 8M
    total_limit_size 512M
    flush_interval 5s
    retry_max_times 5
    retry_type exponential_backoff
  </buffer>
</match>

# Match remaining logs for debug purposes
<match **>
  @type stdout
</match>

# Error handling for Fluentd itself
<label @ERROR>
  <match **>
    @type file
    path /var/log/td-agent/error.log
    append true
  </match>
</label>

```

### 4. Start td-agent

```bash
# Start td-agent
sudo systemctl start td-agent

# Enable td-agent to start on boot
sudo systemctl enable td-agent

# Check status
sudo systemctl status td-agent

```

### 5. Install Python Dependencies

```bash
pip install fluent-logger==0.9.7 schedule==1.2.2

```

## VM2 Setup (Kafka)

### 1. Install Java

```bash
sudo apt update
sudo apt install openjdk-11-jdk

# Download 
wget https://downloads.apache.org/kafka/3.6.0/kafka_2.13-3.6.0.tgz

# Extract 
tar xzf kafka_2.13-3.6.0.tgz
mv kafka_2.13-3.6.0 kafka

# Create directories for Kafka and Zookeeper data
sudo mkdir -p /data/kafka
sudo mkdir -p /data/zookeeper

# Set permissions
sudo chown -R $USER:$USER /data/kafka
sudo chown -R $USER:$USER /data/zookeeper

# Edit Kafka configuration
nano ~/kafka/config/server.properties

```

### 2. Configure Kafka

Locate your Kafka configuration files:

```bash
# Look for server.properties
sudo find / -name "server.properties" 2>/dev/null

```

Edit the server.properties file (replace found_path with the path from above):

```bash
sudo nano found_path/server.properties

```

Add/modify these settings:

```
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#
# This configuration file is intended for use in ZK-based mode, where Apache ZooKeeper is required.
# See kafka.server.KafkaConfig for additional details and defaults
#

############################# Server Basics #############################

# The id of the broker. This must be set to a unique integer for each broker.
broker.id=0

############################# Socket Server Settings #############################

# The address the socket server listens on. If not configured, the host name will be equal to the value of
# java.net.InetAddress.getCanonicalHostName(), with PLAINTEXT listener name, and port 9092.
#   FORMAT:
#     listeners = listener_name://host_name:port
#   EXAMPLE:
#     listeners = PLAINTEXT://your.host.name:9092
listeners=PLAINTEXT://:9092

# Listener name, hostname and port the broker will advertise to clients.
# If not set, it uses the value for "listeners".
advertised.listeners=PLAINTEXT://192.168.238.129:9092

# Maps listener names to security protocols, the default is for them to be the same. See the config documentation for more details
#listener.security.protocol.map=PLAINTEXT:PLAINTEXT,SSL:SSL,SASL_PLAINTEXT:SASL_PLAINTEXT,SASL_SSL:SASL_SSL
delete.topic.enable = true
# The number of threads that the server uses for receiving requests from the network and sending responses to the network
num.network.threads=3

# The number of threads that the server uses for processing requests, which may include disk I/O
num.io.threads=8

# The send buffer (SO_SNDBUF) used by the socket server
socket.send.buffer.bytes=102400

# The receive buffer (SO_RCVBUF) used by the socket server
socket.receive.buffer.bytes=102400

# The maximum size of a request that the socket server will accept (protection against OOM)
socket.request.max.bytes=104857600

############################# Log Basics #############################

# A comma separated list of directories under which to store log files
log.dirs=/data/kafka
# The default number of log partitions per topic. More partitions allow greater
# parallelism for consumption, but this will also result in more files across
# the brokers.
num.partitions=1

# The number of threads per data directory to be used for log recovery at startup and flushing at shutdown.
# This value is recommended to be increased for installations with data dirs located in RAID array.
num.recovery.threads.per.data.dir=1

############################# Internal Topic Settings  #############################
# The replication factor for the group metadata internal topics "__consumer_offsets" and "__transaction_state"
# For anything other than development testing, a value greater than 1 is recommended to ensure availability such as 3.
offsets.topic.replication.factor=1
transaction.state.log.replication.factor=1
transaction.state.log.min.isr=1

############################# Log Flush Policy #############################

# Messages are immediately written to the filesystem but by default we only fsync() to sync
# the OS cache lazily. The following configurations control the flush of data to disk.
# There are a few important trade-offs here:
#    1. Durability: Unflushed data may be lost if you are not using replication.
#    2. Latency: Very large flush intervals may lead to latency spikes when the flush does occur as there will be a lot of data to flush.
#    3. Throughput: The flush is generally the most expensive operation, and a small flush interval may lead to excessive seeks.
# The settings below allow one to configure the flush policy to flush data after a period of time or
# every N messages (or both). This can be done globally and overridden on a per-topic basis.

# The number of messages to accept before forcing a flush of data to disk
#log.flush.interval.messages=10000

# The maximum amount of time a message can sit in a log before we force a flush
#log.flush.interval.ms=1000

############################# Log Retention Policy #############################

# The following configurations control the disposal of log segments. The policy can
# be set to
#delete segments after a period of time, or after a given size has accumulated.
# A segment will be deleted whenever *either* of these criteria are met. Deletion always happens
# from the end of the log.

# The minimum age of a log file to be eligible for deletion due to age
log.retention.hours=168

# A size-based retention policy for logs. Segments are pruned from the log unless the remaining
# segments drop below log.retention.bytes. Functions independently of log.retention.hours.
#log.retention.bytes=1073741824

# The maximum size of a log segment file. When this size is reached a new log segment will be created.
#log.segment.bytes=1073741824

# The interval at which log segments are checked to see if they can be deleted according
# to the retention policies
log.retention.check.interval.ms=300000

############################# Zookeeper #############################

# Zookeeper connection string (see zookeeper docs for details).
# This is a comma separated host:port pairs, each corresponding to a zk
# server. e.g. "127.0.0.1:3000,127.0.0.1:3001,127.0.0.1:3002".
# You can also append an optional chroot string to the urls to specify the
# root directory for all kafka znodes.
zookeeper.connect=localhost:2181

# Timeout in ms for connecting to zookeeper
zookeeper.connection.timeout.ms=18000

############################# Group Coordinator Settings #############################

# The following configuration specifies the time, in milliseconds, that the GroupCoordinator will delay the initial consumer rebalance.
# The rebalance will be further delayed by the value of group.initial.rebalance.delay.ms as new members join the group, up to a maximum of max.poll.interval.ms.
# The default value for this is 3 seconds.
# We override this to 0 here as it makes for a better out-of-the-box experience for development and testing.
# However, in production environments the default value of 3 seconds is more suitable as this will help to avoid unnecessary, and potentially expensive, rebalances during application startup.
group.initial.rebalance.delay.ms=0
```

### 3. Create Kafka Topic

# Zookeeper

```jsx
 # Edit Zookeeper configuration
nano ~/kafka/config/zookeeper.properties

```

```bash

```

```jsx
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# the directory where the snapshot is stored.
dataDir=/data/zookeeper
# the port at which the clients will connect
clientPort=2181
# disable the per-ip limit on the number of connections since this is a non-production config
maxClientCnxns=0
# Disable the adminserver by default to avoid port conflicts.
# Set the port to something non-conflicting if choosing to enable this
admin.enableServer=false
# admin.serverPort=8080
```

```jsx
 # Start Zookeeper first
cd ~/kafka
bin/zookeeper-server-start.sh -daemon config/zookeeper.properties

# Wait a few seconds, then start Kafka
bin/kafka-server-start.sh -daemon config/server.properties

# Create the fitness_logs topic
kafka-topics.sh --create --topic fitness_logs --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```

## Testing the Setup

### 1. On VM2 (Kafka)

Start a Kafka consumer to verify message reception:

```bash
kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic fitness_logs --from-beginning

```

### 2. On VM1 (Fluentd)

Create and run a test script:

```python
from fluent import sender
import time

# Create a test sender
logger = sender.FluentSender('test', host='localhost', port=24224)

# Send a test message
test_data = {
    'message': 'Test message',
    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
}

print("Sending test message...")
success = logger.emit('info', test_data)

if success:
    print("Successfully sent message")
else:
    print(f"Failed to send message: {logger.last_error}")

time.sleep(1)
logger.close()

```

## Install ElasticSearch on VM2

```jsx
 # Install required packages
sudo apt-get update
sudo apt-get install apt-transport-https

# Add Elasticsearch repository key
curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo gpg --dearmor -o /usr/share/keyrings/elastic.gpg

# Add Elasticsearch repository
echo "deb [signed-by=/usr/share/keyrings/elastic.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-8.x.list

# Update and install Elasticsearch
sudo apt-get update
sudo apt-get install elasticsearch

```

Configure elasticsearch

```jsx
sudo nano /etc/elasticsearch/elasticsearch.yml
```

```jsx
cluster.name: fitness-cluster
network.host: 0.0.0.0

xpack.security.enabled: false  
```

```jsx
 sudo systemctl daemon-reload
sudo systemctl enable elasticsearch
sudo systemctl start elasticsearch
```

## Troubleshooting

# 0. Check between two VMS

```jsx
 # On VM2
ip addr show

# On VM1
ping VM2_IP
```

### 1. Check Connectivity

```bash
# From VM1, ping VM2
ping VM2_IP

# Check if Kafka port is accessible
nc -zv VM2_IP 9092

```

### 2. Check Service Status

```bash
# On VM1
sudo systemctl status td-agent
sudo tail -f /var/log/td-agent/td-agent.log

# On VM2
sudo systemctl status kafka

```

### 3. Few notes

- If services won't start, check logs for errors
- Ensure both VMs can communicate (ping test)
- Verify all config files have correct permissions
- Make sure required ports (24224, 9092) are open

### Monitoring

- Check Fluentd status: `sudo systemctl status td-agent`
- Check Kafka status: `sudo systemctl status kafka`
- Monitor log files: `sudo tail -f /var/log/td-agent/td-agent.log`
