import locale
import re
import unicodedata
from typing import Dict, List, Optional


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

    @staticmethod
    def compare_name(name1: str, name2: str, firstname_first: bool = True) -> int:
        """Port 1-1 từ compareName (string.util.ts:L46-60).
        So sánh 2 tên tiếng Việt, ưu tiên so sánh theo firstname hoặc lastname."""
        c1 = StringUtil.get_name_component(name1)
        c2 = StringUtil.get_name_component(name2)
        try:
            locale.setlocale(locale.LC_COLLATE, "vi_VN.UTF-8")
        except locale.Error:
            pass
        if firstname_first:
            cmp = locale.strcoll(c1.get("firstname", ""), c2.get("firstname", ""))
            if cmp != 0:
                return cmp
            cmp = locale.strcoll(c1.get("lastname", ""), c2.get("lastname", ""))
            return cmp if cmp != 0 else 0
        else:
            cmp = locale.strcoll(c1.get("lastname", ""), c2.get("lastname", ""))
            if cmp != 0:
                return cmp
            cmp = locale.strcoll(c1.get("firstname", ""), c2.get("firstname", ""))
            return cmp if cmp != 0 else 0

    @staticmethod
    def normalize_file_name(filename: str) -> str:
        """Port 1-1 từ normalizeFileName (string.util.ts:L62-69).
        Xóa dấu và ký tự đặc biệt khỏi tên file."""
        result = StringUtil.remove_accents(filename)
        result = re.sub(r'[!@%\^*\(\)\+=<>\?/,;:\'"&#\[\]~\$_`\-\{\}\|\\]', '', result)
        return result.strip()

    @staticmethod
    def split_camel_case(s: str) -> List[str]:
        """Port 1-1 từ splitCamelCase (string.util.ts:L106-108)."""
        if not s:
            return [""]
        return re.split(r'(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])', s)

    @staticmethod
    def camel_case_to_word(s: str) -> str:
        """Port 1-1 từ camelCaseToWord (string.util.ts:L110-112)."""
        parts = StringUtil.split_camel_case(s)
        return " ".join(p for p in parts if p)

