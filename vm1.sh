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
read -p "Enter VM2 IP address: " VM2_IP

# Install and configure NTP
echo "Installing and configuring NTP..."
apt-get update
apt-get install -y chrony
systemctl start chronyd
systemctl enable chronyd

# Configure file descriptor limits
echo "Configuring file descriptor limits..."
cat > /etc/security/limits.conf << EOF
root soft nofile 65536
root hard nofile 65536
* soft nofile 65536
* hard nofile 65536
EOF

# Configure sysctl parameters
echo "Configuring kernel parameters..."
cat > /etc/sysctl.conf << EOF
net.core.somaxconn = 1024
net.core.netdev_max_backlog = 5000
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_wmem = 4096 12582912 16777216
net.ipv4.tcp_rmem = 4096 12582912 16777216
net.ipv4.tcp_max_syn_backlog = 8096
net.ipv4.tcp_slow_start_after_idle = 0
net.ipv4.tcp_tw_reuse = 1
net.ipv4.ip_local_port_range = 10240 65535
EOF

# Apply sysctl settings
sysctl -p

# Add Ubuntu focal repository for libssl1.1
echo "deb http://security.ubuntu.com/ubuntu focal-security main" | tee /etc/apt/sources.list.d/focal-security.list
apt-get update
apt-get install -y libssl1.1
rm /etc/apt/sources.list.d/focal-security.list
apt-get update

# Install td-agent
echo "Installing td-agent..."
curl -fsSL https://toolbelt.treasuredata.com/sh/install-ubuntu-jammy-td-agent4.sh | sh

echo "Installing fluent-plugin-kafka..."
/opt/td-agent/bin/fluent-gem install fluent-plugin-kafka

echo "Configuring td-agent..."
mkdir -p /var/log/td-agent
chown -R td-agent:td-agent /var/log/td-agent

cat > /etc/td-agent/td-agent.conf <<EOF
<source>
  @type forward
  port 24224
  bind 0.0.0.0
</source>

<match *.{info,warn,error,heartbeat}>
  @type kafka2
  brokers ${VM2_IP}:9092
  default_topic fitness_logs
  
  required_acks -1
  compression_codec gzip
  max_send_retries 5
  retry_wait 1
  
  <buffer>
    @type memory
    chunk_limit_size 8M
    total_limit_size 512M
    flush_interval 5s
    retry_max_times 5
    retry_type exponential_backoff
  </buffer>

  <format>
    @type json
  </format>
</match>

<label @ERROR>
  <match **>
    @type file
    path /var/log/td-agent/error.log
    append true
  </match>
</label>
EOF

echo "Setting up td-agent service..."
systemctl daemon-reload
systemctl start td-agent
systemctl enable td-agent

echo "Installing Python dependencies..."
apt-get install -y python3-pip
pip3 install fluent-logger==0.9.7 schedule==1.2.2

echo "Verifying installation..."
echo "File descriptor limit:"
ulimit -n
echo "NTP status:"
chronyc tracking
echo "td-agent status:"
systemctl status td-agent --no-pager

echo "VM1 setup completed successfully"
exit 0
