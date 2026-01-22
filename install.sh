#!/bin/bash
#
# Installation script for METAR Collector Service
# Installs and configures the service on Ubuntu/Debian systems
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/home/edu/metar-collector"
SERVICE_USER="edu"
SERVICE_GROUP="edu"

# Get the directory where the script is located (before any cd commands)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================"
echo "METAR Collector Service Installation"
echo "========================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run as root${NC}"
    echo "Please run: sudo ./install.sh"
    exit 1
fi

# Check for required commands
for cmd in python3 pip systemctl; do
    if ! command -v $cmd &> /dev/null; then
        echo -e "${RED}Error: $cmd is not installed${NC}"
        exit 1
    fi
done

# Get API key from user
echo -e "${YELLOW}CheckWX API Configuration${NC}"
echo "Get your free API key at: https://www.checkwx.com/"
echo ""
read -p "Enter your CheckWX API key: " CHECKWX_API_KEY

if [ -z "$CHECKWX_API_KEY" ]; then
    echo -e "${RED}Error: API key cannot be empty${NC}"
    exit 1
fi

# Create installation directory
echo -e "${GREEN}Creating installation directory: $INSTALL_DIR${NC}"
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# Copy files
echo -e "${GREEN}Copying application files${NC}"
cp "$SCRIPT_DIR/metar_collector.py" .
cp "$SCRIPT_DIR/requirements.txt" .
cp "$SCRIPT_DIR/export_data.py" .
chmod +x metar_collector.py export_data.py

# Create virtual environment
echo -e "${GREEN}Creating Python virtual environment${NC}"
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo -e "${GREEN}Installing Python dependencies${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Set permissions
echo -e "${GREEN}Setting file permissions${NC}"
chown -R $SERVICE_USER:$SERVICE_GROUP $INSTALL_DIR
chmod 755 $INSTALL_DIR

# Install systemd service files
echo -e "${GREEN}Installing systemd service files${NC}"
cp "$SCRIPT_DIR/metar-collector.service" /etc/systemd/system/
cp "$SCRIPT_DIR/metar-collector.timer" /etc/systemd/system/

# Update service file with API key (using | as delimiter to handle special chars)
sed -i "s|YOUR_API_KEY_HERE|$CHECKWX_API_KEY|" /etc/systemd/system/metar-collector.service

# Reload systemd
echo -e "${GREEN}Reloading systemd daemon${NC}"
systemctl daemon-reload

# Enable and start timer
echo -e "${GREEN}Enabling and starting timer${NC}"
systemctl enable metar-collector.timer
systemctl start metar-collector.timer

# Run initial collection
echo -e "${GREEN}Running initial data collection${NC}"
systemctl start metar-collector.service

# Wait a moment for service to complete
sleep 2

# Check service status
echo ""
echo "========================================"
echo "Installation Status"
echo "========================================"

if systemctl is-active --quiet metar-collector.timer; then
    echo -e "${GREEN}✓ Timer is active${NC}"
else
    echo -e "${RED}✗ Timer failed to start${NC}"
fi

echo ""
echo "Installation complete!"
echo ""
echo "Useful commands:"
echo "  Check timer status:    systemctl status metar-collector.timer"
echo "  Check service logs:    journalctl -u metar-collector -f"
echo "  Run manual collection: systemctl start metar-collector.service"
echo "  Export data:           cd $INSTALL_DIR && ./venv/bin/python3 export_data.py"
echo "  View database:         sqlite3 $INSTALL_DIR/metar_data.db"
echo ""
echo "Data location: $INSTALL_DIR/metar_data.db"
echo "Logs location: $INSTALL_DIR/metar_collector.log"
echo ""
echo "The service will run daily at 02:00 UTC"
echo ""
