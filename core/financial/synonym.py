synonym = {
    "자기주식": ["자기주식", "자사주"],
    "매출액": ["매출액", "보험료수익", "순영업수익", "보험료수익"],
    "지배주주지분": ["지배주주지분", "지배기업주주지분"]
}


def is_synonym(word, compare):

    return word in synonym.get(compare, []) \
           or compare in synonym.get(word, []) \
           or any(word in words and compare in words for words in synonym.values())


def find_synonyms(word):
    words = synonym.get(word, [])
    if (len(words)) > 0:
        return words

    for key, word_list in synonym.items():
        if word in word_list:
            return synonym.get(key)

    return None


def find_unity_synonym(word):
    for key, word_list in synonym.items():
        if word in word_list:
            return key

