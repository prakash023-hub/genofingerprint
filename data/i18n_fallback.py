"""Fallback patient text by language (when Claude API unavailable)."""

FALLBACK_PATIENT = {
    "English": "Your genetic profile has been analyzed using CPIC international guidelines. Your doctor will explain which medicines are safest for you.",
    "Tamil": "உங்கள் மரபணு சுயவிவரம் CPIC வழிகாட்டுதல்களின் படி பகுப்பாய்வு செய்யப்பட்டது. உங்களுக்கு எந்த மருந்துகள் பாதுகாப்பானவை என்று மருத்துவர் விளக்குவார்.",
    "Hindi": "आपकी आनुवंशिक प्रोफ़ाइल CPIC अंतरराष्ट्रीय दिशानिर्देशों के अनुसार विश्लेषित की गई है। आपके डॉक्टर बताएंगे कि आपके लिए कौन-सी दवाएँ सबसे सुरक्षित हैं।",
    "Spanish": "Su perfil genético se analizó según las guías internacionales CPIC. Su médico le explicará qué medicamentos son más seguros para usted.",
    "French": "Votre profil génétique a été analysé selon les directives internationales CPIC. Votre médecin vous expliquera quels médicaments vous conviennent le mieux.",
    "Arabic": "تم تحليل ملفك الجيني وفق إرشادات CPIC الدولية. سيوضح لك طبيبك الأدوية الأكثر أماناً لك.",
    "Chinese": "您的基因图谱已按 CPIC 国际指南分析。医生将向您说明最适合您的药物。",
    "Portuguese": "Seu perfil genético foi analisado conforme as diretrizes internacionais CPIC. Seu médico explicará quais medicamentos são mais seguros para você.",
}

SUPPORTED_LANGUAGES = list(FALLBACK_PATIENT.keys())

LANGUAGE_LABELS = {
    "English": "English",
    "Tamil": "தமிழ் Tamil",
    "Hindi": "हिन्दी Hindi",
    "Spanish": "Español",
    "French": "Français",
    "Arabic": "العربية",
    "Chinese": "中文",
    "Portuguese": "Português",
}

# Case-specific patient alerts keyed by drug (CPIC action summary)
DRUG_PATIENT_ALERTS: dict[str, dict[str, str]] = {
    "clopidogrel": {
        "English": "Your CYP2C19 genes mean clopidogrel may not protect you well after a stent. Your doctor may switch to prasugrel or ticagrelor — do not stop any medicine without asking them.",
        "Tamil": "உங்கள் CYP2C19 மரபணு காரணமாக clopidogrel stent-க்குப் பிறகு போதுமான பாதுகாப்பு தராது. மருத்துவர் prasugrel அல்லது ticagrelor மாற்றலாம் — மருந்தை நிறுத்த வேண்டாம்.",
        "Hindi": "आपके CYP2C19 जीन के कारण clopidogrel stent के बाद पर्याप्त सुरक्षा नहीं दे सकता। डॉक्टर prasugrel या ticagrelor दे सकते हैं — दवा बिना पूछे बंद न करें।",
        "Spanish": "Sus genes CYP2C19 pueden hacer que clopidogrel no le proteja bien tras un stent. Su médico puede cambiar a prasugrel o ticagrelor; no suspenda medicamentos sin consultar.",
        "French": "Vos gènes CYP2C19 peuvent réduire l'efficacité du clopidogrel après un stent. Votre médecin peut prescrire prasugrel ou ticagrelor — ne stoppez pas seul.",
        "Arabic": "جينات CYP2C19 قد تجعل clopidogrel أقل فعالية بعد الدعامة. قد يختار طبيبك prasugrel أو ticagrelor — لا توقف الدواء دون استشارة.",
        "Chinese": "您的 CYP2C19 基因可能导致氯吡格雷在支架术后保护不足。医生可能改用 prasugrel 或 ticagrelor，请勿自行停药。",
        "Portuguese": "Seus genes CYP2C19 podem reduzir a proteção do clopidogrel após stent. Seu médico pode trocar para prasugrel ou ticagrelor — não pare remédios sozinho.",
    },
    "tamoxifen": {
        "English": "Your CYP2D6 genotype may reduce tamoxifen activation. Your oncologist may choose an aromatase inhibitor instead — follow their plan.",
        "Tamil": "உங்கள் CYP2D6 மரபணு tamoxifen செயல்படுத்தலை குறைக்கலாம். ஆன்காலஜிஸ்ட் aromatase inhibitor தேர்வு செய்யலாம்.",
        "Hindi": "आपका CYP2D6 जीन tamoxifen की सक्रियता कम कर सकता है। ऑन्कोलॉजिस्ट aromatase inhibitor चुन सकते हैं।",
        "Spanish": "Su genotipo CYP2D6 puede reducir la activación de tamoxifeno. Su oncólogo puede elegir un inhibidor de aromatasa.",
        "French": "Votre génotype CYP2D6 peut réduire l'activation du tamoxifène. Votre oncologue peut choisir un inhibiteur de l'aromatase.",
        "Arabic": "نوع CYP2D6 قد يقلل تفعيل tamoxifen. قد يختار طبيب الأورام مثبط aromatase.",
        "Chinese": "您的 CYP2D6 基因型可能降低他莫昔芬活化。肿瘤科医生可能改用芳香化酶抑制剂。",
        "Portuguese": "Seu genótipo CYP2D6 pode reduzir a ativação do tamoxifeno. Seu oncologista pode escolher inibidor de aromatase.",
    },
    "simvastatin": {
        "English": "Your SLCO1B1 genotype raises myopathy risk with simvastatin. Your doctor may lower the dose or switch to pravastatin or rosuvastatin.",
        "Tamil": "உங்கள் SLCO1B1 மரபணு simvastatin-இல் muscle பாதிப்பு அபாயத்தை அதிகரிக்கும். மருத்துவர் dose குறைக்கலாம் அல்லது மாற்றலாம்.",
        "Hindi": "आपका SLCO1B1 जीन simvastatin से muscle damage का जोखिम बढ़ाता है। डॉक्टर dose कम या दवा बदल सकते हैं।",
        "Spanish": "Su gen SLCO1B1 aumenta el riesgo de miopatía con simvastatina. Su médico puede reducir la dosis o cambiar el fármaco.",
        "French": "Votre gène SLCO1B1 augmente le risque de myopathie avec la simvastatine. Votre médecin peut ajuster le traitement.",
        "Arabic": "جين SLCO1B1 يرفع خطر اعتلال العضلات مع simvastatin. قد يعدل طبيبك الجرعة أو الدواء.",
        "Chinese": "SLCO1B1 基因型增加辛伐他汀肌病风险。医生可能减量或换药。",
        "Portuguese": "Seu gene SLCO1B1 aumenta risco de miopatia com sinvastatina. Seu médico pode ajustar dose ou medicamento.",
    },
    "codeine": {
        "English": "Your CYP2D6 profile affects codeine conversion to morphine. Your doctor may avoid codeine or choose a safer pain medicine.",
        "Tamil": "உங்கள் CYP2D6 codeine → morphine மாற்றத்தை பாதிக்கும். மருத்துவர் வேறு pain medicine தேர்வு செய்யலாம்.",
        "Hindi": "आपका CYP2D6 codeine से morphine रूपांतरण को प्रभावित करता है। डॉक्टर सुरक्षित दर्द की दवा चुन सकते हैं।",
        "Spanish": "Su perfil CYP2D6 afecta la conversión de codeína. Su médico puede evitar codeína o elegir otro analgésico.",
        "French": "Votre profil CYP2D6 affecte la conversion de la codéine. Votre médecin peut choisir une autre analgésie.",
        "Arabic": "ملف CYP2D6 يؤثر على تحويل codeine. قد يتجنب طبيبك codeine أو يختار بديلاً.",
        "Chinese": "CYP2D6 影响可待因转化。医生可能避免使用可待因或选择其他止痛药。",
        "Portuguese": "Seu perfil CYP2D6 afeta a conversão da codeína. Seu médico pode evitar codeína ou escolher outro analgésico.",
    },
    "warfarin": {
        "English": "Your CYP2C9 genotype affects warfarin breakdown. Your doctor will likely use a lower starting dose and monitor INR closely.",
        "Tamil": "உங்கள் CYP2C9 warfarin metabolism-ஐ பாதிக்கும். குறைந்த dose மற்றும் INR monitoring தேவை.",
        "Hindi": "आपका CYP2C9 warfarin metabolism को प्रभावित करता है। कम शुरुआती dose और INR monitoring जरूरी हो सकती है।",
        "Spanish": "Su genotipo CYP2C9 afecta la warfarina. Probablemente necesite dosis inicial más baja y control de INR.",
        "French": "Votre génotype CYP2C9 affecte la warfarine. Dose initiale plus basse et surveillance INR probables.",
        "Arabic": "نوع CYP2C9 يؤثر على warfarin. قد تحتاج جرعة أولية أقل ومراقبة INR.",
        "Chinese": "CYP2C9 影响华法林代谢。可能需要更低起始剂量并密切监测 INR。",
        "Portuguese": "Seu genótipo CYP2C9 afeta a warfarina. Dose inicial menor e monitoramento de INR prováveis.",
    },
    "azathioprine": {
        "English": "Your TPMT genotype raises risk with azathioprine. Your doctor must reduce dose sharply or choose an alternative — blood count monitoring is essential.",
        "Tamil": "உங்கள் TPMT azathioprine-இல் அதிக ஆபத்து. dose குறைப்பு அல்லது மாற்று தேவை; blood test monitoring அவசியம்.",
        "Hindi": "आपका TPMT azathioprine के साथ जोखिम बढ़ाता है। dose कम या विकल्प जरूरी; blood monitoring आवश्यक।",
        "Spanish": "Su genotipo TPMT aumenta el riesgo con azatioprina. Se requiere reducir dosis o cambiar fármaco y controlar hemograma.",
        "French": "Votre génotype TPMT augmente le risque avec l'azathioprine. Réduction de dose ou alternative et surveillance sanguine nécessaires.",
        "Arabic": "نوع TPMT يرفع خطر azathioprine. يلزم تخفيض الجرعة أو بديل ومراقبة الدم.",
        "Chinese": "TPMT 基因型增加硫唑嘌呤风险。需减量或换药并监测血常规。",
        "Portuguese": "Seu genótipo TPMT aumenta risco com azatioprina. Redução de dose ou alternativa e monitoramento sanguíneo necessários.",
    },
}
