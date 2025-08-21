class UserNotFound(Exception):
    pass


class UserAlreadyExists(Exception):
    pass


class ReleaseNotInModelError(Exception):
    pass


class InvalidURL(Exception):
    pass


class ReleaseNotInFavorites(Exception):
    pass


class FavoriteAlreadyExists(Exception):
    pass


class ReleaseNotFound(Exception):
    pass


class FeedbackAlreadyExists(Exception):
    pass


class SearchIdNotFound(Exception):
    pass
