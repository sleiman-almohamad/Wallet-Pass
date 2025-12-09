# Database Module

This module provides MariaDB database integration for the Wallet Passes application.

## Files

- **schema.sql**: Database schema definition with Classes_Table and Passes_Table
- **db_manager.py**: Database manager class with CRUD operations
- **init_db.py**: Database initialization script

## Database Schema

### Classes_Table
Stores Google Wallet pass class definitions.

| Column | Type | Description |
|--------|------|-------------|
| class_id | VARCHAR(255) PRIMARY KEY | Unique identifier for the class |
| class_type | VARCHAR(100) NOT NULL | Type of pass (e.g., 'EventTicket', 'LoyaltyCard') |
| base_color | VARCHAR(7) | Hex color code (e.g., '#FF5733') |
| logo_url | VARCHAR(500) | URL to the class logo image |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Record last update timestamp |

### Passes_Table
Stores individual pass instances.

| Column | Type | Description |
|--------|------|-------------|
| id | INT AUTO_INCREMENT PRIMARY KEY | Auto-incrementing primary key |
| object_id | VARCHAR(255) UNIQUE NOT NULL | Unique identifier for the pass object |
| class_id | VARCHAR(255) FOREIGN KEY | Reference to Classes_Table.class_id |
| holder_name | VARCHAR(255) NOT NULL | Name of the pass holder |
| holder_email | VARCHAR(255) NOT NULL | Email of the pass holder |
| status | ENUM('Active', 'Expired') | Current status of the pass |
| pass_data | JSON | Flexible JSON data (seat, gate, match_time, etc.) |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Record last update timestamp |

**Indexes:**
- `idx_class_id` on class_id for faster joins
- `idx_status` on status for filtering
- `idx_holder_email` on holder_email for user lookups

**Foreign Key:**
- `class_id` references `Classes_Table.class_id` with CASCADE delete

## Setup Instructions

### 1. Install MariaDB

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install mariadb-server mariadb-client
sudo systemctl start mariadb
sudo systemctl enable mariadb
```

**macOS:**
```bash
brew install mariadb
brew services start mariadb
```

### 2. Create Database User

```bash
sudo mysql -u root -p
```

Then execute:
```sql
CREATE DATABASE wallet_passes CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'wallet_user'@'localhost' IDENTIFIED BY 'wallet_pass';
GRANT ALL PRIVILEGES ON wallet_passes.* TO 'wallet_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3. Update Configuration

Edit `configs.py` and update the database credentials:

```python
DB_HOST = 'localhost'
DB_PORT = 3306
DB_USER = 'wallet_user'
DB_PASSWORD = 'your_secure_password'  # Change this!
DB_NAME = 'wallet_passes'
```

### 4. Install Python Dependencies

```bash
uv sync
```

### 5. Initialize Database

```bash
uv run python database/init_db.py
```

This will:
- Create the database if it doesn't exist
- Create the tables with proper schema
- Optionally insert sample data for testing

## Usage Examples

### Basic Usage

```python
from database.db_manager import DatabaseManager

# Initialize database manager
db = DatabaseManager()

# Test connection
if db.test_connection():
    print("Database connected successfully!")
```

### Class Operations

```python
# Create a new class
db.create_class(
    class_id='event_class_001',
    class_type='EventTicket',
    base_color='#FF5733',
    logo_url='https://example.com/logo.png'
)

# Get a class
class_data = db.get_class('event_class_001')
print(class_data)

# Update a class
db.update_class('event_class_001', base_color='#3498DB')

# Get all classes
all_classes = db.get_all_classes()

# Delete a class (will cascade delete associated passes)
db.delete_class('event_class_001')
```

### Pass Operations

```python
# Create a new pass
db.create_pass(
    object_id='pass_001',
    class_id='event_class_001',
    holder_name='John Doe',
    holder_email='john@example.com',
    pass_data={'seat': 'A5', 'gate': '3', 'match_time': '20:00'},
    status='Active'
)

# Get a pass
pass_data = db.get_pass('pass_001')
print(pass_data)
# Output: {'id': 1, 'object_id': 'pass_001', ..., 'pass_data': {'seat': 'A5', ...}}

# Update pass status
db.update_pass_status('pass_001', 'Expired')

# Update pass data
db.update_pass('pass_001', 
    holder_name='John Smith',
    pass_data={'seat': 'B10', 'gate': '2', 'match_time': '20:00'}
)

# Get passes by class
class_passes = db.get_passes_by_class('event_class_001')

# Get passes by email
user_passes = db.get_passes_by_email('john@example.com')

# Get active/expired passes
active_passes = db.get_active_passes()
expired_passes = db.get_expired_passes()

# Get pass with class information (JOIN)
full_pass_data = db.get_pass_with_class('pass_001')
print(full_pass_data)
# Includes: pass data + class_type, base_color, logo_url

# Delete a pass
db.delete_pass('pass_001')
```

### Error Handling

```python
try:
    db.create_class('test_class', 'EventTicket')
except Exception as e:
    print(f"Error: {e}")
```

## Database Maintenance

### View Tables
```bash
mysql -u wallet_user -p wallet_passes -e "SHOW TABLES;"
```

### View Table Structure
```bash
mysql -u wallet_user -p wallet_passes -e "DESCRIBE Classes_Table;"
mysql -u wallet_user -p wallet_passes -e "DESCRIBE Passes_Table;"
```

### View Data
```bash
mysql -u wallet_user -p wallet_passes -e "SELECT * FROM Classes_Table;"
mysql -u wallet_user -p wallet_passes -e "SELECT * FROM Passes_Table;"
```

### Backup Database
```bash
mysqldump -u wallet_user -p wallet_passes > backup.sql
```

### Restore Database
```bash
mysql -u wallet_user -p wallet_passes < backup.sql
```

## Notes

- All timestamps are automatically managed by MariaDB
- JSON data in `pass_data` is automatically serialized/deserialized by the DatabaseManager
- Foreign key constraints ensure data integrity
- CASCADE delete means deleting a class will automatically delete all associated passes
- The database uses UTF-8 (utf8mb4) encoding for full Unicode support
