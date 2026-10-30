# -*- coding: utf-8 -*-
r"""A bare `\checkmark` in a table cell must reach pandoc inside math.

DRAMA (2502.18460) writes `\checkmark` outside math and `$\times$` inside it.
pandoc reads the second and drops the first, so 70 check marks in four tables
printed as empty cells -- "not applicable" to a reader -- while every count
and every probe agreed, because the cell was there and no number had changed.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), 'scripts'))

import arxiv_backend as ab  # noqa: E402


class BareCheckmarks(unittest.TestCase):
    def test_a_bare_checkmark_in_a_tabular_is_wrapped(self):
        tex = ('\\begin{tabular}{lc}\nBM25 & \\checkmark \\\\\n'
               'DRAGON & $\\checkmark$ \\\\\n\\end{tabular}')
        out, n = ab.wrap_table_checkmarks(tex)
        self.assertEqual(n, 1)
        self.assertIn('BM25 & $\\checkmark$ \\\\', out)
        self.assertIn('DRAGON & $\\checkmark$ \\\\', out)
        self.assertNotIn('$$', out)

    def test_a_checkmark_in_an_equation_is_left_alone(self):
        tex = '\\begin{equation}\n\\checkmark\n\\end{equation}'
        self.assertEqual(ab.wrap_table_checkmarks(tex), (tex, 0))

    def test_text_after_the_tabular_is_not_a_table(self):
        tex = ('\\begin{tabular}{c}\na\n\\end{tabular}\n'
               'Prose with \\checkmark here.')
        out, n = ab.wrap_table_checkmarks(tex)
        self.assertEqual(n, 0)
        self.assertEqual(out, tex)

    def test_a_nested_tabular_keeps_the_outer_one_open(self):
        tex = ('\\begin{tabular}{c}\n\\begin{tabular}{c}x\\end{tabular}'
               ' & \\checkmark \\\\\n\\end{tabular}')
        out, n = ab.wrap_table_checkmarks(tex)
        self.assertEqual(n, 1)

    def test_an_escaped_dollar_does_not_open_math(self):
        tex = '\\begin{tabular}{cc}\n\\$5 & \\checkmark \\\\\n\\end{tabular}'
        out, n = ab.wrap_table_checkmarks(tex)
        self.assertEqual(n, 1)
        self.assertIn('\\$5 & $\\checkmark$', out)


if __name__ == '__main__':
    unittest.main()
