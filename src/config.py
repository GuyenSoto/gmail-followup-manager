# src/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Centralized application configuration"""
    
    # Main paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / os.getenv('DATA_DIR', 'data')
    EXPORTS_DIR = BASE_DIR / os.getenv('EXPORTS_DIR', 'data/exports')
    CREDENTIALS_FILE = BASE_DIR / os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
    
    # Google APIs Configuration
    GMAIL_SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly'#,'https://www.googleapis.com/auth/gmail.modify'
    ]
    
    CALENDAR_SCOPES = [
        'https://www.googleapis.com/auth/calendar.events',
        'https://www.googleapis.com/auth/calendar.readonly'
    ]
    
    # Application settings
    APP_NAME = os.getenv('APP_NAME', 'Gmail Follow-up Manager')
    DEFAULT_LOOKBACK_DAYS = int(os.getenv('DEFAULT_LOOKBACK_DAYS', '30'))
    MAX_RESULTS = int(os.getenv('MAX_RESULTS', '1000'))
    
    # UI Configuration
    PAGE_TITLE = os.getenv('PAGE_TITLE', 'Gmail Follow-up Manager')
    PAGE_ICON = os.getenv('PAGE_ICON', '📧')
    LAYOUT = os.getenv('LAYOUT', 'wide')
    
    # Default configurations
    DEFAULT_KEYWORDS = 'interview,follow up,proposal,meeting,quotation'
    DEFAULT_REMINDER_TIME = '09:00'
    DEFAULT_TIMEZONE = 'America/New_York'
    
    # Backup configurations
    MAX_BACKUPS = int(os.getenv('MAX_BACKUPS', '10'))
    AUTO_BACKUP = os.getenv('AUTO_BACKUP', 'true').lower() == 'true'
    
    # Network configurations
    OAUTH_PORT_GMAIL = int(os.getenv('OAUTH_PORT_GMAIL', '8080'))
    OAUTH_PORT_CALENDAR = int(os.getenv('OAUTH_PORT_CALENDAR', '8081'))
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist"""
        directories = [cls.DATA_DIR, cls.EXPORTS_DIR]
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                print(f"✅ Directory ensured: {directory}")
            except Exception as e:
                print(f"❌ Error creating directory {directory}: {e}")
                raise
    
    @classmethod
    def validate_setup(cls) -> dict:
        """Validates that the configuration is correct"""
        validation_results = {
            'credentials_file': cls.CREDENTIALS_FILE.exists(),
            'data_directory': cls.DATA_DIR.exists(),
            'exports_directory': cls.EXPORTS_DIR.exists(),
            'environment_loaded': os.getenv('DATA_DIR') is not None
        }
        
        return validation_results
    
    @classmethod
    def get_environment_info(cls) -> dict:
        """Gets environment information"""
        return {
            'base_dir': str(cls.BASE_DIR),
            'data_dir': str(cls.DATA_DIR),
            'exports_dir': str(cls.EXPORTS_DIR),
            'credentials_file': str(cls.CREDENTIALS_FILE),
            'credentials_exists': cls.CREDENTIALS_FILE.exists(),
            'app_name': cls.APP_NAME,
            'default_lookback_days': cls.DEFAULT_LOOKBACK_DAYS,
            'max_results': cls.MAX_RESULTS,
            'auto_backup': cls.AUTO_BACKUP
        }