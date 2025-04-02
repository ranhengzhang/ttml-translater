from xml.dom.minicompat import NodeList
from xml.dom.minidom import Document, Element

from ttml.ttml_line import TTMLLine
from ttml.ttml_error import TTMLError


class TTML:
    def __init__(self, dom: Document):
        self.__have_bg: bool = False
        self.__have_ts: bool = False
        self.__have_duet: bool = False

        self.__lines: list[TTMLLine] = []
        self.__metas: list[tuple[str, str]] = []

        # 获取根元素
        tt: Document = dom.documentElement

        # 获取tt中的body/head元素
        body: Element = tt.getElementsByTagName('body')[0]
        head: Element = tt.getElementsByTagName('head')[0]

        if body and head:
            # 获取body/head中的<div>/<metadata>子元素
            div: Element = body.getElementsByTagName('div')[0]
            metadata: Element = head.getElementsByTagName('metadata')[0]
            meta_elements: NodeList[Element] = metadata.getElementsByTagName('amll:meta')

            # 获取元数据
            for meta in meta_elements:
                key: str = meta.getAttribute("key")
                value: str = meta.getAttribute("value")
                self.__metas.append((key, value))

            # 获取div中的所有<p>子元素
            p_elements: NodeList[Element] = div.getElementsByTagName('p')

            # 遍历每个<p>元素
            for p in p_elements:
                line: TTMLLine = TTMLLine(p)
                self.__lines.append(line)
                self.__have_bg |= line.have_bg()
                self.__have_ts |= line.have_ts()
                self.__have_duet |= line.have_duet()
        else:
            TTMLError.throw_dom_error()

    def get_full_title(self) -> str|None:
        artist: list[str] = []
        title: list[str] = []
        for meta in self.__metas:
            if meta[0] == 'artists':
                artist.append(meta[1])
            if meta[0] == 'musicName':
                title.append(meta[1])

        return (' / '.join(artist) + ' - ' + title[0]) if len(artist) != 0 and len(title) != 0 else None

    def __header(self) -> str:
        header: list[str] = []
        tags: dict[str, str] = {
            "musicName": "ti",
            "album": "al",
            "artists": "ar"
        }

        for key, value in self.__metas:
            if key in tags:
                header.append(f"[{tags[key]}:{value}]")

        return '\n'.join(header)

    def to_lys(self) -> tuple[str, str | None]:
        orig_line: list[str] = []
        ts_line: list[str] | None = [] if self.__have_ts else None

        for line in self.__lines:
            main, duet = line.lys_str(self.__have_bg, self.__have_duet)
            main_orig, main_ts = main
            orig_line.append(main_orig)
            if main_ts:
                ts_line.append(main_ts)
            if duet:
                duet_orig, duet_ts = duet
                orig_line.append(duet_orig)
                if duet_ts:
                    ts_line.append(duet_ts)

        return '\n'.join(orig_line), '\n'.join(ts_line) if ts_line else None

    def to_spl(self) -> str:
        return self.__header() + '\n\n' + '\n'.join([line.spl_str() for line in self.__lines])
