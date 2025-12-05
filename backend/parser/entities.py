# backend/parser/entities.py
"""
Data classes for representing parsed medical report entities.
These are the core data structures used throughout the application.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class TestStatus(Enum):
    """Status of a lab test result"""
    NORMAL = "normal"
    ABNORMAL_LOW = "abnormal_low"
    ABNORMAL_HIGH = "abnormal_high"
    CRITICAL_LOW = "critical_low"
    CRITICAL_HIGH = "critical_high"
    UNKNOWN = "unknown"


class ReportType(Enum):
    """Type of medical report"""
    CBC = "Complete Blood Count"
    BMP = "Basic Metabolic Panel"
    CMP = "Comprehensive Metabolic Panel"
    LIPID_PANEL = "Lipid Panel"
    THYROID = "Thyroid Function"
    LIVER_FUNCTION = "Liver Function Tests"
    UNKNOWN = "Unknown"


@dataclass
class LabTest:
    """
    Represents a single laboratory test result.
    
    Attributes:
        name: Test name (e.g., "Hemoglobin")
        value: Numeric or text value
        unit: Unit of measurement (e.g., "g/dL")
        reference_range: Normal range (e.g., "13.0-17.0")
        is_abnormal: Whether the value is outside normal range
        status: Classification of the result
        flag: Lab flag ('H', 'L', 'HH', 'LL', None)
        timestamp: When this test was performed
    """
    name: str
    value: str
    unit: str
    reference_range: str
    is_abnormal: bool = False
    status: TestStatus = TestStatus.UNKNOWN
    flag: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate and normalize data after initialization"""
        # Normalize name
        self.name = self.name.strip()
        
        # Normalize unit
        self.unit = self.unit.strip()
        
        # Determine status if not set
        if self.status == TestStatus.UNKNOWN and self.is_abnormal:
            if self.flag:
                if self.flag in ['H', 'HH']:
                    self.status = TestStatus.CRITICAL_HIGH if self.flag == 'HH' else TestStatus.ABNORMAL_HIGH
                elif self.flag in ['L', 'LL']:
                    self.status = TestStatus.CRITICAL_LOW if self.flag == 'LL' else TestStatus.ABNORMAL_LOW
        elif not self.is_abnormal:
            self.status = TestStatus.NORMAL
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['status'] = self.status.value
        if self.timestamp:
            data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def get_numeric_value(self) -> Optional[float]:
        """
        Extract numeric value from the value string.
        Returns None if not numeric.
        """
        try:
            # Handle ranges (take first value)
            if '-' in self.value:
                self.value = self.value.split('-')[0]
            
            # Remove common non-numeric characters
            clean_value = self.value.replace(',', '').replace('>', '').replace('<', '').strip()
            return float(clean_value)
        except (ValueError, AttributeError):
            return None
    
    def get_reference_low_high(self) -> tuple[Optional[float], Optional[float]]:
        """
        Parse reference range into low and high values.
        Returns (low, high) or (None, None) if parsing fails.
        """
        try:
            # Handle formats like "13.0-17.0" or "13.0 - 17.0"
            range_clean = self.reference_range.replace(' ', '')
            if '-' in range_clean:
                low, high = range_clean.split('-')
                return float(low), float(high)
        except (ValueError, AttributeError):
            pass
        
        return None, None
    
    def is_critical(self) -> bool:
        """Check if this is a critical value"""
        return self.status in [TestStatus.CRITICAL_LOW, TestStatus.CRITICAL_HIGH]


@dataclass
class ParsedReport:
    """
    Represents a complete parsed medical report.
    
    Attributes:
        patient_id: Patient identifier (anonymized)
        report_date: Date of the report
        report_type: Type of test panel
        lab_name: Laboratory that performed the tests
        tests: List of individual test results
        impression: Clinical impression/conclusion from the report
        raw_text: Original text content
        metadata: Additional metadata
    """
    patient_id: Optional[str] = None
    report_date: Optional[str] = None
    report_type: ReportType = ReportType.UNKNOWN
    lab_name: Optional[str] = None
    tests: List[LabTest] = field(default_factory=list)
    impression: str = ""
    raw_text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization processing"""
        # Ensure tests is a list
        if not isinstance(self.tests, list):
            self.tests = []
        
        # Set default metadata
        if 'parsed_at' not in self.metadata:
            self.metadata['parsed_at'] = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'patient_id': self.patient_id,
            'report_date': self.report_date,
            'report_type': self.report_type.value,
            'lab_name': self.lab_name,
            'tests': [test.to_dict() for test in self.tests],
            'impression': self.impression,
            'metadata': self.metadata,
        }
    
    def get_abnormal_tests(self) -> List[LabTest]:
        """Return list of abnormal tests"""
        return [test for test in self.tests if test.is_abnormal]
    
    def get_critical_tests(self) -> List[LabTest]:
        """Return list of critical tests"""
        return [test for test in self.tests if test.is_critical()]
    
    def get_normal_tests(self) -> List[LabTest]:
        """Return list of normal tests"""
        return [test for test in self.tests if not test.is_abnormal]
    
    def has_critical_values(self) -> bool:
        """Check if report contains any critical values"""
        return len(self.get_critical_tests()) > 0
    
    def get_test_by_name(self, name: str) -> Optional[LabTest]:
        """
        Find a test by name (case-insensitive).
        
        Args:
            name: Test name to search for
            
        Returns:
            LabTest if found, None otherwise
        """
        name_lower = name.lower()
        for test in self.tests:
            if test.name.lower() == name_lower:
                return test
        return None
    
    def summary(self) -> str:
        """Generate a text summary of the report"""
        total = len(self.tests)
        abnormal = len(self.get_abnormal_tests())
        critical = len(self.get_critical_tests())
        
        return (
            f"Report Type: {self.report_type.value}\n"
            f"Total Tests: {total}\n"
            f"Normal: {total - abnormal}\n"
            f"Abnormal: {abnormal}\n"
            f"Critical: {critical}\n"
            f"Date: {self.report_date or 'Unknown'}"
        )


@dataclass
class ExtractionMetadata:
    """
    Metadata about the document extraction process.
    
    Attributes:
        filename: Original filename
        file_type: Type of file (pdf, txt)
        file_size_bytes: Size in bytes
        extraction_method: How text was extracted ('text', 'ocr')
        page_count: Number of pages
        extraction_time_seconds: Time taken for extraction
        ocr_confidence: OCR confidence score (0-100) if applicable
    """
    filename: str
    file_type: str
    file_size_bytes: int
    extraction_method: str
    page_count: int = 1
    extraction_time_seconds: Optional[float] = None
    ocr_confidence: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_lab_test(
    name: str,
    value: str,
    unit: str,
    reference_range: str,
    flag: Optional[str] = None
) -> LabTest:
    """
    Factory function to create a LabTest with automatic abnormality detection.
    
    Args:
        name: Test name
        value: Test value
        unit: Unit of measurement
        reference_range: Normal range
        flag: Optional lab flag
        
    Returns:
        LabTest instance
    """
    test = LabTest(
        name=name,
        value=value,
        unit=unit,
        reference_range=reference_range,
        flag=flag
    )
    
    # Automatically detect if abnormal
    numeric_value = test.get_numeric_value()
    low, high = test.get_reference_low_high()
    
    if numeric_value is not None and low is not None and high is not None:
        test.is_abnormal = numeric_value < low or numeric_value > high
        
        if test.is_abnormal:
            if numeric_value < low:
                test.status = TestStatus.ABNORMAL_LOW
            else:
                test.status = TestStatus.ABNORMAL_HIGH
    
    return test


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "LabTest",
    "ParsedReport",
    "ExtractionMetadata",
    "TestStatus",
    "ReportType",
    "create_lab_test",
]