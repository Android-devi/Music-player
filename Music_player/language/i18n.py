"""国际化翻译模块"""
import locale
import os
from typing import Dict


class Translator:
    def __init__(self):
        self._strings = {}
        self._lang = "zh_cn"
        self._load_lang(self._lang)
    
    def _load_lang(self, lang: str):
        base = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base, f"{lang}.py")
        if os.path.exists(path):
            import importlib.util
            spec = importlib.util.spec_from_file_location(f"lang_{lang}", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            self._strings = getattr(mod, "STRINGS", {})
        else:
            self._strings = {}
    
    def set_lang(self, lang: str):
        self._lang = lang
        self._load_lang(lang)
    
    def get_lang(self) -> str:
        return self._lang
    
    def tr(self, key: str, default: str = None) -> str:
        return self._strings.get(key, default or key)


# 全局单例
_translator = Translator()

def tr(key: str, default: str = None) -> str:
    return _translator.tr(key, default)

def set_lang(lang: str):
    _translator.set_lang(lang)

def get_lang() -> str:
    return _translator.get_lang()
