# scripts/generate_synthetic_data.py
"""Generate synthetic medical reports for testing"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import random
import json

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import Paths

class SyntheticReportGenerator:
    """Generate realistic synthetic lab reports"""
    
    def __init__(self):
        self.output_dir = Paths.SYNTHETIC_REPORTS
        self.templates = {
            "normal_cbc": self.create_normal_cbc,
            "mild_anemia": self.create_mild_anemia,
            "critical_potassium": self.create_critical_potassium,
            "high_glucose": self.create_high_glucose,
            "normal_metabolic": self.create_normal_metabolic,
            "critical_low_glucose": self.create_critical_low_glucose,
            "high_wbc": self.create_high_wbc,
            "low_platelet": self.create_low_platelet,
            "elevated_liver_enzymes": self.create_elevated_liver_enzymes,
            "normal_lipid_panel": self.create_normal_lipid_panel,
        }
    
    def create_normal_cbc(self, patient_id: str) -> str:
        """Complete Blood Count - Normal"""
        date = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")
        
        return f"""LABORATORY REPORT
=================

Patient ID: {patient_id}
Date of Collection: {date}
Test: Complete Blood Count (CBC)

RESULTS:
--------
White Blood Cell Count: 7.2 x10³/µL (4.0-11.0)
Red Blood Cell Count: 4.8 x10⁶/µL (4.5-5.5)
Hemoglobin: 14.5 g/dL (13.0-17.0)
Hematocrit: 42.0 % (38.0-50.0)
Platelet Count: 250 x10³/µL (150-400)
Mean Corpuscular Volume: 88 fL (80-100)

IMPRESSION:
All values within normal limits. No abnormalities detected.

Performing Lab: Quest Diagnostics
Certified by: Dr. Smith, MD
"""

    def create_mild_anemia(self, patient_id: str) -> str:
        """CBC with mild anemia"""
        date = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")
        
        return f"""LABORATORY REPORT
=================

Patient ID: {patient_id}
Date of Collection: {date}
Test: Complete Blood Count (CBC)

RESULTS:
--------
White Blood Cell Count: 6.8 x10³/µL (4.0-11.0)
Red Blood Cell Count: 3.9 x10⁶/µL (4.5-5.5) [L]
Hemoglobin: 11.2 g/dL (13.0-17.0) [L]
Hematocrit: 35.0 % (38.0-50.0) [L]
Platelet Count: 230 x10³/µL (150-400)
Mean Corpuscular Volume: 85 fL (80-100)

IMPRESSION:
Mild anemia noted. Hemoglobin and hematocrit below normal range.
Recommend iron studies and follow-up with primary care physician.

Performing Lab: LabCorp
Certified by: Dr. Johnson, MD
"""

    def create_critical_potassium(self, patient_id: str) -> str:
        """Metabolic panel with critical potassium"""
        date = (datetime.now() - timedelta(days=random.randint(1, 5))).strftime("%Y-%m-%d")
        
        return f"""LABORATORY REPORT - CRITICAL VALUES
====================================

Patient ID: {patient_id}
Date of Collection: {date}
Test: Basic Metabolic Panel

**CRITICAL RESULTS - PHYSICIAN NOTIFIED**

RESULTS:
--------
Sodium: 138 mEq/L (135-145)
Potassium: 6.8 mEq/L (3.5-5.0) [CRITICAL HIGH]
Chloride: 102 mEq/L (98-107)
CO2: 24 mEq/L (22-30)
Glucose: 95 mg/dL (70-100)
BUN: 18 mg/dL (7-20)
Creatinine: 1.1 mg/dL (0.6-1.2)

IMPRESSION:
CRITICAL: Hyperkalemia detected (K+ 6.8 mEq/L).
IMMEDIATE medical evaluation required. 
Physician notified at {datetime.now().strftime("%Y-%m-%d %H:%M")}.

Performing Lab: Hospital Laboratory
Certified by: Dr. Martinez, MD
"""

    def create_high_glucose(self, patient_id: str) -> str:
        """Metabolic panel with elevated glucose"""
        date = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")
        
        return f"""LABORATORY REPORT
=================

Patient ID: {patient_id}
Date of Collection: {date}
Test: Comprehensive Metabolic Panel

RESULTS:
--------
Glucose: 185 mg/dL (70-100) [H]
Sodium: 140 mEq/L (135-145)
Potassium: 4.2 mEq/L (3.5-5.0)
Chloride: 101 mEq/L (98-107)
CO2: 25 mEq/L (22-30)
BUN: 16 mg/dL (7-20)
Creatinine: 0.9 mg/dL (0.6-1.2)
Calcium: 9.5 mg/dL (8.5-10.5)
Total Protein: 7.2 g/dL (6.0-8.3)
Albumin: 4.1 g/dL (3.5-5.0)
Total Bilirubin: 0.8 mg/dL (0.1-1.2)
ALT: 28 U/L (7-56)
AST: 24 U/L (10-40)

IMPRESSION:
Elevated fasting glucose suggestive of impaired glucose tolerance.
Recommend HbA1c testing and endocrinology consultation.

Performing Lab: Quest Diagnostics
Certified by: Dr. Lee, MD
"""

    def create_normal_metabolic(self, patient_id: str) -> str:
        """Normal metabolic panel"""
        date = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")
        
        return f"""LABORATORY REPORT
=================

Patient ID: {patient_id}
Date of Collection: {date}
Test: Basic Metabolic Panel

RESULTS:
--------
Glucose: 88 mg/dL (70-100)
Sodium: 139 mEq/L (135-145)
Potassium: 4.0 mEq/L (3.5-5.0)
Chloride: 103 mEq/L (98-107)
CO2: 26 mEq/L (22-30)
BUN: 14 mg/dL (7-20)
Creatinine: 0.9 mg/dL (0.6-1.2)
Calcium: 9.2 mg/dL (8.5-10.5)

IMPRESSION:
All values within normal limits.

Performing Lab: LabCorp
Certified by: Dr. Williams, MD
"""

    def create_critical_low_glucose(self, patient_id: str) -> str:
        """Critical low glucose"""
        date = datetime.now().strftime("%Y-%m-%d")
        
        return f"""LABORATORY REPORT - CRITICAL VALUES
====================================

Patient ID: {patient_id}
Date of Collection: {date}
Test: Blood Glucose

**CRITICAL RESULTS - PHYSICIAN NOTIFIED**

RESULTS:
--------
Glucose: 38 mg/dL (70-100) [CRITICAL LOW]

IMPRESSION:
CRITICAL: Severe hypoglycemia detected.
Patient requires immediate medical attention.
Physician notified at {datetime.now().strftime("%Y-%m-%d %H:%M")}.

Performing Lab: Hospital Laboratory
Certified by: Dr. Chen, MD
"""

    def create_high_wbc(self, patient_id: str) -> str:
        """Elevated WBC suggesting infection"""
        date = (datetime.now() - timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%d")
        
        return f"""LABORATORY REPORT
=================

Patient ID: {patient_id}
Date of Collection: {date}
Test: Complete Blood Count (CBC)

RESULTS:
--------
White Blood Cell Count: 15.8 x10³/µL (4.0-11.0) [H]
Red Blood Cell Count: 4.6 x10⁶/µL (4.5-5.5)
Hemoglobin: 14.0 g/dL (13.0-17.0)
Hematocrit: 41.0 % (38.0-50.0)
Platelet Count: 280 x10³/µL (150-400)

IMPRESSION:
Elevated white blood cell count suggesting possible infection or inflammation.
Recommend clinical correlation and follow-up.

Performing Lab: Quest Diagnostics
Certified by: Dr. Brown, MD
"""

    def create_low_platelet(self, patient_id: str) -> str:
        """Low platelet count (thrombocytopenia)"""
        date = (datetime.now() - timedelta(days=random.randint(1, 14))).strftime("%Y-%m-%d")
        
        return f"""LABORATORY REPORT
=================

Patient ID: {patient_id}
Date of Collection: {date}
Test: Complete Blood Count (CBC)

RESULTS:
--------
White Blood Cell Count: 6.5 x10³/µL (4.0-11.0)
Red Blood Cell Count: 4.7 x10⁶/µL (4.5-5.5)
Hemoglobin: 13.8 g/dL (13.0-17.0)
Hematocrit: 40.5 % (38.0-50.0)
Platelet Count: 95 x10³/µL (150-400) [L]

IMPRESSION:
Thrombocytopenia detected. Platelet count below normal range.
Recommend repeat testing and hematology consultation if persistent.

Performing Lab: LabCorp
Certified by: Dr. Davis, MD
"""

    def create_elevated_liver_enzymes(self, patient_id: str) -> str:
        """Elevated liver enzymes"""
        date = (datetime.now() - timedelta(days=random.randint(1, 21))).strftime("%Y-%m-%d")
        
        return f"""LABORATORY REPORT
=================

Patient ID: {patient_id}
Date of Collection: {date}
Test: Liver Function Tests

RESULTS:
--------
ALT: 125 U/L (7-56) [H]
AST: 98 U/L (10-40) [H]
Alkaline Phosphatase: 145 U/L (44-147)
Total Bilirubin: 1.1 mg/dL (0.1-1.2)
Albumin: 4.0 g/dL (3.5-5.0)
Total Protein: 7.0 g/dL (6.0-8.3)

IMPRESSION:
Elevated liver transaminases (ALT and AST).
Recommend hepatology consultation and further workup to determine etiology.

Performing Lab: Quest Diagnostics
Certified by: Dr. Garcia, MD
"""

    def create_normal_lipid_panel(self, patient_id: str) -> str:
        """Normal lipid panel"""
        date = (datetime.now() - timedelta(days=random.randint(1, 90))).strftime("%Y-%m-%d")
        
        return f"""LABORATORY REPORT
=================

Patient ID: {patient_id}
Date of Collection: {date}
Test: Lipid Panel (Fasting)

RESULTS:
--------
Total Cholesterol: 182 mg/dL (0-200)
HDL Cholesterol: 58 mg/dL (>40)
LDL Cholesterol: 98 mg/dL (0-100)
Triglycerides: 130 mg/dL (0-150)
VLDL Cholesterol: 26 mg/dL (5-40)

IMPRESSION:
Lipid profile within desirable ranges.
Continue current lifestyle and dietary habits.

Performing Lab: LabCorp
Certified by: Dr. Wilson, MD
"""

    def generate_all(self):
        """Generate all synthetic reports"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        reports = []
        for idx, (report_type, generator) in enumerate(self.templates.items(), 1):
            patient_id = f"TEST{idx:03d}"
            content = generator(patient_id)
            
            # Save as text file
            filename = f"{idx:02d}_{report_type}.txt"
            filepath = self.output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            reports.append({
                "id": idx,
                "patient_id": patient_id,
                "type": report_type,
                "filename": filename,
                "filepath": str(filepath)
            })
            
            print(f"✓ Created: {filename}")
        
        # Save manifest
        manifest_path = self.output_dir / "manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(reports, f, indent=2)
        
        print(f"\n✅ Generated {len(reports)} synthetic reports")
        print(f"✅ Manifest saved to: {manifest_path}")
        
        return reports


if __name__ == "__main__":
    print("="*60)
    print("GENERATING SYNTHETIC LAB REPORTS")
    print("="*60)
    print()
    
    generator = SyntheticReportGenerator()
    generator.generate_all()
    
    print()
    print("="*60)
    print("✅ SYNTHETIC DATA GENERATION COMPLETE")
    print("="*60)