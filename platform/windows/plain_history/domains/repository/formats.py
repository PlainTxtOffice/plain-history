"""Define supported document-repository format rules."""


def validate_format(version: object) -> None:
    """Reject unknown format versions without reading or changing files."""
    if type(version) is not int or version != 1:
        message = "Unsupported repository format."
        raise ValueError(message)
