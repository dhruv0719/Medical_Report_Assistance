# backend/orchestrator/pipeline.py
"""
Main pipeline orchestrator - coordinates all components.
This is the primary interface for processing medical reports end-to-end.
"""

from pathlib import Path
from typing import Optional, Dict
from dataclasses import dataclass, asdict
import time

from backend.ingestion.document_processor import DocumentProcessor
from backend.parser.medical_parser import MedicalReportParser
from backend.parser.entities import ParsedReport
from backend.safety.triage_engine import TriageEngine
from backend.safety.alerts import TriageResult
from backend.safety.next_steps import NextStepsGenerator
from backend.llm.explainer import MedicalExplainer, Explanation
from backend.audit.audit_logger import AuditLogger
from config.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class PipelineResult:
    """Complete result from the medical report pipeline"""
    
    # Input
    filename: str
    file_hash: str
    
    # Extracted data
    extracted_text: str
    extraction_metadata: dict
    
    # Parsed data
    parsed_report: ParsedReport
    
    # Safety triage
    triage_result: TriageResult
    
    # LLM explanations
    explanations: Dict[str, Explanation]
    
    # Audit
    session_id: str
    processing_time: float
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'filename': self.filename,
            'file_hash': self.file_hash,
            'extraction': {
                'text_length': len(self.extracted_text),
                'method': self.extraction_metadata.get('extraction_method'),
                'pages': self.extraction_metadata.get('page_count', 1)
            },
            'parsed': self.parsed_report.to_dict(),
            'triage': self.triage_result.to_dict(),
            'explanations': {
                name: {
                    'text': exp.explanation_text,
                    'sources': exp.sources_used,
                    'is_abnormal': exp.is_abnormal,
                    'is_critical': exp.is_critical
                }
                for name, exp in self.explanations.items()
            },
            'session_id': self.session_id,
            'processing_time': self.processing_time
        }


class MedicalReportPipeline:
    """
    Complete medical report processing pipeline.
    
    Coordinates: Ingestion → Parsing → Triage → RAG → LLM → Audit
    """
    
    def __init__(
        self,
        enable_llm: bool = True,
        enable_audit: bool = True
    ):
        """
        Initialize pipeline with all components.
        
        Args:
            enable_llm: Whether to generate LLM explanations
            enable_audit: Whether to log to audit database
        """
        self.enable_llm = enable_llm
        self.enable_audit = enable_audit
        
        # Initialize components
        logger.info("Initializing pipeline components...")
        
        self.document_processor = DocumentProcessor()
        self.parser = MedicalReportParser()
        self.triage_engine = TriageEngine()
        
        if self.enable_llm:
            self.explainer = MedicalExplainer()
        
        if self.enable_audit:
            self.audit_logger = AuditLogger()
        
        logger.info("✅ Pipeline initialized")
    
    def process_file(self, file_path: Path) -> PipelineResult:
        """
        Process a medical report file end-to-end.
        
        Args:
            file_path: Path to report file
            
        Returns:
            Complete pipeline result
        """
        start_time = time.time()
        
        logger.info(f"="*60)
        logger.info(f"Processing: {file_path.name}")
        logger.info(f"="*60)
        
        try:
            # STEP 1: Ingestion & Extraction
            logger.info("STEP 1: Document extraction...")
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # document_processor.process returns (text, metadata) tuple
            extracted_text, extraction_metadata = self.document_processor.process(
                file_path.name,
                file_content
            )
            
            if self.enable_audit:
                from backend.ingestion.validators import FileValidator
                validator = FileValidator()
                file_hash = validator.get_file_hash(file_content)
                self.audit_logger.log_upload(file_path.name, file_hash, len(file_content))
                self.audit_logger.log_extraction(
                    extraction_metadata.extraction_method,
                    len(extracted_text),
                    extraction_metadata.extraction_time_seconds or 0
                )
            else:
                file_hash = "no-audit"
            
            # STEP 2: Parse medical report
            logger.info("STEP 2: Parsing medical data...")
            parsed_report = self.parser.parse(extracted_text)
            
            if self.enable_audit:
                self.audit_logger.log_parse(
                    len(parsed_report.tests),
                    len(parsed_report.get_abnormal_tests())
                )
            
            # STEP 3: Safety triage
            logger.info("STEP 3: Safety triage...")
            triage_result = self.triage_engine.evaluate_report(parsed_report)
            
            # Add enhanced next steps
            enhanced_steps = NextStepsGenerator.generate_for_triage(
                triage_result,
                parsed_report.tests
            )
            triage_result.next_steps = enhanced_steps
            
            if self.enable_audit and triage_result.critical_count > 0:
                for alert in triage_result.get_critical_alerts():
                    self.audit_logger.log_alert(
                        alert.level.value,
                        alert.test_name,
                        alert.value
                    )
            
            # STEP 4: Generate explanations (if enabled)
            explanations = {}
            if self.enable_llm:
                logger.info("STEP 4: Generating explanations...")
                
                # Prioritize abnormal tests
                tests_to_explain = (
                    parsed_report.get_abnormal_tests()[:5] +  # Top 5 abnormal
                    parsed_report.get_normal_tests()[:2]      # Top 2 normal
                )
                
                explanations = self.explainer.batch_explain(tests_to_explain)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Create result
            result = PipelineResult(
                filename=file_path.name,
                file_hash=file_hash,
                extracted_text=extracted_text,
                extraction_metadata=extraction_metadata.to_dict(),
                parsed_report=parsed_report,
                triage_result=triage_result,
                explanations=explanations,
                session_id=self.audit_logger.session_id if self.enable_audit else "no-audit",
                processing_time=processing_time
            )
            
            logger.info(f"="*60)
            logger.info(f"✅ Processing complete in {processing_time:.2f}s")
            logger.info(f"   Tests: {len(parsed_report.tests)} total, {len(parsed_report.get_abnormal_tests())} abnormal")
            logger.info(f"   Urgency: {triage_result.overall_urgency}")
            logger.info(f"   Explanations: {len(explanations)}")
            logger.info(f"="*60)
            
            return result
            
        except Exception as e:
            logger.error(f"Pipeline error: {str(e)}")
            if self.enable_audit:
                self.audit_logger.log_error("pipeline_error", str(e))
            raise


__all__ = ["MedicalReportPipeline", "PipelineResult"]