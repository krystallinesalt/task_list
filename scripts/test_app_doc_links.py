"""Preserve Task List guidance coverage around the canonical kit checker."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import test_doc_links as kit


class AppDocLinkTests(unittest.TestCase):
	def test_readme_and_recursive_docs_resolve(self):
		docs = [kit.ROOT / "README.md", *sorted(kit.ROOT.glob("docs/**/*.md"))]
		self.assertEqual(kit.broken_links(docs), [])

	def test_read_by_task_requires_skills(self):
		self.assertTrue(
			kit.read_by_task_skills(kit.ROOT / "AGENTS.md"),
			"Read by task must exist and name skills",
		)


class AppDocCoverageTests(unittest.TestCase):
	def test_broken_readme_and_nested_links_fail(self):
		with tempfile.TemporaryDirectory() as directory:
			root = Path(directory)
			(root / "README.md").write_text("[Missing](missing.md)\n")
			nested = root / "docs/decisions/example.md"
			nested.parent.mkdir(parents=True)
			nested.write_text("[Missing anchor](../../README.md#missing)\n")
			with patch.object(kit, "ROOT", root):
				result = AppDocLinkTests("test_readme_and_recursive_docs_resolve").run()
			self.assertEqual(len(result.failures), 1)
			self.assertIn("README.md:1: missing.md (missing file)", result.failures[0][1])
			self.assertIn("docs/decisions/example.md:1:", result.failures[0][1])
			self.assertIn("(missing anchor)", result.failures[0][1])

	def test_missing_or_empty_read_by_task_fails(self):
		with tempfile.TemporaryDirectory() as directory:
			root = Path(directory)
			for guidance in ("# Guidance\n", "## Read by task\n\n| Task | Read first |\n"):
				with self.subTest(guidance=guidance), patch.object(kit, "ROOT", root):
					(root / "AGENTS.md").write_text(guidance)
					result = AppDocLinkTests("test_read_by_task_requires_skills").run()
					self.assertEqual(len(result.failures), 1)
					self.assertFalse(result.skipped)


if __name__ == "__main__":
	unittest.main()
