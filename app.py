import os
import re
import sqlite3
import smtplib
from datetime import date, datetime, timedelta
from email.mime.text import MIMEText

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from sklearn.ensemble import RandomForestClassifier


# ═══════════════════════════════════════
# APP CONFIG
# ═══════════════════════════════════════
st.set_page_config(page_title="MaternalCare India", page_icon="🏥", layout="wide")
DB_NAME = "maternal_health_portal.db"


# ═══════════════════════════════════════
# LANGUAGE
# ═══════════════════════════════════════
if "lang" not in st.session_state:
    st.session_state["lang"] = "en"

L = st.session_state["lang"]


def T(en, hi):
    return hi if st.session_state.get("lang", "en") == "hi" else en


# ═══════════════════════════════════════
# PAGE DEFINITIONS
# ═══════════════════════════════════════
PAGES = [
    ("home", "🏠 Home", "🏠 होम"),
    ("register", "📝 Register Beneficiary", "📝 लाभार्थी पंजीकरण"),
    ("journey", "🤰 Maternal Journey", "🤰 मातृ यात्रा"),
    ("baby_dev", "🌱 Baby Development", "🌱 शिशु विकास"),
    ("health", "💓 Health Tracker", "💓 स्वास्थ्य ट्रैकर"),
    ("medicine", "💊 Medicine Tracker", "💊 दवाई ट्रैकर"),
    ("nutrition", "🥗 Nutrition Guide", "🥗 पोषण मार्गदर्शिका"),
    ("yoga", "🧘 Yoga & Wellness", "🧘 योग और कल्याण"),
    ("risk", "🤖 Risk Assessment", "🤖 जोखिम मूल्यांकन"),
    ("checkup", "📅 Checkup Schedule", "📅 जाँच अनुसूची"),
    ("govt", "🏛️ Government Benefits", "🏛️ सरकारी योजनाएँ"),
    ("postdelivery", "👶 Post-Delivery Care", "👶 प्रसव बाद देखभाल"),
    ("ppd", "🧠 PPD Screening", "🧠 प्रसवोत्तर अवसाद जाँच"),
    ("kick", "👣 Kick Counter", "👣 किक काउंटर"),
    ("chatbot", "💬 AI Chatbot", "💬 AI चैटबॉट"),
    ("emergency", "🆘 Emergency Guide", "🆘 आपातकालीन मार्गदर्शिका"),
    ("dashboard", "📊 Dashboard", "📊 डैशबोर्ड"),
]


# ═══════════════════════════════════════
# BABY DEVELOPMENT DATA
# ═══════════════════════════════════════
BABY_WEEKS = {
    1: {"emoji": "🔸", "size": "Poppy Seed / खसखस", "wt": "-", "ln": "-",
        "dev": "Fertilization happens. The fertilized egg travels toward the uterus, dividing rapidly into a ball of cells.",
        "dev_hi": "निषेचन होता है। निषेचित अंडा गर्भाशय की ओर बढ़ता है, तेजी से कोशिकाओं में विभाजित होता है।",
        "mom": "No noticeable changes yet. Body prepares uterine lining.",
        "mom_hi": "अभी कोई ध्यान देने योग्य बदलाव नहीं। शरीर गर्भाशय की परत तैयार करता है।",
        "tip": "Start folic acid 400mcg daily. Avoid alcohol & smoking.",
        "tip_hi": "फोलिक एसिड 400mcg रोज शुरू करें। शराब और धूम्रपान से बचें।"},
    2: {"emoji": "🔸", "size": "Poppy Seed / खसखस", "wt": "-", "ln": "-",
        "dev": "Blastocyst implants into uterine wall. Placenta begins forming.",
        "dev_hi": "ब्लास्टोसिस्ट गर्भाशय की दीवार में प्रत्यारोपित होता है। प्लेसेंटा बनना शुरू होता है।",
        "mom": "Light spotting possible, called implantation bleeding.",
        "mom_hi": "हल्की स्पॉटिंग संभव, जिसे प्रत्यारोपण रक्तस्राव कहा जाता है।",
        "tip": "Continue folic acid. Stay hydrated.",
        "tip_hi": "फोलिक एसिड जारी रखें। पानी पीती रहें।"},
    3: {"emoji": "🔹", "size": "Sesame Seed / तिल", "wt": "-", "ln": "0.1 mm",
        "dev": "Neural tube forming, future brain and spinal cord. Heart cells begin to develop.",
        "dev_hi": "न्यूरल ट्यूब बनना शुरू, जो आगे मस्तिष्क और रीढ़ बनेगी। हृदय कोशिकाएँ विकसित होती हैं।",
        "mom": "Mild fatigue and breast tenderness may begin.",
        "mom_hi": "हल्की थकान और स्तनों में कसाव शुरू हो सकता है।",
        "tip": "Take pregnancy test if period is missed.",
        "tip_hi": "पीरियड मिस होने पर प्रेगनेंसी टेस्ट करें।"},
    4: {"emoji": "🟡", "size": "Mustard Seed / राई", "wt": "<1g", "ln": "2 mm",
        "dev": "Heart starts beating. Three cell layers form different body systems. Tiny limb buds appear.",
        "dev_hi": "दिल धड़कना शुरू करता है। तीन कोशिका परतें विभिन्न शारीरिक प्रणालियाँ बनाती हैं। छोटे अंगों की कलियाँ दिखती हैं।",
        "mom": "Morning sickness may begin. Fatigue and mood swings are common.",
        "mom_hi": "मॉर्निंग सिकनेस शुरू हो सकती है। थकान और मूड स्विंग सामान्य हैं।",
        "tip": "Schedule first prenatal visit. Eat small frequent meals.",
        "tip_hi": "पहली प्रसव पूर्व जाँच का समय तय करें। थोड़ा-थोड़ा बार-बार खाएँ।"},
    5: {"emoji": "🍎", "size": "Apple Seed / सेब का बीज", "wt": "<1g", "ln": "3 mm",
        "dev": "Heart beating regularly. Arm and leg buds visible. Brain growing rapidly.",
        "dev_hi": "दिल नियमित धड़क रहा है। हाथ-पैर की कलियाँ दिखती हैं। मस्तिष्क तेजी से बढ़ रहा है।",
        "mom": "Nausea may intensify. Frequent urination begins.",
        "mom_hi": "मतली बढ़ सकती है। बार-बार पेशाब आना शुरू हो सकता है।",
        "tip": "Avoid heavy lifting. Ginger tea may help nausea.",
        "tip_hi": "भारी सामान न उठाएँ। अदरक की चाय मतली में मदद कर सकती है।"},
    6: {"emoji": "🫛", "size": "Sweet Pea / मटर", "wt": "<1g", "ln": "6 mm",
        "dev": "Facial features are forming: nostrils, mouth, and ears. Heart beats rapidly.",
        "dev_hi": "चेहरे की विशेषताएँ बन रही हैं: नथुने, मुँह और कान। दिल तेजी से धड़कता है।",
        "mom": "Increased fatigue, mood swings, and mild cramping may happen.",
        "mom_hi": "बढ़ी थकान, मूड बदलाव और हल्की ऐंठन हो सकती है।",
        "tip": "Light walks are beneficial. Avoid raw or undercooked food.",
        "tip_hi": "हल्की सैर फायदेमंद है। कच्चा या अधपका खाना न खाएँ।"},
    7: {"emoji": "🫐", "size": "Blueberry / ब्लूबेरी", "wt": "<1g", "ln": "1 cm",
        "dev": "Fingers begin forming. Brain generates many new cells. Arms and legs are growing.",
        "dev_hi": "उँगलियाँ बनना शुरू। मस्तिष्क कई नई कोशिकाएँ बना रहा है। हाथ-पैर बढ़ रहे हैं।",
        "mom": "Nausea can peak. Food cravings and aversions may be strong.",
        "mom_hi": "मतली चरम पर हो सकती है। खाने की इच्छा या अरुचि तेज हो सकती है।",
        "tip": "Eat what you can tolerate. Ask doctor about Vitamin B6 if nausea is severe.",
        "tip_hi": "जो खा सकें वो खाएँ। मतली बहुत हो तो डॉक्टर से विटामिन B6 के बारे में पूछें।"},
    8: {"emoji": "🍇", "size": "Raspberry / रसभरी", "wt": "1g", "ln": "1.6 cm",
        "dev": "Baby can move, though you cannot feel it yet. Fingers, toes, and eyes are developing.",
        "dev_hi": "शिशु हिल सकता है, हालांकि आप अभी महसूस नहीं करेंगी। उँगलियाँ, पैर और आँखें विकसित हो रहे हैं।",
        "mom": "Uterus expanding. Bloating is common. First ultrasound is often around this time.",
        "mom_hi": "गर्भाशय फैल रहा है। पेट फूलना सामान्य है। पहला अल्ट्रासाउंड अक्सर इस समय होता है।",
        "tip": "Take prenatal vitamins and attend your first ultrasound if advised.",
        "tip_hi": "प्रसव पूर्व विटामिन लें और सलाह होने पर पहला अल्ट्रासाउंड कराएँ।"},
    10: {"emoji": "🍊", "size": "Kumquat / छोटा संतरा", "wt": "4g", "ln": "3 cm",
        "dev": "Bones and cartilage are forming. Baby can swallow and kick. Vital organs are functioning.",
        "dev_hi": "हड्डियाँ और उपास्थि बन रही हैं। शिशु निगल और लात मार सकता है। महत्वपूर्ण अंग काम कर रहे हैं।",
        "mom": "Morning sickness may reduce. Veins may be more visible.",
        "mom_hi": "मॉर्निंग सिकनेस कम हो सकती है। नसें अधिक दिख सकती हैं।",
        "tip": "Continue prenatal vitamins and start thinking about a birth plan.",
        "tip_hi": "प्रसव पूर्व विटामिन जारी रखें और जन्म योजना के बारे में सोचें।"},
    12: {"emoji": "🍋", "size": "Lime / नींबू", "wt": "14g", "ln": "5.4 cm",
        "dev": "All essential organs are formed. Baby opens and closes fingers. Reflexes develop.",
        "dev_hi": "सभी आवश्यक अंग बन चुके हैं। शिशु उँगलियाँ खोल-बंद कर सकता है। रिफ्लेक्स विकसित हो रहे हैं।",
        "mom": "End of first trimester. Nausea usually reduces and miscarriage risk drops.",
        "mom_hi": "पहली तिमाही समाप्त। मतली आमतौर पर कम होती है और गर्भपात जोखिम घटता है।",
        "tip": "Trimester 1 complete. Continue ANC visits.",
        "tip_hi": "पहली तिमाही पूरी। ANC जाँच जारी रखें।"},
    14: {"emoji": "🍑", "size": "Peach / आड़ू", "wt": "43g", "ln": "8.5 cm",
        "dev": "Second trimester. Fingerprints form. Facial muscles begin working.",
        "dev_hi": "दूसरी तिमाही। फिंगरप्रिंट बनते हैं। चेहरे की मांसपेशियाँ काम करना शुरू करती हैं।",
        "mom": "Energy may return. Appetite increases and pregnancy glow may appear.",
        "mom_hi": "ऊर्जा लौट सकती है। भूख बढ़ती है और प्रेगनेंसी ग्लो दिख सकता है।",
        "tip": "Start moderate exercise if doctor agrees. Eat calcium-rich foods.",
        "tip_hi": "डॉक्टर की सलाह से मध्यम व्यायाम शुरू करें। कैल्शियम युक्त भोजन खाएँ।"},
    16: {"emoji": "🥑", "size": "Avocado / एवोकैडो", "wt": "100g", "ln": "11.5 cm",
        "dev": "Baby makes facial expressions. Skeleton is hardening. Baby can hear sounds.",
        "dev_hi": "शिशु चेहरे के भाव बना सकता है। कंकाल कठोर हो रहा है। शिशु आवाज़ सुन सकता है।",
        "mom": "You may feel first flutters. Baby bump may become visible.",
        "mom_hi": "आप पहली हलचल महसूस कर सकती हैं। बेबी बंप दिखना शुरू हो सकता है।",
        "tip": "Talk or sing to baby. Schedule anomaly scan.",
        "tip_hi": "शिशु से बात करें या गाएँ। एनॉमली स्कैन का समय तय करें।"},
    20: {"emoji": "🍌", "size": "Banana / केला", "wt": "300g", "ln": "25 cm",
        "dev": "Halfway. Baby swallows, tastes, and has sleep-wake cycles. Hair starts growing.",
        "dev_hi": "आधा सफर पूरा। शिशु निगल सकता है, स्वाद ले सकता है और सोने-जागने का चक्र बनता है। बाल बढ़ते हैं।",
        "mom": "Belly is clearly visible. Regular movements may be felt. Back pain may increase.",
        "mom_hi": "पेट स्पष्ट दिखता है। नियमित हलचल महसूस हो सकती है। पीठ दर्द बढ़ सकता है।",
        "tip": "Get anomaly scan. Sleep on left side.",
        "tip_hi": "एनॉमली स्कैन कराएँ। बाईं करवट सोएँ।"},
    24: {"emoji": "🌽", "size": "Corn Cob / मक्के का भुट्टा", "wt": "600g", "ln": "30 cm",
        "dev": "Lungs develop surfactant. Baby responds to sound and light. Taste buds are formed.",
        "dev_hi": "फेफड़ों में सर्फैक्टेंट विकसित होता है। शिशु ध्वनि और प्रकाश पर प्रतिक्रिया देता है। स्वाद कलिकाएँ बनती हैं।",
        "mom": "Glucose test is recommended. Stretch marks and Braxton Hicks may occur.",
        "mom_hi": "ग्लूकोज़ टेस्ट की सलाह दी जाती है। स्ट्रेच मार्क्स और ब्रेक्सटन हिक्स हो सकते हैं।",
        "tip": "Get gestational diabetes test. Practice breathing exercises.",
        "tip_hi": "गर्भकालीन मधुमेह जाँच कराएँ। साँस के व्यायाम करें।"},
    28: {"emoji": "🍆", "size": "Eggplant / बैंगन", "wt": "1 kg", "ln": "37 cm",
        "dev": "Third trimester. Baby opens eyes, recognizes your voice, and brain develops rapidly.",
        "dev_hi": "तीसरी तिमाही। शिशु आँखें खोलता है, आपकी आवाज़ पहचानता है और मस्तिष्क तेजी से विकसित होता है।",
        "mom": "Shortness of breath, frequent urination, and leg cramps may occur.",
        "mom_hi": "साँस फूलना, बार-बार पेशाब और पैरों में ऐंठन हो सकती है।",
        "tip": "Start counting kicks: 10 movements in 2 hours.",
        "tip_hi": "किक गिनना शुरू करें: 2 घंटे में 10 हलचल।"},
    32: {"emoji": "🎃", "size": "Squash / कद्दू", "wt": "1.7 kg", "ln": "42 cm",
        "dev": "Baby practices breathing. Fat layers build. Bones are developed but soft.",
        "dev_hi": "शिशु साँस लेने का अभ्यास करता है। वसा परतें बनती हैं। हड्डियाँ विकसित हैं पर नरम हैं।",
        "mom": "Sleeping may be difficult. Heartburn may increase. Baby may be head-down.",
        "mom_hi": "सोने में कठिनाई हो सकती है। एसिडिटी बढ़ सकती है। शिशु सिर नीचे हो सकता है।",
        "tip": "Pack hospital bag. Learn labor signs.",
        "tip_hi": "अस्पताल बैग तैयार करें। प्रसव संकेत जानें।"},
    36: {"emoji": "🍈", "size": "Honeydew Melon / खरबूज़ा", "wt": "2.6 kg", "ln": "47 cm",
        "dev": "Lungs are nearly mature. Immune system strengthens. Baby gains weight quickly.",
        "dev_hi": "फेफड़े लगभग परिपक्व हैं। प्रतिरक्षा मजबूत होती है। शिशु तेजी से वजन बढ़ाता है।",
        "mom": "Baby may drop into pelvis. Breathing can feel easier but pelvic pressure increases.",
        "mom_hi": "शिशु श्रोणि में उतर सकता है। साँस आसान लग सकती है लेकिन श्रोणि दबाव बढ़ता है।",
        "tip": "Weekly check-ups now. Keep hospital bag ready.",
        "tip_hi": "अब साप्ताहिक जाँच। अस्पताल बैग तैयार रखें।"},
    38: {"emoji": "🎃", "size": "Pumpkin / कद्दू", "wt": "3.1 kg", "ln": "49 cm",
        "dev": "Final weight gain. Brain and lungs keep maturing. Baby prepares for birth.",
        "dev_hi": "अंतिम वजन बढ़ता है। मस्तिष्क और फेफड़े परिपक्व होते रहते हैं। शिशु जन्म की तैयारी करता है।",
        "mom": "Pelvic pressure increases. Mucus plug may release. Watch labor signs.",
        "mom_hi": "श्रोणि दबाव बढ़ता है। म्यूकस प्लग निकल सकता है। प्रसव संकेत देखें।",
        "tip": "Rest, eat energy foods, and stay near your hospital.",
        "tip_hi": "आराम करें, ऊर्जा वाला भोजन खाएँ और अस्पताल के पास रहें।"},
    40: {"emoji": "🍉", "size": "Watermelon / तरबूज़", "wt": "3.4 kg", "ln": "51 cm",
        "dev": "Due date. Baby is ready. Organs are mature and baby is ready to breathe independently.",
        "dev_hi": "ड्यू डेट। शिशु तैयार है। अंग परिपक्व हैं और शिशु स्वतंत्र साँस लेने के लिए तैयार है।",
        "mom": "Contractions may begin any time. Doctor may discuss induction if needed.",
        "mom_hi": "संकुचन कभी भी शुरू हो सकते हैं। जरूरत होने पर डॉक्टर इंडक्शन पर चर्चा कर सकते हैं।",
        "tip": "Your baby is ready. Trust your body and follow medical advice.",
        "tip_hi": "शिशु तैयार है। अपने शरीर पर भरोसा रखें और डॉक्टर की सलाह मानें।"},
}


# ═══════════════════════════════════════
# CSS
# ═══════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] {font-family:'Noto Sans','Segoe UI',sans-serif;}
.stApp {background:#f0f4f8;color:#1d2939;}
.tricolor-bar {display:flex;height:6px;width:100%;margin-bottom:0;}
.tricolor-bar .orange{flex:1;background:#FF9933;} .tricolor-bar .white{flex:1;background:#FFF;} .tricolor-bar .green{flex:1;background:#138808;}
.gov-header{background:linear-gradient(135deg,#0b2545,#13315c,#0b2545);padding:20px 28px;border-radius:0 0 16px 16px;margin-bottom:16px;box-shadow:0 6px 20px rgba(11,37,69,.25);position:relative;overflow:hidden;}
.gov-header::before{content:'';position:absolute;top:0;left:0;right:0;height:4px;background:linear-gradient(90deg,#FF9933,#FFF,#138808);}
.gov-header-flex{display:flex;align-items:center;gap:18px;flex-wrap:wrap;}
.gov-emblem{font-size:44px;line-height:1;}
.gov-header-title{font-size:26px;font-weight:800;color:#fff;margin-bottom:2px;}
.gov-header-subtitle{font-size:13px;color:#b0c4de;}
.gov-header-ministry{font-size:11px;color:#7a9cc6;margin-top:4px;}
.gov-header-badge{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.2);border-radius:10px;padding:8px 14px;text-align:center;color:#fff;margin-left:auto;}
.hero-banner{background:linear-gradient(135deg,#1a4b8c,#2563eb,#1e40af);border-radius:16px;padding:32px 28px;margin-bottom:18px;color:#fff;box-shadow:0 6px 24px rgba(30,64,175,.2);}
.hero-title{font-size:28px;font-weight:800;margin-bottom:6px;}
.hero-subtitle{font-size:15px;color:#bfdbfe;max-width:800px;}
.hero-stats{display:flex;gap:20px;margin-top:18px;flex-wrap:wrap;}
.hero-stat{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.2);border-radius:12px;padding:10px 18px;text-align:center;}
.hero-stat-num{font-size:24px;font-weight:800;color:#FF9933;}
.hero-stat-label{font-size:11px;color:#bfdbfe;}
.section-header{background:linear-gradient(90deg,#e8f1ff,#fff);border-left:6px solid #0b5cab;border-radius:0 10px 10px 0;padding:12px 18px;margin:16px 0;font-weight:700;font-size:18px;color:#0b3b78;}
.section-header-orange{background:linear-gradient(90deg,#fff8f0,#fff);border-left:6px solid #FF9933;border-radius:0 10px 10px 0;padding:12px 18px;margin:16px 0;font-weight:700;font-size:18px;color:#7c4a00;}
.gov-card{background:#fff;border:1px solid #d7deea;border-radius:14px;padding:18px;box-shadow:0 4px 14px rgba(16,24,40,.05);margin-bottom:14px;}
.metric-card{background:#fff;border:1px solid #d7deea;border-radius:14px;padding:16px;text-align:center;box-shadow:0 3px 12px rgba(16,24,40,.05);}
.metric-card h3{font-size:28px;font-weight:800;color:#0b5cab;margin:0;}
.metric-card div{font-size:12px;color:#667085;margin-top:4px;}
.feature-card{background:#fff;border:1px solid #d7deea;border-radius:14px;padding:20px;text-align:center;box-shadow:0 3px 14px rgba(16,24,40,.06);margin-bottom:14px;transition:transform .2s;min-height:150px;}
.feature-card:hover{transform:translateY(-4px);box-shadow:0 8px 24px rgba(16,24,40,.12);}
.feature-card .icon{font-size:36px;margin-bottom:8px;}
.feature-card h4{color:#0b3b78;margin:6px 0;font-size:16px;}
.feature-card p{color:#667085;font-size:13px;margin:0;}
.scheme-card{background:linear-gradient(135deg,#fffdf7,#fff9eb);border:1px solid #f5d08a;border-left:6px solid #c98a00;border-radius:14px;padding:18px;margin-bottom:14px;}
.scheme-card h4{color:#7c4a00;margin-bottom:8px;}
.scheme-card .amount{display:inline-block;background:#FF9933;color:#fff;padding:3px 12px;border-radius:20px;font-weight:700;font-size:13px;margin-bottom:8px;}
.alert-danger{background:#fff4f2;border:1px solid #f2b8b5;border-left:6px solid #d92d20;border-radius:12px;padding:14px 18px;margin-bottom:12px;}
.alert-warning{background:#fffcf0;border:1px solid #fde68a;border-left:6px solid #f59e0b;border-radius:12px;padding:14px 18px;margin-bottom:12px;}
.alert-success{background:#ecfdf3;border:1px solid #abefc6;border-left:6px solid #12b76a;border-radius:12px;padding:14px 18px;margin-bottom:12px;}
.alert-info{background:#eff8ff;border:1px solid #b2ddff;border-left:6px solid #2e90fa;border-radius:12px;padding:14px 18px;margin-bottom:12px;}
div.stButton>button,div.stFormSubmitButton>button{background:linear-gradient(90deg,#0b5cab,#2563eb);color:#fff;border:none;border-radius:10px;padding:.6rem 1.4rem;font-weight:700;}
div.stButton>button:hover{background:linear-gradient(90deg,#084a8d,#1d4ed8);}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0b2545,#0f3460);border-right:2px solid #1a3a6b;}
[data-testid="stSidebar"] .stMarkdown,[data-testid="stSidebar"] .stMarkdown p,[data-testid="stSidebar"] .stMarkdown div,[data-testid="stSidebar"] .stMarkdown span,[data-testid="stSidebar"] .stCaption,[data-testid="stSidebar"] .stAlert,[data-testid="stSidebar"] .stAlert p{color:#f8fafc!important;}
[data-testid="stSidebar"] .stRadio label,[data-testid="stSidebar"] .stRadio label span,[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label,[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label span{color:#fff!important;opacity:1!important;font-weight:600!important;}
[data-testid="stSidebar"] hr{border-color:rgba(255,255,255,.15)!important;}
[data-testid="stSidebar"] .stSelectbox label,[data-testid="stSidebar"] .stTextInput label{color:#fff!important;font-weight:600!important;}
.stTextInput label,.stNumberInput label,.stDateInput label,.stSelectbox label,.stTextArea label,.stMultiSelect label,.stSlider label{color:#0b2545!important;font-weight:700!important;font-size:14px!important;opacity:1!important;}
div[data-testid="stAppViewContainer"] .stRadio>label{color:#0b2545!important;font-weight:700!important;}
div[data-testid="stAppViewContainer"] .stRadio div[role="radiogroup"] label,div[data-testid="stAppViewContainer"] .stRadio div[role="radiogroup"] label span,div[data-testid="stAppViewContainer"] .stRadio div[role="radiogroup"] p{color:#0b2545!important;opacity:1!important;}
.gov-footer{background:#0b2545;color:#f8fafc;padding:24px 28px;border-radius:16px 16px 0 0;margin-top:30px;text-align:center;font-size:13px;line-height:1.8;border-top:4px solid #FF9933;}
.gov-footer div{color:#f8fafc!important;}
.gov-footer .footer-subtext{color:#cbd5e1!important;font-size:12px;}
.video-card{background:#fff;border:1px solid #d7deea;border-radius:14px;padding:14px;box-shadow:0 3px 12px rgba(16,24,40,.05);margin-bottom:14px;}
.video-card h4{color:#0b3b78;margin:8px 0 4px;font-size:15px;} .video-card p{color:#667085;font-size:13px;margin:0 0 8px;}
.team-card{background:#fff;border:1px solid #d7deea;border-radius:14px;padding:18px;text-align:center;box-shadow:0 3px 12px rgba(16,24,40,.05);margin-bottom:14px;}
.team-card .emoji{font-size:40px;margin-bottom:6px;} .team-card h4{color:#0b3b78;margin:4px 0;} .team-card .role{color:#2563eb;font-size:12px;font-weight:700;} .team-card p{color:#667085;font-size:12px;margin:0;}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════
# PREMIUM UI ENHANCEMENTS
# ═══════════════════════════════════════
st.markdown("""
<style>
/* ---------- App Background + Layout ---------- */
.stApp {
    background:
        radial-gradient(circle at top left, rgba(37,99,235,.16), transparent 32%),
        radial-gradient(circle at top right, rgba(255,153,51,.14), transparent 30%),
        linear-gradient(180deg, #f8fbff 0%, #eef4fb 42%, #f7fafc 100%) !important;
}
.block-container {
    padding-top: 1.15rem !important;
    padding-bottom: 2rem !important;
    max-width: 1280px !important;
}
#MainMenu, footer {visibility: hidden;}
header[data-testid="stHeader"] {background: transparent !important;}

/* ---------- Smooth Typography ---------- */
html, body, [class*="css"] {
    -webkit-font-smoothing: antialiased;
    text-rendering: geometricPrecision;
}
p, li, span {line-height: 1.65;}

/* ---------- Premium Header ---------- */
.gov-header {
    background:
        linear-gradient(135deg, rgba(7,23,54,.96), rgba(15,52,96,.96), rgba(11,37,69,.98)),
        radial-gradient(circle at 15% 20%, rgba(255,153,51,.28), transparent 25%) !important;
    border: 1px solid rgba(255,255,255,.12) !important;
    border-radius: 0 0 24px 24px !important;
    box-shadow: 0 18px 45px rgba(11,37,69,.25) !important;
}
.gov-header::after {
    content: '';
    position: absolute;
    width: 180px;
    height: 180px;
    right: -55px;
    top: -65px;
    background: radial-gradient(circle, rgba(255,255,255,.14), transparent 65%);
    border-radius: 50%;
}
.gov-emblem {
    background: rgba(255,255,255,.10);
    border: 1px solid rgba(255,255,255,.18);
    width: 64px;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 18px;
    box-shadow: inset 0 1px 0 rgba(255,255,255,.18);
}
.gov-header-title {
    letter-spacing: -.4px;
    font-size: clamp(24px, 3vw, 34px) !important;
}
.gov-header-badge {
    backdrop-filter: blur(14px);
    box-shadow: inset 0 1px 0 rgba(255,255,255,.18);
}

/* ---------- Hero ---------- */
.hero-banner {
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,.38) !important;
    border-radius: 24px !important;
    background:
      radial-gradient(circle at top right, rgba(255,153,51,.34), transparent 28%),
      linear-gradient(135deg,#123b78,#2563eb,#1d4ed8) !important;
    box-shadow: 0 20px 55px rgba(37,99,235,.22) !important;
}
.hero-banner::before {
    content:'';
    position:absolute;
    inset:0;
    background: linear-gradient(120deg, rgba(255,255,255,.16), transparent 38%);
    pointer-events:none;
}
.hero-title {font-size: clamp(26px, 4vw, 42px) !important; letter-spacing: -.7px;}
.hero-subtitle {font-size: 16px !important; line-height: 1.75;}
.hero-stat {
    min-width: 128px;
    backdrop-filter: blur(12px);
    transition: transform .18s ease, background .18s ease;
}
.hero-stat:hover {transform: translateY(-4px); background: rgba(255,255,255,.18) !important;}

/* ---------- Section Headers ---------- */
.section-header, .section-header-orange {
    border-radius: 16px !important;
    padding: 14px 20px !important;
    box-shadow: 0 8px 24px rgba(16,24,40,.06);
    border-top: 1px solid rgba(255,255,255,.85);
    font-size: 19px !important;
    letter-spacing: -.2px;
}
.section-header {
    background: linear-gradient(90deg, #dbeafe, rgba(255,255,255,.95)) !important;
}
.section-header-orange {
    background: linear-gradient(90deg, #fff3df, rgba(255,255,255,.95)) !important;
}

/* ---------- Cards ---------- */
.gov-card, .feature-card, .metric-card, .scheme-card, .video-card, .team-card {
    border-radius: 20px !important;
    border: 1px solid rgba(209,218,232,.9) !important;
    box-shadow: 0 12px 32px rgba(16,24,40,.08) !important;
}
.gov-card, .feature-card, .metric-card, .video-card, .team-card {
    background: rgba(255,255,255,.92) !important;
    backdrop-filter: blur(10px);
}
.gov-card:hover, .metric-card:hover, .video-card:hover, .team-card:hover {
    box-shadow: 0 18px 45px rgba(16,24,40,.12) !important;
}
.feature-card {
    min-height: 168px !important;
    position: relative;
    overflow: hidden;
}
.feature-card::before {
    content:'';
    position:absolute;
    top:0; left:0; right:0;
    height: 4px;
    background: linear-gradient(90deg,#FF9933,#2563eb,#138808);
    opacity:.85;
}
.feature-card .icon {
    width: 58px;
    height: 58px;
    display:flex;
    align-items:center;
    justify-content:center;
    margin: 0 auto 10px auto;
    border-radius: 18px;
    background: linear-gradient(135deg,#eff6ff,#fff7ed);
    box-shadow: inset 0 1px 0 rgba(255,255,255,.9);
}
.metric-card h3 {
    background: linear-gradient(90deg,#0b5cab,#2563eb);
    -webkit-background-clip: text;
    color: transparent !important;
}

/* ---------- Alerts ---------- */
.alert-danger, .alert-warning, .alert-success, .alert-info {
    border-radius: 16px !important;
    box-shadow: 0 10px 26px rgba(16,24,40,.06);
}

/* ---------- Sidebar Polish ---------- */
[data-testid="stSidebar"] {
    background:
      radial-gradient(circle at top, rgba(255,153,51,.20), transparent 25%),
      linear-gradient(180deg,#071736,#0b2545 45%,#0f3460) !important;
}
[data-testid="stSidebar"] > div:first-child {padding-top: 1.5rem;}
[data-testid="stSidebar"] [data-testid="stRadio"] label,
[data-testid="stSidebar"] [data-testid="stSelectbox"] label,
[data-testid="stSidebar"] [data-testid="stTextInput"] label {
    color:#fff !important;
}
[data-testid="stSidebar"] div[role="radiogroup"] label {
    background: rgba(255,255,255,.08);
    border: 1px solid rgba(255,255,255,.12);
    border-radius: 12px;
    padding: 7px 10px;
    margin-bottom: 5px;
    transition: all .16s ease;
}
[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: rgba(255,255,255,.16);
    transform: translateX(3px);
}

/* ---------- Inputs / Forms ---------- */
.stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox div[data-baseweb="select"] > div,
.stTextArea textarea, div[data-baseweb="select"] {
    border-radius: 12px !important;
}
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
    border-color: #2563eb !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,.14) !important;
}
div.stButton>button, div.stFormSubmitButton>button, .stDownloadButton button {
    border-radius: 13px !important;
    box-shadow: 0 9px 22px rgba(37,99,235,.22) !important;
    transition: transform .15s ease, box-shadow .15s ease !important;
}
div.stButton>button:hover, div.stFormSubmitButton>button:hover, .stDownloadButton button:hover {
    transform: translateY(-2px);
    box-shadow: 0 14px 30px rgba(37,99,235,.30) !important;
}

/* ---------- Tabs ---------- */
button[data-baseweb="tab"] {
    border-radius: 999px !important;
    padding: 8px 16px !important;
    background: rgba(255,255,255,.65) !important;
    margin-right: 8px !important;
    border: 1px solid #dbe4f0 !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(90deg,#0b5cab,#2563eb) !important;
    color: white !important;
}
button[data-baseweb="tab"][aria-selected="true"] p {color: white !important;}

/* ---------- Dataframes / Charts ---------- */
[data-testid="stDataFrame"] {
    border-radius: 18px;
    overflow: hidden;
    box-shadow: 0 10px 30px rgba(16,24,40,.08);
}
.js-plotly-plot {
    border-radius: 18px;
    overflow: hidden;
}

/* ---------- Video iframe wrapper helper ---------- */
.yt-wrap {
    border-radius: 20px;
    overflow: hidden;
    box-shadow: 0 16px 45px rgba(16,24,40,.16);
    border: 1px solid rgba(209,218,232,.9);
    background: #000;
}

/* ---------- Footer ---------- */
.gov-footer {
    border-radius: 24px 24px 0 0 !important;
    box-shadow: 0 -16px 40px rgba(11,37,69,.12);
}

/* ---------- Mobile ---------- */
@media (max-width: 768px) {
    .gov-header {padding: 18px !important;}
    .gov-emblem {width: 54px; height: 54px;}
    .hero-banner {padding: 24px 18px !important;}
    .hero-stat {width: 100%;}
    .feature-card {min-height: auto !important;}
}
</style>
""", unsafe_allow_html=True)



# ═══════════════════════════════════════
# SIDEBAR NAVIGATION READABILITY FIX
# ═══════════════════════════════════════
st.markdown("""
<style>
/* Make sidebar navigation text clearly visible */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #081a35 0%, #0b2a52 52%, #0f3a70 100%) !important;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div {
    color: #f8fafc !important;
}

/* Radio option pills */
[data-testid="stSidebar"] div[role="radiogroup"] label {
    width: 100% !important;
    min-height: 42px !important;
    padding: 8px 12px !important;
    margin: 5px 0 !important;
    border-radius: 14px !important;
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.14) !important;
    box-shadow: none !important;
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
    transition: all .18s ease !important;
}

[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: rgba(255,255,255,0.16) !important;
    border-color: rgba(255,255,255,0.28) !important;
    transform: translateX(3px);
}

/* Active selected navigation item */
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
    background: linear-gradient(90deg, #2563eb, #0b5cab) !important;
    border-color: rgba(255,255,255,0.45) !important;
    box-shadow: 0 10px 24px rgba(37,99,235,0.35) !important;
}

[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) * {
    color: #ffffff !important;
    font-weight: 800 !important;
}

/* Force option label text color */
[data-testid="stSidebar"] div[role="radiogroup"] label p,
[data-testid="stSidebar"] div[role="radiogroup"] label span,
[data-testid="stSidebar"] div[role="radiogroup"] label div {
    color: #f8fafc !important;
    font-size: 14px !important;
    font-weight: 650 !important;
    line-height: 1.35 !important;
}

/* Keep radio circle clean */
[data-testid="stSidebar"] input[type="radio"] {
    accent-color: #ff6b6b !important;
}

/* Inputs inside sidebar */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] div[data-baseweb="select"] > div {
    color: #0f172a !important;
    background: #ffffff !important;
    border-radius: 12px !important;
}

/* Reduce sidebar title spacing */
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
    margin-bottom: 6px !important;
}
</style>
""", unsafe_allow_html=True)



# ═══════════════════════════════════════
# FULL WIDTH GOVERNMENT THEME OVERRIDES
# ═══════════════════════════════════════
st.markdown("""
<style>
/* Full page professional government layout */
.block-container {
    max-width: 100% !important;
    width: 100% !important;
    padding-left: 1.35rem !important;
    padding-right: 1.35rem !important;
    padding-top: 1rem !important;
}

/* Professional government-style background */
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at 8% 8%, rgba(255,153,51,.18), transparent 22%),
        radial-gradient(circle at 92% 12%, rgba(19,136,8,.13), transparent 24%),
        radial-gradient(circle at 50% 0%, rgba(37,99,235,.12), transparent 28%),
        linear-gradient(180deg, #f7fbff 0%, #eef5fc 42%, #e8f0f8 100%) !important;
}

/* Subtle official pattern */
[data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    opacity: .22;
    background-image:
        linear-gradient(rgba(11,37,69,.045) 1px, transparent 1px),
        linear-gradient(90deg, rgba(11,37,69,.045) 1px, transparent 1px);
    background-size: 34px 34px;
    z-index: 0;
}

/* Keep content above pattern */
[data-testid="stAppViewContainer"] > .main,
section.main {
    position: relative;
    z-index: 1;
}

/* Make main government header feel official */
.gov-header {
    border-radius: 0 0 28px 28px !important;
    border: 1px solid rgba(255,255,255,.16) !important;
    box-shadow: 0 20px 55px rgba(11,37,69,.25) !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
}

/* Wider hero and sections */
.hero-banner,
.gov-card,
.feature-card,
.metric-card,
.scheme-card,
.video-card,
.team-card,
.alert-danger,
.alert-warning,
.alert-success,
.alert-info {
    width: 100% !important;
}

/* Official white cards with stronger structure */
.gov-card,
.feature-card,
.metric-card,
.video-card,
.team-card {
    background: rgba(255,255,255,.96) !important;
    border: 1px solid #cbd8e8 !important;
    box-shadow: 0 14px 36px rgba(11,37,69,.10) !important;
}

/* Government-style section bars */
.section-header {
    background: linear-gradient(90deg, #dbeafe 0%, #ffffff 70%) !important;
    border-left: 7px solid #0b5cab !important;
    border-bottom: 1px solid #cbd8e8 !important;
}
.section-header-orange {
    background: linear-gradient(90deg, #fff1df 0%, #ffffff 70%) !important;
    border-left: 7px solid #FF9933 !important;
    border-bottom: 1px solid #f3c98b !important;
}

/* Feature cards look like official service tiles */
.feature-card {
    min-height: 185px !important;
    border-radius: 22px !important;
}
.feature-card h4 {
    color: #08376b !important;
    font-weight: 800 !important;
}
.feature-card p {
    color: #5d6b82 !important;
}

/* Footer should stretch across full content width */
.gov-footer {
    width: 100% !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
    border-radius: 26px 26px 0 0 !important;
    background:
        linear-gradient(180deg, #0b2a52 0%, #08213f 100%) !important;
    border-top: 5px solid #FF9933 !important;
}

/* Better page ending spacing */
.gov-footer + div {
    margin-bottom: 0 !important;
}

/* Make Plotly/DataFrame sections blend better */
[data-testid="stDataFrame"],
.js-plotly-plot {
    background: #ffffff !important;
    border-radius: 20px !important;
    border: 1px solid #cbd8e8 !important;
    box-shadow: 0 14px 34px rgba(11,37,69,.10) !important;
}

/* Responsive padding */
@media (max-width: 768px) {
    .block-container {
        padding-left: .75rem !important;
        padding-right: .75rem !important;
    }
    .feature-card {min-height: auto !important;}
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════
# HEADER
# ═══════════════════════════════════════
st.markdown(f"""<div style="margin:10px 0 20px 0;border-radius:28px;overflow:hidden;background:linear-gradient(135deg,#071a34 0%,#0b2a52 52%,#08213f 100%);box-shadow:0 18px 48px rgba(11,37,69,.24);border:1px solid rgba(255,255,255,.16);position:relative;">
<div style="display:flex;height:7px;width:100%;"><div style="flex:1;background:#FF9933;"></div><div style="flex:1;background:#ffffff;"></div><div style="flex:1;background:#138808;"></div></div>
<div style="padding:30px 36px 28px 36px;display:flex;align-items:center;justify-content:space-between;gap:24px;flex-wrap:wrap;">
<div style="display:flex;align-items:center;gap:20px;min-width:300px;flex:1;"><div style="width:70px;height:70px;border-radius:22px;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.22);font-size:38px;box-shadow:inset 0 1px 0 rgba(255,255,255,.18);">🏥</div><div><div style="color:#ffffff;font-size:38px;font-weight:900;letter-spacing:-1px;line-height:1.08;">{T("MaternalCare India", "मातृ-देखभाल भारत")}</div><div style="color:#dbeafe;font-size:16px;line-height:1.55;margin-top:12px;">{T("AI-Powered Maternal Health & Wellness Platform", "AI-संचालित मातृ स्वास्थ्य एवं कल्याण मंच")}</div><div style="color:#93c5fd;font-size:13px;line-height:1.5;margin-top:7px;">{T("Ministry of Health & Family Welfare • Government of India", "स्वास्थ्य एवं परिवार कल्याण मंत्रालय • भारत सरकार")}</div></div></div>
<div style="min-width:210px;text-align:right;display:flex;justify-content:flex-end;"><div style="padding:16px 20px;border-radius:18px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.22);box-shadow:inset 0 1px 0 rgba(255,255,255,.16);"><div style="color:#FF9933;font-size:24px;font-weight:900;letter-spacing:.5px;">{T("INDIA", "भारत")}</div><div style="color:#cbd5e1;font-size:12px;margin-top:7px;font-weight:700;">{T("Service & Safety", "सेवा और सुरक्षा")}</div></div></div>
</div>
</div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════
def get_conn():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, age INTEGER, phone TEXT, email TEXT, village TEXT, district TEXT, state TEXT,
        lmp_date TEXT, pregnancy_confirm_date TEXT, edd_date TEXT, current_week INTEGER,
        trimester TEXT, stage_mode TEXT, weight REAL, height REAL, bmi REAL, blood_group TEXT,
        previous_pregnancies INTEGER, previous_complications TEXT, delivery_date TEXT, registered_on TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS health_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,log_date TEXT,weight REAL,
        bp_systolic INTEGER,bp_diastolic INTEGER,hemoglobin REAL,blood_sugar REAL,
        temperature REAL,symptoms TEXT,water_intake INTEGER,sleep_hours INTEGER,mood TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS medicine_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,log_date TEXT,medicines_taken TEXT,compliance_percent REAL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS nutrition_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,log_date TEXT,breakfast TEXT,lunch TEXT,snack TEXT,dinner TEXT,diet_score INTEGER
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS risk_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,assessed_on TEXT,risk_level TEXT,probability_low REAL,probability_medium REAL,probability_high REAL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS ppd_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,screened_on TEXT,total_score INTEGER,risk_level TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS kick_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,log_date TEXT,log_time TEXT,kick_count INTEGER,duration_minutes INTEGER
    )""")
    conn.commit()
    conn.close()


init_db()


# ═══════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════
def calc_pregnancy(lmp_date):
    days = (date.today() - lmp_date).days
    week = max(0, days // 7)
    edd = lmp_date + timedelta(days=280)
    tri = "First Trimester" if week <= 12 else "Second Trimester" if week <= 26 else "Third Trimester"
    return week, edd, tri


def calc_bmi(w, h_cm):
    h = h_cm / 100
    return round(w / (h * h), 1) if h > 0 else 0


def save_user(d):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO users
        (name,age,phone,email,village,district,state,lmp_date,pregnancy_confirm_date,edd_date,current_week,trimester,stage_mode,weight,height,bmi,blood_group,previous_pregnancies,previous_complications,delivery_date,registered_on)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (d["name"], d["age"], d["phone"], d["email"], d["village"], d["district"], d["state"], d["lmp_date"],
         d["pregnancy_confirm_date"], d["edd_date"], d["current_week"], d["trimester"], d["stage_mode"], d["weight"],
         d["height"], d["bmi"], d["blood_group"], d["previous_pregnancies"], d["previous_complications"],
         d["delivery_date"], datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    uid = c.lastrowid
    conn.close()
    return uid


def save_health_log(uid, l):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO health_logs
        (user_id,log_date,weight,bp_systolic,bp_diastolic,hemoglobin,blood_sugar,temperature,symptoms,water_intake,sleep_hours,mood)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (uid, date.today().strftime("%Y-%m-%d"), l["weight"], l["bp_systolic"], l["bp_diastolic"], l["hemoglobin"],
         l["blood_sugar"], l["temperature"], ", ".join(l["symptoms"]), l["water_intake"], l["sleep_hours"], l["mood"]))
    conn.commit()
    conn.close()


def save_medicine_log(uid, meds, comp):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO medicine_logs (user_id,log_date,medicines_taken,compliance_percent) VALUES (?,?,?,?)",
              (uid, date.today().strftime("%Y-%m-%d"), ", ".join(meds), comp))
    conn.commit()
    conn.close()


def save_nutrition_log(uid, b, lu, s, d, score):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO nutrition_logs (user_id,log_date,breakfast,lunch,snack,dinner,diet_score) VALUES (?,?,?,?,?,?,?)",
              (uid, date.today().strftime("%Y-%m-%d"), ", ".join(b), ", ".join(lu), ", ".join(s), ", ".join(d), score))
    conn.commit()
    conn.close()


def save_risk_log(uid, level, p0, p1, p2):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO risk_logs (user_id,assessed_on,risk_level,probability_low,probability_medium,probability_high) VALUES (?,?,?,?,?,?)",
              (uid, date.today().strftime("%Y-%m-%d"), level, p0, p1, p2))
    conn.commit()
    conn.close()


def save_ppd_log(uid, score, level):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO ppd_logs (user_id,screened_on,total_score,risk_level) VALUES (?,?,?,?)",
              (uid, date.today().strftime("%Y-%m-%d"), score, level))
    conn.commit()
    conn.close()


def save_kick_log(uid, count, dur):
    conn = get_conn()
    c = conn.cursor()
    now = datetime.now()
    c.execute("INSERT INTO kick_logs (user_id,log_date,log_time,kick_count,duration_minutes) VALUES (?,?,?,?,?)",
              (uid, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"), count, dur))
    conn.commit()
    conn.close()


def get_counts():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    u = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM health_logs")
    l = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM risk_logs WHERE risk_level IN ('HIGH RISK','उच्च जोखिम')")
    h = c.fetchone()[0]
    conn.close()
    return u, l, h


def get_users_df():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM users", conn)
    conn.close()
    return df


def get_all_users():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id,name,phone,district,state FROM users ORDER BY id DESC")
    u = c.fetchall()
    conn.close()
    return u


def get_user_by_id(uid):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (uid,))
    u = c.fetchone()
    conn.close()
    return u


def get_user_by_phone(ph):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE phone=?", (ph,))
    u = c.fetchone()
    conn.close()
    return u


def set_active_user(row):
    if not row:
        return
    st.session_state["user_id"] = row[0]
    st.session_state["user_data"] = {
        "name": row[1], "age": row[2], "phone": row[3], "email": row[4], "village": row[5],
        "district": row[6], "state": row[7], "lmp_date": row[8], "pregnancy_confirm_date": row[9],
        "edd_date": row[10], "current_week": row[11], "trimester": row[12], "stage_mode": row[13],
        "weight": row[14], "height": row[15], "bmi": row[16], "blood_group": row[17],
        "previous_pregnancies": row[18], "previous_complications": row[19], "delivery_date": row[20]
    }


def get_config_value(key, default=""):
    """Read config from environment first, then Streamlit secrets if available."""
    val = os.getenv(key, default)
    if val:
        return val
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


def send_email(to_email, name, week, edd):
    """Send registration email using Gmail SMTP.

    Required configuration:
    - SMTP_USER = your Gmail address
    - SMTP_PASS = Gmail App Password, not your normal Gmail password

    You can set these in Streamlit secrets or as environment variables.
    """
    st.session_state["last_email_error"] = ""
    try:
        smtp_user = get_config_value("SMTP_USER", "")
        smtp_pass = get_config_value("SMTP_PASS", "")

        if not smtp_user or not smtp_pass:
            st.session_state["last_email_error"] = (
                "SMTP_USER / SMTP_PASS not configured. Create .streamlit/secrets.toml "
                "or set environment variables."
            )
            return False

        msg = MIMEText(
            f"Dear {name},\n\n"
            f"Registration confirmed on MaternalCare India.\n"
            f"Current Week: {week}\n"
            f"Expected Delivery Date: {edd}\n\n"
            f"Please continue regular checkups and follow your doctor's advice.\n\n"
            f"Regards,\nMaternalCare India",
            "plain",
            "utf-8"
        )
        msg["Subject"] = "Registration Confirmed - MaternalCare India"
        msg["From"] = smtp_user
        msg["To"] = to_email

        with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as s:
            s.ehlo()
            s.starttls()
            s.ehlo()
            s.login(smtp_user, smtp_pass)
            s.send_message(msg)

        return True
    except Exception as e:
        st.session_state["last_email_error"] = str(e)
        return False


def embed_yt(vid_id, h=315):
    components.html(f"""
    <div style="border-radius:20px;overflow:hidden;box-shadow:0 16px 45px rgba(16,24,40,.18);border:1px solid rgba(209,218,232,.9);background:#000;">
        <iframe width="100%" height="{h}" src="https://www.youtube.com/embed/{vid_id}"
            frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen>
        </iframe>
    </div>
    """, height=h + 26)


# ═══════════════════════════════════════
# SESSION + ML
# ═══════════════════════════════════════
for k, v in [("user_id", None), ("user_data", None), ("kick_count", 0), ("kick_start", None), ("chat_history", [])]:
    if k not in st.session_state:
        st.session_state[k] = v


@st.cache_resource
def train_model():
    np.random.seed(42)
    n = 1200
    a = np.random.randint(16, 45, n)
    b = np.random.uniform(16, 38, n)
    s1 = np.random.randint(85, 185, n)
    d1 = np.random.randint(55, 120, n)
    hb = np.random.uniform(5, 16, n)
    su = np.random.randint(60, 300, n)
    pr = np.random.choice([0, 1], n, p=[.7, .3])
    wk = np.random.randint(1, 42, n)
    r = []
    for i in range(n):
        sc = 0
        if a[i] < 20 or a[i] > 35:
            sc += 2
        if b[i] < 18.5 or b[i] > 30:
            sc += 2
        if s1[i] > 140:
            sc += 3
        if d1[i] > 90:
            sc += 2
        if hb[i] < 7:
            sc += 3
        elif hb[i] < 11:
            sc += 1
        if su[i] > 200:
            sc += 3
        elif su[i] > 140:
            sc += 1
        if pr[i] == 1:
            sc += 2
        r.append(2 if sc >= 6 else 1 if sc >= 3 else 0)
    m = RandomForestClassifier(n_estimators=120, random_state=42, class_weight="balanced")
    m.fit(np.column_stack([a, b, s1, d1, hb, su, pr, wk]), np.array(r))
    return m


risk_model = train_model()


# ═══════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════
st.sidebar.markdown(f"### 🇮🇳 {T('MaternalCare Services', 'मातृ-देखभाल सेवाएँ')}")
st.sidebar.markdown("---")

lang_choice = st.sidebar.radio("🌐 Language / भाषा", ["English", "हिंदी"], index=0 if L == "en" else 1)
if lang_choice == "English" and L != "en":
    st.session_state["lang"] = "en"
    st.rerun()
if lang_choice == "हिंदी" and L != "hi":
    st.session_state["lang"] = "hi"
    st.rerun()

st.sidebar.markdown("---")
nav_labels = [p[2] if L == "hi" else p[1] for p in PAGES]
nav_keys = [p[0] for p in PAGES]
sel_label = st.sidebar.radio(T("Navigate to:", "यहाँ जाएँ:"), nav_labels)
page_key = nav_keys[nav_labels.index(sel_label)]

st.sidebar.markdown("---")
ud = st.session_state["user_data"]
if ud:
    st.sidebar.success(f"👤 {ud['name']}")
    st.sidebar.caption(f"📍 {ud['district']}, {ud['state']}")
    st.sidebar.caption(f"📅 Week {ud.get('current_week', '-')} • {ud.get('trimester', '-')}")
else:
    st.sidebar.info(T("No beneficiary registered", "कोई लाभार्थी पंजीकृत नहीं"))

st.sidebar.markdown("---")
st.sidebar.markdown(f"### {T('Load Beneficiary', 'लाभार्थी लोड करें')}")
all_users = get_all_users()
if all_users:
    opts = {f"{u[1]} | {u[2]}": u[0] for u in all_users}
    sel = st.sidebar.selectbox(T("Select", "चुनें"), ["--"] + list(opts.keys()))
    if sel != "--" and st.sidebar.button("Load"):
        set_active_user(get_user_by_id(opts[sel]))
        st.rerun()
    ph = st.sidebar.text_input(T("Search by Phone", "फ़ोन से खोजें"))
    if st.sidebar.button("🔍"):
        r = get_user_by_phone(ph.strip())
        if r:
            set_active_user(r)
            st.rerun()
        else:
            st.sidebar.error("Not found")

st.sidebar.markdown("---")
st.sidebar.caption("📞 Helpline: 104 | 🚑 Emergency: 108")


# ═══════════════════════════════════════
# UI HELPERS
# ═══════════════════════════════════════
def need_user():
    if not st.session_state["user_data"]:
        st.markdown(f'<div class="alert-warning">{T("Please register or load a beneficiary first.", "कृपया पहले लाभार्थी पंजीकरण करें या लोड करें।")}</div>', unsafe_allow_html=True)
        return True
    return False


def user_card():
    u = st.session_state["user_data"]
    st.markdown(f'<div class="gov-card"><b>{T("Beneficiary", "लाभार्थी")}:</b> {u["name"]} | <b>{T("Week", "सप्ताह")}:</b> {u["current_week"]} | <b>{T("Stage", "स्थिति")}:</b> {u["trimester"]}</div>', unsafe_allow_html=True)


YOGA_VIDEOS = {
    "first": [{"id": "j7rKKpwdXNE", "t": "Gentle Prenatal Yoga – First Trimester", "d": "25 min"}],
    "second": [{"id": "K-X3fDqBcBg", "t": "Prenatal Yoga – Second Trimester", "d": "30 min"}],
    "third": [{"id": "CBxYHPMC_os", "t": "Third Trimester Yoga", "d": "25 min"}],
    "post": [{"id": "GQyU9tBnS3U", "t": "Postnatal Yoga Recovery", "d": "20 min"}],
}
MED_VIDEOS = [{"id": "QHkXvPq2pQE", "t": "Pregnancy Meditation – Calm & Connect", "d": "15 min"}, {"id": "inpok4MKVLM", "t": "Body Scan Meditation", "d": "10 min"}]
BREATH_VIDEOS = [{"id": "8VwufJrUhic", "t": "Prenatal Breathing for Labor", "d": "12 min"}]


# ═══════════════════════════════════════
# AI CHATBOT HELPER - rule-based maternal assistant
# ═══════════════════════════════════════
def maternal_chatbot_reply(user_msg):
    """Rule-based bilingual maternal health chatbot.
    This works offline and does not require an external API key.
    """
    q = (user_msg or "").lower().strip()

    emergency_words = [
        "bleeding", "blood", "severe pain", "chest pain", "blurred", "convulsion", "fits", "faint", "breathing", "no movement", "reduced movement",
        "रक्तस्राव", "खून", "तेज दर्द", "सीने", "धुंधला", "दौरे", "बेहोश", "सांस", "हलचल नहीं", "कम हलचल"
    ]
    if any(w in q for w in emergency_words):
        return T(
            "🚨 This may be a danger sign. Please call 108 or visit the nearest hospital/PHC immediately. If there is bleeding, severe headache with blurred vision, chest pain, convulsions, difficulty breathing, or reduced baby movement, do not wait.",
            "🚨 यह खतरे का संकेत हो सकता है। कृपया तुरंत 108 पर कॉल करें या नजदीकी अस्पताल/PHC जाएँ। रक्तस्राव, तेज सिरदर्द के साथ धुंधली दृष्टि, सीने में दर्द, दौरे, सांस लेने में कठिनाई या शिशु की कम हलचल हो तो इंतजार न करें।"
        )

    if any(w in q for w in ["food", "diet", "nutrition", "eat", "meal", "protein", "iron", "पोषण", "भोजन", "खाना", "आहार", "प्रोटीन", "आयरन"]):
        return T(
            "🥗 Pregnancy diet tip: Eat dal/beans/eggs/milk/curd for protein, green leafy vegetables/dates/jaggery for iron, milk/curd/ragi for calcium, fruits for vitamins, and drink 8–10 glasses of water. Avoid alcohol, smoking, raw/undercooked foods, and excess junk food.",
            "🥗 गर्भावस्था आहार सुझाव: प्रोटीन के लिए दाल/बीन्स/अंडा/दूध/दही, आयरन के लिए हरी पत्तेदार सब्जियाँ/खजूर/गुड़, कैल्शियम के लिए दूध/दही/रागी, विटामिन के लिए फल लें और 8–10 गिलास पानी पिएँ। शराब, धूम्रपान, कच्चा/अधपका भोजन और अधिक जंक फूड से बचें।"
        )

    if any(w in q for w in ["medicine", "tablet", "ifa", "iron", "calcium", "folic", "दवाई", "गोली", "कैल्शियम", "फोलिक"]):
        return T(
            "💊 Common pregnancy supplements include folic acid, iron-folic acid (IFA), and calcium, but dose and timing should follow your doctor/ANM advice. Do not stop prescribed medicines without consulting a healthcare provider.",
            "💊 गर्भावस्था में सामान्य सप्लीमेंट में फोलिक एसिड, आयरन-फोलिक एसिड (IFA) और कैल्शियम शामिल हैं, लेकिन खुराक और समय डॉक्टर/ANM की सलाह अनुसार ही रखें। डॉक्टर से पूछे बिना दवाई बंद न करें।"
        )

    if any(w in q for w in ["checkup", "anc", "visit", "ultrasound", "scan", "जांच", "चेकअप", "अल्ट्रासाउंड", "स्कैन"]):
        return T(
            "📅 ANC schedule: 1st visit before 12 weeks, 2nd between 14–26 weeks, 3rd between 28–32 weeks, and 4th at 36+ weeks. Check BP, weight, hemoglobin, urine, glucose, and fetal growth as advised.",
            "📅 ANC अनुसूची: पहली जाँच 12 सप्ताह से पहले, दूसरी 14–26 सप्ताह, तीसरी 28–32 सप्ताह, और चौथी 36+ सप्ताह पर कराएँ। BP, वजन, हीमोग्लोबिन, यूरिन, ग्लूकोज़ और शिशु विकास की जाँच सलाह अनुसार कराएँ।"
        )

    if any(w in q for w in ["kick", "movement", "baby moving", "किक", "हलचल", "बच्चा हिल"]):
        return T(
            "👣 From around 28 weeks, monitor baby movements daily. A common method is to feel 10 movements within 2 hours when the baby is usually active. If movement is much less than usual, contact your doctor immediately.",
            "👣 लगभग 28 सप्ताह से शिशु की हलचल रोज़ देखें। सामान्य तरीका है कि जब शिशु सक्रिय हो, 2 घंटे में 10 हलचल महसूस हों। अगर हलचल सामान्य से बहुत कम लगे, तुरंत डॉक्टर से संपर्क करें।"
        )

    if any(w in q for w in ["depression", "sad", "anxiety", "cry", "stress", "ppd", "अवसाद", "उदास", "चिंता", "रोना", "तनाव"]):
        return T(
            "🧠 After delivery, mood changes can happen. But if sadness, anxiety, crying, hopelessness, or guilt lasts more than 2 weeks, please talk to a doctor/counsellor/ASHA. If there are thoughts of self-harm or harming the baby, call 108 immediately and do not stay alone.",
            "🧠 प्रसव के बाद मूड बदलना हो सकता है। लेकिन उदासी, चिंता, रोना, निराशा या अपराधबोध 2 सप्ताह से अधिक रहे तो डॉक्टर/काउंसलर/आशा से बात करें। खुद को या शिशु को नुकसान के विचार आएँ तो तुरंत 108 पर कॉल करें और अकेले न रहें।"
        )

    if any(w in q for w in ["scheme", "benefit", "money", "jsy", "pmmvy", "ayushman", "योजना", "लाभ", "पैसा", "सरकारी"]):
        return T(
            "🏛️ Important schemes: JSY provides cash support for institutional delivery, PMMVY provides maternity benefit for eligible mothers, JSSK provides free delivery-related services in government facilities, and Ayushman Bharat may cover hospitalization for eligible families.",
            "🏛️ महत्वपूर्ण योजनाएँ: JSY संस्थागत प्रसव के लिए नकद सहायता देती है, PMMVY पात्र माताओं को मातृत्व लाभ देती है, JSSK सरकारी संस्थानों में प्रसव संबंधित मुफ्त सेवाएँ देती है, और आयुष्मान भारत पात्र परिवारों को अस्पताल कवरेज दे सकता है।"
        )

    if any(w in q for w in ["exercise", "yoga", "walk", "breathing", "व्यायाम", "योग", "सैर", "सांस"]):
        return T(
            "🧘 Safe activity: Gentle walking, breathing exercises, and doctor-approved prenatal yoga can help. Stop immediately if you feel pain, bleeding, dizziness, breathlessness, or contractions. Always consult your doctor before starting exercise.",
            "🧘 सुरक्षित गतिविधि: हल्की सैर, साँस के व्यायाम और डॉक्टर द्वारा अनुमत प्रीनेटल योग मदद कर सकते हैं। दर्द, रक्तस्राव, चक्कर, सांस फूलना या संकुचन हो तो तुरंत रुकें। व्यायाम शुरू करने से पहले डॉक्टर से सलाह लें।"
        )

    if any(w in q for w in ["breastfeeding", "milk", "latch", "स्तनपान", "दूध"]):
        return T(
            "🤱 Breastfeeding tip: Start breastfeeding as early as possible after birth. Feed on demand, ensure good latch, and drink enough fluids. If baby has poor latch, low urine, weight loss, or you have breast pain/fever, seek help.",
            "🤱 स्तनपान सुझाव: जन्म के बाद जितनी जल्दी हो सके स्तनपान शुरू करें। मांग पर दूध पिलाएँ, सही ल latch रखें और पर्याप्त पानी पिएँ। शिशु सही से दूध न पीए, पेशाब कम हो, वजन घटे या माँ को स्तन दर्द/बुखार हो तो सहायता लें।"
        )

    return T(
        "I can help with pregnancy diet, medicines, ANC checkups, danger signs, baby kicks, postpartum depression, breastfeeding, yoga, and government schemes. Please ask your question in simple words. Note: I am not a doctor; for urgent symptoms call 108.",
        "मैं गर्भावस्था आहार, दवाई, ANC जाँच, खतरे के संकेत, शिशु किक, प्रसवोत्तर अवसाद, स्तनपान, योग और सरकारी योजनाओं में मदद कर सकता हूँ। कृपया अपना सवाल सरल शब्दों में पूछें। ध्यान दें: मैं डॉक्टर नहीं हूँ; आपात स्थिति में 108 पर कॉल करें।"
    )


# ══════════════════════════════════════════
# PAGES
# ══════════════════════════════════════════
if page_key == "home":
    users, logs, high = get_counts()
    st.markdown(f"""
    <div class="hero-banner">
        <div class="hero-title">{T("From Pregnancy to Recovery — Powered by AI & Care", "गर्भावस्था से रिकवरी तक — AI और देखभाल द्वारा संचालित")}</div>
        <div class="hero-subtitle">{T("Comprehensive maternal health platform with AI risk prediction, yoga & meditation, nutrition, government schemes, and postnatal support.", "AI जोखिम भविष्यवाणी, योग, ध्यान, पोषण, सरकारी योजनाएँ और प्रसवोत्तर सहायता के साथ व्यापक मातृ स्वास्थ्य मंच।")}</div>
        <div class="hero-stats">
            <div class="hero-stat"><div class="hero-stat-num">{users}</div><div class="hero-stat-label">{T("Registered Women", "पंजीकृत महिलाएँ")}</div></div>
            <div class="hero-stat"><div class="hero-stat-num">{logs}</div><div class="hero-stat-label">{T("Health Logs", "स्वास्थ्य रिकॉर्ड")}</div></div>
            <div class="hero-stat"><div class="hero-stat-num">{high}</div><div class="hero-stat-label">{T("High Risk", "उच्च जोखिम")}</div></div>
            <div class="hero-stat"><div class="hero-stat-num">5+</div><div class="hero-stat-label">{T("Schemes", "योजनाएँ")}</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f'<div class="section-header">{T("Platform Features", "मंच की विशेषताएँ")}</div>', unsafe_allow_html=True)
    feats = [
        ("🤖", T("AI Risk", "AI जोखिम"), T("ML pregnancy risk analysis", "ML गर्भावस्था जोखिम विश्लेषण")),
        ("🌱", T("Baby Journey", "शिशु यात्रा"), T("Animated growth + month video", "एनिमेटेड विकास + माह वीडियो")),
        ("🧘", T("Yoga & Wellness", "योग एवं कल्याण"), T("Videos, breathing, exercises", "वीडियो, साँस, व्यायाम")),
        ("💊", T("Medicine", "दवाई"), T("Stage-specific compliance", "चरण-विशिष्ट अनुपालन")),
        ("🥗", T("Nutrition", "पोषण"), T("Diet scoring & analysis", "आहार स्कोरिंग और विश्लेषण")),
        ("🏛️", T("Govt Schemes", "सरकारी योजनाएँ"), T("JSY, PMMVY, JSSK check", "JSY, PMMVY, JSSK जाँच")),
        ("🧠", T("PPD Screening", "PPD जाँच"), T("EPDS assessment", "EPDS मूल्यांकन")),
        ("📊", T("Dashboard", "डैशबोर्ड"), T("Analytics & export", "एनालिटिक्स और निर्यात")),
    ]
    cols = st.columns(4)
    for i, (ic, tt, dd) in enumerate(feats):
        with cols[i % 4]:
            st.markdown(f'<div class="feature-card"><div class="icon">{ic}</div><h4>{tt}</h4><p>{dd}</p></div>', unsafe_allow_html=True)


elif page_key == "register":
    st.markdown(f'<div class="section-header">{T("Beneficiary Registration", "लाभार्थी पंजीकरण")}</div>', unsafe_allow_html=True)
    with st.form("reg"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"##### {T('Personal Info', 'व्यक्तिगत जानकारी')}")
            name = st.text_input(T("Full Name*", "पूरा नाम *"))
            age = st.number_input(T("Age", "उम्र"), 15, 50, 24)
            phone = st.text_input(T("Phone*", "फ़ोन *"), max_chars=10)
            email = st.text_input(T("Email*", "ईमेल *"))
            village = st.text_input(T("Village", "गाँव"))
            district = st.text_input(T("District", "जिला"))
            state = st.selectbox(T("State", "राज्य"), ["Uttar Pradesh", "Bihar", "Madhya Pradesh", "Rajasthan", "Jharkhand", "Odisha", "Chhattisgarh", "Assam", "West Bengal", "Maharashtra", "Other"])
        with c2:
            st.markdown(f"##### {T('Medical Info', 'चिकित्सा जानकारी')}")
            stage_mode = st.selectbox(T("Stage", "स्थिति"), ["Pregnancy", "Post-Delivery"])
            if stage_mode == "Pregnancy":
                lmp = st.date_input("LMP")
                conf = st.date_input(T("Confirmation Date", "पुष्टि तिथि"))
                dd = None
                wk, edd, tri = calc_pregnancy(lmp)
            else:
                dd = st.date_input(T("Delivery Date", "प्रसव तिथि"))
                lmp = date.today()
                conf = date.today()
                wk = 0
                edd = dd
                tri = "Post-Delivery"
            ht = st.number_input(T("Height (cm)", "ऊँचाई (सेमी)"), 120, 210, 155)
            wt = st.number_input(T("Weight (kg)", "वज़न (किग्रा)"), 30.0, 160.0, 55.0, 0.5)
            bg = st.selectbox(T("Blood Group", "रक्त समूह"), ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-", "Don't know"])
            pp = st.number_input(T("Previous Pregnancies", "पिछली गर्भावस्थाएँ"), 0, 10, 0)
            pc = st.selectbox(T("Complications", "जटिलताएँ"), ["No", "High BP", "Diabetes", "Miscarriage", "C-Section", "Other"])
        bmi = calc_bmi(wt, ht)
        st.markdown(f'<div class="alert-info"><b>BMI:</b> {bmi} | <b>Week:</b> {wk if stage_mode == "Pregnancy" else "Post-Delivery"} | <b>EDD:</b> {edd}</div>', unsafe_allow_html=True)
        sub = st.form_submit_button(T("✅ Complete Registration", "✅ पंजीकरण पूरा करें"))
    if sub:
        nm, ph, em = name.strip(), phone.strip(), email.strip()
        if not nm or not ph or not em:
            st.error("Fill all required fields")
        elif not ph.isdigit() or len(ph) != 10:
            st.error("Phone must be 10 digits")
        elif not re.match(r"^[\w\.\-\+]+@[\w\.\-]+\.\w+$", em):
            st.error("Invalid email")
        else:
            data = {"name": nm, "age": age, "phone": ph, "email": em, "village": village, "district": district, "state": state,
                    "lmp_date": str(lmp), "pregnancy_confirm_date": str(conf), "edd_date": str(edd), "current_week": wk,
                    "trimester": tri, "stage_mode": stage_mode, "weight": wt, "height": ht, "bmi": bmi, "blood_group": bg,
                    "previous_pregnancies": pp, "previous_complications": pc, "delivery_date": str(dd) if dd else None}
            uid = save_user(data)
            st.session_state["user_id"] = uid
            st.session_state["user_data"] = data
            st.markdown(f'<div class="alert-success"><b>{T("✅ Registration Successful!", "✅ पंजीकरण सफल!")}</b></div>', unsafe_allow_html=True)
            email_sent = send_email(em, nm, wk, str(edd))
            if email_sent:
                st.markdown(
                    f'<div class="alert-success">{T("📧 Confirmation email sent successfully.", "📧 पुष्टि ईमेल सफलतापूर्वक भेजा गया।")}</div>',
                    unsafe_allow_html=True
                )
            else:
                err = st.session_state.get("last_email_error", "Unknown email error")
                st.markdown(
                    f'<div class="alert-warning">{T("Registration saved, but email was not sent.", "पंजीकरण सहेजा गया, लेकिन ईमेल नहीं भेजा गया।")}<br><b>{T("Reason", "कारण")}:</b> {err}<br>{T("Please configure SMTP_USER and SMTP_PASS correctly.", "कृपया SMTP_USER और SMTP_PASS सही तरीके से सेट करें।")}</div>',
                    unsafe_allow_html=True
                )


elif page_key == "journey":
    st.markdown(f'<div class="section-header">{T("Maternal Journey Guide", "मातृ यात्रा मार्गदर्शिका")}</div>', unsafe_allow_html=True)
    if not need_user():
        user_card()
        u = st.session_state["user_data"]
        wk = int(u["current_week"] or 0)
        if u["stage_mode"] == "Post-Delivery":
            st.markdown(f'<div class="alert-info">{T("Focus on recovery, breastfeeding, vaccines, mental health.", "रिकवरी, स्तनपान, टीकाकरण, मानसिक स्वास्थ्य पर ध्यान दें।")}</div>', unsafe_allow_html=True)
        else:
            if wk <= 12:
                msg = T("Start folic acid, early tests, register at PHC, learn warning signs.", "फोलिक एसिड शुरू करें, जल्दी जाँच, PHC पंजीकरण, चेतावनी संकेत जानें।")
            elif wk <= 26:
                msg = T("Nutrition, weight gain, anomaly scan, glucose test, safe exercise.", "पोषण, वज़न, एनॉमली स्कैन, ग्लूकोज़ टेस्ट, सुरक्षित व्यायाम।")
            else:
                msg = T("Prepare for delivery, monitor danger signs, final ANC visits.", "प्रसव तैयारी, खतरे संकेत, अंतिम ANC जाँच।")
            st.markdown(f'<div class="gov-card"><h4>{T("Current Guidance", "वर्तमान मार्गदर्शन")}</h4><p>{msg}</p></div>', unsafe_allow_html=True)
            prog = min(wk / 40 * 100, 100)
            st.markdown(f'<div class="gov-card"><h4>{T("Progress", "प्रगति")}</h4><div style="background:#e5e7eb;border-radius:10px;height:26px;overflow:hidden;"><div style="background:linear-gradient(90deg,#2563eb,#38a169);height:100%;width:{prog}%;border-radius:10px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:13px;">Week {wk}/40 ({prog:.0f}%)</div></div></div>', unsafe_allow_html=True)


elif page_key == "baby_dev":
    st.markdown(f'<div class="section-header">{T("🌱 Week-by-Week Baby Development", "🌱 सप्ताह-दर-सप्ताह शिशु विकास")}</div>', unsafe_allow_html=True)

    u = st.session_state["user_data"]
    if u:
        user_card()

    week_view_label = T("Week-by-Week Development", "सप्ताह-दर-सप्ताह विकास")
    video_view_label = T("Video Journey: Month 0 to 9", "वीडियो यात्रा: माह 0 से 9")
    view_mode = st.radio(T("Choose View", "दृश्य चुनें"), [week_view_label, video_view_label], horizontal=True, key="baby_dev_view_mode")

    if view_mode == video_view_label:
        st.markdown(f'<div class="section-header-orange">🎥 {T("Baby Journey from Month 0 to 9", "माह 0 से 9 तक शिशु की यात्रा")}</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="gov-card">
            <h4>{T("Animated Baby Development Video", "एनिमेटेड शिशु विकास वीडियो")}</h4>
            <p>{T("Watch how the baby develops month by month inside the womb, from conception to birth.", "देखें कि गर्भ में शिशु गर्भधारण से जन्म तक हर महीने कैसे विकसित होता है।")}</p>
        </div>
        """, unsafe_allow_html=True)
        # Language-based video selection
        # English video: Pregnancy Journey - Month by Month
        # Hindi video: Baby development from 0 to 9 months in Hindi
        BABY_JOURNEY_VIDEO_ID_EN = "NNKq8zr-hBg"
        BABY_JOURNEY_VIDEO_ID_HI = "CthcwUM-kXk"
        BABY_JOURNEY_VIDEO_ID = BABY_JOURNEY_VIDEO_ID_HI if L == "hi" else BABY_JOURNEY_VIDEO_ID_EN

        st.markdown(
            f'<div class="alert-success">🎬 {T("English video selected", "हिंदी वीडियो चुना गया")}</div>',
            unsafe_allow_html=True
        )
        embed_yt(BABY_JOURNEY_VIDEO_ID, h=430)
        st.markdown(f'<div class="alert-info"><b>{T("Note", "ध्यान दें")}:</b> {T("This video is for education only. Always follow your doctor\'s advice for pregnancy care.", "यह वीडियो केवल शैक्षिक उद्देश्य के लिए है। गर्भावस्था देखभाल के लिए हमेशा डॉक्टर की सलाह मानें।")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="section-header">{T("Month-by-Month Summary", "माह-दर-माह सारांश")}</div>', unsafe_allow_html=True)
        month_data = [
            ("🌱", T("Month 1", "माह 1"), T("Fertilization, implantation, and early cell division begin. The baby is very tiny.", "निषेचन, प्रत्यारोपण और शुरुआती कोशिका विभाजन शुरू होता है। शिशु बहुत छोटा होता है।")),
            ("💓", T("Month 2", "माह 2"), T("Heart starts beating. Brain, spinal cord, arms, and legs begin forming.", "दिल धड़कना शुरू करता है। मस्तिष्क, रीढ़, हाथ और पैर बनने लगते हैं।")),
            ("👶", T("Month 3", "माह 3"), T("Major organs are formed. Fingers, toes, and facial features become clearer.", "मुख्य अंग बन जाते हैं। उंगलियाँ, पैर की उंगलियाँ और चेहरे की बनावट स्पष्ट होती है।")),
            ("🤰", T("Month 4", "माह 4"), T("Baby grows quickly. Bones become stronger and movements may begin.", "शिशु तेजी से बढ़ता है। हड्डियाँ मजबूत होती हैं और हलचल शुरू हो सकती है।")),
            ("👣", T("Month 5", "माह 5"), T("Mother may feel baby kicks. Hair, eyebrows, and hearing develop.", "माँ को शिशु की हलचल महसूस हो सकती है। बाल, भौहें और सुनने की क्षमता विकसित होती है।")),
            ("🌟", T("Month 6", "माह 6"), T("Baby responds to sound and light. Lungs continue developing.", "शिशु आवाज़ और रोशनी पर प्रतिक्रिया देता है। फेफड़े विकसित होते रहते हैं।")),
            ("🧠", T("Month 7", "माह 7"), T("Brain develops rapidly. Baby opens eyes and gains weight.", "मस्तिष्क तेजी से विकसित होता है। शिशु आँखें खोलता है और वजन बढ़ता है।")),
            ("💪", T("Month 8", "माह 8"), T("Baby gains more fat and strength. Most organs are nearly mature.", "शिशु अधिक वसा और ताकत प्राप्त करता है। अधिकांश अंग लगभग परिपक्व होते हैं।")),
            ("🎉", T("Month 9", "माह 9"), T("Baby is ready for birth. Lungs mature and baby moves into birth position.", "शिशु जन्म के लिए तैयार होता है। फेफड़े परिपक्व होते हैं और शिशु जन्म की स्थिति में आता है।")),
        ]
        cols = st.columns(3)
        for i, (emoji, month, desc) in enumerate(month_data):
            with cols[i % 3]:
                st.markdown(f'<div class="feature-card"><div class="icon">{emoji}</div><h4>{month}</h4><p>{desc}</p></div>', unsafe_allow_html=True)

    else:
        cur_wk = int(u["current_week"]) if u and u["stage_mode"] == "Pregnancy" and u.get("current_week") is not None else 20
        week_list = sorted(BABY_WEEKS.keys())
        closest = min(week_list, key=lambda x: abs(x - cur_wk))
        sel_wk = st.select_slider(T("Select Week", "सप्ताह चुनें"), options=week_list, value=closest)
        w = BABY_WEEKS[sel_wk]
        tri_label = T("First Trimester", "पहली तिमाही") if sel_wk <= 12 else T("Second Trimester", "दूसरी तिमाही") if sel_wk <= 26 else T("Third Trimester", "तीसरी तिमाही")
        tri_color = "#2563eb" if sel_wk <= 12 else "#12b76a" if sel_wk <= 26 else "#f79009"
        prog_pct = min(sel_wk / 40 * 100, 100)
        dev_text = w["dev_hi"] if L == "hi" else w["dev"]
        mom_text = w["mom_hi"] if L == "hi" else w["mom"]
        tip_text = w["tip_hi"] if L == "hi" else w["tip"]
        size_label, wt_label, ln_label = T("Baby Size", "शिशु का आकार"), T("Weight", "वज़न"), T("Length", "लंबाई")
        dev_label, mom_label, tip_label = T("Baby's Development", "शिशु का विकास"), T("Mother's Body Changes", "माँ के शरीर में बदलाव"), T("Tips for This Week", "इस सप्ताह के सुझाव")
        wk_label = T("Week", "सप्ताह")
        animated_html = f"""
        <!DOCTYPE html><html><head><style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;600;700;800&display=swap');
        *{{margin:0;padding:0;box-sizing:border-box;}} body{{font-family:'Noto Sans',sans-serif;background:transparent;}}
        @keyframes fadeInUp{{from{{opacity:0;transform:translateY(30px);}}to{{opacity:1;transform:translateY(0);}}}}
        @keyframes pulse{{0%,100%{{transform:scale(1);}}50%{{transform:scale(1.15);}}}}
        @keyframes glow{{0%,100%{{box-shadow:0 0 10px rgba(37,99,235,.2);}}50%{{box-shadow:0 0 25px rgba(37,99,235,.4);}}}}
        @keyframes slideRight{{from{{width:0%;}}to{{width:{prog_pct}%;}}}}
        @keyframes bounceIn{{0%{{transform:scale(.3);opacity:0;}}50%{{transform:scale(1.05);}}70%{{transform:scale(.95);}}100%{{transform:scale(1);opacity:1;}}}}
        .card{{background:linear-gradient(135deg,#f0f9ff,#fff);border:2px solid #bfdbfe;border-left:8px solid {tri_color};border-radius:18px;padding:28px;animation:fadeInUp .6s ease-out;}}
        .header-row{{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-bottom:18px;}}
        .week-badge{{background:linear-gradient(90deg,#2563eb,#1d4ed8);color:#fff;padding:8px 22px;border-radius:22px;font-weight:800;font-size:18px;animation:bounceIn .8s ease-out;}}
        .tri-badge{{background:{tri_color};color:#fff;padding:5px 16px;border-radius:16px;font-weight:700;font-size:13px;animation:fadeInUp .8s ease-out .2s both;}}
        .size-box{{display:flex;align-items:center;gap:16px;background:rgba(37,99,235,.06);border-radius:14px;padding:16px 20px;margin:16px 0;animation:fadeInUp .7s ease-out .3s both;}}
        .size-emoji{{font-size:56px;animation:pulse 2s ease-in-out infinite;}}
        .size-name{{font-size:20px;font-weight:800;color:#1d4ed8;}} .size-detail{{font-size:13px;color:#667085;margin-top:2px;}}
        .section{{margin-top:18px;padding:14px 18px;background:#fff;border-radius:12px;border:1px solid #e5e7eb;}}
        .s1{{animation:fadeInUp .7s ease-out .4s both;}} .s2{{animation:fadeInUp .7s ease-out .6s both;}} .s3{{animation:fadeInUp .7s ease-out .8s both;border-left:4px solid #12b76a;}}
        .section h3{{font-size:15px;font-weight:700;color:#0b3b78;margin-bottom:8px;}} .section p{{font-size:14px;color:#374151;line-height:1.7;}}
        .progress-container{{margin-top:20px;animation:fadeInUp .7s ease-out 1s both;}} .progress-label{{font-size:12px;color:#667085;margin-bottom:6px;}}
        .progress-bar{{background:#e5e7eb;border-radius:12px;height:22px;overflow:hidden;animation:glow 2s ease-in-out infinite;}}
        .progress-fill{{background:linear-gradient(90deg,#2563eb,{tri_color});height:100%;border-radius:12px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:12px;animation:slideRight 1.5s ease-out 1.2s both;}}
        </style></head><body><div class="card">
        <div class="header-row"><div class="week-badge">{wk_label} {sel_wk}</div><div class="tri-badge">{tri_label}</div></div>
        <div class="size-box"><div class="size-emoji">{w['emoji']}</div><div><div class="size-name">{size_label}: {w['size']}</div><div class="size-detail">{wt_label}: {w['wt']} | {ln_label}: {w['ln']}</div></div></div>
        <div class="section s1"><h3>👶 {dev_label}</h3><p>{dev_text}</p></div>
        <div class="section s2"><h3>🤰 {mom_label}</h3><p>{mom_text}</p></div>
        <div class="section s3"><h3>💡 {tip_label}</h3><p>{tip_text}</p></div>
        <div class="progress-container"><div class="progress-label">{T("Pregnancy Progress", "गर्भावस्था प्रगति")}</div><div class="progress-bar"><div class="progress-fill">{wk_label} {sel_wk}/40 ({prog_pct:.0f}%)</div></div></div>
        </div></body></html>
        """
        components.html(animated_html, height=620, scrolling=True)
        if st.checkbox(T("Show All Weeks Timeline", "सभी सप्ताह की समयरेखा दिखाएँ")):
            for wn in week_list:
                wd = BABY_WEEKS[wn]
                tc = "#2563eb" if wn <= 12 else "#12b76a" if wn <= 26 else "#f79009"
                dev = wd["dev_hi"] if L == "hi" else wd["dev"]
                dev_preview = dev[:100] + "..." if len(dev) > 100 else dev
                hl = "border:2px solid #d92d20;background:#fff5f5;" if wn == closest else ""
                st.markdown(f'<div style="display:flex;gap:12px;margin-bottom:10px;padding:10px 14px;border-radius:10px;background:#fff;border:1px solid #e5e7eb;{hl}"><div style="width:12px;height:12px;border-radius:50%;background:{tc};margin-top:5px;flex-shrink:0;"></div><div><b>{T("Week", "सप्ताह")} {wn}</b> — {wd["emoji"]} {wd["size"]}<br><span style="color:#667085;font-size:13px;">{dev_preview}</span></div></div>', unsafe_allow_html=True)


elif page_key == "health":
    st.markdown(f'<div class="section-header">{T("Daily Health Monitoring", "दैनिक स्वास्थ्य निगरानी")}</div>', unsafe_allow_html=True)
    if not need_user():
        user_card()
        u = st.session_state["user_data"]
        c1, c2, c3 = st.columns(3)
        with c1:
            weight = st.number_input(T("Weight (kg)", "वज़न (किग्रा)"), 30.0, 160.0, float(u["weight"]), 0.5)
            temperature = st.number_input(T("Temperature (°F)", "तापमान (°F)"), 95.0, 105.0, 98.6, 0.1)
        with c2:
            bp_sys = st.number_input(T("BP Systolic", "BP सिस्टोलिक"), 70, 220, 120)
            bp_dia = st.number_input(T("BP Diastolic", "BP डायस्टोलिक"), 40, 140, 80)
        with c3:
            hemoglobin = st.number_input(T("Hemoglobin (g/dL)", "हीमोग्लोबिन"), 4.0, 18.0, 11.0, 0.1)
            blood_sugar = st.number_input(T("Blood Sugar (mg/dL)", "रक्त शर्करा"), 50.0, 400.0, 100.0, 1.0)
        symptoms = st.multiselect(T("Symptoms Today", "आज के लक्षण"), ["Headache", "Swelling", "Bleeding", "Blurred vision", "Severe nausea", "Chest pain", "Reduced baby movement", "Fever", "Back pain", "Difficulty breathing", "No symptoms"])
        c4, c5, c6 = st.columns(3)
        with c4:
            water = st.slider(T("Water (glasses)", "पानी (गिलास)"), 0, 15, 8)
        with c5:
            sleep = st.slider(T("Sleep (hours)", "नींद (घंटे)"), 0, 14, 7)
        with c6:
            mood = st.selectbox(T("Mood", "मनोदशा"), ["Very Sad", "Sad", "Okay", "Good", "Very Happy"])
        if st.button(T("💾 Save Health Log", "💾 स्वास्थ्य रिकॉर्ड सहेजें")):
            save_health_log(st.session_state["user_id"], {"weight": weight, "bp_systolic": bp_sys, "bp_diastolic": bp_dia, "hemoglobin": hemoglobin, "blood_sugar": blood_sugar, "temperature": temperature, "symptoms": symptoms, "water_intake": water, "sleep_hours": sleep, "mood": mood})
            st.markdown(f'<div class="alert-success">{T("Health log saved!", "स्वास्थ्य रिकॉर्ड सहेजा गया!")}</div>', unsafe_allow_html=True)
            if bp_sys > 140 or bp_dia > 90:
                st.markdown(f'<div class="alert-danger">{T("⚠️ High BP detected!", "⚠️ उच्च रक्तचाप!")}</div>', unsafe_allow_html=True)
            if hemoglobin < 7:
                st.markdown(f'<div class="alert-danger">{T("⚠️ Severe anemia!", "⚠️ गंभीर एनीमिया!")}</div>', unsafe_allow_html=True)
            elif hemoglobin < 11:
                st.markdown(f'<div class="alert-warning">{T("⚠️ Low hemoglobin", "⚠️ कम हीमोग्लोबिन")}</div>', unsafe_allow_html=True)
            if blood_sugar > 200:
                st.markdown(f'<div class="alert-danger">{T("⚠️ Very high blood sugar!", "⚠️ बहुत अधिक रक्त शर्करा!")}</div>', unsafe_allow_html=True)
            if "Bleeding" in symptoms:
                st.markdown(f'<div class="alert-danger">{T("🚨 Bleeding reported — seek medical help!", "🚨 रक्तस्राव — चिकित्सा सहायता लें!")}</div>', unsafe_allow_html=True)


elif page_key == "medicine":
    st.markdown(f'<div class="section-header">{T("Medicine & Supplement Compliance", "दवाई अनुपालन")}</div>', unsafe_allow_html=True)
    if not need_user():
        user_card()
        u = st.session_state["user_data"]
        if u["stage_mode"] == "Post-Delivery":
            meds = [("Iron / आयरन", "1 tablet", "Night", T("Recovery", "रिकवरी")), ("Calcium / कैल्शियम", "500mg", "Morning", T("Bone support", "हड्डी सहायता")), ("Vitamin A", "As prescribed", "As advised", T("Postnatal recovery", "प्रसवोत्तर रिकवरी"))]
        else:
            wk = int(u["current_week"] or 0)
            if wk <= 12:
                meds = [("Folic Acid / फोलिक एसिड", "400mcg", "Morning", T("Baby brain development", "शिशु मस्तिष्क विकास")), ("Iron+Folic Acid (IFA)", "1 tablet", "Night", T("Prevents anemia", "एनीमिया रोकता है"))]
            elif wk <= 26:
                meds = [("IFA", "1 tablet", "Night", T("Blood health", "रक्त स्वास्थ्य")), ("Calcium", "500mg", "Morning", T("Bone development", "हड्डी विकास")), ("Vitamin D", "As prescribed", "With meals", T("Calcium absorption", "कैल्शियम अवशोषण"))]
            else:
                meds = [("IFA", "1 tablet", "Night", T("Blood health", "रक्त स्वास्थ्य")), ("Calcium", "500mg", "Morning", T("Late pregnancy", "देर गर्भावस्था")), ("TT Vaccine Reminder", "Scheduled", "Health center", T("Tetanus protection", "टेटनस सुरक्षा"))]
        tk = 0
        for i, (nm, dose, tm, why) in enumerate(meds):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f'<div class="gov-card"><b>{nm}</b><br>{T("Dose", "खुराक")}: {dose} | {T("When", "कब")}: {tm}<br>{T("Why", "क्यों")}: {why}</div>', unsafe_allow_html=True)
            with c2:
                if st.checkbox("✓", key=f"med_{i}"):
                    tk += 1
        if st.button(T("💾 Save Compliance", "💾 अनुपालन सहेजें")):
            comp = (tk / len(meds)) * 100 if meds else 0
            taken = [m[0] for i, m in enumerate(meds) if st.session_state.get(f"med_{i}", False)]
            save_medicine_log(st.session_state["user_id"], taken, comp)
            if comp == 100:
                st.markdown(f'<div class="alert-success">{T("100% compliance! Excellent!", "100% अनुपालन! उत्कृष्ट!")}</div>', unsafe_allow_html=True)
            elif comp >= 50:
                st.markdown(f'<div class="alert-warning">{T("Partial compliance. Some missed.", "आंशिक अनुपालन। कुछ छूट गया।")}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="alert-danger">{T("Low compliance! Take medicines regularly.", "कम अनुपालन! नियमित दवाई लें।")}</div>', unsafe_allow_html=True)


elif page_key == "nutrition":
    st.markdown(f'<div class="section-header">{T("Nutrition Guide & Food Logger", "पोषण मार्गदर्शिका और फूड लॉगर")}</div>', unsafe_allow_html=True)
    if not need_user():
        user_card()
        u = st.session_state["user_data"]
        if u["stage_mode"] == "Post-Delivery":
            st.markdown(f'<div class="alert-info">{T("Focus: Recovery nutrition, hydration, iron, calcium, breastfeeding foods.", "फोकस: रिकवरी पोषण, पानी, आयरन, कैल्शियम, स्तनपान भोजन।")}</div>', unsafe_allow_html=True)
        else:
            wk = int(u["current_week"] or 0)
            if wk <= 12:
                focus = T("Focus: Folic acid, iron, light foods, fruits, hydration.", "फोकस: फोलिक एसिड, आयरन, हल्का भोजन, फल, पानी।")
            elif wk <= 26:
                focus = T("Focus: Protein, calcium, iron, milk, eggs, dal, curd, green vegetables.", "फोकस: प्रोटीन, कैल्शियम, आयरन, दूध, अंडे, दाल, दही, हरी सब्जियाँ।")
            else:
                focus = T("Focus: Iron, hydration, protein, energy foods, calcium.", "फोकस: आयरन, पानी, प्रोटीन, ऊर्जा भोजन, कैल्शियम।")
            st.markdown(f'<div class="alert-info">{focus}</div>', unsafe_allow_html=True)
        tab1, tab2 = st.tabs([T("Food Log", "फूड लॉग"), T("Nutrition Advice", "पोषण सलाह")])
        with tab1:
            bf = st.multiselect(T("Breakfast", "नाश्ता"), ["Roti", "Paratha", "Poha", "Upma", "Daliya", "Egg", "Milk", "Banana", "Apple", "Sprouts", "Curd"])
            lu = st.multiselect(T("Lunch", "दोपहर"), ["Rice", "Roti", "Dal", "Rajma", "Green leafy vegetables", "Mixed vegetables", "Curd", "Egg", "Fish", "Chicken"])
            sn = st.multiselect(T("Snack", "नाश्ता"), ["Fruit", "Milk", "Roasted chana", "Peanuts", "Sprouts", "Juice", "Dry fruits"])
            dn = st.multiselect(T("Dinner", "रात"), ["Roti", "Rice", "Dal", "Sabzi", "Khichdi", "Curd", "Egg", "Soup", "Fruit", "Milk"])
            if st.button(T("🔍 Analyze Nutrition", "🔍 पोषण विश्लेषण")):
                foods = bf + lu + sn + dn
                pr = {"Dal", "Rajma", "Egg", "Milk", "Curd", "Fish", "Chicken", "Sprouts"}
                ir = {"Green leafy vegetables", "Dal", "Rajma", "Dry fruits", "Peanuts", "Sprouts"}
                ca = {"Milk", "Curd"}
                vi = {"Fruit", "Apple", "Banana", "Juice", "Green leafy vegetables", "Mixed vegetables"}
                cb = {"Rice", "Roti", "Paratha", "Poha", "Upma", "Daliya", "Khichdi"}
                score = sum([any(f in pr for f in foods), any(f in ir for f in foods), any(f in ca for f in foods), any(f in vi for f in foods), any(f in cb for f in foods)])
                save_nutrition_log(st.session_state["user_id"], bf, lu, sn, dn, score)
                lbl = T("Diet Score", "आहार स्कोर")
                if score == 5:
                    st.markdown(f'<div class="alert-success"><b>{lbl}: 5/5 — {T("Excellent!", "उत्कृष्ट!")}</b></div>', unsafe_allow_html=True)
                elif score >= 3:
                    st.markdown(f'<div class="alert-warning"><b>{lbl}: {score}/5 — {T("Good, needs improvement", "अच्छा, सुधार आवश्यक")}</b></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="alert-danger"><b>{lbl}: {score}/5 — {T("Major gaps!", "प्रमुख कमियाँ!")}</b></div>', unsafe_allow_html=True)
        with tab2:
            st.markdown(f"""
            <div class="gov-card"><h4>{T("Recommended Foods", "अनुशंसित भोजन")}</h4><ul>
            <li><b>{T("Protein", "प्रोटीन")}:</b> {T("Dal, eggs, milk, curd, sprouts, paneer", "दाल, अंडे, दूध, दही, अंकुर, पनीर")}</li>
            <li><b>{T("Iron", "आयरन")}:</b> {T("Green leafy vegetables, jaggery, dates, rajma, beetroot", "हरी पत्तेदार सब्जियाँ, गुड़, खजूर, राजमा, चुकंदर")}</li>
            <li><b>{T("Calcium", "कैल्शियम")}:</b> {T("Milk, curd, paneer, ragi", "दूध, दही, पनीर, रागी")}</li>
            <li><b>{T("Hydration", "जलयोजन")}:</b> {T("8-10 glasses water, coconut water, buttermilk", "8-10 गिलास पानी, नारियल पानी, छाछ")}</li>
            </ul></div>
            """, unsafe_allow_html=True)


elif page_key == "yoga":
    st.markdown(f'<div class="section-header">{T("Yoga, Meditation & Exercise", "योग, ध्यान और व्यायाम")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="alert-warning"><b>{T("⚠️ Consult doctor before exercising. Stop if pain/bleeding/dizziness.", "⚠️ व्यायाम से पहले डॉक्टर से सलाह लें। दर्द/रक्तस्राव/चक्कर आने पर रुकें।")}</b></div>', unsafe_allow_html=True)
    u = st.session_state["user_data"]
    if u and u["stage_mode"] == "Post-Delivery":
        stage = "post"
    elif u and int(u["current_week"] or 0) <= 12:
        stage = "first"
    elif u and int(u["current_week"] or 0) <= 26:
        stage = "second"
    elif u:
        stage = "third"
    else:
        stage = "first"
    t1, t2, t3 = st.tabs([T("🧘 Yoga Videos", "🧘 योग वीडियो"), T("🧠 Meditation", "🧠 ध्यान"), T("🌬️ Breathing", "🌬️ साँस के व्यायाम")])
    with t1:
        for v in YOGA_VIDEOS.get(stage, []):
            st.markdown(f'<div class="video-card"><h4>🎬 {v["t"]}</h4><p>{v["d"]}</p></div>', unsafe_allow_html=True)
            embed_yt(v["id"])
    with t2:
        for v in MED_VIDEOS:
            st.markdown(f'<div class="video-card"><h4>🧘 {v["t"]}</h4><p>{v["d"]}</p></div>', unsafe_allow_html=True)
            embed_yt(v["id"])
    with t3:
        for v in BREATH_VIDEOS:
            st.markdown(f'<div class="video-card"><h4>🌬️ {v["t"]}</h4><p>{v["d"]}</p></div>', unsafe_allow_html=True)
            embed_yt(v["id"])
        for nm, desc in [(T("4-7-8 Breathing", "4-7-8 श्वास"), T("Inhale 4 counts → Hold 7 → Exhale 8. Repeat 4 cycles.", "4 गिनती साँस लें → 7 रोकें → 8 छोड़ें। 4 बार दोहराएँ।")), (T("Anulom Vilom", "अनुलोम विलोम"), T("Close right nostril → Inhale left → Exhale right. Repeat gently.", "दायाँ बंद → बाएँ से साँस → दाएँ से छोड़ें। धीरे-धीरे दोहराएँ।"))]:
            st.markdown(f'<div class="gov-card"><h4>🌬️ {nm}</h4><p>{desc}</p></div>', unsafe_allow_html=True)


elif page_key == "risk":
    st.markdown(f'<div class="section-header">{T("AI Risk Assessment", "AI जोखिम मूल्यांकन")}</div>', unsafe_allow_html=True)
    if not need_user():
        user_card()
        u = st.session_state["user_data"]
        c1, c2 = st.columns(2)
        with c1:
            age = st.number_input(T("Age", "उम्र"), 15, 50, int(u["age"]), key="ra")
            wt = st.number_input(T("Weight", "वज़न"), 30.0, 160.0, float(u["weight"]), key="rw")
            ht = st.number_input(T("Height", "ऊँचाई"), 120, 210, int(u["height"]), key="rh")
            bp_s = st.number_input("BP Systolic", 70, 220, 120, key="rs")
        with c2:
            bp_d = st.number_input("BP Diastolic", 40, 140, 80, key="rd")
            hb = st.number_input(T("Hemoglobin", "हीमोग्लोबिन"), 4.0, 18.0, 11.0, key="rhb")
            sugar = st.number_input(T("Blood Sugar", "रक्त शर्करा"), 50.0, 400.0, 100.0, key="rsu")
            week_default = max(1, int(u["current_week"] or 1))
            week = st.number_input(T("Week", "सप्ताह"), 1, 42, week_default, key="rwk")
        prev = st.selectbox(T("Previous Complications?", "पिछली जटिलताएँ?"), ["No", "Yes"], key="rp")
        bmi = calc_bmi(wt, ht)
        st.markdown(f'<div class="alert-info"><b>BMI:</b> {bmi}</div>', unsafe_allow_html=True)
        if st.button(T("🔍 Predict Risk", "🔍 जोखिम पता करें")):
            X = np.array([[age, bmi, bp_s, bp_d, hb, sugar, 1 if prev == "Yes" else 0, week]])
            pred = risk_model.predict(X)[0]
            probs = risk_model.predict_proba(X)[0]
            labels = {0: T("LOW RISK", "कम जोखिम"), 1: T("MEDIUM RISK", "मध्यम जोखिम"), 2: T("HIGH RISK", "उच्च जोखिम")}
            save_risk_log(st.session_state["user_id"], labels[pred], probs[0], probs[1], probs[2])
            cls = {0: "alert-success", 1: "alert-warning", 2: "alert-danger"}
            st.markdown(f'<div class="{cls[pred]}"><b>{labels[pred]}</b></div>', unsafe_allow_html=True)
            fig = go.Figure(data=[go.Bar(x=[T("Low", "कम"), T("Medium", "मध्यम"), T("High", "उच्च")], y=[probs[0] * 100, probs[1] * 100, probs[2] * 100], marker_color=["#12b76a", "#f79009", "#d92d20"], text=[f"{p * 100:.1f}%" for p in probs], textposition="auto")])
            fig.update_layout(height=380, title=T("Risk Distribution", "जोखिम वितरण"), yaxis_title="%")
            st.plotly_chart(fig, use_container_width=True)


elif page_key == "checkup":
    st.markdown(f'<div class="section-header">{T("ANC & PNC Schedule", "ANC और PNC अनुसूची")}</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"##### {T('Antenatal (ANC)', 'प्रसव पूर्व (ANC)')}")
        st.dataframe(pd.DataFrame({"Visit": ["ANC 1", "ANC 2", "ANC 3", "ANC 4"], "When": [T("Before 12 wks", "12 सप्ताह से पहले"), T("14-26 wks", "14-26 सप्ताह"), T("28-32 wks", "28-32 सप्ताह"), T("36+ wks", "36+ सप्ताह")], "Services": [T("Registration, blood tests, BP", "पंजीकरण, रक्त जाँच, BP"), T("Ultrasound, glucose, TT", "अल्ट्रासाउंड, ग्लूकोज़, TT"), T("Hemoglobin, BP, fetal check", "हीमोग्लोबिन, BP, शिशु जाँच"), T("Birth prep, final checks", "प्रसव तैयारी, अंतिम जाँच")]}), use_container_width=True, hide_index=True)
    with c2:
        st.markdown(f"##### {T('Postnatal (PNC)', 'प्रसव बाद (PNC)')}")
        st.dataframe(pd.DataFrame({"Visit": ["PNC 1", "PNC 2", "PNC 3"], "When": [T("Within 48 hrs", "48 घंटे में"), T("Day 3-7", "दिन 3-7"), T("Day 42", "दिन 42")], "Services": [T("Mother & newborn check", "माँ-शिशु जाँच"), T("Breastfeeding check", "स्तनपान जाँच"), T("Full postnatal review", "पूर्ण प्रसवोत्तर समीक्षा")]}), use_container_width=True, hide_index=True)


elif page_key == "govt":
    st.markdown(f'<div class="section-header">{T("Government Scheme Eligibility", "सरकारी योजना पात्रता")}</div>', unsafe_allow_html=True)
    if not need_user():
        user_card()
        c1, c2 = st.columns(2)
        with c1:
            area = st.selectbox(T("Area", "क्षेत्र"), ["Rural", "Urban"])
            income = st.selectbox(T("Income", "आय"), ["Below 1 Lakh (BPL)", "1-3 Lakh", "3-5 Lakh", "Above 5 Lakh"])
            first = st.selectbox(T("First live birth?", "पहला जन्म?"), ["Yes", "No"])
        with c2:
            deliv = st.selectbox(T("Delivery Place", "प्रसव स्थान"), ["Government Hospital", "Private Hospital", "Not Decided"])
            aadhar = st.selectbox(T("Has Aadhaar?", "आधार है?"), ["Yes", "No"])
            bank = st.selectbox(T("Has Bank Account?", "बैंक खाता?"), ["Yes", "No"])
        if st.button(T("Check Benefits", "लाभ जाँचें")):
            total = 0
            st.markdown(f'<div class="section-header-orange">{T("Eligible Schemes", "पात्र योजनाएँ")}</div>', unsafe_allow_html=True)
            if area == "Rural" or income == "Below 1 Lakh (BPL)":
                amt = 1400 if area == "Rural" else 1000
                total += amt
                st.markdown(f'<div class="scheme-card"><h4>1. Janani Suraksha Yojana (JSY)</h4><div class="amount">₹{amt}</div><p>{T("Cash for institutional delivery. Register through ASHA worker.", "संस्थागत प्रसव के लिए नकद। ASHA कार्यकर्ता से पंजीकरण।")}</p></div>', unsafe_allow_html=True)
            if first == "Yes":
                total += 5000
                st.markdown(f'<div class="scheme-card"><h4>2. Pradhan Mantri Matru Vandana Yojana (PMMVY)</h4><div class="amount">₹5,000</div><p>{T("Cash transfer in installments for first birth. Apply via Anganwadi.", "पहले जन्म के लिए किस्तों में नकद। आँगनवाड़ी से आवेदन।")}</p></div>', unsafe_allow_html=True)
            if deliv == "Government Hospital":
                st.markdown(f'<div class="scheme-card"><h4>3. Janani Shishu Suraksha Karyakram (JSSK)</h4><div class="amount">{T("Free Services", "मुफ्त सेवाएँ")}</div><p>{T("Free delivery, C-section, medicines, diagnostics, blood, diet, transport.", "मुफ्त प्रसव, सी-सेक्शन, दवाइयाँ, जाँच, रक्त, आहार, परिवहन।")}</p></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="scheme-card"><h4>4. Poshan Abhiyaan</h4><div class="amount">{T("Nutrition Support", "पोषण सहायता")}</div><p>{T("Supplementary nutrition through Anganwadi.", "आँगनवाड़ी से पूरक पोषण।")}</p></div>', unsafe_allow_html=True)
            if income in ["Below 1 Lakh (BPL)", "1-3 Lakh"]:
                st.markdown(f'<div class="scheme-card"><h4>5. Ayushman Bharat (PM-JAY)</h4><div class="amount">{T("Up to ₹5 Lakh", "₹5 लाख तक")}</div><p>{T("Hospitalization coverage for eligible families.", "पात्र परिवारों के लिए अस्पताल में भर्ती कवरेज।")}</p></div>', unsafe_allow_html=True)
            if aadhar == "No":
                st.markdown(f'<div class="alert-warning">{T("Aadhaar missing — many schemes need it.", "आधार नहीं — कई योजनाओं में ज़रूरी।")}</div>', unsafe_allow_html=True)
            if bank == "No":
                st.markdown(f'<div class="alert-warning">{T("Bank account missing — cash benefits need it.", "बैंक खाता नहीं — नकद लाभ के लिए ज़रूरी।")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="alert-success"><b>{T("Total Estimated Cash", "कुल अनुमानित नकद")}: ₹{total:,}+</b></div>', unsafe_allow_html=True)


elif page_key == "postdelivery":
    st.markdown(f'<div class="section-header">{T("Post-Delivery Care", "प्रसव बाद देखभाल")}</div>', unsafe_allow_html=True)
    if not need_user():
        user_card()
        st.markdown(f"""<div class="gov-card"><h4>{T("Postnatal Checklist", "प्रसवोत्तर चेकलिस्ट")}</h4><ul>
        <li>{T("Monitor bleeding, fever, wound healing", "रक्तस्राव, बुखार, घाव भरने की निगरानी")}</li>
        <li>{T("Breastfeeding support & hydration", "स्तनपान सहायता और पानी")}</li>
        <li>{T("Continue iron & calcium", "आयरन और कैल्शियम जारी रखें")}</li>
        <li>{T("Newborn vaccination schedule", "नवजात टीकाकरण अनुसूची")}</li>
        <li>{T("PNC visits: 48hrs, Day 3-7, Day 42", "PNC: 48 घंटे, दिन 3-7, दिन 42")}</li>
        </ul></div>""", unsafe_allow_html=True)

        # ─────────────────────────────────────
        # 🧠 Postpartum Depression / Emotional Care
        # ─────────────────────────────────────
        st.markdown(
            f'<div class="section-header-orange">🧠 {T("Postpartum Depression & Emotional Care", "प्रसवोत्तर अवसाद और मानसिक देखभाल")}</div>',
            unsafe_allow_html=True
        )
        st.markdown(f"""
        <div class="gov-card">
            <h4>{T("What to watch for", "किन बातों पर ध्यान दें")}</h4>
            <p>{T(
                "Feeling tired or emotional after delivery is common, but sadness, anxiety, crying, guilt, hopelessness, or scary thoughts lasting more than 2 weeks may need medical support.",
                "प्रसव के बाद थकान या भावुकता सामान्य हो सकती है, लेकिन 2 सप्ताह से अधिक उदासी, चिंता, बार-बार रोना, अपराधबोध, निराशा या डरावने विचार हों तो चिकित्सा सहायता जरूरी हो सकती है।"
            )}</p>
            <ul>
                <li>{T("Talk to your doctor, ASHA/ANM, or counsellor.", "अपने डॉक्टर, आशा/ANM या काउंसलर से बात करें।")}</li>
                <li>{T("Ask family for help with baby care, sleep, meals, and household work.", "परिवार से शिशु देखभाल, नींद, भोजन और घर के काम में मदद लें।")}</li>
                <li>{T("If there are thoughts of self-harm or harming the baby, seek emergency help immediately.", "अगर खुद को या शिशु को नुकसान पहुँचाने के विचार आएँ, तो तुरंत आपातकालीन सहायता लें।")}</li>
            </ul>
            <p><b>{T("Helplines", "हेल्पलाइन")}:</b> 104 | 108 | {T("Mental Health", "मानसिक स्वास्थ्य")}: 9152987821</p>
        </div>
        """, unsafe_allow_html=True)

        with st.expander(T("🧠 Quick Postpartum Depression Check", "🧠 त्वरित प्रसवोत्तर अवसाद जाँच"), expanded=False):
            st.caption(T(
                "This is a quick screening tool, not a diagnosis. Answer based on the last 7 days.",
                "यह एक त्वरित स्क्रीनिंग है, निदान नहीं। पिछले 7 दिनों के आधार पर उत्तर दें।"
            ))
            ppd_opts = [
                f"(0) {T('Not at all', 'बिल्कुल नहीं')}",
                f"(1) {T('Sometimes', 'कभी-कभी')}",
                f"(2) {T('Often', 'अक्सर')}",
                f"(3) {T('Most of the time', 'अधिकांश समय')}"
            ]
            quick_qs = [
                T("I felt sad, low, or hopeless", "मैं उदास, निराश या बहुत कमजोर महसूस कर रही हूँ"),
                T("I felt anxious, worried, or panicky", "मैं चिंतित, परेशान या घबराई हुई महसूस कर रही हूँ"),
                T("I cried more than usual", "मैं सामान्य से अधिक रोई हूँ"),
                T("I felt overwhelmed and unable to cope", "मुझे सब कुछ बहुत भारी लगा और संभालना मुश्किल लगा"),
                T("I had difficulty sleeping even when the baby was asleep", "शिशु के सोने पर भी मुझे नींद आने में कठिनाई हुई"),
                T("I had thoughts of harming myself or the baby", "मुझे खुद को या शिशु को नुकसान पहुँचाने के विचार आए")
            ]
            quick_responses = []
            for qi, qq in enumerate(quick_qs, 1):
                quick_responses.append(st.radio(f"{qi}. {qq}", ppd_opts, key=f"postdelivery_ppd_{qi}_{st.session_state['user_id']}"))

            if st.button(T("Calculate PPD Quick Score", "PPD त्वरित स्कोर निकालें"), key="postdelivery_ppd_calc"):
                quick_scores = [int(resp[1]) for resp in quick_responses]
                quick_total = sum(quick_scores)
                self_harm_score = quick_scores[-1]

                if self_harm_score > 0 or quick_total >= 11:
                    ppd_level = T("HIGH RISK", "उच्च जोखिम")
                    ppd_class = "alert-danger"
                elif quick_total >= 6:
                    ppd_level = T("MODERATE RISK", "मध्यम जोखिम")
                    ppd_class = "alert-warning"
                else:
                    ppd_level = T("LOW RISK", "कम जोखिम")
                    ppd_class = "alert-success"

                save_ppd_log(st.session_state["user_id"], quick_total, ppd_level)
                st.markdown(
                    f'<div class="{ppd_class}"><b>{T("PPD Quick Score", "PPD त्वरित स्कोर")}: {quick_total}/18 — {ppd_level}</b></div>',
                    unsafe_allow_html=True
                )

                if self_harm_score > 0:
                    st.markdown(
                        f'<div class="alert-danger"><b>{T("Emergency", "आपातकाल")}:</b> {T("Self-harm thoughts reported. Please call 108 or go to the nearest hospital immediately. Do not stay alone.", "खुद को नुकसान पहुँचाने के विचार बताए गए हैं। कृपया तुरंत 108 पर कॉल करें या नजदीकी अस्पताल जाएँ। अकेले न रहें।")}</div>',
                        unsafe_allow_html=True
                    )
                elif quick_total >= 6:
                    st.markdown(
                        f'<div class="alert-warning">{T("Please discuss this with your doctor/ASHA/ANM. Early support helps recovery.", "कृपया इस बारे में डॉक्टर/आशा/ANM से बात करें। जल्दी सहायता लेने से सुधार में मदद मिलती है।")}</div>',
                        unsafe_allow_html=True
                    )

        c1, c2 = st.columns(2)
        with c1:
            bleeding = st.selectbox(T("Bleeding", "रक्तस्राव"), ["Normal", "Heavy", "Irregular"])
            feeding = st.selectbox(T("Breastfeeding", "स्तनपान"), ["Going well", "Difficulty latching", "Low milk", "Not started"])
            wound = st.selectbox(T("Wound Healing", "घाव"), ["Healing well", "Some pain", "Infection signs", "N/A"])
        with c2:
            fever = st.selectbox(T("Fever", "बुखार"), ["No", "Yes"])
            bwt = st.selectbox(T("Baby Weight Gain", "शिशु वज़न"), ["Normal", "Slow", "Not sure"])
            vacc = st.multiselect(T("Vaccines Given", "दिए गए टीके"), ["BCG", "OPV-0", "Hepatitis B"])
        if st.button(T("📋 Review Status", "📋 स्थिति समीक्षा")):
            alerts = []
            if bleeding != "Normal": alerts.append(("alert-warning", T("Abnormal bleeding", "असामान्य रक्तस्राव")))
            if feeding != "Going well": alerts.append(("alert-warning", T("Breastfeeding support needed", "स्तनपान सहायता चाहिए")))
            if wound == "Infection signs": alerts.append(("alert-danger", T("Wound infection — see doctor!", "घाव संक्रमण — डॉक्टर को दिखाएँ!")))
            if fever == "Yes": alerts.append(("alert-danger", T("Postnatal fever — evaluate!", "प्रसवोत्तर बुखार — जाँच कराएँ!")))
            if bwt == "Slow": alerts.append(("alert-warning", T("Slow baby weight gain", "शिशु वज़न धीमा")))
            if not vacc: alerts.append(("alert-warning", T("No vaccines marked", "कोई टीका नहीं लगा")))
            if alerts:
                for c, m in alerts:
                    st.markdown(f'<div class="{c}">{m}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="alert-success">{T("Status stable for mother & baby.", "माँ और शिशु की स्थिति स्थिर।")}</div>', unsafe_allow_html=True)


elif page_key == "ppd":
    st.markdown(f'<div class="section-header">{T("Postpartum Depression Screening (EPDS)", "प्रसवोत्तर अवसाद जाँच (EPDS)")}</div>', unsafe_allow_html=True)
    if not need_user():
        user_card()
        qs = [T("I have been able to laugh", "मैं हँस पाई हूँ"), T("I have looked forward to things", "मैंने चीज़ों का आनंद लिया"), T("I blamed myself unnecessarily", "अनावश्यक दोषी महसूस किया"), T("I felt anxious for no reason", "बिना कारण चिंतित"), T("I felt scared for no reason", "बिना कारण डर लगा"), T("Things getting too much", "चीज़ें भारी लगीं"), T("So unhappy, difficulty sleeping", "इतनी दुखी कि नींद न आई"), T("I have felt sad", "दुखी महसूस किया"), T("I have been crying", "रोई"), T("Thought of harming myself", "खुद को नुकसान का विचार")]
        opts = [f"(0) {T('Not at all', 'बिल्कुल नहीं')}", f"(1) {T('Sometimes', 'कभी-कभी')}", f"(2) {T('Often', 'अक्सर')}", f"(3) {T('Most of the time', 'अधिकांश समय')}"]
        responses = []
        for i, q in enumerate(qs, 1):
            responses.append(st.radio(f"{i}. {q}", opts, key=f"ppd_{i}_{st.session_state['user_id']}"))
        if st.button(T("Calculate Score", "स्कोर गणना")):
            scores = [int(r[1]) for r in responses]
            total = sum(scores)
            if total <= 8:
                lv, bx = T("LOW RISK", "कम जोखिम"), "alert-success"
            elif total <= 12:
                lv, bx = T("MODERATE RISK", "मध्यम जोखिम"), "alert-warning"
            else:
                lv, bx = T("HIGH RISK", "उच्च जोखिम"), "alert-danger"
            save_ppd_log(st.session_state["user_id"], total, lv)
            st.markdown(f'<div class="{bx}"><b>EPDS: {total}/30 — {lv}</b></div>', unsafe_allow_html=True)
            if total > 12:
                st.markdown(f'<div class="alert-danger">{T("⚠️ Seek professional help. Call 104.", "⚠️ पेशेवर मदद लें। 104 पर कॉल करें।")}</div>', unsafe_allow_html=True)


elif page_key == "kick":
    st.markdown(f'<div class="section-header">👣 {T("Baby Kick Counter", "शिशु किक काउंटर")}</div>', unsafe_allow_html=True)
    if not need_user():
        user_card()
        st.markdown(f'<div class="alert-info">{T("From week 28: Count 10 movements in 2 hours. Less = see doctor.", "सप्ताह 28 से: 2 घंटे में 10 हलचल गिनें। कम हो तो डॉक्टर से मिलें।")}</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            st.markdown(f'<div class="metric-card"><h3>👶 {st.session_state["kick_count"]}</h3><div>{T("Kicks This Session", "इस सत्र में किक")}</div></div>', unsafe_allow_html=True)
        with c2:
            if st.button("👣 Kick!", use_container_width=True):
                st.session_state["kick_count"] += 1
                if not st.session_state["kick_start"]:
                    st.session_state["kick_start"] = datetime.now()
                st.rerun()
        with c3:
            if st.button("🔄 Reset", use_container_width=True):
                st.session_state["kick_count"] = 0
                st.session_state["kick_start"] = None
                st.rerun()
        if st.session_state["kick_start"]:
            mins = int((datetime.now() - st.session_state["kick_start"]).total_seconds() // 60)
            st.markdown(f'<div class="gov-card"><b>⏱ {T("Duration", "अवधि")}:</b> {mins} {T("minutes", "मिनट")}</div>', unsafe_allow_html=True)
        if st.session_state["kick_count"] > 0 and st.button(T("💾 Save Session", "💾 सत्र सहेजें")):
            mins = int((datetime.now() - st.session_state["kick_start"]).total_seconds() // 60) if st.session_state["kick_start"] else 0
            save_kick_log(st.session_state["user_id"], st.session_state["kick_count"], max(1, mins))
            kc = st.session_state["kick_count"]
            if kc >= 10:
                st.markdown(f'<div class="alert-success">{T("Great! 10+ movements 🎉", "बहुत अच्छा! 10+ हलचल 🎉")}</div>', unsafe_allow_html=True)
            elif kc >= 5:
                st.markdown(f'<div class="alert-warning">{T("Some movement. Keep monitoring.", "कुछ हलचल। निगरानी जारी रखें।")}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="alert-danger">{T("Low movement. Contact doctor if persists.", "कम हलचल। जारी रहे तो डॉक्टर से संपर्क करें।")}</div>', unsafe_allow_html=True)
            st.session_state["kick_count"] = 0
            st.session_state["kick_start"] = None
        conn = get_conn()
        kdf = pd.read_sql_query("SELECT log_date,log_time,kick_count,duration_minutes FROM kick_logs WHERE user_id=? ORDER BY id DESC LIMIT 10", conn, params=(st.session_state["user_id"],))
        conn.close()
        if not kdf.empty:
            st.markdown(f"##### {T('Recent Sessions', 'हाल के सत्र')}")
            st.dataframe(kdf, use_container_width=True, hide_index=True)



elif page_key == "chatbot":
    st.markdown(f'<div class="section-header">💬 {T("AI Maternal Health Chatbot", "AI मातृ स्वास्थ्य चैटबॉट")}</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="alert-info">
        <b>{T("Important", "महत्वपूर्ण")}:</b>
        {T(
            "This chatbot gives general maternal health guidance only. It is not a replacement for a doctor. For emergency symptoms, call 108 immediately.",
            "यह चैटबॉट केवल सामान्य मातृ स्वास्थ्य मार्गदर्शन देता है। यह डॉक्टर का विकल्प नहीं है। आपातकालीन लक्षणों में तुरंत 108 पर कॉल करें।"
        )}
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.get("user_data"):
        user_card()

    if not st.session_state.get("chat_history"):
        st.session_state["chat_history"] = [
            {"role": "assistant", "content": T(
                "Namaste! I am your MaternalCare assistant. Ask me about diet, medicines, checkups, baby kicks, warning signs, breastfeeding, PPD, or government schemes.",
                "नमस्ते! मैं आपकी MaternalCare सहायक हूँ। आहार, दवाई, जाँच, शिशु किक, खतरे के संकेत, स्तनपान, PPD या सरकारी योजनाओं के बारे में पूछें।"
            )}
        ]

    st.markdown(f'<div class="section-header-orange">{T("Quick Questions", "त्वरित प्रश्न")}</div>', unsafe_allow_html=True)
    quick_prompts = [
        T("What should I eat during pregnancy?", "गर्भावस्था में क्या खाना चाहिए?"),
        T("What are danger signs?", "खतरे के संकेत क्या हैं?"),
        T("When should I count baby kicks?", "शिशु की किक कब गिननी चाहिए?"),
        T("Tell me about postpartum depression", "प्रसवोत्तर अवसाद के बारे में बताएं"),
    ]
    qcols = st.columns(4)
    chosen_prompt = None
    for i, qp in enumerate(quick_prompts):
        with qcols[i]:
            if st.button(qp, key=f"quick_chat_{i}", use_container_width=True):
                chosen_prompt = qp

    st.markdown(f'<div class="section-header">{T("Conversation", "बातचीत")}</div>', unsafe_allow_html=True)
    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    typed_prompt = st.chat_input(T("Type your question here...", "अपना सवाल यहाँ लिखें..."))
    prompt = chosen_prompt or typed_prompt

    if prompt:
        st.session_state["chat_history"].append({"role": "user", "content": prompt})
        reply = maternal_chatbot_reply(prompt)
        st.session_state["chat_history"].append({"role": "assistant", "content": reply})
        st.rerun()

    c1, c2 = st.columns([1, 5])
    with c1:
        if st.button(T("Clear Chat", "चैट साफ करें"), use_container_width=True):
            st.session_state["chat_history"] = []
            st.rerun()


elif page_key == "emergency":
    st.markdown(f'<div class="section-header">🆘 {T("Emergency & Warning Signs", "आपातकालीन और चेतावनी संकेत")}</div>', unsafe_allow_html=True)
    st.markdown('<div class="alert-danger"><b>🚨 CALL 108 IMMEDIATELY</b></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""<div class="gov-card"><h4>🔴 {T("During Pregnancy", "गर्भावस्था में")}</h4><ul>
        <li>{T("Heavy vaginal bleeding", "भारी योनि रक्तस्राव")}</li><li>{T("Severe headache + blurred vision", "तेज सिरदर्द + धुंधली दृष्टि")}</li><li>{T("High fever >101°F", "तेज बुखार >101°F")}</li><li>{T("Severe abdominal pain", "गंभीर पेट दर्द")}</li><li>{T("Sudden swelling face/hands", "अचानक चेहरे/हाथों में सूजन")}</li><li>{T("Convulsions", "दौरे")}</li><li>{T("Water breaking <37 weeks", "37 सप्ताह से पहले पानी टूटना")}</li><li>{T("Baby not moving >12 hours", "12 घंटे से अधिक शिशु न हिले")}</li>
        </ul></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="gov-card"><h4>🔴 {T("After Delivery", "प्रसव बाद")}</h4><ul>
        <li>{T("Heavy bleeding", "भारी रक्तस्राव")}</li><li>{T("Fever >100.4°F", "बुखार >100.4°F")}</li><li>{T("Foul-smelling discharge", "दुर्गंधयुक्त स्राव")}</li><li>{T("Severe headache/vision changes", "तेज सिरदर्द/दृष्टि बदलाव")}</li><li>{T("Leg pain/swelling/redness", "पैर दर्द/सूजन/लालिमा")}</li><li>{T("Difficulty breathing", "साँस लेने में कठिनाई")}</li><li>{T("Thoughts of self-harm", "खुद को नुकसान का विचार")}</li>
        </ul></div>""", unsafe_allow_html=True)
    st.markdown(f'<div class="gov-card"><h4>📞 {T("Helplines", "हेल्पलाइन")}</h4><p>🚑 {T("Emergency", "आपातकालीन")}: <b>108</b> | 📞 {T("Health", "स्वास्थ्य")}: <b>104</b> | 👩 {T("Women", "महिला")}: <b>181</b> | 🧠 {T("Mental Health", "मानसिक स्वास्थ्य")}: <b>9152987821</b></p></div>', unsafe_allow_html=True)


elif page_key == "dashboard":
    st.markdown(f'<div class="section-header">{T("Dashboard & Analytics", "डैशबोर्ड और एनालिटिक्स")}</div>', unsafe_allow_html=True)
    udf = get_users_df()
    tu, tl, hr = get_counts()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card"><h3>{tu}</h3><div>{T("Beneficiaries", "लाभार्थी")}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><h3>{tl}</h3><div>{T("Health Logs", "स्वास्थ्य लॉग")}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><h3>{hr}</h3><div>{T("High Risk", "उच्च जोखिम")}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-card"><h3>{udf["state"].nunique() if not udf.empty else 0}</h3><div>{T("States", "राज्य")}</div></div>', unsafe_allow_html=True)
    if not udf.empty:
        t1, t2, t3 = st.tabs([T("📋 List", "📋 सूची"), T("📈 Charts", "📈 चार्ट"), T("📤 Export", "📤 निर्यात")])
        with t1:
            st.dataframe(udf, use_container_width=True, hide_index=True)
        with t2:
            cc1, cc2 = st.columns(2)
            with cc1:
                sc = udf["state"].value_counts().reset_index()
                sc.columns = ["State", "Count"]
                st.plotly_chart(px.bar(sc, x="State", y="Count", title=T("By State", "राज्य अनुसार"), color="Count"), use_container_width=True)
            with cc2:
                tc = udf["trimester"].value_counts().reset_index()
                tc.columns = ["Trimester", "Count"]
                st.plotly_chart(px.pie(tc, names="Trimester", values="Count", title=T("Stage Distribution", "स्थिति वितरण")), use_container_width=True)
            cc3, cc4 = st.columns(2)
            with cc3:
                st.plotly_chart(px.histogram(udf, x="age", nbins=15, title=T("Age Distribution", "उम्र वितरण")), use_container_width=True)
            with cc4:
                st.plotly_chart(px.histogram(udf, x="bmi", nbins=15, title=T("BMI Distribution", "BMI वितरण")), use_container_width=True)
            conn = get_conn()
            rdf = pd.read_sql_query("SELECT risk_level,COUNT(*) as cnt FROM risk_logs GROUP BY risk_level", conn)
            conn.close()
            if not rdf.empty:
                st.plotly_chart(px.pie(rdf, names="risk_level", values="cnt", title=T("Risk Distribution", "जोखिम वितरण")), use_container_width=True)
        with t3:
            csv = udf.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download CSV", csv, "beneficiaries.csv", "text/csv")
    else:
        st.info(T("No data yet. Register beneficiaries.", "अभी डेटा नहीं। लाभार्थी पंजीकरण करें।"))


elif page_key == "about":
    st.markdown(f"""<div class="hero-banner"><div class="hero-title">{T("MaternalCare India", "मातृ-देखभाल भारत")}</div>
    <div class="hero-subtitle">{T("AI-powered platform to reduce maternal mortality in rural India.", "ग्रामीण भारत में मातृ मृत्यु दर कम करने के लिए AI मंच।")}</div></div>""", unsafe_allow_html=True)
    st.markdown(f"""<div class="gov-card"><h4>🛠️ {T("Tech Stack", "तकनीक")}</h4><ul>
    <li><b>Frontend:</b> Streamlit + Custom CSS</li><li><b>Database:</b> SQLite</li>
    <li><b>ML:</b> scikit-learn RandomForest</li><li><b>Charts:</b> Plotly</li>
    <li><b>Video:</b> YouTube iframe</li><li><b>Email:</b> SMTP via secrets/env variables</li></ul></div>""", unsafe_allow_html=True)
    st.markdown(f'<div class="section-header-orange">👥 {T("Team", "टीम")}</div>', unsafe_allow_html=True)
    team = [("👩‍💻", "Member 1", T("Team Lead & ML", "टीम लीड और ML"), T("Risk model, architecture", "जोखिम मॉडल, वास्तुकला")), ("👨‍💻", "Member 2", T("Full-Stack Dev", "फुल-स्टैक डेव"), T("Registration, trackers, DB", "पंजीकरण, ट्रैकर, DB")), ("👩‍🎨", "Member 3", T("UI/UX & Wellness", "UI/UX और कल्याण"), T("Baby dev, yoga, UI design", "शिशु विकास, योग, UI डिज़ाइन")), ("👨‍⚕️", "Member 4", T("Health & Policy", "स्वास्थ्य और नीति"), T("Nutrition, govt schemes, PPD", "पोषण, सरकारी योजनाएँ, PPD"))]
    cols = st.columns(4)
    for col, (e, n, r, w) in zip(cols, team):
        with col:
            st.markdown(f'<div class="team-card"><div class="emoji">{e}</div><h4>{n}</h4><div class="role">{r}</div><p>{w}</p></div>', unsafe_allow_html=True)





# ═══════════════════════════════════════
# ATTRACTIVE FOOTER + CLEAN PAGE END
# ═══════════════════════════════════════
st.markdown("""
<style>
/* Keep page end clean but not forcefully cut */
.block-container,
.main .block-container {
    padding-bottom: .85rem !important;
}

footer {display: none !important;}

/* Premium government footer */
.gov-footer.enhanced-footer {
    position: relative;
    overflow: hidden;
    width: 100% !important;
    margin: 34px 0 10px 0 !important;
    padding: 0 !important;
    border-radius: 30px !important;
    background:
        radial-gradient(circle at 8% 20%, rgba(255,153,51,.22), transparent 24%),
        radial-gradient(circle at 92% 16%, rgba(19,136,8,.18), transparent 24%),
        linear-gradient(135deg, #071a34 0%, #0b2a52 48%, #08213f 100%) !important;
    border: 1px solid rgba(255,255,255,.14) !important;
    box-shadow: 0 18px 48px rgba(11,37,69,.22) !important;
}

.gov-footer.enhanced-footer::before {
    content: '';
    position: absolute;
    width: 240px;
    height: 240px;
    right: -95px;
    top: -110px;
    background: radial-gradient(circle, rgba(255,255,255,.12), transparent 67%);
    border-radius: 50%;
}

.gov-footer.enhanced-footer::after {
    content: '';
    position: absolute;
    width: 180px;
    height: 180px;
    left: -80px;
    bottom: -95px;
    background: radial-gradient(circle, rgba(255,153,51,.18), transparent 65%);
    border-radius: 50%;
}

.footer-tricolor {
    display: flex;
    height: 7px;
    width: 100%;
}
.footer-tricolor .orange {background: #FF9933; flex: 1;}
.footer-tricolor .white {background: #ffffff; flex: 1;}
.footer-tricolor .green {background: #138808; flex: 1;}

.footer-grid {
    position: relative;
    z-index: 2;
    display: grid;
    grid-template-columns: 1.45fr 1fr 1.15fr;
    gap: 22px;
    align-items: center;
    padding: 24px 30px 18px 30px;
}

.footer-brand {
    display: flex;
    align-items: center;
    gap: 14px;
    text-align: left;
}

.footer-logo {
    width: 54px;
    height: 54px;
    border-radius: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    background: rgba(255,255,255,.12);
    border: 1px solid rgba(255,255,255,.18);
    box-shadow: inset 0 1px 0 rgba(255,255,255,.15);
}

.footer-brand h3,
.footer-info h4,
.footer-helpline h4 {
    color: #ffffff !important;
    margin: 0 0 5px 0 !important;
    font-weight: 800 !important;
    letter-spacing: -.2px;
}

.footer-brand p,
.footer-info p,
.footer-bottom,
.footer-subtext {
    color: #cbd5e1 !important;
    margin: 0 !important;
    font-size: 13px !important;
    line-height: 1.55 !important;
}

.footer-info {
    text-align: center;
    padding: 0 18px;
    border-left: 1px solid rgba(255,255,255,.12);
    border-right: 1px solid rgba(255,255,255,.12);
}

.footer-helpline {
    text-align: right;
}

.footer-badges {
    display: flex;
    justify-content: flex-end;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 8px;
}

.footer-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 7px 11px;
    border-radius: 999px;
    background: rgba(255,255,255,.10);
    color: #ffffff !important;
    border: 1px solid rgba(255,255,255,.16);
    font-size: 12px;
    font-weight: 800;
    white-space: nowrap;
}

.footer-bottom {
    position: relative;
    z-index: 2;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    padding: 12px 20px 16px 20px;
    border-top: 1px solid rgba(255,255,255,.10);
    background: rgba(0,0,0,.10);
    text-align: center;
}

.footer-dot {
    width: 5px;
    height: 5px;
    border-radius: 999px;
    background: #FF9933;
    display: inline-block;
}

@media (max-width: 900px) {
    .footer-grid {
        grid-template-columns: 1fr;
        text-align: center;
        padding: 22px 18px 14px 18px;
    }
    .footer-brand {
        justify-content: center;
        text-align: center;
    }
    .footer-info {
        border-left: none;
        border-right: none;
        border-top: 1px solid rgba(255,255,255,.12);
        border-bottom: 1px solid rgba(255,255,255,.12);
        padding: 16px 0;
    }
    .footer-helpline {text-align: center;}
    .footer-badges {justify-content: center;}
    .footer-bottom {flex-direction: column; gap: 4px;}
    .footer-dot {display: none;}
}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════
st.markdown(f"""<div style="margin:32px 0 14px 0;border-radius:28px;overflow:hidden;background:linear-gradient(135deg,#071a34 0%,#0b2a52 52%,#08213f 100%);box-shadow:0 18px 48px rgba(11,37,69,.24);border:1px solid rgba(255,255,255,.16);">
<div style="display:flex;height:7px;width:100%;"><div style="flex:1;background:#FF9933;"></div><div style="flex:1;background:#ffffff;"></div><div style="flex:1;background:#138808;"></div></div>
<div style="padding:26px 30px 22px 30px;display:flex;align-items:center;justify-content:space-between;gap:24px;flex-wrap:wrap;">
<div style="display:flex;align-items:center;gap:14px;min-width:270px;flex:1;"><div style="width:56px;height:56px;border-radius:18px;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.20);font-size:30px;box-shadow:inset 0 1px 0 rgba(255,255,255,.16);">🏥</div><div><div style="color:#ffffff;font-size:19px;font-weight:800;line-height:1.25;">{T("MaternalCare India", "मातृ-देखभाल भारत")}</div><div style="color:#cbd5e1;font-size:13px;line-height:1.55;margin-top:4px;">{T("AI-Powered Maternal Health & Wellness Platform", "AI-संचालित मातृ स्वास्थ्य एवं कल्याण मंच")}</div></div></div>
<div style="min-width:260px;flex:1;text-align:center;padding:10px 18px;border-left:1px solid rgba(255,255,255,.14);border-right:1px solid rgba(255,255,255,.14);"><div style="color:#ffffff;font-size:15px;font-weight:800;line-height:1.35;">🇮🇳 {T("Government Health Initiative", "सरकारी स्वास्थ्य पहल")}</div><div style="color:#cbd5e1;font-size:13px;line-height:1.6;margin-top:5px;">{T("Ministry of Health & Family Welfare", "स्वास्थ्य एवं परिवार कल्याण मंत्रालय")}<br>{T("Government of India", "भारत सरकार")}</div></div>
<div style="min-width:240px;flex:1;text-align:right;"><div style="color:#ffffff;font-size:15px;font-weight:800;margin-bottom:10px;">{T("Quick Helplines", "त्वरित हेल्पलाइन")}</div><div style="display:flex;justify-content:flex-end;gap:8px;flex-wrap:wrap;"><span style="padding:8px 12px;border-radius:999px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.18);color:#ffffff;font-size:13px;font-weight:800;">🚑 108</span><span style="padding:8px 12px;border-radius:999px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.18);color:#ffffff;font-size:13px;font-weight:800;">📞 104</span><span style="padding:8px 12px;border-radius:999px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.18);color:#ffffff;font-size:13px;font-weight:800;">👩 181</span></div></div>
</div>
<div style="border-top:1px solid rgba(255,255,255,.12);background:rgba(0,0,0,.14);padding:13px 20px;text-align:center;color:#cbd5e1;font-size:13px;line-height:1.6;"><b style="color:#ffffff;">{T("MaternalCare India", "मातृ-देखभाल भारत")}</b><span style="color:#FF9933;padding:0 8px;">•</span>{T("Service • Safety • Support", "सेवा • सुरक्षा • सहयोग")}<span style="color:#FF9933;padding:0 8px;">•</span>© 2026</div>
</div>""", unsafe_allow_html=True)
