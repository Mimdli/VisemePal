"""讯飞英文音素（ARPAbet 风格）到 IPA 的映射。"""

from __future__ import annotations

ARPABET_TO_IPA: dict[str, str] = {
    "AA": "ɑː",
    "AE": "æ",
    "AH": "ʌ",
    "AO": "ɔː",
    "AW": "aʊ",
    "AY": "aɪ",
    "B": "b",
    "CH": "tʃ",
    "D": "d",
    "DH": "ð",
    "EH": "e",
    "ER": "ɜː",
    "EY": "eɪ",
    "F": "f",
    "G": "g",
    "HH": "h",
    "IH": "ɪ",
    "IY": "iː",
    "JH": "dʒ",
    "K": "k",
    "L": "l",
    "M": "m",
    "N": "n",
    "NG": "ŋ",
    "OW": "oʊ",
    "OY": "ɔɪ",
    "P": "p",
    "R": "r",
    "S": "s",
    "SH": "ʃ",
    "T": "t",
    "TH": "θ",
    "UH": "ʊ",
    "UW": "uː",
    "V": "v",
    "W": "w",
    "Y": "j",
    "Z": "z",
    "ZH": "ʒ",
}

IPA_TO_ARPABET = {ipa: code for code, ipa in ARPABET_TO_IPA.items()}


def to_ipa(symbol: str) -> str:
    token = symbol.strip().strip("/")
    if not token:
        return token
    upper = token.upper().rstrip("0123456789")
    if upper in ARPABET_TO_IPA:
        return ARPABET_TO_IPA[upper]
    if token in ARPABET_TO_IPA.values():
        return token
    return token
