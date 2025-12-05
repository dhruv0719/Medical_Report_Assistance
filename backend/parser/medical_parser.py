# backend/parser/medical_parser.py
"""
Main medical report parser.
Extracts structured data from normalized text.
"""

from typing import List, Optional
from config.logging_config import get_logger
from backend.parser.entities import LabTest, ParsedReport, ReportType, create_lab_test
from backend.parser.patterns import (
    PATIENT_ID_PATTERNS,
    DATE_PATTERNS,
    LAB_NAME_PATTERNS,
    LAB_TEST_PATTERNS,
    IMPRESSION_PATTERNS,
    extract_with_pattern,
    find_all_matches,
)
from backend.parser.normalizer import TextNormalizer
from backend.parser.llm_parser import LLMParser

logger = get_logger(__name__)

class MedicalReportParser:
    """Parses medical reports and extracts structured data"""
    
    def __init__(self):
        self.normalizer = TextNormalizer()
        self.llm_parser = LLMParser()

    def parse(self, raw_text: str) -> ParsedReport:
        """
        Parse a medical report from raw text.
        
        Args:
            raw_text: Extracted text from document
            
        Returns:
            ParsedReport with structured data
        """
        logger.info("Starting report parsing...")
        
        # Normalize text
        normalized_text = self.normalizer.normalize(raw_text)
        
        # Extract metadata
        patient_id = self._extract_patient_id(normalized_text)
        report_date = self._extract_date(normalized_text)
        lab_name = self._extract_lab_name(normalized_text)
        report_type = self._determine_report_type(normalized_text)
        
        # Extract tests
        tests = self._extract_tests(normalized_text)
        
        # Extract impression
        impression = self._extract_impression(normalized_text)
        
        if len(tests) >= 3:
            logger.info(f"Regex parser succeeded, found {len(tests)} tests.")
            # Create report
            report = ParsedReport(
                patient_id=patient_id,
                report_date=report_date,
                report_type=report_type,
                lab_name=lab_name,
                tests=tests,
                impression=impression,
                raw_text=raw_text,
                metadata={}
            )
            logger.info(f"Parsing complete: {len(tests)} tests extracted.")
            return report
    
        logger.warning(f"Regex parser found only {len(tests)} tests. Falling back to LLM parser.")
        llm_report = self.llm_parser.parse(raw_text)

        if llm_report:
            return llm_report
        else:
            # If even LLM fails, return the partial regex result
            logger.error("LLM parser also failed. Returning partial data from regex.")
            return ParsedReport(raw_text=raw_text, tests=tests)
    
    def _extract_patient_id(self, text: str) -> Optional[str]:
        """Extract patient ID"""
        patient_id = extract_with_pattern(text, PATIENT_ID_PATTERNS)
        return patient_id if patient_id else None
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Extract report date"""
        date = extract_with_pattern(text, DATE_PATTERNS)
        return date if date else None
    
    def _extract_lab_name(self, text: str) -> Optional[str]:
        """Extract performing laboratory name"""
        lab = extract_with_pattern(text, LAB_NAME_PATTERNS)
        return lab if lab else None
    
    def _determine_report_type(self, text: str) -> ReportType:
        """Determine type of report based on content"""
        text_lower = text.lower()
        
        if 'complete blood count' in text_lower or 'cbc' in text_lower:
            return ReportType.CBC
        elif 'basic metabolic' in text_lower or 'bmp' in text_lower:
            return ReportType.BMP
        elif 'comprehensive metabolic' in text_lower or 'cmp' in text_lower:
            return ReportType.CMP
        elif 'lipid panel' in text_lower:
            return ReportType.LIPID_PANEL
        elif 'thyroid' in text_lower:
            return ReportType.THYROID
        elif 'liver function' in text_lower or 'lft' in text_lower:
            return ReportType.LIVER_FUNCTION
        else:
            return ReportType.UNKNOWN
    
    def _extract_tests(self, text: str) -> List[LabTest]:
        """Extract all lab test results (robust parsing + clearer logging)."""
        tests: List[LabTest] = []
        seen_tests = set()  # Avoid duplicates

        # Find all matches across patterns
        all_matches = find_all_matches(text, LAB_TEST_PATTERNS)

        for m in all_matches:
            # Normalize match object: some helpers may return raw tuples instead of re.Match
            if hasattr(m, "groups"):
                match_obj = m
            else:
                class _MatchWrapper:
                    def __init__(self, groups):
                        self._groups = tuple(groups)
                    def groups(self):
                        return self._groups
                    def __repr__(self):
                        return f"_MatchWrapper({self._groups!r})"

                match_obj = _MatchWrapper(m)

            try:
                test = self._parse_test_match(match_obj)
            except Exception as exc:
                # Ensure message is always formatted (use f-string) and include traceback
                logger.exception(f"Exception while parsing test match: {match_obj!r}")
                continue

            if not test:
                logger.debug(f"Skipped non-matching/empty test for match: {match_obj!r}")
                continue

            # de-duplicate by (name, value)
            name_key = (getattr(test, "name", "") or "").lower()
            value_key = str(getattr(test, "value", "") or "")
            key = (name_key, value_key)
            if key in seen_tests:
                logger.debug(f"Duplicate test skipped: {key}")
                continue

            seen_tests.add(key)
            tests.append(test)

        return tests
    
    def _parse_test_match(self, match) -> Optional[LabTest]:
        """Parse a single test from regex match"""
        groups = match.groups()
        
        logger.debug(f"Parsing match with {len(groups)} groups: {groups}")
        
        # Need at least name, value, unit/range
        if len(groups) < 4:
            logger.debug(f"Insufficient groups, skipping")
            return None
        
        # Extract components
        name = groups[0].strip() if groups[0] else None
        value = groups[1].strip() if groups[1] else None
        
        if not name or not value:
            logger.debug(f"Missing name or value")
            return None
        
        # Normalize name
        name = self.normalizer.normalize_test_name(name)
        
        # groups[2] is unit, groups[3] is range
        unit = self.normalizer.normalize_units(groups[2]) if groups[2] else ""
        reference_range = groups[3].strip() if groups[3] else ""
        
        # groups[4] is optional flag
        flag = groups[4].strip().upper() if len(groups) > 4 and groups[4] else None
        
        # Create test
        try:
            test = create_lab_test(
                name=name,
                value=value,
                unit=unit,
                reference_range=reference_range,
                flag=flag
            )
            logger.debug(f"✅ Created test: {name} = {value} {unit}")
            return test
        except Exception as e:
            logger.warning(f"Failed to create test from {name}={value}: {str(e)}")
            return None
    
    def _extract_impression(self, text: str) -> str:
        """Extract clinical impression/conclusion"""
        impression = extract_with_pattern(text, IMPRESSION_PATTERNS)
        return impression if impression else ""


__all__ = [
    "MedicalReportParser",
]