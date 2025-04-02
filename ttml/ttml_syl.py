from xml.dom.minidom import Element

from ttml.ttml_time import TTMLTime


class TTMLSyl:
    def __init__(self, element: Element):
        self.__begin: TTMLTime = TTMLTime(element.getAttribute("begin"))
        self.__end: TTMLTime = TTMLTime(element.getAttribute("end"))
        self.text: str = element.childNodes[0].nodeValue

    def get_begin(self) -> TTMLTime:
        return self.__begin

    def get_end(self) -> TTMLTime:
        return self.__end

    def lys_str(self) -> str:
        return f'{self.text}({int(self.__begin)},{self.__end - self.__begin})'

    def spl_str(self) -> tuple[TTMLTime, str, TTMLTime]:
        return self.__begin, self.text, self.__end