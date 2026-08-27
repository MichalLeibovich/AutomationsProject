"""Selectors, and nothing else.

Every selector in the suite lives in this package. Page objects import from here;
test modules never do. When a page changes, exactly one file needs editing.
"""

from core.locators.google_locators import GoogleLocators

__all__ = ["GoogleLocators"]
