from re import Match, Pattern, compile
from typing import Iterator


class TTMLTime:
    __pattern: Pattern = compile(r'\d+')

    def __init__(self, centi: str = ''):
        if centi == '': return
        # 获取匹配结果的数组
        match: list[str] = self.__pattern.findall(centi)

        if len(match) < 2:
            raise ValueError(f'Invalid time: {centi}')

        count: int = 0
        for t in match[:-1]:
            count = count * 60 + int(t)
        count = count * 1000 + int(match[-1])
        self.__micros: int = count % 1000
        count //= 1000
        self.__second: int = count % 60
        self.__minute: int = count // 60

    def __str__(self) -> str:
        return f'{self.__minute:02}:{self.__second:02}.{self.__micros:03}'

    def __int__(self) -> int:
        return (self.__minute * 60 + self.__second) * 1000 + self.__micros

    def __gt__(self, other) -> bool:
        return (self.__minute, self.__second, self.__micros) > (other.__minute, other.__second, other.__micros)

    def __ge__(self, other) -> bool:
        return (self.__minute, self.__second, self.__micros) >= (other.__minute, other.__second, other.__micros)

    def __ne__(self, other) -> bool:
        return (self.__minute, self.__second, self.__micros) != (other.__minute, other.__second, other.__micros)

    def __sub__(self, other) -> int:
        return abs(int(self) - int(other))
