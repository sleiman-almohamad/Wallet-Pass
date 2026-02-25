-- MariaDB Database Schema for Wallet Passes - RELATIONAL V2
-- This schema defines the structure for managing Google Wallet pass classes and instances

-- ============================================================================
-- Classes_Table: Stores Google Wallet pass class definitions (common fields)
-- ============================================================================
CREATE TABLE IF NOT EXISTS Classes_Table (
    class_id VARCHAR(255) PRIMARY KEY COMMENT 'Unique identifier for the pass class (suffix only)',
    class_type VARCHAR(100) NOT NULL COMMENT 'Type of pass (e.g., EventTicket, LoyaltyCard, Generic, GiftCard, TransitPass)',
    issuer_name VARCHAR(255) DEFAULT NULL COMMENT 'Name of the issuer/business',
    base_color VARCHAR(50) DEFAULT NULL COMMENT 'hexBackgroundColor',
    logo_url TEXT DEFAULT NULL COMMENT 'logo.sourceUri.uri or programLogo.sourceUri.uri',
    hero_image_url TEXT DEFAULT NULL COMMENT 'heroImage.sourceUri.uri',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation timestamp',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Record last update timestamp',
    
    INDEX idx_class_type (class_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Stores Google Wallet pass class definitions';

-- ============================================================================
-- GenericClass_Fields: Fields specific to Generic pass classes
-- ============================================================================
CREATE TABLE IF NOT EXISTS GenericClass_Fields (
    class_id VARCHAR(255) PRIMARY KEY,
    header VARCHAR(255) COMMENT 'header.defaultValue.value',
    card_title VARCHAR(255) COMMENT 'cardTitle.defaultValue.value',
    
    CONSTRAINT fk_generic_class
        FOREIGN KEY (class_id)
        REFERENCES Classes_Table(class_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- EventTicketClass_Fields: Fields specific to EventTicket pass classes
-- ============================================================================
CREATE TABLE IF NOT EXISTS EventTicketClass_Fields (
    class_id VARCHAR(255) PRIMARY KEY,
    event_name VARCHAR(255) COMMENT 'eventName.defaultValue.value',
    venue_name VARCHAR(255) COMMENT 'venue.name.defaultValue.value',
    venue_address VARCHAR(500) COMMENT 'venue.address.defaultValue.value',
    event_start VARCHAR(50) COMMENT 'dateTime.start',
    
    CONSTRAINT fk_event_ticket_class
        FOREIGN KEY (class_id)
        REFERENCES Classes_Table(class_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- LoyaltyClass_Fields: Fields specific to LoyaltyCard pass classes
-- ============================================================================
CREATE TABLE IF NOT EXISTS LoyaltyClass_Fields (
    class_id VARCHAR(255) PRIMARY KEY,
    program_name VARCHAR(255) COMMENT 'localizedProgramName.defaultValue.value',
    
    CONSTRAINT fk_loyalty_class
        FOREIGN KEY (class_id)
        REFERENCES Classes_Table(class_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- TransitClass_Fields: Fields specific to TransitPass pass classes
-- ============================================================================
CREATE TABLE IF NOT EXISTS TransitClass_Fields (
    class_id VARCHAR(255) PRIMARY KEY,
    transit_type VARCHAR(100) COMMENT 'transitType (e.g. TRANSIT_TYPE_BUS)',
    transit_operator_name VARCHAR(255) COMMENT 'transitOperatorName.defaultValue.value',
    
    CONSTRAINT fk_transit_class
        FOREIGN KEY (class_id)
        REFERENCES Classes_Table(class_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- Passes_Table: Stores individual pass instances (common fields)
-- ============================================================================
CREATE TABLE IF NOT EXISTS Passes_Table (
    object_id VARCHAR(255) PRIMARY KEY COMMENT 'Unique identifier for the pass object (suffix only)',
    class_id VARCHAR(255) NOT NULL COMMENT 'Reference to the pass class',
    holder_name VARCHAR(255) NOT NULL COMMENT 'Name of the pass holder',
    holder_email VARCHAR(255) NOT NULL COMMENT 'Email of the pass holder',
    status ENUM('Active', 'Expired') DEFAULT 'Active' NOT NULL COMMENT 'Current status of the pass',
    sync_status ENUM('synced', 'pending', 'failed') DEFAULT 'pending' COMMENT 'Sync status with Google Wallet',
    last_synced_at TIMESTAMP NULL COMMENT 'When the pass was last synced to Google Wallet',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation timestamp',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Record last update timestamp',
    
    -- Foreign key constraint
    CONSTRAINT fk_passes_class_id 
        FOREIGN KEY (class_id) 
        REFERENCES Classes_Table(class_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    
    -- One pass per person per class
    UNIQUE KEY unique_class_holder (class_id, holder_email),
    
    -- Indexes for performance
    INDEX idx_class_id (class_id),
    INDEX idx_status (status),
    INDEX idx_holder_email (holder_email),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Stores individual pass instances';

-- ============================================================================
-- EventTicket_Fields: scalar fields specific to Event Tickets
-- ============================================================================
CREATE TABLE IF NOT EXISTS EventTicket_Fields (
    object_id VARCHAR(255) PRIMARY KEY,
    ticket_holder_name VARCHAR(255),
    confirmation_code VARCHAR(255),
    seat VARCHAR(255),
    section VARCHAR(255),
    gate VARCHAR(255),
    
    CONSTRAINT fk_event_ticket_pass 
        FOREIGN KEY (object_id) 
        REFERENCES Passes_Table(object_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- Generic_Fields: scalar fields specific to Generic passes
-- ============================================================================
CREATE TABLE IF NOT EXISTS Generic_Fields (
    object_id VARCHAR(255) PRIMARY KEY,
    header_value VARCHAR(255),
    subheader_value VARCHAR(255),
    
    CONSTRAINT fk_generic_pass 
        FOREIGN KEY (object_id) 
        REFERENCES Passes_Table(object_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- Pass_Text_Modules: array of text modules
-- ============================================================================
CREATE TABLE IF NOT EXISTS Pass_Text_Modules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    object_id VARCHAR(255) NOT NULL,
    module_id VARCHAR(255),
    header VARCHAR(255),
    body TEXT,
    display_order INT DEFAULT 0,
    
    CONSTRAINT fk_text_module_pass 
        FOREIGN KEY (object_id) 
        REFERENCES Passes_Table(object_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
        
    INDEX idx_text_module_object (object_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- Pass_Messages: array of messages
-- ============================================================================
CREATE TABLE IF NOT EXISTS Pass_Messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    object_id VARCHAR(255) NOT NULL,
    message_id VARCHAR(255),
    header VARCHAR(255),
    body TEXT,
    message_type VARCHAR(100),
    start_date VARCHAR(100),
    end_date VARCHAR(100),
    
    CONSTRAINT fk_message_pass 
        FOREIGN KEY (object_id) 
        REFERENCES Passes_Table(object_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
        
    INDEX idx_message_object (object_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- Notifications_Table: historical table
-- ============================================================================
CREATE TABLE IF NOT EXISTS Notifications_Table (
    id INT AUTO_INCREMENT PRIMARY KEY,
    class_id VARCHAR(255),
    object_id VARCHAR(255),
    event_type ENUM('class_update', 'pass_update', 'custom_message') DEFAULT 'custom_message',
    status ENUM('Sent', 'Failed') NOT NULL,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_notif_class (class_id),
    INDEX idx_notif_object (object_id),
    INDEX idx_notif_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
