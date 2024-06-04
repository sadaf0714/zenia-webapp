import inspect

from exceptions.app_exceptions import AppException


class ServiceResult(object):
    def __init__(self, arg):
        if isinstance(arg, AppException):
            self.success = False
            self.exception_case = arg.exception_case
            self.status_code = arg.status_code
        else:
            self.success = True
            self.exception_case = None
            self.status_code = None
        self.value = arg

    def __str__(self):
        return "[Success]" if self.success else f'[Exception] "{self.exception_case}"'

    def __repr__(self):
        return "<ServiceResult Success>" if self.success else f"<ServiceResult AppException {self.exception_case}>"

    def __enter__(self):
        return self.value

    def __exit__(self, *kwargs):
        pass


def caller_info() -> str:
    info = inspect.getframeinfo(inspect.stack()[2][0])
    return f"{info.filename}:{info.function}:{info.lineno}"


def handle_result(result: ServiceResult):
    if not result.success:
        with result as exception:
            raise exception
    with result as result:
        return result
