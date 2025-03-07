from Login.abstract import LoginMethod
from Login.cookie import Cookie
from Login.cp import CoursePlatform

class Login:
    """
    登录类，支持通过cookie/课程平台/MIS登录
    """
    def __init__(self, method: str = None) -> None:
        self.cookie = None
        self.enabled_methods = {
            # "mis": Mis,
            "cookie": Cookie,
            "cp": CoursePlatform
        }
        if method is not None:
            raise Exception("未知的登录方式")

    def login(self, **kwargs) -> None:
        """
        登录
        :return:
        """
        if self.method is None:
            raise Exception("未设置登录方式")
        self.method.login(**kwargs)
        self.cookie = self.method.getCookies()
