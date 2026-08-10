import re
import unicodedata
from typing import Dict, Optional


class StringUtil:
    """Port 1-1 từ StringUtil trong base-backend (src/common/utils/string.util.ts)."""

    @staticmethod
    def capitalize(s: str) -> str:
        if not s:
            return ""
        s = s.strip()
        return s[0].upper() + s[1:].lower() if s else ""

    @staticmethod
    def capitalize_component(s: str) -> str:
        if not s:
            return ""
        return " ".join(StringUtil.capitalize(comp) for comp in s.split(" "))

    @staticmethod
    def get_name_component(name: str) -> Dict[str, Optional[str]]:
        if not name:
            return {"fullname": ""}
        name = name.strip()
        try:
            temp = [StringUtil.capitalize(comp) for comp in name.split(" ") if comp]
            fullname = " ".join(temp)
            firstname = temp[-1] if temp else ""
            lastname = " ".join(temp[:-1]) if len(temp) > 1 else ""
            return {"fullname": fullname, "firstname": firstname, "lastname": lastname}
        except Exception:
            return {"fullname": name}

    @staticmethod
    def remove_accents(s: str) -> str:
        if not s:
            return ""
        s = s.strip()
        # Normalize Unicode NFD
        nfd_format = unicodedata.normalize('NFD', s)
        no_accent = "".join([c for c in nfd_format if unicodedata.category(c) != 'Mn'])
        return no_accent.lower().replace("đ", "d").replace("Đ", "D")

    @staticmethod
    def regex_match_vietnamese(keyword: str) -> str:
        """Regex tiếng Việt không dấu / có dấu phục vụ tìm kiếm mongo."""
        if not keyword:
            return ""
        clean = StringUtil.remove_accents(keyword)
        clean = re.sub(r'[aàáạảãâầấậẩẫăằắặẳẵ]', '[aàáạảãâầấậẩẫăằắặẳẵ]', clean)
        clean = re.sub(r'[eèéẹẻẽêềếệểễ]', '[eèéẹẻẽêềếệểễ]', clean)
        clean = re.sub(r'[iìíịỉĩ]', '[iìíịỉĩ]', clean)
        clean = re.sub(r'[oòóọỏõôồốộổỗơờớợởỡ]', '[oòóọỏõôồốộổỗơờớợởỡ]', clean)
        clean = re.sub(r'[uùúụủũưừứựửữ]', '[uùúụủũưừứựửữ]', clean)
        clean = re.sub(r'[yỳýỵỷỹ]', '[yỳýỵỷỹ]', clean)
        clean = re.sub(r'[dđ]', '[dđ]', clean)
        return clean
