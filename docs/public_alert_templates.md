# JALDRISHTI AI — Public Alert Multilingual Templates

## 1. Governance & Parameterization
Public safety messages must never claim to be official government warnings and must not allow uncontrolled, generative hallucination. All messages are parameterized according to pre-approved standard templates.

### Official Authority Disclaimers
- **English**: `JALDRISHTI DECISION SUPPORT: Follow official SDMA/DDMA emergency instructions.`
- **Hindi**: `जलदृष्टि निर्णय सहायता: कृपया आधिकारिक आपदा प्रबंधन (SDMA/DDMA) के निर्देशों का पालन करें।`

## 2. English Template Specifications (`en`)

| Severity | Template ID | Title Format | Body Format |
|---|---|---|---|
| `WATCH` | `DLT-JALDRISHTI-WATCH-EN` | `JALDRISHTI ADVISORY: Monitoring Active near {locality}` | `JALDRISHTI ADVISORY: Elevated water levels or moderate rainfall active near {locality}. Expected window: {expected_time}. {disclaimer}` |
| `WARNING` | `DLT-JALDRISHTI-WARNING-EN` | `JALDRISHTI WARNING: Flood Risk Rising near {locality}` | `JALDRISHTI WARNING: High rainfall and rising river stage detected near {locality}. Impact expected around {expected_time}. Move valuables to high ground. {disclaimer}` |
| `HIGH_RISK` | `DLT-JALDRISHTI-HIGH_RISK-EN` | `JALDRISHTI ALERT: Severe Inundation Threat near {locality}` | `JALDRISHTI ALERT: River level nearing danger mark near {locality}. Flooding expected within {expected_time}. Prepare for possible evacuation. {disclaimer}` |
| `CRITICAL` | `DLT-JALDRISHTI-CRITICAL-EN` | `JALDRISHTI CRITICAL: Immediate Flood Danger near {locality}` | `JALDRISHTI CRITICAL: Extreme flood inundation active near {locality}. Immediate safety precautions required. {disclaimer}` |
| `RESOLVED` | `DLT-JALDRISHTI-RESOLVED-EN` | `JALDRISHTI NOTICE: Flood Risk Receding near {locality}` | `JALDRISHTI NOTICE: Water levels have crest and are receding near {locality}. Continue monitoring local advisories. {disclaimer}` |

## 3. Hindi Template Specifications (`hi`)

| Severity | Template ID | Title Format | Body Format |
|---|---|---|---|
| `WATCH` | `DLT-JALDRISHTI-WATCH-HI` | `जलदृष्टि सूचना: {locality} के पास जलस्तर निगरानी जारी` | `जलदृष्टि सूचना: {locality} के पास वर्षा और जलस्तर में वृद्धि देखी गई है। संभावित समय: {expected_time}। {disclaimer}` |
| `WARNING` | `DLT-JALDRISHTI-WARNING-HI` | `जलदृष्टि चेतावनी: {locality} के निकट बाढ़ का खतरा` | `जलदृष्टि चेतावनी: {locality} में भारी वर्षा व नदी जलस्तर में तेजी से वृद्धि। अनुमानित समय: {expected_time}। सतर्क रहें। {disclaimer}` |
| `HIGH_RISK` | `DLT-JALDRISHTI-HIGH_RISK-HI` | `जलदृष्टि अलर्ट: {locality} में गंभीर जलभराव का खतरा` | `जलदृष्टि अलर्ट: {locality} में नदी का स्तर खतरे के निशान के पास। {expected_time} के भीतर जलभराव संभव। सुरक्षित स्थान पर जाने की तैयारी करें। {disclaimer}` |
| `CRITICAL` | `DLT-JALDRISHTI-CRITICAL-HI` | `जलदृष्टि आपातकालीन: {locality} में तुरंत सुरक्षा उपाय करें` | `जलदृष्टि आपातकालीन: {locality} में गंभीर बाढ़ का खतरा। तुरंत सुरक्षित स्थानों पर जाएं और निर्देशों का पालन करें। {disclaimer}` |
| `RESOLVED` | `DLT-JALDRISHTI-RESOLVED-HI` | `जलदृष्टि सूचना: {locality} में जलस्तर में कमी` | `जलदृष्टि सूचना: {locality} में नदी का जलस्तर कम हो रहा है। स्थिति सामान्य होने तक सतर्क रहें। {disclaimer}` |
