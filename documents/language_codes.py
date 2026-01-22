"""
ISO 639-1 language codes for OCR and document processing.
These codes are commonly used by OCR engines like EasyOCR, Tesseract, etc.
"""

# Common ISO 639-1 language codes
# Format: (code, name)
LANGUAGE_CHOICES = [
    ('en', 'English'),
    ('es', 'Spanish'),
    ('fr', 'French'),
    ('de', 'German'),
    ('it', 'Italian'),
    ('pt', 'Portuguese'),
    ('nl', 'Dutch'),
    ('pl', 'Polish'),
    ('ru', 'Russian'),
    ('ar', 'Arabic'),
    ('zh', 'Chinese'),
    ('ja', 'Japanese'),
    ('ko', 'Korean'),
    ('hi', 'Hindi'),
    ('tr', 'Turkish'),
    ('vi', 'Vietnamese'),
    ('th', 'Thai'),
    ('sv', 'Swedish'),
    ('da', 'Danish'),
    ('no', 'Norwegian'),
    ('fi', 'Finnish'),
    ('cs', 'Czech'),
    ('sk', 'Slovak'),
    ('hu', 'Hungarian'),
    ('ro', 'Romanian'),
    ('bg', 'Bulgarian'),
    ('uk', 'Ukrainian'),
    ('el', 'Greek'),
    ('he', 'Hebrew'),
    ('id', 'Indonesian'),
    ('ms', 'Malay'),
    ('fa', 'Persian'),
    ('bn', 'Bengali'),
    ('ur', 'Urdu'),
    ('te', 'Telugu'),
    ('ta', 'Tamil'),
    ('mr', 'Marathi'),
    ('gu', 'Gujarati'),
    ('kn', 'Kannada'),
    ('ml', 'Malayalam'),
]

# Simple dict for easy lookup
LANGUAGE_CODES = {code: name for code, name in LANGUAGE_CHOICES}

# Tesseract uses 3-letter ISO 639-2 codes
# Common mappings from ISO 639-1 to ISO 639-2
ISO_639_1_TO_639_2 = {
    'en': 'eng',
    'es': 'spa',
    'fr': 'fra',
    'de': 'deu',
    'it': 'ita',
    'pt': 'por',
    'nl': 'nld',
    'pl': 'pol',
    'ru': 'rus',
    'ar': 'ara',
    'zh': 'chi_sim',  # Simplified Chinese
    'ja': 'jpn',
    'ko': 'kor',
    'hi': 'hin',
    'tr': 'tur',
    'vi': 'vie',
    'th': 'tha',
    'sv': 'swe',
    'da': 'dan',
    'no': 'nor',
    'fi': 'fin',
    'cs': 'ces',
    'sk': 'slk',
    'hu': 'hun',
    'ro': 'ron',
    'bg': 'bul',
    'uk': 'ukr',
    'el': 'ell',
    'he': 'heb',
    'id': 'ind',
    'ms': 'msa',
    'fa': 'fas',
    'bn': 'ben',
    'ur': 'urd',
    'te': 'tel',
    'ta': 'tam',
    'mr': 'mar',
    'gu': 'guj',
    'kn': 'kan',
    'ml': 'mal',
}

def get_tesseract_lang(iso_639_1_code: str) -> str:
    """Convert ISO 639-1 code to Tesseract language code"""
    return ISO_639_1_TO_639_2.get(iso_639_1_code, iso_639_1_code)
