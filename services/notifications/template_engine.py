"""
Multilingual Notification Template Engine for JALDRISHTI AI.
Generates parameterized SMS, Push, and In-App messages in English and Hindi
with strict official authority disclaimers.
"""

from typing import Dict, Any, Optional
from services.notifications.notification_types import NotificationSeverityPolicy

# Base official disclaimers
DISCLAIMER_EN = "JALDRISHTI DECISION SUPPORT: Follow official SDMA/DDMA emergency instructions."
DISCLAIMER_HI = "जलदृष्टि निर्णय सहायता: कृपया आधिकारिक आपदा प्रबंधन (SDMA/DDMA) के निर्देशों का पालन करें।"

# Approved parameterized notification templates
TEMPLATES: Dict[str, Dict[str, Dict[str, str]]] = {
    "en": {
        "WATCH": {
            "title": "JALDRISHTI ADVISORY: Monitoring Active near {locality}",
            "body": "JALDRISHTI ADVISORY: Elevated water levels or moderate rainfall active near {locality}. Expected window: {expected_time}. {disclaimer}"
        },
        "WARNING": {
            "title": "JALDRISHTI WARNING: Flood Risk Rising near {locality}",
            "body": "JALDRISHTI WARNING: High rainfall and rising river stage detected near {locality}. Impact expected around {expected_time}. Move valuables to high ground. {disclaimer}"
        },
        "HIGH_RISK": {
            "title": "JALDRISHTI ALERT: Severe Inundation Threat near {locality}",
            "body": "JALDRISHTI ALERT: River level nearing danger mark near {locality}. Flooding expected within {expected_time}. Prepare for possible evacuation. {disclaimer}"
        },
        "CRITICAL": {
            "title": "JALDRISHTI CRITICAL: Immediate Flood Danger near {locality}",
            "body": "JALDRISHTI CRITICAL: Extreme flood inundation active near {locality}. Immediate safety precautions required. {disclaimer}"
        },
        "RESOLVED": {
            "title": "JALDRISHTI NOTICE: Flood Risk Receding near {locality}",
            "body": "JALDRISHTI NOTICE: Water levels have crest and are receding near {locality}. Continue monitoring local advisories. {disclaimer}"
        }
    },
    "hi": {
        "WATCH": {
            "title": "जलदृष्टि सूचना: {locality} के पास जलस्तर निगरानी जारी",
            "body": "जलदृष्टि सूचना: {locality} के पास वर्षा और जलस्तर में वृद्धि देखी गई है। संभावित समय: {expected_time}। {disclaimer}"
        },
        "WARNING": {
            "title": "जलदृष्टि चेतावनी: {locality} के निकट बाढ़ का खतरा",
            "body": "जलदृष्टि चेतावनी: {locality} में भारी वर्षा व नदी जलस्तर में तेजी से वृद्धि। अनुमानित समय: {expected_time}। सतर्क रहें। {disclaimer}"
        },
        "HIGH_RISK": {
            "title": "जलदृष्टि अलर्ट: {locality} में गंभीर जलभराव का खतरा",
            "body": "जलदृष्टि अलर्ट: {locality} में नदी का स्तर खतरे के निशान के पास। {expected_time} के भीतर जलभराव संभव। सुरक्षित स्थान पर जाने की तैयारी करें। {disclaimer}"
        },
        "CRITICAL": {
            "title": "जलदृष्टि आपातकालीन: {locality} में तुरंत सुरक्षा उपाय करें",
            "body": "जलदृष्टि आपातकालीन: {locality} में गंभीर बाढ़ का खतरा। तुरंत सुरक्षित स्थानों पर जाएं और निर्देशों का पालन करें। {disclaimer}"
        },
        "RESOLVED": {
            "title": "जलदृष्टि सूचना: {locality} में जलस्तर में कमी",
            "body": "जलदृष्टि सूचना: {locality} में नदी का जलस्तर कम हो रहा है। स्थिति सामान्य होने तक सतर्क रहें। {disclaimer}"
        }
    }
}

class TemplateEngine:
    """
    Renders parameterized SMS, Push, and In-App notification content.
    """

    @classmethod
    def render_notification(
        cls,
        severity: NotificationSeverityPolicy,
        locality: str,
        expected_time: str = "next 6-12 hours",
        language: str = "en",
        data_degraded_notice: bool = False
    ) -> Dict[str, str]:
        """
        Renders template into {title, body, template_id}.
        """
        lang = language if language in TEMPLATES else "en"
        sev_key = severity.value if hasattr(severity, "value") else str(severity)
        if sev_key not in TEMPLATES[lang]:
            sev_key = "WATCH"

        template = TEMPLATES[lang][sev_key]
        disclaimer = DISCLAIMER_HI if lang == "hi" else DISCLAIMER_EN

        title = template["title"].format(locality=locality)
        body = template["body"].format(
            locality=locality,
            expected_time=expected_time,
            disclaimer=disclaimer
        )

        if data_degraded_notice:
            if lang == "hi":
                body += " (सूचना: प्राथमिक टेलीमेट्री ऑफलाइन होने के कारण यह पूर्वानुमान आंशिक रूप से मॉडल पर आधारित है।)"
            else:
                body += " (Note: Forecast is partly model-based due to telemetry degradation.)"

        return {
            "title": title,
            "body": body,
            "template_id": f"DLT-JALDRISHTI-{sev_key}-{lang.upper()}"
        }

# Global singleton
template_engine = TemplateEngine()
