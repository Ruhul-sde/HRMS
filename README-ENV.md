
# Geo Attendance System - Environment Setup

## Overview
This document provides guidance on setting up the environment for the Geo Attendance System.

## Environment Variables
The application uses environment variables for configuration. These are stored in a `.env` file at the root of the project.

1. Copy the example file to create your own:
   ```
   cp .env.example .env
   ```

2. Edit the `.env` file with your specific configuration:
   - `FLASK_SECRET_KEY`: Secret key for Flask sessions
   - `GOOGLE_MAPS_API_KEY`: Your Google Maps API key
   - `DATABASE_FILE`: Path to the database file
   - `DEBUG`: Set to True/False for development/production
   - `HOST`: Host to bind the application to
   - `PORT`: Port to run the application on

## Installation
To install required packages:

```bash
pip install -r requirements.txt
```

## Running the Application
After setting up your environment variables, run the application:

```bash
python app.py
```

The application will be available at http://0.0.0.0:8080 by default.
