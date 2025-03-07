from .. import env

CAPTCHA_FONT_SIZE = 40
CAPTCHA_CHALLENGE_FUNCT = "captcha.helpers.random_char_challenge"
CAPTCHA_TEST_MODE = env("CAPTCHA_TEST_MODE")
CAPTCHA_GET_FROM_POOL = True
