from django.contrib.auth.models import User

# If you need to define other models in this file, add them here
# Otherwise, this file can be empty or deleted

INSTALLED_APPS = [
    # ...existing apps...
    'users',  # ensure the users app is listed so settings can import users.validators
    # ...existing apps...
]

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'users.validators.SimplePasswordValidator',
        'OPTIONS': {
            'min_length': 1,  # set to the minimum length you want (1 allows very short passwords)
        }
    },
]

# Add these lines to further reduce password restrictions
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]