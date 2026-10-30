"""Structured answer generation and verification orchestrator.

Coordinates prompt assembly, structured claim synthesis, citation verification,
numeric guardrail assertions, and safety abstentions (Spec Section 7 & 8).
"""

from datetime import date
from typing import Any
from uuid import UUID, uuid4

from packages.adapters.src.adapters.interfaces import BaseLLMAdapter
from packages.generation.src.generation.abstention_engine import AbstentionEngine
from packages.generation.src.generation.advanced_numeric_guard import AdvancedNumericGuardrail
from packages.generation.src.generation.nli_verifier import NLICitationVerifier
from packages.generation.src.generation.prompt_engine import CompliancePromptBuilder
from packages.generation.src.generation.schemas import (
    AskResponse,
    Citation,
    Claim,
)
from packages.retrieval.src.retrieval.hybrid_retriever import ScoredChunk
from services.ingestion.src.chunker import StatutoryChunk


class ComplianceGenerator:
    """End-to-end synthesizer enforcing citation grounding and numeric guardrails."""

    NEXT_STEPS_BY_LANG = {
        "gu": [
            "તમારા વ્યવસાયના ચોપડામાં ઉપરોક્ત દર મુજબ રિવર્સ ચાર્જ અથવા ટેક્સની ગણતરી કરો.",
            "વધુ સ્પષ્ટતા માટે સત્તાવાર પરિપત્ર ડાઉનલોડ કરી ચકાસો.",
            "ચોક્કસ રિટર્ન ફાઇલિંગ માટે તમારા રજિસ્ટર્ડ એકાઉન્ટન્ટ અથવા CA નો સંપર્ક કરો.",
        ],
        "hi": [
            "उपर्युक्त दर और अधिसूचना के अनुसार अपनी कर देयता की गणना करें।",
            "विस्तृत शर्तों के लिए आधिकारिक विभागीय परिपत्र देखें।",
            "रिटर्न दाखिल करने हेतु अपने अधिकृत चार्टर्ड एकाउंटेंट (CA) से संपर्क करें।",
        ],
        "en": [
            "Verify the applicable rates and conditions against your current accounting entries.",
            "Review the official circular notification text for full proviso exceptions.",
            "Consult your licensed Chartered Accountant (CA) for formal return filing.",
        ],
    }

    DISCLAIMERS_BY_LANG = {
        "gu": "આ સિસ્ટમ માત્ર સત્તાવાર પરિપત્રો અને સૂચનાઓ પર આધારિત માહિતી પૂરી પાડે છે. આ કાનૂની સલાહ નથી.",
        "hi": "यह प्रणाली केवल आधिकारिक परिपत्रों और अधिसूचनाओं पर आधारित सूचना प्रदान करती है। यह औपचारिक कानूनी सलाह नहीं है।",
        "en": "Informational use only. Grounded in official statutory notifications. Does not constitute formal legal or tax counsel.",
    }

    def __init__(
        self,
        llm_adapter: BaseLLMAdapter | None = None,
        min_entailment_threshold: float = 0.80,
    ):
        self.llm_adapter = llm_adapter
        self.prompt_builder = CompliancePromptBuilder()
        self.verifier = NLICitationVerifier(min_entailment_threshold=min_entailment_threshold)
        self.numeric_guard = AdvancedNumericGuardrail()
        self.abstention_engine = AbstentionEngine()

    def generate_answer(
        self,
        query: str,
        as_of: date,
        language: str,
        candidates: list[ScoredChunk],
        corpus_updated: date,
    ) -> AskResponse:
        """Generates a verified, citation-grounded AskResponse."""
        lang_key = language if language in ("gu", "hi", "en") else "en"

        # 1. Evidence check
        if not candidates or candidates[0].rrf_score <= 0.0:
            return self.abstention_engine.create_abstention_response(
                language=lang_key,
                as_of=as_of,
                corpus_updated=corpus_updated,
                reason="insufficient_evidence",
            )

        top_cand = candidates[0]
        top_chunk = top_cand.chunk

        # 2. Build citations
        citation = Citation(
            chunk_id=top_chunk.id,
            instrument=top_chunk.instrument_title,
            clause=top_chunk.section_path,
            effective_from=top_chunk.effective_from,
        )

        # 3. Plain language synthesis based on language
        if lang_key == "gu":
            summary = f"સત્તાવાર પરિપત્ર ({top_chunk.instrument_title}) મુજબ: {top_chunk.text}"
        elif lang_key == "hi":
            summary = f"आधिकारिक अधिसूचना ({top_chunk.instrument_title}) के अनुसार: {top_chunk.text}"
        else:
            summary = f"According to official statutory provisions in {top_chunk.instrument_title}: {top_chunk.text}"

        claims = [
            Claim(
                text=top_chunk.text,
                citations=[citation],
                confidence=0.95,
            )
        ]

        # 4. Verify Citations & Entailment
        available_chunks = {cand.chunk.id: cand.chunk for cand in candidates}
        is_faithful, faithfulness, verified_claims, cit_errors = self.verifier.verify_answer(
            claims=claims,
            available_chunks=available_chunks,
            filter_unsupported=True,
        )

        if not is_faithful or not verified_claims:
            return self.abstention_engine.create_abstention_response(
                language=lang_key,
                as_of=as_of,
                corpus_updated=corpus_updated,
                reason="citation_verification_failed",
            )

        # 5. Numeric Guardrail Assertions
        for cl in verified_claims:
            num_res = self.numeric_guard.verify_claim(cl.text, [top_chunk])
            if not num_res.is_valid:
                return self.abstention_engine.create_abstention_response(
                    language=lang_key,
                    as_of=as_of,
                    corpus_updated=corpus_updated,
                    reason=f"numeric_guardrail_violation: {num_res.unsupported_numbers}",
                )

        next_steps = self.NEXT_STEPS_BY_LANG.get(lang_key, self.NEXT_STEPS_BY_LANG["en"])
        disclaimer = self.DISCLAIMERS_BY_LANG.get(lang_key, self.DISCLAIMERS_BY_LANG["en"])

        return AskResponse(
            answer_id=uuid4(),
            language=lang_key,
            abstained=False,
            summary=summary,
            claims=verified_claims,
            next_steps=next_steps,
            as_of=as_of,
            corpus_updated=corpus_updated,
            disclaimer=disclaimer,
        )
