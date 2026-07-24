from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from nightwatch.errors import ValidationError
from nightwatch.models import Brief, load_brief, normalize_relative_path, path_is_allowed
from tests.helpers import brief_data, task


class BriefValidationTests(unittest.TestCase):
    def test_valid_brief_is_normalized(self) -> None:
        brief = Brief.from_dict(brief_data())
        self.assertEqual(brief.run_id, "test-run")
        self.assertEqual(brief.allowed_paths, ("workspace/out",))
        self.assertEqual(brief.tasks[0].retry.max_attempts, 1)

    def test_required_fields_are_reported(self) -> None:
        data = brief_data()
        data["objective"] = ""
        with self.assertRaisesRegex(ValidationError, "objective"):
            Brief.from_dict(data)

    def test_unsafe_and_nonportable_paths_are_rejected(self) -> None:
        for unsafe in (
            "../outside",
            "/absolute",
            "C:/private",
            "workspace\\out",
            ".",
            "workspace//out",
            "workspace/bad:name/file.md",
            "workspace/CON/file.md",
        ):
            with self.subTest(unsafe=unsafe), self.assertRaises(ValidationError):
                normalize_relative_path(unsafe)

    def test_allowed_path_uses_components_not_string_prefixes(self) -> None:
        self.assertTrue(path_is_allowed("workspace/app/file.md", ["workspace/app"]))
        self.assertFalse(path_is_allowed("workspace/application/file.md", ["workspace/app"]))

    def test_task_output_must_be_inside_allowlist(self) -> None:
        data = brief_data(tasks=[task(outputs=["workspace/other/result.md"])])
        with self.assertRaisesRegex(ValidationError, "outside allowed_paths"):
            Brief.from_dict(data)

    def test_allowed_paths_cannot_target_controller_state(self) -> None:
        data = brief_data(
            allowed_paths=["manifest.json"],
            tasks=[task(outputs=["manifest.json"])],
        )
        with self.assertRaisesRegex(ValidationError, "beneath 'workspace/'"):
            Brief.from_dict(data)

    def test_duplicate_task_outputs_are_rejected(self) -> None:
        shared = "workspace/out/shared.md"
        data = brief_data(
            tasks=[task("task-one", outputs=[shared]), task("task-two", outputs=[shared])]
        )
        with self.assertRaisesRegex(ValidationError, "declared by both"):
            Brief.from_dict(data)

    def test_unknown_dependency_and_cycle_are_rejected(self) -> None:
        unknown = brief_data(tasks=[task(depends_on=["missing-task"])])
        with self.assertRaisesRegex(ValidationError, "unknown task"):
            Brief.from_dict(unknown)
        cycle = brief_data(
            tasks=[
                task("task-one", depends_on=["task-two"]),
                task("task-two", depends_on=["task-one"]),
            ]
        )
        with self.assertRaisesRegex(ValidationError, "cycle"):
            Brief.from_dict(cycle)

    def test_handoff_source_must_declare_that_it_produces_one(self) -> None:
        data = brief_data(
            tasks=[
                task("task-one"),
                task(
                    "task-two",
                    kind="review",
                    depends_on=["task-one"],
                    handoff_from="task-one",
                    fresh_context=True,
                ),
            ]
        )
        with self.assertRaisesRegex(ValidationError, "does not produce one"):
            Brief.from_dict(data)

    def test_fresh_context_is_reserved_for_review_tasks(self) -> None:
        data = brief_data(tasks=[task(kind="implementation", fresh_context=True)])
        with self.assertRaisesRegex(ValidationError, "fresh_context"):
            Brief.from_dict(data)

    def test_handoff_source_must_also_be_dependency(self) -> None:
        data = brief_data(
            tasks=[
                task("task-one", produce_handoff=True),
                task("task-two", handoff_from="task-one"),
            ]
        )
        with self.assertRaisesRegex(ValidationError, "must depend"):
            Brief.from_dict(data)

    def test_load_brief_reports_malformed_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "brief.json"
            path.write_text("{not json", encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "not valid JSON"):
                load_brief(path)

    def test_round_trip_preserves_valid_structure(self) -> None:
        original = Brief.from_dict(brief_data())
        encoded = json.loads(json.dumps(original.as_dict()))
        restored = Brief.from_dict(encoded)
        self.assertEqual(original, restored)


if __name__ == "__main__":
    unittest.main()
