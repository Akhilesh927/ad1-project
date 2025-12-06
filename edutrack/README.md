# EduTrack

A comprehensive web application for parents and teachers to monitor student progress, attendance, grades, fees, and bus tracking. This portal helps prevent kidnapping by providing real-time attendance tracking and bus monitoring.

## Features

### For Parents:
- **Real-time Attendance Tracking**: Monitor your child's attendance for each hour of the school day
- **Bus Tracking**: Track when your child enters and exits the school bus
- **Leave Request Management**: Submit sick leave and other leave requests to teachers
- **Grade Monitoring**: View your child's academic performance and grades
- **Fee Management**: Track pending fees and payment history
- **Dashboard Overview**: Get a comprehensive view of your child's school activities

### For Teachers:
- **Student Management**: Manage attendance for all assigned students
- **Grade Management**: Add and update student grades
- **Leave Request Approval**: Review and approve/reject leave requests from parents
- **Fee Management**: Add and track student fees
- **Bus Attendance**: Update bus entry and exit times
- **Dashboard Analytics**: View statistics and pending tasks

## Security Features

- **Hour-by-hour Attendance**: Prevents kidnapping by tracking student presence in each class
- **Bus Entry/Exit Tracking**: Monitors when students board and leave school buses
- **Real-time Updates**: Instant notifications and updates for parents
- **Role-based Access**: Teachers can modify data, parents can only view and submit requests

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd school_monitoring_portal
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Access the app**:
Open your browser and go to `http://localhost:5000`

## Demo Credentials

### Parent Login:
- **Username**: parent1
- **Password**: parent123
- **Role**: Parent

### Teacher Login:
- **Username**: teacher1
- **Password**: teacher123
- **Role**: Teacher

## Database Structure

The application uses SQLite database with the following models:

- **User**: Parent and teacher accounts
- **Student**: Student information linked to parents and teachers
- **Attendance**: Hour-by-hour attendance records
- **BusAttendance**: Bus entry and exit tracking
- **Grade**: Academic performance records
- **Fee**: Fee management and payment tracking
- **LeaveRequest**: Leave request management system

## Key Features Explained

### 1. Anti-Kidnapping Measures
- **Hourly Attendance**: Teachers mark attendance for each hour, allowing immediate detection if a student goes missing
- **Bus Tracking**: Parents can see exactly when their child boards and exits the school bus
- **Real-time Updates**: All attendance data is updated in real-time

### 2. Leave Request System
- **Parent Submission**: Parents can submit leave requests with detailed reasons
- **Teacher Approval**: Teachers can approve, reject, or add comments to requests
- **Status Tracking**: Real-time status updates for all leave requests

### 3. Academic Monitoring
- **Grade Management**: Teachers can add grades for different subjects and semesters
- **Performance Tracking**: Parents can monitor their child's academic progress
- **Historical Data**: Complete grade history and performance trends

### 4. Fee Management
- **Fee Tracking**: Teachers can add various types of fees
- **Payment Status**: Parents can view pending and paid fees
- **Due Date Monitoring**: Automatic tracking of fee due dates

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, JavaScript
- **Styling**: Custom CSS with Font Awesome icons
- **Security**: Password hashing with Werkzeug

## File Structure

```
school_monitoring_portal/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── static/
│   └── css/
│       └── style.css     # Custom styling
├── templates/
│   ├── index.html        # Login page
│   ├── parent_dashboard.html
│   ├── teacher_dashboard.html
│   ├── attendance.html
│   ├── teacher_attendance.html
│   ├── grades.html
│   ├── teacher_grades.html
│   ├── fees.html
│   ├── leave_requests.html
│   └── bus_tracking.html
└── instance/
    └── school_monitoring.db  # SQLite database (created automatically)
```

## Usage Instructions

### For Parents:
1. Login with parent credentials
2. View dashboard for overview of child's activities
3. Check attendance for real-time updates
4. Submit leave requests when needed
5. Monitor grades and academic performance
6. Track bus attendance and fee payments

### For Teachers:
1. Login with teacher credentials
2. Mark daily attendance for all students
3. Add and update student grades
4. Review and respond to leave requests
5. Manage student fees
6. Update bus attendance records

## Security Considerations

- All passwords are hashed using Werkzeug's security functions
- Session-based authentication
- Role-based access control
- Input validation and sanitization
- SQL injection protection through SQLAlchemy ORM

## Future Enhancements

- Email notifications for parents
- Mobile app development
- GPS tracking for school buses
- Advanced analytics and reporting
- Integration with school management systems
- Multi-language support

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please contact the development team or create an issue in the repository. 