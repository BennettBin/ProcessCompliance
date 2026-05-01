from backend.process_compliance.config.loader import load_config


def test_config_loading_default():
    cfg = load_config()
    assert cfg.dataset.name
    assert cfg.paths.run_dir
    assert cfg.ollama.chat_model


