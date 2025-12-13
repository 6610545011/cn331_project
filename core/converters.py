import re

class CaseInsensitiveSlugConverter:
    # Accept any non-slash characters (allows spaces, dashes, etc.)
    regex = "[^/]+"

    # Input from URL → Python
    def to_python(self, value):
        return value  # keep original case

    # Python → URL reversing
    def to_url(self, value):
        return value
