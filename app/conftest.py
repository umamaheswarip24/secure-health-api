import sys, os

# Add the app directory to Python path
# This lets pytest find server.py, storage.py, etc.
sys.path.insert(0, os.path.dirname(__file__))