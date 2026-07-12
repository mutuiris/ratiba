def test_settings_load(settings):
    assert settings.SLOT_MINUTES == 30
    assert settings.USE_TZ is True
    assert settings.AUTH_USER_MODEL == "accounts.User"
