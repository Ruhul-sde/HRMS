
import json
import os
import config

def initialize_db():
    """Initialize the database file if it doesn't exist"""
    if not os.path.exists(config.DATABASE_FILE):
        data = {
            'users': {
                'admin': {
                    'password': 'admin123',
                    'name': 'Admin User',
                    'role': 'admin',
                    'employee_id': 'ADMIN001'
                },
                'user': {
                    'password': 'user123',
                    'name': 'Test User',
                    'role': 'employee',
                    'employee_id': 'EMP001',
                    'manager': 'admin'
                }
            },
            'locations': {
                'loc1': {
                    'name': 'Main Office',
                    'latitude': 28.7041,
                    'longitude': 77.1025,
                    'radius': 100
                },
                'loc2': {
                    'name': 'Branch Office',
                    'latitude': 28.6139,
                    'longitude': 77.2090,
                    'radius': 100
                }
            },
            'attendance': {},
            'leaves': {}
        }
        with open(config.DATABASE_FILE, 'w') as f:
            json.dump(data, f, indent=2)

def get_db():
    """Get the database contents"""
    with open(config.DATABASE_FILE, 'r') as f:
        return json.load(f)

def save_db(data):
    """Save data to the database"""
    with open(config.DATABASE_FILE, 'w') as f:
        json.dump(data, f, indent=2)
