from re import Pattern, compile
from typing import AnyStr
from xml.dom.minidom import Element

from ttml.ttml_syl import TTMLSyl


class TTMLLine:
    __before: Pattern[AnyStr] = compile(r'^\(+')
    __after: Pattern[AnyStr] = compile(r'\)+$')

    def __init__(self, element: Element, is_bg: bool = False):
        self.__orig_line: list[TTMLSyl | str] = []
        self.__bg_line: TTMLLine | None = None

        self.__ts_line: str | None = None
        self.__roma_line: str | None = None

        self.__is_bg: bool = is_bg

        # 获取传入元素的 agent 属性
        agent: str = element.getAttribute("ttm:agent")
        self.__is_duet: bool = bool(agent and agent != 'v1')

        # 获取 <p> 元素的所有子节点，包括文本节点
        child_elements: list[Element] = element.childNodes  # iter() 会返回所有子元素和文本节点

        # 遍历所有子元素
        for child in child_elements:
            if child.nodeType == 3 and child.nodeValue:  # 如果是文本节点（例如空格或换行）
                self.__orig_line.append(child.nodeValue)
            else:
                # 获取 <span> 中的属性
                role: str = child.getAttribute("ttm:role")

                # 没有role代表是一个syl
                if role == "":
                    if child.childNodes[0].nodeValue:
                        self.__orig_line.append(TTMLSyl(child))

                elif role == "x-bg":
                    # 和声行
                    self.__bg_line = TTMLLine(child, True)
                elif role == "x-translation":
                    # 翻译行
                    self.__ts_line = f'{child.childNodes[0].data}'
                elif role == "x-roma":
                    # 音译行
                    self.__roma_line = f'{child.childNodes[0].nodeValue.data}'

        self.__begin = self.__orig_line[0].get_begin()

        if is_bg:
            if TTMLLine.__before.search(self.__orig_line[0].text):
                self.__orig_line[0].text = TTMLLine.__before.sub(self.__orig_line[0].text, '')
            if TTMLLine.__after.search(self.__orig_line[-1].text):
                self.__orig_line[-1].text = TTMLLine.__after.sub(self.__orig_line[-1].text, '')

    def have_bg(self) -> bool:
        return self.__bg_line is not None

    def have_ts(self) -> bool:
        return self.__ts_line is not None

    def have_duet(self) -> bool:
        return self.__is_duet

    def __lys_role(self, have_bg: bool, have_duet: bool) -> int:
        return ((int(have_bg) + int(self.__is_bg)) * 3
                + int(have_duet) + int(self.__is_duet))

    def __lys_raw(self, have_bg: bool, have_duet: bool) -> tuple[str, str | None]:
        return (f'[{self.__lys_role(have_bg, have_duet)}]' + ''.join(
            [v if type(v) == str else v.lys_str() for v in self.__orig_line]),
                f'[{self.__begin}]{self.__ts_line}' if self.__ts_line else None)

    def lys_str(self, have_bg: bool, have_duet: bool) -> tuple[tuple[str, str | None], tuple[str, str | None] | None]:
        return self.__lys_raw(have_bg, have_duet), (
            self.__bg_line.__lys_raw(have_bg, have_duet) if self.__bg_line else None)
