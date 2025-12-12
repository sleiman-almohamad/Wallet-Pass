-- MariaDB Database Schema for Wallet Passes
-- This schema defines the structure for managing Google Wallet pass classes and instances

-- Create database (optional - uncomment if needed)
-- CREATE DATABASE IF NOT EXISTS wallet_passes CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- USE wallet_passes;

-- ============================================================================
-- Classes_Table: Stores Google Wallet pass class definitions
-- ============================================================================
CREATE TABLE IF NOT EXISTS Classes_Table (
    class_id VARCHAR(255) PRIMARY KEY COMMENT 'Unique identifier for the pass class',
    class_type VARCHAR(100) NOT NULL COMMENT 'Type of pass (e.g., EventTicket, LoyaltyCard)',
    base_color VARCHAR(7) COMMENT 'Hex color code for the pass (e.g., #FF5733)',
    logo_url VARCHAR(500) COMMENT 'URL to the class logo image',
    issuer_name VARCHAR(255) COMMENT 'Name of the issuer/business',
    header_text VARCHAR(255) COMMENT 'Header text for the pass',
    card_title VARCHAR(255) COMMENT 'Card title for the pass',
    class_json JSON COMMENT 'Complete Google Wallet class JSON configuration',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation timestamp',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Record last update timestamp',
    
    INDEX idx_class_type (class_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Stores Google Wallet pass class definitions';

-- ============================================================================
-- Passes_Table: Stores individual pass instances
-- ============================================================================
CREATE TABLE IF NOT EXISTS Passes_Table (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Auto-incrementing primary key',
    object_id VARCHAR(255) UNIQUE NOT NULL COMMENT 'Unique identifier for the pass object',
    class_id VARCHAR(255) NOT NULL COMMENT 'Reference to the pass class',
    holder_name VARCHAR(255) NOT NULL COMMENT 'Name of the pass holder',
    holder_email VARCHAR(255) NOT NULL COMMENT 'Email of the pass holder',
    status ENUM('Active', 'Expired') DEFAULT 'Active' NOT NULL COMMENT 'Current status of the pass',
    pass_data JSON COMMENT 'Flexible JSON data (seat, gate, match_time, etc.)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation timestamp',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Record last update timestamp',
    
    -- Foreign key constraint
    CONSTRAINT fk_passes_class_id 
        FOREIGN KEY (class_id) 
        REFERENCES Classes_Table(class_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    
    -- Indexes for performance
    INDEX idx_class_id (class_id),
    INDEX idx_status (status),
    INDEX idx_holder_email (holder_email),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Stores individual pass instances';

-- ============================================================================
-- Sample Data (optional - for testing purposes)
-- ============================================================================
-- Uncomment the following lines to insert sample data

-- INSERT INTO Classes_Table (class_id, class_type, base_color, logo_url) VALUES
-- ('event_class_001', 'EventTicket', '#FF5733', 'https://example.com/logos/event.png'),
-- ('loyalty_class_001', 'LoyaltyCard', '#3498DB', 'https://example.com/logos/loyalty.png');

-- INSERT INTO Passes_Table (object_id, class_id, holder_name, holder_email, status, pass_data) VALUES
-- ('pass_001', 'event_class_001', 'John Doe', 'john@example.com', 'Active', 
--  '{"seat": "A5", "gate": "3", "match_time": "20:00"}'),
-- ('pass_002', 'event_class_001', 'Jane Smith', 'jane@example.com', 'Active',
--  '{"seat": "B12", "gate": "2", "match_time": "20:00"}'),
-- ('pass_003', 'loyalty_class_001', 'Bob Johnson', 'bob@example.com', 'Active',
--  '{"points": 1500, "tier": "Gold", "member_since": "2024-01-15"}');
