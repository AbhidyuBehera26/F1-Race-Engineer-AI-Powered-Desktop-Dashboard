import sys
import os
import logging

# Turn down logging levels for FastF1 and network packages to keep output clean
logging.basicConfig(level=logging.WARNING)
loggers = ['fastf1', 'fastf1.core', 'fastf1.req', 'fastf1._api', 'urllib3', 'requests_cache']
for name in loggers:
    logging.getLogger(name).setLevel(logging.ERROR)

# Add current folder to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import main

if __name__ == '__main__':
    main()
