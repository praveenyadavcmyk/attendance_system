# Attendance System

A simple web-based employee attendance tracking system built with Flask and SQLite.

## Features

- **User Authentication**: Login and signup functionality
- **Attendance Tracking**: Mark attendance with GPS location verification
- **Distance Calculation**: Uses geolocation to verify user is at office location
- **Employee Dashboard**: View and manage attendance records
- **Database**: SQLite for data persistence

## Requirements

- Python 3.7+
- Flask
- SQLite3

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/attendance_system.git
cd attendance_system
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install flask
```

## Usage

1. Run the application:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

3. Default credentials:
   - Email: emp@mail.com
   - Password: 123

## Project Structure

```
attendance_system/
├── app.py                 # Main Flask application
├── database.db            # SQLite database (auto-created)
├── templates/
│   ├── login.html        # Login page
│   ├── signup.html       # Registration page
│   └── employee.html     # Employee dashboard
└── README.md             # This file
```

## Technologies Used

- **Backend**: Flask (Python)
- **Database**: SQLite3
- **Frontend**: HTML/CSS/JavaScript
- **Location**: Geolocation API

## License

MIT License

## Author

Your Name
