#!/bin/bash
#
# Create deployment package for METAR Collector Service
# This script bundles all necessary files for deployment to Ubuntu server
#

set -e

PACKAGE_NAME="metar-collector-package"
PACKAGE_DIR="/tmp/${PACKAGE_NAME}"
OUTPUT_FILE="${PACKAGE_NAME}.tar.gz"

echo "========================================"
echo "Creating METAR Collector Package"
echo "========================================"
echo ""

# Clean up any existing package
if [ -d "$PACKAGE_DIR" ]; then
    echo "Removing old package directory..."
    rm -rf "$PACKAGE_DIR"
fi

if [ -f "$OUTPUT_FILE" ]; then
    echo "Removing old package file..."
    rm -f "$OUTPUT_FILE"
fi

# Create package directory
echo "Creating package directory..."
mkdir -p "$PACKAGE_DIR"

# Copy files
echo "Copying files..."

# Python scripts
cp metar_collector.py "$PACKAGE_DIR/"
cp export_data.py "$PACKAGE_DIR/"
cp requirements.txt "$PACKAGE_DIR/"

# Systemd files
cp metar-collector.service "$PACKAGE_DIR/"
cp metar-collector.timer "$PACKAGE_DIR/"

# Installation script
cp install.sh "$PACKAGE_DIR/"
chmod +x "$PACKAGE_DIR/install.sh"

# Documentation
cp DEPLOYMENT.md "$PACKAGE_DIR/"

# Create README for the package
cat > "$PACKAGE_DIR/README.txt" << 'EOF'
METAR Collector Service Package
================================

This package contains everything needed to deploy the METAR data
collection service on your Ubuntu server.

Quick Start
-----------

1. Upload this package to your server:
   scp metar-collector-package.tar.gz root@your-server:/tmp/

2. SSH to your server:
   ssh root@your-server

3. Extract and install:
   cd /tmp
   tar -xzf metar-collector-package.tar.gz
   cd metar-collector-package
   sudo ./install.sh

4. Follow the prompts to enter your CheckWX API key

For detailed documentation, see DEPLOYMENT.md

Files Included
--------------

metar_collector.py         - Main data collection script
export_data.py             - Data export utility
requirements.txt           - Python dependencies
install.sh                 - Installation script
metar-collector.service    - Systemd service unit
metar-collector.timer      - Systemd timer unit
DEPLOYMENT.md              - Full deployment documentation
README.txt                 - This file

Requirements
------------

- Ubuntu 20.04 LTS or newer
- Python 3.8+
- CheckWX API key (free at https://www.checkwx.com/)

Support
-------

See DEPLOYMENT.md for troubleshooting and detailed usage instructions.
EOF

# Make Python scripts executable
chmod +x "$PACKAGE_DIR/metar_collector.py"
chmod +x "$PACKAGE_DIR/export_data.py"

# Create tarball
echo "Creating tarball..."
tar -czf "$OUTPUT_FILE" -C /tmp "$PACKAGE_NAME"

# Clean up temp directory
rm -rf "$PACKAGE_DIR"

# Show results
echo ""
echo "========================================"
echo "Package Created Successfully!"
echo "========================================"
echo ""
echo "Package file: $OUTPUT_FILE"
echo "Package size: $(du -h "$OUTPUT_FILE" | cut -f1)"
echo ""
echo "Next steps:"
echo "  1. Upload to your server:"
echo "     scp $OUTPUT_FILE root@your-server-ip:/tmp/"
echo ""
echo "  2. SSH to server and install:"
echo "     ssh root@your-server-ip"
echo "     cd /tmp"
echo "     tar -xzf $OUTPUT_FILE"
echo "     cd $PACKAGE_NAME"
echo "     sudo ./install.sh"
echo ""
echo "See DEPLOYMENT.md for full documentation"
echo ""
