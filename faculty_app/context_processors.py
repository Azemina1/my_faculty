"""
Context processor to inject current language dictionary into all templates.
"""
from .translations import TRANSLATIONS

def language_context(request):
    lang = request.session.get('lang', 'en')
    if lang not in TRANSLATIONS:
        lang = 'en'
    return {
        't': TRANSLATIONS[lang],
        'current_lang': lang
    }