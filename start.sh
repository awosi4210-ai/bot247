#!/bin/bash

# Minecraft Bot Start Script
echo "========================================"
echo "  🤖 STARTING MINECRAFT ALIVE BOT"
echo "========================================"
echo "  Server: funark.aternos.me:57003"
echo "  Version: PaperMC 1.21.11"
echo "========================================"

# Install dependencies
pip install -r requirements.txt

# Run bot with keep-alive
python -c "
from keep_alive import keep_alive
keep_alive()
import main
main.main()
"