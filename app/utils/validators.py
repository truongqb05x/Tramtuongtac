import re
import unicodedata

# Bảng chữ cái tiếng Việt, gồm chữ không dấu và có dấu.
VIETNAMESE_LETTERS = (
    "a-eghikl-vxyA-EGHIKL-VXY"
    "ÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬ"
    "ĐÈÉẺẼẸÊỀẾỂỄỆ"
    "ÌÍỈĨỊ"
    "ÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢ"
    "ÙÚỦŨỤƯỪỨỬỮỰ"
    "ỲÝỶỸỴ"
    "àáảãạăằắẳẵặâầấẩẫậ"
    "đèéẻẽẹêềếểễệ"
    "ìíỉĩị"
    "òóỏõọôồốổỗộơờớởỡợ"
    "ùúủũụưừứửữự"
    "ỳýỷỹỵ"
)

# Chỉ cho phép chữ cái tiếng Việt và dấu cách ASCII.
NAME_PATTERN = re.compile(
    rf"^[{VIETNAMESE_LETTERS}]+(?: [{VIETNAMESE_LETTERS}]+)*$"
)

def is_vietnamese_name(name: str) -> bool:
    """
    Kiểm tra định dạng tên theo bảng chữ cái tiếng Việt.
    """
    if not isinstance(name, str):
        return False

    name = unicodedata.normalize("NFC", name).strip()

    if not name:
        return False

    if "  " in name or any(char.isspace() and char != " " for char in name):
        return False

    if not NAME_PATTERN.fullmatch(name):
        return False

    return True
