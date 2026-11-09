import unittest

from assert_cache_reuse import verify


class CacheReuseTests(unittest.TestCase):
    def test_actual_cold_and_restored_shapes(self):
        prefix = "No errors found in 13ms for CacheSmoke.roc\n"
        verify(prefix + "    Modules: 1 total, 0 cached, 1 built\n", "cold")
        verify(prefix + "    Modules: 1 total, 1 cached, 0 built\n", "restored")

    def test_missing_zero_unrelated_and_duplicate_metrics_refuse(self):
        prefix = "No errors found in 13ms for CacheSmoke.roc\n"
        bad = [
            prefix, prefix + "Modules: 1 total, 0 cached, 1 built\n",
            prefix + "Modules: 2 total, 1 cached, 1 built\n",
            "No errors found in 13ms for Other.roc\nModules: 1 total, 1 cached, 0 built\n",
            prefix + "Modules: 1 total, 1 cached, 0 built\n" * 2,
            "All (1) tests passed (cached)\n",
            prefix + "Checked node cache hits 42\n",
        ]
        for text in bad:
            with self.subTest(text=text), self.assertRaises(ValueError):
                verify(text, "restored")

    def test_cold_control_cannot_already_be_warm(self):
        with self.assertRaises(ValueError):
            verify("No errors found in 13ms for CacheSmoke.roc\nModules: 1 total, 1 cached, 0 built\n", "cold")
