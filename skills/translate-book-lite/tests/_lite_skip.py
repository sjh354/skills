"""Marker for tests that assert the wording of the ORIGINAL translate-book SKILL.md.

translate-book-lite rewrites SKILL.md on purpose (shorter, file-based briefs, opt-in audit,
no advisors), so tests that look for the original's sentences, step numbers or advisor
names cannot pass here. Tests of script behaviour are untouched. See LITE.md.
"""
import unittest

asserts_original_skill_md = unittest.skip(
    'asserts the wording of the original SKILL.md; translate-book-lite rewrites it (see LITE.md)')
