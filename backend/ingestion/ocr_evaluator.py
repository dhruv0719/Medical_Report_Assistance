# backend/ingestion/ocr_evaluator.py
"""
OCR output quality evaluator.

Scores an OCR result using four independent signals:

  1. tesseract_confidence  (40%) — raw engine per-word certainty
  2. character_quality     (25%) — printable/clean character ratio
  3. word_quality          (20%) — word-length distribution
  4. structure_coherence   (15%) — domain-agnostic structured-document signals

Signal 4 replaces the old `medical_semantic` score.

WHY THE CHANGE
──────────────
`medical_semantic` used a hardcoded CBC/haematology keyword list.
Any lab report that wasn't a blood count (thyroid, lipid, biochemistry,
urine, culture, etc.) scored near-zero on that component and lost up to
15 composite points — even when perfectly OCR'd.

`structure_coherence` asks instead: "does this text look like a
well-extracted structured data document?" using five signals that are
true for EVERY lab report regardless of specialty:

  numeric_density     — lab reports are always number-heavy
  range_patterns      — every report has reference ranges (X.X – Y.Y)
  unit_patterns       — any measurement unit, not specialty-specific ones
  kv_density          — label → value pairs appear in all tabular reports
  line_completeness   — fragmented lines signal bad preprocessing

Final composite = weighted sum of all four signals, each normalised 0-100.
"""

import re
import string
from dataclasses import dataclass
from typing import List


# ---------------------------------------------------------------------------
# Compiled patterns — built once at import time
# ---------------------------------------------------------------------------

# Reference ranges: "13.0 - 17.0", "4000-11000", "3.5–5.5"
_RANGE_RE = re.compile(
    r"\b\d+\.?\d*\s*[-\u2013\u2014]\s*\d+\.?\d*\b"
)

# Measurement units — broad enough to cover any lab specialty.
# Matches a number immediately followed by a known unit token.
_UNIT_RE = re.compile(
    r"\b\d+\.?\d*\s*"
    r"(?:"
    r"g/dL|mg/dL|mmol/L|µmol/L|umol/L|nmol/L|pmol/L"
    r"|mEq/L|IU/L|U/L|kU/L|mU/L"
    r"|/cmm|/cumm|million/cmm|cells/µL"
    r"|fL|pg|%|mm/1hr|mm/hr"
    r"|mg/L|µg/L|ng/mL|ng/dL|ng/L|pg/mL"
    r"|mIU/L|mIU/mL|µIU/mL"
    r"|ratio|index"
    r")\b",
    re.IGNORECASE,
)

# Key-value pairs: one or more word-chars, optional spaces, then a number.
# Catches "Hemoglobin 14.5", "TSH 2.30", "LDL Cholesterol 120", "Glucose 98"
_KV_RE = re.compile(
    r"\b[A-Za-z][\w\s]{2,30}\s+\d+\.?\d*\b"
)

# Any numeric token (integer or decimal)
_NUMERIC_RE = re.compile(r"\b\d+\.?\d*\b")

# Characters that reliably signal OCR noise / garbage
_GARBAGE_CHARS = frozenset(r"\|~^`_{}[]<>")


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

@dataclass
class OCRScore:
    """
    Composite OCR quality score for a single strategy result.

    All sub-scores and composite are in the range 0-100.
    """

    strategy: str
    text: str

    tesseract_confidence: float   # raw Tesseract average confidence
    character_quality:    float   # printable / clean char ratio
    word_quality:         float   # word-length distribution health
    structure_coherence:  float   # domain-agnostic structured-doc signals
    composite:            float   # final weighted score

    def __repr__(self) -> str:
        return (
            f"OCRScore(strategy={self.strategy!r}, "
            f"composite={self.composite:.1f}, "
            f"tess={self.tesseract_confidence:.1f}, "
            f"char={self.character_quality:.1f}, "
            f"word={self.word_quality:.1f}, "
            f"struct={self.structure_coherence:.1f})"
        )


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------

class OCREvaluator:
    """
    Evaluates OCR output quality using four independent, domain-agnostic
    signals.

    Designed to work correctly for ANY structured lab report — CBC,
    thyroid, lipid, biochemistry, urine analysis, microbiology, etc.
    No specialist terminology is assumed or required.

    Weights
    -------
    tesseract_confidence  0.40
    character_quality     0.25
    word_quality          0.20
    structure_coherence   0.15
    """

    _WEIGHTS = {
        "tesseract_confidence": 0.40,
        "character_quality":    0.25,
        "word_quality":         0.20,
        "structure_coherence":  0.15,
    }

    def score(
        self,
        text: str,
        tesseract_confidence: float,
        strategy: str = "unknown",
    ) -> OCRScore:
        """
        Score a single OCR result.

        Args:
            text:                  Text extracted by Tesseract.
            tesseract_confidence:  Mean per-word confidence from pytesseract
                                   (0-100).
            strategy:              Name of the preprocessing strategy used,
                                   e.g. "raw", "light", "medical_report".

        Returns:
            OCRScore with individual signal scores and final composite.
        """
        char_q   = self._score_character_quality(text)
        word_q   = self._score_word_quality(text)
        struct_q = self._score_structure_coherence(text)

        composite = (
            tesseract_confidence * self._WEIGHTS["tesseract_confidence"]
            + char_q             * self._WEIGHTS["character_quality"]
            + word_q             * self._WEIGHTS["word_quality"]
            + struct_q           * self._WEIGHTS["structure_coherence"]
        )

        return OCRScore(
            strategy=strategy,
            text=text,
            tesseract_confidence=tesseract_confidence,
            character_quality=char_q,
            word_quality=word_q,
            structure_coherence=struct_q,
            composite=max(0.0, min(100.0, composite)),
        )

    # ------------------------------------------------------------------
    # Signal 2 — Character quality
    # ------------------------------------------------------------------

    def _score_character_quality(self, text: str) -> float:
        """
        Reward clean, printable characters; penalise OCR garbage markers.

        High score → mostly letters, digits, normal punctuation.
        Low score  → lots of \\|~^`[] or non-printable bytes.
        """
        if not text.strip():
            return 0.0

        printable = set(string.printable)
        total     = len(text)

        clean   = sum(1 for c in text if c in printable)
        garbage = sum(1 for c in text if c in _GARBAGE_CHARS)

        clean_ratio   = clean   / total
        garbage_ratio = garbage / total

        # Garbage penalty capped at 30 points so one bad character cluster
        # doesn't completely zero out an otherwise decent result.
        penalty = min(garbage_ratio * 2.0, 0.30)

        return max(0.0, min(100.0, (clean_ratio - penalty) * 100))

    # ------------------------------------------------------------------
    # Signal 3 — Word quality
    # ------------------------------------------------------------------

    def _score_word_quality(self, text: str) -> float:
        """
        Score based on word-length distribution.

        Real extracted text → varied lengths, mostly 2-20 chars.
        Over-preprocessed image → flood of 1-char OCR fragments.
        Very noisy image → many absurdly long tokens.
        """
        words = text.split()
        if not words:
            return 0.0

        lengths = [len(w) for w in words]
        n       = len(lengths)

        good = sum(1 for l in lengths if 2 <= l <= 20)
        tiny = sum(1 for l in lengths if l == 1)

        good_ratio   = good / n
        tiny_penalty = min((tiny / n) * 0.5, 0.30)

        return max(0.0, min(100.0, (good_ratio - tiny_penalty) * 100))

    # ------------------------------------------------------------------
    # Signal 4 — Structure coherence (domain-agnostic)
    # ------------------------------------------------------------------

    def _score_structure_coherence(self, text: str) -> float:
        """
        Measure how well the text preserves structured, data-rich document
        content — without assuming any specific medical specialty.

        Five sub-signals (each 0-1, then combined and scaled to 0-100):

        numeric_density
            Lab reports of any kind are heavily numeric. If preprocessing
            breaks glyphs, digit recognition fails first.
            Saturates at 25% numeric tokens (realistic upper bound for a
            mixed-content page).

        range_patterns
            Every lab report has reference ranges ("13.0 - 17.0",
            "3.5–5.5", "4000-11000"). The pattern is specialty-agnostic.
            Saturates at 6 occurrences per page.

        unit_patterns
            Covers units from all common specialties: haematology (g/dL,
            fL, pg), biochemistry (mmol/L, µmol/L), endocrinology
            (mIU/L, ng/mL), etc.
            Saturates at 6 occurrences per page.

        kv_density
            Label → numeric value pairs: "Hemoglobin 14.5", "TSH 2.3",
            "LDL 120". Present in every structured result table regardless
            of specialty. Saturates at 8 pairs per page.

        line_completeness
            Poorly preprocessed images cause Tesseract to fragment table
            rows into very short lines. Average line length below 15 chars
            is a reliable fragmentation signal.
            Full score at >= 30 chars/line, zero at <= 5 chars/line.

        Sub-signal weights:
            numeric_density    0.25
            range_patterns     0.25
            unit_patterns      0.20
            kv_density         0.20
            line_completeness  0.10
        """
        words   = text.split()
        n_words = len(words) or 1

        # 1. Numeric density
        numbers       = _NUMERIC_RE.findall(text)
        numeric_score = min(len(numbers) / (n_words * 0.25), 1.0)

        # 2. Reference range patterns
        ranges      = _RANGE_RE.findall(text)
        range_score = min(len(ranges) / 6.0, 1.0)

        # 3. Measurement unit patterns
        units      = _UNIT_RE.findall(text)
        unit_score = min(len(units) / 6.0, 1.0)

        # 4. Key-value pair density
        kv_pairs = _KV_RE.findall(text)
        kv_score = min(len(kv_pairs) / 8.0, 1.0)

        # 5. Line completeness
        lines = [l for l in text.splitlines() if l.strip()]
        if lines:
            avg_line_len = sum(len(l) for l in lines) / len(lines)
            # Linear ramp: 5 chars → 0.0, 30 chars → 1.0
            line_score = max(0.0, min(1.0, (avg_line_len - 5) / 25.0))
        else:
            line_score = 0.0

        composite = (
            numeric_score * 0.25
            + range_score * 0.25
            + unit_score  * 0.20
            + kv_score    * 0.20
            + line_score  * 0.10
        ) * 100

        return max(0.0, min(100.0, composite))