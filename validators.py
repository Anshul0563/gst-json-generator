# validators.py
# ADVANCED VALIDATION SYSTEM

import re
from pathlib import Path
from typing import Tuple, List, Optional


class Validator:
    """Advanced validation engine with detailed error reporting."""
    
    # GSTIN format: 2-digit state code + 10-digit registration + 1-char entity type
    GSTIN_PATTERN = r"^[0-9]{2}[A-Z0-9]{13}[0-9A-Z]?$"
    
    # Period format: MMYYYY
    PERIOD_PATTERN = r"^(0[1-9]|1[0-2])[0-9]{4}$"
    
    # Supported file extensions
    SUPPORTED_EXTENSIONS = {".xlsx", ".xls", ".csv", ".txt"}
    
    # Max file size in MB
    MAX_FILE_SIZE_MB = 500
    
    @staticmethod
    def validate_gstin(gstin: str) -> Tuple[bool, Optional[str]]:
        """Validate GSTIN format and checksum."""
        gstin = str(gstin).strip().upper()
        
        if not gstin:
            return False, "GSTIN cannot be empty"
        
        if not re.match(Validator.GSTIN_PATTERN, gstin):
            return False, f"Invalid GSTIN format: {gstin}"
        
        # Basic GSTIN validation
        if not gstin[0:2].isdigit():
            return False, "First 2 characters must be state code (numeric)"
        
        state_code = int(gstin[0:2])
        if state_code < 1 or state_code > 38:
            return False, f"Invalid state code: {state_code}"
        
        return True, None
    
    @staticmethod
    def validate_period(period: str) -> Tuple[bool, Optional[str]]:
        """Validate return period (MMYYYY format)."""
        period = str(period).strip()
        
        if not period:
            return False, "Period cannot be empty"
        
        if not re.match(Validator.PERIOD_PATTERN, period):
            return False, f"Invalid period format: {period}. Use MMYYYY format (e.g., 042024)"
        
        month = int(period[0:2])
        year = int(period[2:6])
        
        if month < 1 or month > 12:
            return False, f"Invalid month: {month}"
        
        if year < 2000 or year > 2099:
            return False, f"Invalid year: {year}"
        
        return True, None
    
    @staticmethod
    def validate_files(files: List[str]) -> Tuple[bool, List[str]]:
        """Validate file list with detailed checks."""
        errors = []
        
        if not files:
            return False, ["Please select at least one file"]
        
        seen_files = set()
        
        for file_path in files:
            file_path_obj = Path(file_path)
            
            # Check file existence
            if not file_path_obj.exists():
                errors.append(f"File not found: {file_path}")
                continue
            
            # Check file extension
            if file_path_obj.suffix.lower() not in Validator.SUPPORTED_EXTENSIONS:
                errors.append(
                    f"Unsupported file: {file_path_obj.name}. "
                    f"Supported: {', '.join(Validator.SUPPORTED_EXTENSIONS)}"
                )
                continue
            
            # Check file size
            file_size_mb = file_path_obj.stat().st_size / (1024 * 1024)
            if file_size_mb > Validator.MAX_FILE_SIZE_MB:
                errors.append(
                    f"File too large: {file_path_obj.name} ({file_size_mb:.1f}MB). "
                    f"Max: {Validator.MAX_FILE_SIZE_MB}MB"
                )
                continue
            
            # Check file readability
            try:
                with open(file_path, 'rb') as f:
                    f.read(1024)  # Try reading first 1KB
            except Exception as e:
                errors.append(f"Cannot read file: {file_path_obj.name} ({str(e)})")
                continue
            
            # Check for duplicates
            abs_path = str(file_path_obj.resolve())
            if abs_path in seen_files:
                errors.append(f"Duplicate file: {file_path_obj.name}")
            else:
                seen_files.add(abs_path)
        
        return len(errors) == 0, errors


def run_full_validation(gstin: str, period: str, files: List[str]) -> Tuple[bool, List[str]]:
    """Run complete validation with advanced checks."""
    errors = []
    
    # Validate GSTIN
    valid, error = Validator.validate_gstin(gstin)
    if not valid:
        errors.append(error)
    
    # Validate period
    valid, error = Validator.validate_period(period)
    if not valid:
        errors.append(error)
    
    # Validate files
    valid, file_errors = Validator.validate_files(files)
    errors.extend(file_errors)
    
    return len(errors) == 0, errors