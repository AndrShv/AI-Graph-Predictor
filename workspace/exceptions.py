from fastapi import HTTPException, status

class UserNotFoundByEmailException(HTTPException):
    def __init__(self, message: str = "User not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=message)

class InvalidTokenException(HTTPException):
    def __init__(self, message: str = "Invalid token"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

class EmailSendingException(HTTPException):
    def __init__(self, message: str = "Email service unavailable"):
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=message)


class UserAlreadyExistsException(HTTPException):
    def __init__(self, message: str = "User already exists"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


class InvalidCredentialsException(HTTPException):
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=message)

class InsufficientCredentialsException(HTTPException):
    def __init__(self, message: str = "Insufficient credentials"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=message)

class UserNotFoundException(HTTPException):
    def __init__(self, message: str = "User not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=message)


class CredentialsInvalidException(HTTPException):
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=message)

class AccessDeniedException(HTTPException):
    def __init__(self, message: str = "Access denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=message)





