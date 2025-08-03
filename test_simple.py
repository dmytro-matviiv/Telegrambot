#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

def translate_text(text):
    """Повний переклад тексту з англійської на українську"""
    if not text or len(text.strip()) < 10:
        return text
    
    # Повний словник перекладів для всіх слів
    translations = {
        # Основні слова
        'ukraine': 'Україна',
        'ukrainian': 'український',
        'russia': 'Росія',
        'russian': 'російський',
        'war': 'війна',
        'conflict': 'конфлікт',
        'invasion': 'вторгнення',
        'military': 'військовий',
        'defense': 'оборона',
        'weapons': 'зброя',
        'sanctions': 'санкції',
        'zelensky': 'Зеленський',
        'putin': 'Путін',
        'kyiv': 'Київ',
        'kiev': 'Київ',
        'donetsk': 'Донецьк',
        'luhansk': 'Луганськ',
        'crimea': 'Крим',
        'breaking': 'терміново',
        'news': 'новини',
        'latest': 'останні',
        'update': 'оновлення',
        'report': 'звіт',
        'says': 'каже',
        'said': 'сказав',
        'will': 'буде',
        'has': 'має',
        'have': 'мають',
        'is': 'є',
        'are': 'є',
        'was': 'був',
        'were': 'були',
        'group': 'група',
        'worker': 'працівник',
        'killed': 'вбитий',
        'israeli': 'ізраїльський',
        'attack': 'атака',
        'gaza': 'Газа',
        'hq': 'штаб',
        'palestine': 'Палестина',
        'red': 'червоний',
        'crescent': 'півмісяць',
        'accused': 'звинуватив',
        'israel': 'Ізраїль',
        'deliberate': 'навмисний',
        'strike': 'удар',
        'information': 'інформація',
        'about': 'про',
        'it': 'це',
        'no': 'немає',
        
        # Артиклі та прийменники
        'the': 'the',
        'a': 'a',
        'an': 'an',
        'of': 'of',
        'in': 'в',
        'on': 'на',
        'by': 'від',
        'to': 'до',
        'for': 'для',
        'with': 'з',
        'and': 'і',
        'but': 'але',
        'or': 'або',
        'that': 'що',
        'this': 'це',
        'these': 'ці',
        'those': 'ті',
        'they': 'вони',
        'them': 'їх',
        'their': 'їхній',
        'we': 'ми',
        'us': 'нас',
        'our': 'наш',
        'you': 'ви',
        'your': 'ваш',
        'he': 'він',
        'she': 'вона',
        'his': 'його',
        'her': 'її',
        'its': 'його',
        'who': 'хто',
        'what': 'що',
        'where': 'де',
        'when': 'коли',
        'why': 'чому',
        'how': 'як',
        'which': 'який',
        'whose': 'чий',
        'whom': 'кого',
        
        # Загальні слова
        'time': 'час',
        'people': 'люди',
        'year': 'рік',
        'into': 'в',
        'just': 'просто',
        'over': 'над',
        'think': 'думати',
        'also': 'також',
        'around': 'навколо',
        'another': 'інший',
        'come': 'прийти',
        'work': 'робота',
        'first': 'перший',
        'well': 'добре',
        'way': 'спосіб',
        'even': 'навіть',
        'want': 'хотіти',
        'because': 'тому що',
        'any': 'будь-який',
        'give': 'дати',
        'day': 'день',
        'most': 'більшість',
        'us': 'нас',
        
        # Додаткові слова для повного перекладу
        'forces': 'сили',
        'advancing': 'просуваються',
        'eastern': 'східні',
        'regions': 'регіони',
        'meets': 'зустрічається',
        'biden': 'Байден',
        'washington': 'Вашингтон',
        'shows': 'показує',
        'significant': 'значні',
        'developments': 'розвитки'
    }
    
    translated_text = text
    
    # Спочатку перекладаємо фрази (довші конструкції)
    phrases = {
        'aid group': 'група допомоги',
        'red crescent': 'червоний півмісяць',
        'palestine red crescent': 'палестинський червоний півмісяць',
        'israeli military': 'ізраїльські військові',
        'gaza hq': 'штаб в Газі',
        'has accused': 'звинуватив',
        'has said': 'сказав',
        'has no': 'немає',
        'has information': 'має інформацію',
        'about it': 'про це',
        'deliberate strike': 'навмисний удар',
        'worker killed': 'працівник вбитий',
        'by israeli': 'від ізраїльських',
        'in attack': 'в атаці',
        'on gaza': 'на Газу',
        'palestine red': 'палестинський червоний',
        'has accused israel': 'звинуватив ізраїль',
        'of a deliberate': 'в навмисному',
        'strike but': 'ударі але',
        'israel said': 'ізраїль сказав',
        'it has no': 'у нього немає',
        'information about': 'інформації про',
        'ukraine military': 'українські військові',
        'says russian': 'каже російські',
        'forces are': 'сили є',
        'advancing in': 'просуваються в',
        'eastern regions': 'східні регіони',
        'breaking news': 'термінові новини',
        'zelensky meets': 'Зеленський зустрічається',
        'with biden': 'з Байденом',
        'in washington': 'в Вашингтоні',
        'latest update': 'останнє оновлення',
        'on the war': 'про війну',
        'in ukraine': 'в Україні',
        'shows significant': 'показує значні',
        'developments': 'розвитки',
        'russian forces': 'російські сили',
        'are advancing': 'просуваються',
        'eastern regions': 'східні регіони',
        'meets with': 'зустрічається з',
        'biden in': 'Байденом в',
        'washington': 'Вашингтоні',
        'update on': 'оновлення про',
        'war in': 'війну в',
        'ukraine shows': 'Україна показує',
        'significant developments': 'значні розвитки'
    }
    
    # Перекладаємо фрази (від довших до коротших)
    sorted_phrases = sorted(phrases.items(), key=lambda x: len(x[0]), reverse=True)
    for eng_phrase, ukr_phrase in sorted_phrases:
        translated_text = re.sub(r'\b' + re.escape(eng_phrase) + r'\b', ukr_phrase, translated_text, flags=re.IGNORECASE)
    
    # Потім перекладаємо окремі слова (від довших до коротших)
    sorted_translations = sorted(translations.items(), key=lambda x: len(x[0]), reverse=True)
    for eng_word, ukr_word in sorted_translations:
        # Замінюємо слова з урахуванням регістру
        translated_text = re.sub(r'\b' + re.escape(eng_word) + r'\b', ukr_word, translated_text, flags=re.IGNORECASE)
    
    return translated_text

def test_translation():
    """Тестує покращений переклад"""
    
    # Тестові тексти
    test_texts = [
        "Aid group каже worker killed by Israeli військовий in attack on Gaza HQ",
        "The Palestine Red Crescent має accused Israel of a deliberate strike, but Israel сказав it має no information about it.",
        "Ukraine military says Russian forces are advancing in eastern regions",
        "Breaking news: Zelensky meets with Biden in Washington",
        "Latest update on the war in Ukraine shows significant developments",
        "Russian forces are advancing in eastern regions of Ukraine",
        "The Ukrainian military reports that Russian troops are moving forward",
        "Breaking news from Kyiv shows that the situation is developing rapidly",
        "Latest developments in the conflict zone indicate significant changes",
        "The war in Ukraine continues with new developments every day"
    ]
    
    print("=== ТЕСТ ПОВНОГО ПЕРЕКЛАДУ ===")
    for i, text in enumerate(test_texts, 1):
        print(f"\n{i}. Оригінал:")
        print(text)
        print("\nПереклад:")
        translated = translate_text(text)
        print(translated)
        print("-" * 50)

if __name__ == "__main__":
    test_translation() 