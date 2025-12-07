import re

class CaseInsensitiveSlugConverter:
    # Accept any letters or digits, any case
    regex = '[A-Za-z0-9]+'

    # Input from URL → Python
    def to_python(self, value):
        return value  # keep original case

    # Python → URL reversing
    def to_url(self, value):
        return value
