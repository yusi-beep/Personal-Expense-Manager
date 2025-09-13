# Personal Expense Tracker

## Overview

A comprehensive personal expense tracking web application built with Flask. The system provides user authentication, expense/income management, data visualization, and import/export capabilities. Users can manage their financial records with categorization, filtering, and reporting features. The application includes both a web interface and REST API for programmatic access.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **Flask**: Core web framework with modular blueprint architecture
- **Flask-Login**: Session-based user authentication and authorization
- **Flask-SQLAlchemy**: ORM for database operations with SQLite (development) and production-ready database support

### Database Design
- **User Model**: Handles authentication with hashed passwords (PBKDF2-SHA256)
- **Record Model**: Stores financial transactions with date, type, category, amount, and description
- **Category Model**: User-specific expense/income categories with unique constraints
- **Cascading Deletions**: Automatic cleanup of user data when accounts are deleted

### Authentication & Security
- **Session Management**: Flask-Login for secure user sessions
- **Password Security**: Werkzeug password hashing with salt
- **API Authentication**: Token-based authentication using URLSafeTimedSerializer
- **Production Security**: HTTPS-only cookies, HTTPONLY flags, and secure session configuration

### Frontend Architecture
- **Template Engine**: Jinja2 with responsive Bootstrap 5 UI
- **Data Visualization**: Chart.js for pie charts (expense categories) and bar charts (monthly trends)
- **Theme System**: Dark/light mode toggle with localStorage persistence
- **Progressive Enhancement**: Auto-hiding flash messages and responsive design

### API Design
- **RESTful Endpoints**: Full CRUD operations for records and categories
- **Token Authentication**: Bearer token system with configurable expiration
- **Export/Import**: CSV and PDF generation with pandas and ReportLab
- **Error Handling**: Consistent JSON error responses

### Data Management
- **Filtering & Pagination**: Advanced filtering by category, type, date range, and search terms
- **Export Formats**: CSV (pandas) and PDF (ReportLab) with formatted tables
- **Import System**: CSV import with automatic category creation and data validation
- **Period Analysis**: Day/week/month/year financial summaries with navigation

### Configuration Management
- **Environment-Based Config**: Separate development and production configurations
- **Security Validation**: Runtime checks for production secret keys
- **Database Flexibility**: SQLite for development, configurable for production databases

## External Dependencies

### Core Framework
- **Flask 3.1.1**: Web application framework
- **Flask-Login 0.6.3**: User session management
- **Flask-SQLAlchemy 3.1.1**: Database ORM integration

### Data Processing
- **pandas 2.3.1**: CSV import/export and data manipulation
- **ReportLab 4.4.3**: PDF generation for financial reports
- **python-dotenv 1.1.1**: Environment variable management

### Frontend Libraries
- **Bootstrap 5.3.3**: Responsive CSS framework (CDN)
- **Chart.js**: Client-side data visualization (CDN)
- **Google Fonts (Inter)**: Typography enhancement (CDN)

### Security & Utilities
- **Werkzeug 3.1.3**: Password hashing and security utilities
- **itsdangerous 2.2.0**: Secure token generation and validation
- **SQLAlchemy 2.0.43**: Database abstraction layer

### Development Tools
- **matplotlib 3.10.5**: Optional data visualization (legacy pet.py script)
- **numpy 2.3.2**: Mathematical operations support

### Database Support
- **SQLite**: Default development database (file-based)
- **PostgreSQL**: Production database support (configurable via DATABASE_URL)
- **MySQL**: Alternative production database option
