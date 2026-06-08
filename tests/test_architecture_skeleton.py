from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_target_monorepo_directories_exist():
    expected = [
        ROOT / "apps" / "api" / "alpha_sim",
        ROOT / "apps" / "api" / "alembic",
        ROOT / "apps" / "web" / "app",
        ROOT / "apps" / "web" / "components",
        ROOT / "packages" / "shared",
        ROOT / "docs" / "technical",
    ]

    missing = [path for path in expected if not path.exists()]

    assert not missing


def test_api_application_factory_exposes_versioned_app():
    from apps.api.alpha_sim.main import create_app

    app = create_app()

    assert app.title == "AI投资想法体检器 API"
    assert app.version == "2.0.0"
    assert any(route.path == "/api/v1/health" for route in app.routes)
    assert any(route.path == "/" for route in app.routes)

