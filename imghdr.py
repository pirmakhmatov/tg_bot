# Minimal imghdr replacement that uses mimetypes
import mimetypes

def what(file, h=None):
    kind = mimetypes.guess_type(file)[0]
    if kind and "image" in kind:
        return kind.split("/")[-1]
    return None
