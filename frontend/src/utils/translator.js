import { translateText } from '../api/client.js';

export const SUPPORTED_LANGUAGES = [
  { code: 'en', label: 'English', native: 'English' },
  { code: 'hi', label: 'Hindi', native: 'हिंदी' },
  { code: 'ta', label: 'Tamil', native: 'தமிழ்' },
  { code: 'bn', label: 'Bengali', native: 'বাংলা' },
  { code: 'te', label: 'Telugu', native: 'తెలుగు' },
  { code: 'mr', label: 'Marathi', native: 'मराठी' },
  { code: 'gu', label: 'Gujarati', native: 'ગુજરાતી' },
  { code: 'kn', label: 'Kannada', native: 'ಕನ್ನಡ' },
  { code: 'ml', label: 'Malayalam', native: 'മലയാളം' },
  { code: 'pa', label: 'Punjabi', native: 'ਪੰਜਾਬੀ' },
  { code: 'or', label: 'Odia', native: 'ଓଡ଼ିଆ' },
  { code: 'ur', label: 'Urdu', native: 'اردو' },
];

const UI_DICTIONARY = {
  hi: {
    // App Header & Navigation
    'IP-SAKTI Sahayak': 'आईपी-शक्ति सहायक',
    'AYUSH IP & regulatory guidance': 'आयुष आईपी एवं नियामक मार्गदर्शन',
    'Jurisdiction': 'क्षेत्राधिकार',
    'Questionnaire': 'प्रश्नावली',
    'Classification': 'वर्गीकरण',
    'Ask & Explore': 'पूछें और अन्वेषण करें',

    // Landing Screen
    'Know how the law treats your Ayurvedic product — before you file anything.': 'जानें कि कानून आपके आयुर्वेदिक उत्पाद का इलाज कैसे करता है — कुछ भी दायर करने से पहले।',
    'Classical formulation or new combination? India or international? Patent, trademark, or regulatory pathway? Answer a few questions and get a grounded, citation-backed answer — with a confidence score, and an honest "we don\'t know" when the corpus doesn\'t cover it.': 'शास्त्रीय फॉर्मूलेशन या नया संयोजन? भारत या अंतर्राष्ट्रीय? पेटेंट, ट्रेडमार्क, या नियामक मार्ग? कुछ प्रश्नों के उत्तर दें और एक आधारित, उद्धरण-समर्थित उत्तर प्राप्त करें — एक आत्मविश्वास स्कोर के साथ।',
    'Formulation-aware classification, not a generic chatbot guess': 'फॉर्मूलेशन-जागरूक वर्गीकरण, न कि एक सामान्य चैटबॉट अनुमान',
    'Every claim traces back to an actual statute, rule, or treaty section': 'प्रत्येक दावा एक वास्तविक कानून, नियम या संधि अनुभाग तक वापस जाता है',
    'India and international answers are kept in separate, labelled lanes': 'भारत और अंतर्राष्ट्रीय उत्तरों को अलग, लेबल वाली श्रेणियों में रखा गया है',
    'Start Assessment': 'मूल्यांकन शुरू करें',
    'Starting session…': 'सत्र शुरू हो रहा है…',
    'Try again': 'पुनः प्रयास करें',
    'This tool provides information, not legal advice.': 'यह उपकरण जानकारी प्रदान करता है, कानूनी सलाह नहीं।',

    // Jurisdiction Screen
    'Select Jurisdiction': 'क्षेत्राधिकार चुनें',
    'Which legal framework applies to your question?': 'आपके प्रश्न पर कौन सा कानूनी ढांचा लागू होता है?',
    'Choose the jurisdiction applicable for your product assessment:': 'अपने उत्पाद मूल्यांकन के लिए उपयुक्त क्षेत्राधिकार चुनें:',
    'India': 'भारत',
    'International': 'अंतर्राष्ट्रीय',
    'Products intended primarily for protection or market entry in India.': 'मुख्य रूप से भारत में सुरक्षा या बाजार प्रवेश के लिए उत्पाद।',
    'Products seeking international patent or PCT pathways.': 'अंतर्राष्ट्रीय पेटेंट या पीसीटी मार्गों की तलाश करने वाले उत्पाद।',

    // Questionnaire Screen
    'Tell us about your product': 'हमें अपने उत्पाद के बारे में बताएं',
    'Product Intake Questionnaire': 'उत्पाद सेवन प्रश्नावली',
    'Tell us about your product to classify its IP and regulatory pathway.': 'अपने उत्पाद के आईपी और नियामक मार्ग को वर्गीकृत करने के लिए हमें इसके बारे में बताएं।',
    'Product name (optional)': 'उत्पाद का नाम (वैकल्पिक)',
    'What are you trying to protect?': 'आप किसकी सुरक्षा का प्रयास कर रहे हैं?',
    'Composition': 'संरचना / घटक',
    'Add ingredient': 'घटक जोड़ें',
    'Intended use': 'अभिप्रेत उपयोग',
    'Is it based on a classical/existing Ayurvedic formulation?': 'क्या यह शास्त्रीय/मौजूदा आयुर्वेदिक फॉर्मूलेशन पर आधारित है?',
    'Is the formulation new, modified, or existing?': 'क्या फॉर्मूलेशन नया, संशोधित या मौजूदा है?',
    'Source of ingredients (select all that apply)': 'सामग्री का स्रोत (सभी लागू विकल्प चुनें)',
    'Do you know the geographic origin of these ingredients?': 'क्या आप इन सामग्रियों के भौगोलिक मूल को जानते हैं?',
    'Yes': 'हाँ',
    'No': 'नहीं',
    'Development status': 'विकास की स्थिति',
    'What do you want to know? (select all that apply)': 'आप क्या जानना चाहते हैं? (सभी लागू विकल्प चुनें)',
    'Please tell us what you’re trying to protect.': 'कृपया हमें बताएं कि आप किसकी सुरक्षा का प्रयास कर रहे हैं।',
    'Please select at least one thing you want to know.': 'कृपया कम से कम एक चीज़ चुनें जो आप जानना चाहते हैं।',
    'Analyze & Classify': 'विश्लेषण और वर्गीकरण करें',
    'Classifying…': 'वर्गीकृत किया जा रहा है…',
    'Continue to classification': 'वर्गीकरण के लिए आगे बढ़ें',

    // Questionnaire Option Labels
    'Entire formulation / combination product': 'संपूर्ण फॉर्मूलेशन / संयोजन उत्पाद',
    'Single biological resource / extract / plant ingredient': 'एकल जैविक संसाधन / अर्क / पौधे की सामग्री',
    'Brand / product name / logo': 'ब्रांड / उत्पाद का नाम / लोगो',
    'Unsure / need guidance on what can be protected': 'अनिश्चित / क्या संरक्षित किया जा सकता है इस पर मार्गदर्शन की आवश्यकता है',
    'Human health / therapeutic / disease prevention': 'मानव स्वास्थ्य / उपचारात्मक / बीमारी की रोकथाम',
    'Wellness / dietary supplement / nutraceutical / general health': 'वेलनेस / आहार अनुपूरक / न्यूट्रास्युटिकल / सामान्य स्वास्थ्य',
    'Cosmetic / skincare / personal care': 'सौंदर्य प्रसाधन / त्वचा की देखभाल / व्यक्तिगत देखभाल',
    'Yes — mentioned in classical texts (e.g. Charaka, Sushruta, Ayurvedic Pharmacopoeia)': 'हाँ — शास्त्रीय ग्रंथों में उल्लेखित (जैसे चरक, सुश्रुत, आयुर्वेदिक फार्माकोपोइया)',
    'No — newly developed formulation / combination': 'नहीं — नया विकसित फॉर्मूलेशन / संयोजन',
    'Unsure whether it is classical or new': 'अनिश्चित कि यह शास्त्रीय है या नया',
    'Completely new formulation (no prior public record)': 'पूरी तरह से नया फॉर्मूलेशन (कोई पूर्व सार्वजनिक रिकॉर्ड नहीं)',
    'Modified version of a classical formulation (new ratio, ingredient, or form)': 'शास्त्रीय फॉर्मूलेशन का संशोधित संस्करण (नया अनुपात, घटक या रूप)',
    'Existing formulation being produced/sold under a new brand': 'नये ब्रांड के तहत निर्मित/बेचा जा रहा मौजूदा फॉर्मूलेशन',
    'Plant / botanical / herbal': 'पौधा / वनस्पति / हर्बल',
    'Animal-derived ingredient (e.g. ghee, milk, honey, lard)': 'पशु-व्युत्पन्न सामग्री (जैसे घी, दूध, शहद)',
    'Mineral / metallic / Bhasma / Rasa shastra ingredient': 'खनिज / धात्विक / भस्म / रस शास्त्र घटक',
    'Synthetic / chemical ingredient added': 'सिंथेटिक / रासायनिक घटक जोड़ा गया',
    'Concept / lab scale formulation': 'अवधारणा / लैब स्केल फॉर्मूलेशन',
    'Formulation finalized, ready for testing/launch': 'फॉर्मूलेशन को अंतिम रूप दिया गया, परीक्षण/लॉन्च के लिए तैयार',
    'Commercial product already in market': 'बाजार में पहले से ही वाणिज्यिक उत्पाद मौजूद है',
    'Patentability / IPR eligibility of formulation': 'फॉर्मूलेशन की पेटेंट योग्यता / आईपीआर पात्रता',
    'Regulatory classification (Drug vs AYUSH vs Food/FSSAI vs Cosmetic)': 'नियामक वर्गीकरण (दवा बनाम आयुष बनाम खाद्य/एफएसएसएआई बनाम सौंदर्य प्रसाधन)',
    'Trademark / brand protection': 'ट्रेडमार्क / ब्रांड सुरक्षा',
    'Prior art / TKDL conflict check': 'पूर्व कला / टीकेडीएल संघर्ष जाँच',
    'Access and Benefit-Sharing (ABS) compliance under Biological Diversity Act': 'जैविक विविधता अधिनियम के तहत पहुंच और लाभ-साझाकरण (एबीएस) अनुपालन',
    'Overall legal protection pathway': 'समग्र कानूनी सुरक्षा मार्ग',

    // Classification Result Screen
    'Deterministic rule engine — not an AI guess': 'निश्चित नियम इंजन — कोई एआई अनुमान नहीं',
    'confidence': 'आत्मविश्वास',
    'Flagged for your review': 'आपकी समीक्षा के लिए फ़्लैग किया गया',
    'Back to Questionnaire': 'प्रश्नावली पर वापस जाएं',
    'Continue to Ask & Explore': 'पूछें और अन्वेषण करें पर जारी रखें',

    // Workspace & Voice Chat
    'Based on what you told us, you might ask:': 'आपने जो बताया उसके आधार पर आप पूछ सकते हैं:',
    'Text Chat': 'पाठ चैट',
    'Voice AI Assistant': 'आवाज एआई सहायक',
    'Can I patent this formulation?': 'क्या मैं इस फॉर्मूलेशन को पेटेंट करा सकता हूं?',
    'What regulatory category does this product fall under?': 'यह उत्पाद किस नियामक श्रेणी में आता है?',
    'How can I protect the brand or product name?': 'मैं ब्रांड या उत्पाद का नाम कैसे सुरक्षित कर सकता हूं?',
    'Has a formulation like this been done before?': 'क्या इस तरह का फॉर्मूलेशन पहले कभी किया गया है?',
    'Do Access and Benefit-Sharing obligations apply to this product?': 'क्या इस उत्पाद पर पहुंच और लाभ-साझाकरण दायित्व लागू होते हैं?',
    'What is the overall legal pathway for protecting this product?': 'इस उत्पाद की सुरक्षा के लिए समग्र कानूनी मार्ग क्या है?',
    'What should I know about protecting this product?': 'मुझे इस उत्पाद की सुरक्षा के बारे में क्या जानना चाहिए?',
    'Ask a question about this product\'s IP or regulatory pathway…': 'इस उत्पाद के आईपी या नियामक मार्ग के बारे में एक प्रश्न पूछें…',
    'Ask': 'पूछें',
    'Asking…': 'पूछ रहे हैं…',
    'Click the microphone and speak your question…': 'माइक्रोफोन पर क्लिक करें और अपना प्रश्न बोलें…',
    'Listening... Speak now': 'सुन रहे हैं... अब बोलें',
    'Processing voice query with Bhashini...': 'भाषिणी के साथ आवाज प्रश्न संसाधित कर रहे हैं...',
    'Stop Recording & Send': 'रिकॉर्डिंग रोकें और भेजें',
    'Tap to speak': 'बोलने के लिए टैप करें',
    'Listen Voice': 'उत्तर सुनें',
    'Pause': 'रोकें',
    'TKDL Search': 'टीकेडीएल खोज',
    'ABS Helper': 'एबीएस सहायक',
  },
  ta: {
    'IP-SAKTI Sahayak': 'ஐபி-சக்தி சகாயக்',
    'AYUSH IP & regulatory guidance': 'ஆயுஷ் ஐபி மற்றும் ஒழுங்குமுறை வழிகாட்டுதல்',
    'Jurisdiction': 'அதிகார வரம்பு',
    'Questionnaire': 'கேள்வித்தாள்',
    'Classification': 'வகைப்பாடு',
    'Ask & Explore': 'கேளுங்கள் & ஆராயுங்கள்',
    'Start Assessment': 'மதிப்பீட்டைத் தொடங்குங்கள்',
    'Select Jurisdiction': 'அதிகார வரம்பைத் தேர்ந்தெடுக்கவும்',
    'India': 'இந்தியா',
    'International': 'சர்வதேசம்',
    'Product Intake Questionnaire': 'தயாரிப்பு உட்கொள்ளல் கேள்வித்தாள்',
    'Tell us about your product': 'உங்கள் தயாரிப்பைப் பற்றி எங்களிடம் கூறுங்கள்',
    'Analyze & Classify': 'பகுப்பாய்வு செய்து வகைப்படுத்துக',
    'Back': 'பின்னால்',
    'Text Chat': 'உரை அரட்டை',
    'Voice AI Assistant': 'குரல் AI உதவியாளர்',
    'Ask': 'கேளுங்கள்',
    'Tap to speak': 'பேச தட்டவும்',
  },
  bn: {
    'IP-SAKTI Sahayak': 'আইপি-শক্তি সহায়ক',
    'Jurisdiction': 'এখতিয়ার',
    'Questionnaire': 'প্রশ্নাবলী',
    'Classification': 'শ্রেণীবিভাগ',
    'Ask & Explore': 'জিজ্ঞাসা ও অন্বেষণ',
    'Start Assessment': 'মূল্যায়ন শুরু করুন',
    'Select Jurisdiction': 'এখতিয়ার নির্বাচন করুন',
    'India': 'ভারত',
    'International': 'আন্তর্জাতিক',
    'Product Intake Questionnaire': 'পণ্য গ্রহণ প্রশ্নাবলী',
    'Analyze & Classify': 'বিশ্লেষণ ও শ্রেণীবদ্ধ করুন',
    'Back': 'ফিরে যান',
    'Text Chat': 'টেক্সট চ্যাট',
    'Voice AI Assistant': 'ভয়েস এআই সহকারী',
    'Ask': 'জিজ্ঞাসা করুন',
  },
  te: {
    'IP-SAKTI Sahayak': 'ఐపి-శక్తి సహాయక్',
    'Jurisdiction': 'పరిధి',
    'Questionnaire': 'ప్రశ్నాపత్రం',
    'Classification': 'వర్గీకరణ',
    'Ask & Explore': 'అడగండి & అన్వేషించండి',
    'Start Assessment': 'అంచనాను ప్రారంభించండి',
    'Select Jurisdiction': 'పరిధిని ఎంచుకోండి',
    'India': 'భారతదేశం',
    'International': 'అంతర్జాతీయ',
    'Text Chat': 'టెక్స్ట్ చాట్',
    'Voice AI Assistant': 'వాయిస్ AI అసిస్టెంట్',
  },
};

const translationCache = new Map();
const pendingTranslations = new Map();

/**
 * Translate a single UI string synchronously if in dictionary or cache.
 */
export function t(text, lang = 'en') {
  if (!text || lang === 'en') return text;

  // Check static dictionary first
  if (UI_DICTIONARY[lang] && UI_DICTIONARY[lang][text]) {
    return UI_DICTIONARY[lang][text];
  }

  // Check dynamic memory cache
  const cacheKey = `${lang}:${text}`;
  if (translationCache.has(cacheKey)) {
    return translationCache.get(cacheKey);
  }

  return text;
}

/**
 * Translate arbitrary UI text dynamically using Bhashini NMT API if missing from dictionary.
 */
export async function translateAsync(text, targetLang) {
  if (!text || targetLang === 'en') return text;

  const cacheKey = `${targetLang}:${text}`;
  if (translationCache.has(cacheKey)) {
    return translationCache.get(cacheKey);
  }

  if (UI_DICTIONARY[targetLang] && UI_DICTIONARY[targetLang][text]) {
    return UI_DICTIONARY[targetLang][text];
  }

  if (!pendingTranslations.has(cacheKey)) {
    pendingTranslations.set(cacheKey, translateText(text, targetLang, 'en')
      .then((res) => {
        const translated = res.translated_text || text;
        if (translated !== text) translationCache.set(cacheKey, translated);
        return translated;
      })
      .catch((err) => {
        console.warn('[translateAsync] failed:', err);
        return text;
      })
      .finally(() => pendingTranslations.delete(cacheKey)));
  }
  return pendingTranslations.get(cacheKey);
}
