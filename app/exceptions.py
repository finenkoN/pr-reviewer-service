class ServiceException(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class TeamExistsError(ServiceException):
    def __init__(self, message: str):
        super().__init__("TEAM_EXISTS", message)


class TeamNotFoundError(ServiceException):
    def __init__(self, message: str):
        super().__init__("NOT_FOUND", message)


class UserNotFoundError(ServiceException):
    def __init__(self, message: str):
        super().__init__("NOT_FOUND", message)


class PRExistsError(ServiceException):
    def __init__(self, message: str):
        super().__init__("PR_EXISTS", message)


class PRNotFoundError(ServiceException):
    def __init__(self, message: str):
        super().__init__("NOT_FOUND", message)


class PRMergedError(ServiceException):
    def __init__(self, message: str):
        super().__init__("PR_MERGED", message)


class ReviewerNotAssignedError(ServiceException):
    def __init__(self, message: str):
        super().__init__("NOT_ASSIGNED", message)


class NoCandidateError(ServiceException):
    def __init__(self, message: str):
        super().__init__("NO_CANDIDATE", message)

