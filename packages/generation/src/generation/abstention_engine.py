"""Abstention engine for out-of-scope, low-confidence, or ambiguous queries."""

from datetime import date
from uuid import uuid4
from packages.generation.src.generation.schemas import AskResponse


class AbstentionEngine:
    """Produces structured abstention responses adhering to safety requirements."""

    ABSTENTION_MESSAGES = {
        "gu": {
            "summary": "માફ કરશો, આ પ્રશ્ન માટે સત્તાવાર નિયમોમાં પૂરતો પુરાવો ઉપલબ્ધ નથી અથવા આ પ્રશ્ન વ્યક્તિગત કર ગણતરી/કોર્ટ કેસ સંબંધિત છે.",
            "next_steps": [
                "કૃપા કરીને પ્રશ્નમાં વધુ વિગતો (જેમ કે ટર્નઓવર અથવા માલ/સેવાનો પ્રકાર) ઉમેરી ફરી પૂછો.",
                "સત્તાવાર સરકારી પોર્ટલ (cbic-gst.gov.in અથવા udyamregistration.gov.in) ની મુલાકાત લો.",
                "યોગ્ય કર સલાહ માટે તમારા રજિસ્ટર્ડ ચાર્ટર્ડ એકાઉન્ટન્ટ (CA) નો સંપર્ક કરો."
            ],
            "disclaimer": "આ સિસ્ટમ માત્ર સત્તાવાર પરિપત્રો અને સૂચનાઓ પર આધારિત માહિતી પૂરી પાડે છે. આ કાનૂની સલાહ નથી."
        },
        "hi": {
            "summary": "क्षमा करें, इस प्रश्न के लिए आधिकारिक नियमों में पर्याप्त प्रमाण उपलब्ध नहीं है अथवा यह व्यक्तिगत कर गणना से संबंधित है।",
            "next_steps": [
                "कृपया प्रश्न में स्पष्ट विवरण (जैसे टर्नओवर अथवा वस्तु/सेवा का प्रकार) देकर पुनः प्रयास करें।",
                "आधिकारिक सरकारी पोर्टल (cbic-gst.gov.in) पर अधिसूचना देखें।",
                "विस्तृत कर परामर्श के लिए अपने चार्टर्ड एकाउंटेंट (CA) से संपर्क करें।"
            ],
            "disclaimer": "यह प्रणाली केवल आधिकारिक परिपत्रों और अधिसूचनाओं पर आधारित सूचना प्रदान करती है।"
        },
        "en": {
            "summary": "We could not find sufficient authoritative evidence in official circulars to answer this query with high confidence, or the query requires personalized tax computation.",
            "next_steps": [
                "Refine your query by specifying exact details such as turnover threshold, goods vs services, or state jurisdiction.",
                "Refer to official government portals at cbic-gst.gov.in or udyamregistration.gov.in.",
                "Consult a licensed Chartered Accountant (CA) or tax professional for personalized filing guidance."
            ],
            "disclaimer": "Informational use only. Does not constitute formal legal or tax counsel."
        }
    }

    def create_abstention_response(
        self,
        language: str,
        as_of: date,
        corpus_updated: date,
    ) -> AskResponse:
        """Constructs an AskResponse marked as abstained."""
        lang_key = language if language in self.ABSTENTION_MESSAGES else "en"
        copy = self.ABSTENTION_MESSAGES[lang_key]

        return AskResponse(
            answer_id=uuid4(),
            language=lang_key,
            abstained=True,
            summary=copy["summary"],
            claims=[],
            next_steps=copy["next_steps"],
            as_of=as_of,
            corpus_updated=corpus_updated,
            disclaimer=copy["disclaimer"],
        )
