from __future__ import annotations

import unittest

from classify_ci_scope import is_allowed_infrastructure_path, is_infrastructure_only


class InfrastructurePathTests(unittest.TestCase):
    def test_exact_workflow_and_schema_paths_are_allowed(self):
        self.assertTrue(is_allowed_infrastructure_path(".github/workflows/ci.yml"))
        self.assertTrue(is_allowed_infrastructure_path("schemas/infra-task-v1.schema.json"))

    def test_infrastructure_documentation_and_code_are_allowed(self):
        self.assertTrue(is_allowed_infrastructure_path("docs/infra/worker-sandbox.md"))
        self.assertTrue(is_allowed_infrastructure_path("docs/governance/PROJECT_STATE.md"))
        self.assertTrue(is_allowed_infrastructure_path("infra/control_plane/worker_runtime.py"))

    def test_product_and_unknown_paths_are_rejected(self):
        self.assertFalse(is_allowed_infrastructure_path("user/analysis-engine/model.py"))
        self.assertFalse(is_allowed_infrastructure_path("user/user-backend/src/app.ts"))
        self.assertFalse(is_allowed_infrastructure_path(".github/workflows/deploy.yml"))

    def test_schedule_is_infrastructure_only(self):
        self.assertTrue(is_infrastructure_only("schedule", "main", []))

    def test_infra_pull_request_with_only_allowlisted_paths_is_allowed(self):
        self.assertTrue(is_infrastructure_only(
            "pull_request",
            "infra/provider-neutral-control-plane-2026-11",
            [
                ".github/workflows/ci.yml",
                "docs/infra/worker-sandbox.md",
                "infra/control_plane/worker_runtime.py",
            ],
        ))

    def test_infra_push_with_only_allowlisted_paths_is_allowed(self):
        self.assertTrue(is_infrastructure_only(
            "push", "infra/ci-freeze", ["requirements-infra.txt"]
        ))

    def test_non_infra_branch_is_rejected(self):
        self.assertFalse(is_infrastructure_only(
            "pull_request", "feature/product", [".github/workflows/ci.yml"]
        ))

    def test_mixed_infra_and_product_changes_are_rejected(self):
        self.assertFalse(is_infrastructure_only(
            "pull_request",
            "infra/attempt",
            ["infra/control_plane/worker_runtime.py", "user/analysis-engine/model.py"],
        ))

    def test_empty_or_unknown_scope_is_rejected(self):
        self.assertFalse(is_infrastructure_only("pull_request", "infra/empty", []))
        self.assertFalse(is_infrastructure_only("workflow_dispatch", "infra/manual", []))


if __name__ == "__main__":
    unittest.main()
