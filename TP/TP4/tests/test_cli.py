"""La commande maintai-predict, appelée comme une fonction."""
from maintai.cli import main


def test_cli_prints_probability(trained_model, capsys):
    assert main(["72", "6", "85", "15000"]) == 0
    out = capsys.readouterr().out
    assert "Probabilité de panne" in out and "%" in out


def test_cli_without_model(settings_env, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("MAINTAI_MODELS_DIR", str(tmp_path / "vide"))
    assert main(["72", "6", "85", "15000"]) == 1
    assert "Modèle introuvable" in capsys.readouterr().err
