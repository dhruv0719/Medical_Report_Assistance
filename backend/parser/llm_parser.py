# backend/parser/llm_parser.py
"""
LLM-based parser for extracting structured data from messy OCR text.
This acts as a fallback when the regex parser fails.
"""

from typing import List, Optional
import json
from backend.llm.groq_client import GroqClient
from backend.parser.entities import LabTest, ParsedReport, ReportType, create_lab_test
from config.logging_config import get_logger
from backend.parser.normalizer import TextNormalizer

logger = get_logger(__name__)

class LLMParser:
    """Uses an LLM to parse raw text into a ParsedReport object."""

    def __init__(self):
        self.llm_client = GroqClient()
        self.normalizer = TextNormalizer()
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """Builds the system prompt with instructions for the LLM."""
        return """
You are an expert medical data extraction assistant. Your task is to extract structured information from the raw text of a medical lab report, which may contain OCR errors.

You MUST extract the following information and format it as a JSON object.
- patient_id: The patient's Medical Record Number (MRN) or Patient ID.
- report_date: The date the report was generated or the sample was collected.
- report_type: The name of the test panel (e.g., "Complete Blood Count", "Lipid Panel").
- lab_name: The name of the laboratory that performed the test.
- impression: The clinical impression or summary section of the report.
- tests: A list of all individual lab tests.

Each item in the 'tests' list must be a JSON object with these exact keys:
- "name": The full name of the test (e.g., "Hemoglobin", "White Blood Cell Count").
- "value": The result value as a string (e.g., "12.5", "9000").
- "unit": The unit of measurement (e.g., "g/dL", "cumm").
- "reference_range": The normal range as a string (e.g., "13.0-17.0", "4000-11000").
- "flag": Any flag indicating high or low, like "Low", "High", or "H", "L". If none, use an empty string.

IMPORTANT RULES:
1.  **BE ACCURATE**: Do not invent data. If a field is missing, use null or an empty string.
2.  **HANDLE OCR ERRORS**: Correct obvious OCR mistakes (e.g., '$' instead of '4').
3.  **JSON ONLY**: Your entire response MUST be a single, valid JSON object and nothing else. Do not include any explanatory text before or after the JSON.
4.  **COMPLETE LIST**: Extract ALL tests listed in the report.
"""

    def parse(self, raw_text: str) -> Optional[ParsedReport]:
        """
        Parses the raw text using the LLM.
        
        Args:
            raw_text: The raw text from the document.
            
        Returns:
            A ParsedReport object, or None if parsing fails.
        """
        logger.info("Attempting to parse report using LLM fallback...")
        user_prompt = f"Here is the lab report text:\n\n---\n{raw_text}\n---"

        try:
            # Use JSON mode if available, or instruct the LLM
            response_text = self.llm_client.complete(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.0, # Be deterministic
                max_tokens=4096, # Allow for long reports
                # For OpenAI, you'd add: response_format={"type": "json_object"}
            )

            # Clean up the response to ensure it's valid JSON
            json_str = self._extract_json_from_response(response_text)
            parsed_data = json.loads(json_str)

            return self._create_report_from_json(parsed_data, raw_text)

        except Exception as e:
            logger.error(f"LLM parsing failed: {e}")
            return None

    def _extract_json_from_response(self, text: str) -> str:
        """Finds and extracts the JSON block from the LLM's response."""
        # Find the start and end of the JSON object
        start_index = text.find('{')
        end_index = text.rfind('}')
        
        if start_index != -1 and end_index != -1:
            return text[start_index : end_index + 1]
        
        raise ValueError("No valid JSON object found in the LLM response.")

    def _create_report_from_json(self, data: dict, raw_text: str) -> ParsedReport:
        """Converts the parsed JSON data into a ParsedReport object."""
        tests: List[LabTest] = []
        for test_data in data.get("tests", []):
            try:
                # Normalize units and names from LLM output
                test = create_lab_test(
                    name=self.normalizer.normalize_test_name(test_data.get("name", "")),
                    value=str(test_data.get("value", "")),
                    unit=self.normalizer.normalize_units(test_data.get("unit", "")),
                    reference_range=test_data.get("reference_range", ""),
                    flag=test_data.get("flag", None)
                )
                tests.append(test)
            except Exception as e:
                logger.warning(f"Skipping invalid test data from LLM: {test_data}. Error: {e}")

        report_type_str = data.get("report_type", "Unknown").lower()
        report_type = ReportType.UNKNOWN
        if "cbc" in report_type_str or "complete blood count" in report_type_str:
            report_type = ReportType.CBC
        
        report = ParsedReport(
            patient_id=data.get("patient_id"),
            report_date=data.get("report_date"),
            report_type=report_type,
            lab_name=data.get("lab_name"),
            tests=tests,
            impression=data.get("impression", ""),
            raw_text=raw_text,
        )
        logger.info(f"LLM successfully parsed {len(tests)} tests from the report.")
        return report