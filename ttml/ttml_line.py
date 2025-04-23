from re import Pattern, compile
from typing import AnyStr
from xml.dom.minidom import Element
from ttml.ttml_syl import TTMLSyl
from ttml.ttml_time import TTMLTime


class TTMLLine:
    class ASSTime:
        def __init__(self, ttml_time: TTMLTime):
            count: int = int(ttml_time) // 10
            self.__count: int = count
            self.__centis = count % 100
            count //= 100
            self.__second = count % 60
            count //= 60
            self.__minute = count % 60
            self.__hour = count // 60

        def __str__(self) -> str:
            return f'{self.__hour:02}:{self.__minute:02}:{self.__second:02}.{self.__centis:02}'

        def __sub__(self, other) -> int:
            return self.__count - other.__count

    class LRCTime:
        def __init__(self, ttml_time: TTMLTime):
            count: int = int(ttml_time) // 10
            self.centis = count % 100
            count //= 100
            self.__second = count % 60
            self.__minute = count // 60

        def __str__(self) -> str:
            return f'{self.__minute:02}:{self.__second:02}.{self.centis:02}'

    __before: Pattern[AnyStr] = compile(r'^\(+')
    __after: Pattern[AnyStr] = compile(r'\)+$')

    def __init__(self, element: Element, is_bg: bool = False):
        self.__orig_line: list[TTMLSyl | str] = []
        self.__bg_line: TTMLLine | None = None

        self.__ts_line: list[tuple[str,str]] = []
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
                    if len(child.childNodes) != 0 and child.childNodes[0].nodeValue:
                        self.__orig_line.append(TTMLSyl(child))

                elif role == "x-bg":
                    # 和声行
                    self.__bg_line = TTMLLine(child, True)
                elif role == "x-translation":
                    # 翻译行
                    self.__ts_line.append((f'{child.childNodes[0].data}',child.getAttribute("xml:lang")))
                elif role == "x-roman":
                    # 音译行
                    self.__roma_line = f'{child.childNodes[0].data}'

        self.__begin: TTMLTime = TTMLTime(element.getAttribute("begin"))
        self.__end: TTMLTime = TTMLTime(element.getAttribute("end"))

        if is_bg:
            if TTMLLine.__before.search(self.__orig_line[0].text):
                self.__orig_line[0].text = TTMLLine.__before.sub('', self.__orig_line[0].text)
            if TTMLLine.__after.search(self.__orig_line[-1].text):
                self.__orig_line[-1].text = TTMLLine.__after.sub('', self.__orig_line[-1].text)

    def have_bg(self) -> bool:
        return self.__bg_line is not None

    def have_ts(self) -> bool:
        return len(self.__ts_line) != 0

    def have_duet(self) -> bool:
        return self.__is_duet

    def get_begin(self) -> TTMLTime:
        return self.__orig_line[0].get_begin()

    def get_end(self) -> TTMLTime:
        return self.__orig_line[-1].get_end()

    @staticmethod
    def __lys_pre_process(line: list[TTMLSyl|str]) -> list[TTMLSyl|str]:
        new_line: list[TTMLSyl|str] = []
        for syl in line:
            if type(syl) == str and len(new_line) > 0 and line.index(syl) != 0 and len(syl) < 2:
                last_syl = new_line.pop()
                last_syl.text += syl
                new_line.append(last_syl)
            else:
                new_line.append(syl)

        return new_line

    def __lys_role(self, have_bg: bool, have_duet: bool) -> int:
        return ((int(have_bg) + int(self.__is_bg)) * 3
                + int(have_duet) + int(self.__is_duet))

    def __lys_raw(self, have_bg: bool, have_duet: bool) -> tuple[str, str | None]:
        return (f'[{self.__lys_role(have_bg, have_duet)}]' + ''.join(
            [v if type(v) == str else v.lys_str() for v in TTMLLine.__lys_pre_process(self.__orig_line)]),
                f'[{self.__begin}]{self.__ts_line[0][0]}' if len(self.__ts_line) != 0 else None)

    def lys_str(self, have_bg: bool, have_duet: bool) -> tuple[tuple[str, str | None], tuple[str, str | None] | None]:
        return self.__lys_raw(have_bg, have_duet), (
            self.__bg_line.__lys_raw(have_bg, have_duet) if self.__bg_line else None)

    def spl_str(self) -> str:
        orig: list[str] = []
        pure: list[str] = []
        last: TTMLTime|None = None

        orig.append(f'[{self.__begin}]')
        for syl in self.__orig_line:
            if type(syl) == str:
                orig.append(syl)
                last = None
                continue
            begin, text, end = syl.spl_str()
            if not (last is not None and not begin > last): # 空拍(下一词起始时间大于上一词结束时间)
                orig.append(f'<{begin}>')
            orig.append(text)
            orig.append(f'<{end}>')
            last = end
        orig.append(f'[{self.__end}]')
        pure.append(''.join(orig))
        if len(self.__ts_line) != 0:
            for ts_line in self.__ts_line:
                pure.append(ts_line[0])
        if self.__roma_line:
            pure.append(self.__roma_line)
        if self.__bg_line:
            pure.append(''.join([str(syl) for syl in self.__bg_line.__orig_line]))
            if len(self.__bg_line.__ts_line) != 0:
                for ts_line in self.__bg_line.__ts_line:
                    pure.append(ts_line[0])
            if self.__bg_line.__roma_line:
                pure.append(self.__bg_line.__roma_line)

        return '\n'.join(pure)

    def __ass_text(self) -> str:
        syls: list[tuple[TTMLLine.ASSTime,str]] = []
        last: TTMLTime = self.__begin

        for index, syl in enumerate(self.__orig_line):
            if type(syl) == str: #  文本节点
                # 以上一 syl 的结束作为起点，下一 syl 的起始作为终点
                syls.append((TTMLLine.ASSTime(last), syl))
                last = self.__orig_line[index + 1].get_begin() if index < len(self.__orig_line) - 1 else self.__end
            else:
                sbegin: TTMLTime = syl.get_begin()
                if sbegin > last: # 出现空拍
                    syls.append((TTMLLine.ASSTime(last), ''))
                syls.append((TTMLLine.ASSTime(sbegin), syl.text))
                last = syl.get_end()

        send: TTMLLine.ASSTime = TTMLLine.ASSTime(self.__end)
        text: list[str] = []

        syls.reverse()
        for sstart, stext in syls:
            text.insert(0, rf'{{\k{send - sstart}}}{stext}')
            send = sstart

        return ''.join(text)

    def ass_str(self) -> str:
        line: list[str] = []

        line.append('Dialogue: 0')
        line.append(str(TTMLLine.ASSTime(self.__begin)))
        line.append(str(TTMLLine.ASSTime(self.__end)))
        line.append('orig')
        line.append('x-bg' if self.__is_bg else 'x-duet' if self.__is_duet else '')
        line.append('0')
        line.append('0')
        line.append('0')
        line.append('karaoke')
        line.append(self.__ass_text())

        text: str = ','.join(line)
        if len(self.__ts_line) != 0:
            for ts_line in self.__ts_line:
                text += f'\nDialogue: 0,{str(TTMLLine.ASSTime(self.__begin))},{str(TTMLLine.ASSTime(self.__end))},ts,x-lang:{ts_line[1]},0,0,0,karaoke,{ts_line[0]}'
        if self.__roma_line:
            text += f'\nDialogue: 0,{str(TTMLLine.ASSTime(self.__begin))},{str(TTMLLine.ASSTime(self.__end))},roma,,0,0,0,karaoke,{self.__roma_line}'
        if self.__bg_line:
            text += '\n' + self.__bg_line.ass_str()

        return text

    def lrc_str(self, ext: str|None = None) -> str:
        lbegin: str = f'[{TTMLLine.LRCTime(self.__orig_line[0].get_begin())}]'
        line: str = lbegin

        line += ''.join([v if type(v) == str else v.text for v in self.__orig_line])
        if self.__bg_line:
            line += '\n' + f'({"".join([syl if type(syl) == str else syl.text for syl in self.__bg_line.__orig_line])})'

        if ext == 'ts':
            if len(self.__ts_line) != 0:
                line += f'\n{lbegin}' + self.__ts_line[0][0]
            if self.__bg_line and len(self.__bg_line.__ts_line) != 0:
                line += f'({self.__bg_line.__ts_line[0][0]})'

        if ext == 'roma':
            if self.__roma_line:
                line += f'\n{lbegin}' + self.__roma_line
            if self.__bg_line and self.__bg_line.__roma_line:
                line += f'({self.__bg_line.__roma_line})'

        return line