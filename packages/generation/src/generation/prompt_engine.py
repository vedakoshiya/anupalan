"""Structured prompt engineering and XML context orchestration.

Builds prompt payloads with strict citation grounding constraints, prompt injection
defenses, and trilingual output instructions (Spec Section 8).
"""

import html
import re
from datetime import date
from typing import Any

from services.ingestion.src.chunker import StatutoryChunk


class CompliancePromptBuilder:
    """Assembles structured prompt payloads for statutory question-answering."""

    SYSTEM_PROMPTS = {
        "gu": (
            "તમે અનુપાલન (Anupalan) છો — ભારતીય MSME વેપારીઓ અને એકાઉન્ટન્ટ્સ માટેનો અધિકૃત નિયમ નેવિગેટર.\n"
            "તમારો ઉદ્દેશ્ય પૂછાયેલા પ્રશ્નનો સ્પષ્ટ, સચોટ અને કાનૂની સંદર્ભ સાથે જવાબ આપવાનો છે.\n"
            "મહત્વપૂર્ણ નિયમો:\n"
            "1. આપેલા સત્તાવાર દસ્તાવેજો (<context_document>) માંથી જ હકીકતો જણાવો. મનઘડંત અંદાજ ન લગાવો.\n"
            "2. દરેક દાવો (Claim) ઓછામાં ઓછા એક અધિકૃત દસ્તાવેજના ID સાથે ટાંકો (Cite કરો).\n"
            "3. કરના દરો (GST Rates), મર્યાદા (Limits) અને તારીખો દસ્તાવેજ મુજબ જ હોવી જોઈએ.\n"
            "4. જો પૂરી માહિતી ન હોય તો પ્રામાણિકપણે સ્વીકારો અને CA નો સંપર્ક કરવાની સલાહ આપો."
        ),
        "hi": (
            "आप अनुपालन (Anupalan) हैं — भारतीय MSME उद्यमियों और लेखाकारों के लिए आधिकारिक विनियामक सहायक।\n"
            "आपका उद्देश्य पूछे गए प्रश्न का स्पष्ट, सटीक और प्रमाणिक उत्तर देना है।\n"
            "महत्वपूर्ण नियम:\n"
            "1. केवल दिए गए आधिकारिक दस्तावेजों (<context_document>) के आधार पर ही उत्तर दें। कोई मनगढ़ंत दावा न करें।\n"
            "2. प्रत्येक दावे (Claim) को संबंधित दस्तावेज ID के साथ उद्धृत (Cite) करें।\n"
            "3. जीएसटी दरें, मौद्रिक सीमाएं और तिथियां हूबहू वैधानिक अधिसूचना के अनुसार होनी चाहिए।\n"
            "4. अपूर्ण जानकारी होने पर स्पष्ट अस्वीकरण दें और सीए से परामर्श लेने का सुझाव दें।"
        ),
        "en": (
            "You are Anupalan — an authoritative statutory compliance navigator for Indian MSMEs and accountants.\n"
            "Your objective is to answer business compliance questions with rigorous grounding in official circulars and acts.\n"
            "Crucial Rules:\n"
            "1. Ground every claim strictly in the provided official documents (<context_document>). Never hallucinate rates or dates.\n"
            "2. Every claim MUST cite the chunk ID, instrument name, and clause.\n"
            "3. Numeric limits (turnover, GST rates, days) must match the source circulars exactly.\n"
            "4. If documents do not provide conclusive proof, abstain gracefully and suggest escalation to a Chartered Accountant."
        ),
    }

    def __init__(self, default_language: str = "en"):
        self.default_language = default_language

    def sanitize_user_input(self, user_query: str) -> str:
        """Escapes XML tags and strips prompt injection delimiters."""
        clean = html.escape(user_query.strip())
        # Neutralize common injection phrases
        clean = re.sub(r"(?i)<\s*/?\s*context_document[^>]*>", "", clean)
        clean = re.sub(r"(?i)<\s*/?\s*system[^>]*>", "", clean)
        return clean

    def build_system_prompt(self, language: str = "en") -> str:
        """Returns the localized system instructions."""
        lang_key = language if language in self.SYSTEM_PROMPTS else self.default_language
        return self.SYSTEM_PROMPTS.get(lang_key, self.SYSTEM_PROMPTS["en"])

    def format_context_documents(
        self,
        chunks: list[StatutoryChunk],
        as_of: date,
    ) -> str:
        """Formats statutory chunks into structured XML context tags."""
        if not chunks:
            return "<context_documents count='0'>No authoritative in-force documents found.</context_documents>"

        docs = [f"<context_documents as_of='{as_of.isoformat()}' count='{len(chunks)}'>"]
        for c in chunks:
            text_body = getattr(c, "expanded_text", None) or c.text
            doc_tag = (
                f"  <context_document id='{c.id}' "
                f"authority='{html.escape(c.authority)}' "
                f"instrument='{html.escape(c.instrument_title)}' "
                f"section='{html.escape(c.section_path)}' "
                f"effective_from='{c.effective_from.isoformat() if c.effective_from else 'None'}'>\n"
                f"    <context_header>{html.escape(c.context_header)}</context_header>\n"
                f"    <content>{html.escape(text_body)}</content>\n"
                f"  </context_document>"
            )
            docs.append(doc_tag)
        docs.append("</context_documents>")
        return "\n".join(docs)

    def build_user_prompt(
        self,
        query: str,
        as_of: date,
        chunks: list[StatutoryChunk],
        language: str = "en",
    ) -> str:
        """Constructs the complete user prompt combining context documents and sanitized query."""
        sanitized_query = self.sanitize_user_input(query)
        context_xml = self.format_context_documents(chunks, as_of)

        prompt = (
            f"Statutory Context Documents (evaluated in-force as of {as_of.isoformat()}):\n"
            f"{context_xml}\n\n"
            f"User Question: \"{sanitized_query}\"\n"
            f"Target Response Language: {language}\n"
            f"Instructions:\n"
            f"Synthesize an authoritative compliance answer answering the question.\n"
            f"Each claim must link to one or more <context_document id='...'> tags.\n"
            f"Format as valid JSON matching the AskResponse schema."
        )
        return prompt

    def build_prompt_payload(
        self,
        query: str,
        as_of: date,
        language: str,
        chunks: list[StatutoryChunk],
    ) -> dict[str, str]:
        """Returns standard system and user prompt dictionary for LLM adapters."""
        return {
            "system": self.build_system_prompt(language),
            "user": self.build_user_prompt(query, as_of, chunks, language),
        }
