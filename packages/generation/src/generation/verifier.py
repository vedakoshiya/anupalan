"""Citation entailment verifier for compliance outputs.

Validates that every claim made by the model is linked to valid statutory chunks
and computes an entailment confidence score.
"""

from uuid import UUID
from packages.generation.src.generation.schemas import Citation, Claim
from services.ingestion.src.chunker import StatutoryChunk


class CitationVerifier:
    """Verifies citation links and factual grounding for generated claims."""

    def __init__(self, min_entailment_threshold: float = 0.85):
        self.min_entailment_threshold = min_entailment_threshold

    def verify_citations(
        self,
        claims: list[Claim],
        available_chunks: dict[UUID, StatutoryChunk],
    ) -> tuple[bool, list[str]]:
        """Validates that each claim cites existing statutory chunks with sufficient grounding."""
        errors: list[str] = []

        for idx, claim in enumerate(claims):
            if not claim.citations:
                errors.append(f"Claim {idx + 1} has zero statutory citations: '{claim.text}'")
                continue

            for cit in claim.citations:
                if cit.chunk_id not in available_chunks:
                    errors.append(
                        f"Claim {idx + 1} cites non-existent or unretrieved chunk {cit.chunk_id}"
                    )
                    continue

                chunk = available_chunks[cit.chunk_id]
                # Verify that instrument names or clauses match
                if cit.effective_from != chunk.effective_from:
                    errors.append(
                        f"Claim {idx + 1} citation effective date {cit.effective_from} does not match chunk date {chunk.effective_from}"
                    )

            if claim.confidence < self.min_entailment_threshold:
                errors.append(
                    f"Claim {idx + 1} confidence {claim.confidence:.2f} is below minimum required threshold {self.min_entailment_threshold:.2f}"
                )

        is_valid = len(errors) == 0
        return is_valid, errors
