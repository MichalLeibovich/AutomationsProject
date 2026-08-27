"""Page Object Model.

Page objects are the only consumers of the :mod:`core.locators` package. They
expose intent-named methods, so a test reads as behaviour and contains no
selector, wait or CSS.
"""

from core.pages.base_page import BasePage
from core.pages.google_home_page import GoogleHomePage

__all__ = ["BasePage", "GoogleHomePage"]
