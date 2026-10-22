import recon


def test_package_is_importable() -> None:
    # Guards the src-layout install: fails if `recon` is not installed into the venv.
    # Also keeps pytest from exiting with code 5 ("no tests collected") in CI.
    assert recon.__name__ == "recon"
