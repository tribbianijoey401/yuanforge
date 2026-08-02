class YuanError(Exception):
    """预期 fail-closed Error 的基类。"""


class ValidationError(YuanError):
    """Input 或不可变 Record 不合法。"""


class IntegrityError(YuanError):
    """内容寻址 State 或 Event History 不一致。"""


class AuthorizationError(YuanError):
    """原本有意义的 Action 超出 Active Grant。"""
