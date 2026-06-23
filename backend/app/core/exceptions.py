class AppError(Exception):
    """Базовая ошибка приложения"""

    status_code = 400

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class NotFoundError(AppError):
    """Ошибка отсутствующей сущности"""

    status_code = 404


class ConflictError(AppError):
    """Ошибка конфликта состояния"""

    status_code = 409


class ForbiddenError(AppError):
    """Ошибка недостаточных прав"""

    status_code = 403


class UnauthorizedError(AppError):
    """Ошибка аутентификации"""

    status_code = 401
