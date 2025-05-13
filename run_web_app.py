#!/usr/bin/env python3
"""
Run script for Semantic DevOps Bot Web Interface
"""

import os
import sys
from web.app import app

def main():
    """Run the web application"""
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() == "true"
    
    print(f"Starting Semantic DevOps Bot Web Interface on port {port}")
    print(f"Debug mode: {'ON' if debug else 'OFF'}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)

if __name__ == "__main__":
    sys.exit(main())
    