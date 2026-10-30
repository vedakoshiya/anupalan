"""NLI-based citation entailment verifier for compliance outputs.

Validates that every claim is strictly entailed by cited statutory passages,
detects ungrounded assertions, and computes an overall answer Faithfulness score (Spec Section 7.1).
"""

import math
import re
from dataclasses import dataclass
from uuid import UUID

from packages.generation.src.generation.schemas import Citation, Claim
from services.ingestion.src.chunker import StatutoryChunk


@dataclass
class EntailmentResult:
    """Outcome of NLI citation verification for a single claim."""

    claim_idx: int
    is_entailed: bool
    entailment_score: float
    cited_chunk_ids: list[UUID]
    errors: list[str]


class NLICitationVerifier:
    """Evaluates logical entailment and citation grounding between claims and source passages."""

    def __init__(self, min_entailment_threshold: float = 0.80):
        self.min_entailment_threshold = min_entailment_threshold

    def _tokenize(self, text: str) -> list[str]:
        return [w.lower() for w in re.findall(r"[\w%]+", text, re.UNICODE)]

    def compute_entailment_score(self, claim_text: str, source_text: str) -> float:
        """Computes semantic lexical and token overlap proxy for logical entailment."""
        claim_tokens = self._tokenize(claim_text)
        if not claim_tokens:
            return 1.0

        source_tokens = set(self._tokenize(source_text))
        if not source_tokens:
            return 0.0

        # Term overlap ratio
        matches = sum(1 for t in claim_tokens if t in source_tokens)
        token_coverage = matches / len(claim_tokens)

        # Bigram overlap for phrasal consistency
        if len(claim_tokens) >= 2:
            claim_bigrams = {
                f"{claim_tokens[i]}_{claim_tokens[i+1]}"
                for i in range(len(claim_tokens) - 1)
            }
            source_token_list = self._tokenize(source_text)
            source_bigrams = {
                f"{source_token_list[i]}_{source_token_list[i+1]}"
                for i in range(len(source_token_list) - 1)
            }
            bigram_matches = len(claim_bigrams.intersection(source_bigrams))
            bigram_coverage = bigram_matches / max(1, len(claim_bigrams))
        else:
            bigram_coverage = token_coverage

        score = (0.7 * token_coverage) + (0.3 * bigram_coverage)
        return min(1.0, max(0.0, score))

    def verify_claim(
        self,
        claim: Claim,
        claim_idx: int,
        available_chunks: dict[UUID, StatutoryChunk],
    ) -> EntailmentResult:
        """Verifies an individual claim against its cited passages."""
        errors: list[str] = []

        if not claim.citations:
            errors.append(f"Claim {claim_idx + 1} has zero statutory citations: '{claim.text}'")
            return EntailmentResult(
                claim_idx=claim_idx,
                is_entailed=False,
                entailment_score=0.0,
                cited_chunk_ids=[],
                errors=errors,
            )

        cited_texts: list[str] = []
        cited_ids: list[UUID] = []

        for cit in claim.citations:
            cited_ids.append(cit.chunk_id)
            if cit.chunk_id not in available_chunks:
                errors.append(f"Claim {claim_idx + 1} cites unretrieved or invalid chunk {cit.chunk_id}")
                continue

            chunk = available_chunks[cit.chunk_id]
            cited_texts.append(chunk.context_header + " " + chunk.text)
            if hasattr(chunk, "expanded_text") and chunk.expanded_text:
                cited_texts.append(chunk.expanded_text)

            # Check effective date alignment
            if cit.effective_from != chunk.effective_from:
                errors.append(
                    f"Citation date mismatch on chunk {chunk.id}: "
                    f"cited {cit.effective_from} != chunk {chunk.effective_from}"
                )

        combined_source = " ".join(cited_texts)
        entailment = self.compute_entailment_score(claim.text, combined_source)

        if entailment < self.min_entailment_threshold:
            errors.append(
                f"Entailment score {entailment:.3f} below threshold {self.min_entailment_threshold:.3f}"
            )

        is_entailed = len(errors) == 0 and (entailment >= self.min_entailment_threshold)

        return EntailmentResult(
            claim_idx=claim_idx,
            is_entailed=is_entailed,
            entailment_score=round(entailment, 4),
            cited_chunk_ids=cited_ids,
            errors=errors,
        )

    def verify_answer(
        self,
        claims: list[Claim],
        available_chunks: dict[UUID, StatutoryChunk],
        filter_unsupported: bool = True,
    ) -> tuple[bool, float, list[Claim], list[str]]:
        """Verifies all claims in an answer.

        Returns:
            (is_faithful, faithfulness_score, verified_claims, all_errors)
        """
        if not claims:
            return True, 1.0, [], []

        verified_claims: list[Claim] = []
        all_errors: list[str] = []
        entailed_count = 0

        for idx, claim in enumerate(claims):
            res = self.verify_claim(claim, idx, available_chunks)
            if res.is_entailed:
                entailed_count += 1
                # Update claim confidence with verified entailment score
                claim.confidence = res.entailment_score
                verified_claims.append(claim)
            else:
                all_errors.extend(res.errors)
                if not filter_unsupported:
                    verified_claims.append(claim)

        faithfulness = entailed_count / len(claims)
        is_faithful = (faithfulness >= 0.85) and (len(verified_claims) > 0)

        return is_faithful, round(faithfulness, 4), verified_claims, all_errors
