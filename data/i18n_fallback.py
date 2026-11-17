"""Approved patient-facing guidance shared by the app and report."""

FALLBACK_PATIENT = {
    "English": "Review these research results with your clinician. Talk to them before starting, stopping, or changing any medicine.",
    "Tamil": "இந்த ஆராய்ச்சி முடிவுகளை உங்கள் மருத்துவருடன் பரிசீலிக்கவும். எந்த மருந்தையும் தொடங்குவதற்கு, நிறுத்துவதற்கு அல்லது மாற்றுவதற்கு முன் அவரிடம் பேசுங்கள்.",
    "Hindi": "इन शोध परिणामों की समीक्षा अपने डॉक्टर के साथ करें। कोई दवा शुरू करने, बंद करने या बदलने से पहले उनसे बात करें।",
    "Spanish": "Revise estos resultados de investigación con su médico. Consulte antes de iniciar, suspender o cambiar cualquier medicamento.",
    "French": "Examinez ces résultats de recherche avec votre médecin. Consultez-le avant de commencer, d’arrêter ou de modifier un médicament.",
    "Arabic": "راجع نتائج هذا البحث مع طبيبك. تحدث معه قبل البدء بأي دواء أو إيقافه أو تغييره.",
    "Chinese": "请与医生一起审阅这些研究结果。在开始、停止或更改任何药物之前，请先咨询医生。",
    "Portuguese": "Revise estes resultados de pesquisa com seu médico. Converse com ele antes de iniciar, interromper ou alterar qualquer medicamento.",
}

SUPPORTED_LANGUAGES = list(FALLBACK_PATIENT)

LANGUAGE_LABELS = {
    "English": "English",
    "Tamil": "தமிழ் Tamil",
    "Hindi": "हिन्दी Hindi",
    "Spanish": "Español",
    "French": "Français",
    "Arabic": "العربية Arabic",
    "Chinese": "中文 Chinese",
    "Portuguese": "Português",
}
