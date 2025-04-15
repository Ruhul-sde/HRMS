
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Flask configuration
SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'geo_attendance_system_secret')
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8080))

# Google Maps API key - directly in config
GOOGLE_MAPS_API_KEY = 'AAIzaSyCmXjJG8HAHktiKxhhg5hBFeLg311OlptA'

# Database configuration
DATABASE_FILE = os.getenv('DATABASE_FILE', 'database.json')
