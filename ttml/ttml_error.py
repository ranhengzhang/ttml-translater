class TTMLError(Exception):
    @staticmethod
    def throw_dom_error():
        raise TTMLError("TTML 文件结构错误")

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)  # 初始化父类，确保异常信息完整
