from scripts.perf_probe import route_specs


def test_route_specs_include_core_phase5_pages() -> None:
    routes = [spec.path for spec in route_specs()]

    assert "/v1/me" in routes
    assert "/v1/projects" in routes
    assert "/v1/tasks" in routes
    assert "/v1/approvals" in routes
    assert "/v1/director/overview" in routes
    assert "/v1/audit-events" in routes
