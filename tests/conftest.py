from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.pdf_builder import build_minimal_pdf

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=str(cwd), check=True, capture_output=True, text=True)


def write_pdf(path: Path, page_texts: list[str | None]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(build_minimal_pdf(page_texts))
    return path


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def synthetic_corpus(tmp_path: Path) -> Path:
    """Build a small, deliberately messy corpus tree for scanner tests.

    Layout (all PDFs are tiny hand-built stand-ins, not real ENADE content):

    2005/
        b1_prova.pdf, b2_gabarito.pdf, b3_padrao.pdf   -> complete trio
    2008/
        e1_prova.pdf                                    -> exam with NO answer_key/answer_standard
    2011/
        1_prova.pdf, 2_gabarito.pdf, 3_padrao.pdf        -> unified booklet (no course letter)
    2014/
        l2_gabarito.pdf                                  -> answer_key with NO exam ("gabarito sem prova")
        x9_relatorio.pdf                                 -> unexpected filename (orphan)
    misc/                                                -> unexpected directory (not a 4-digit year)
    notes.txt                                            -> unexpected root entry
    """
    root = tmp_path / "corpus"

    write_pdf(root / "2005" / "b1_prova.pdf", ["FORMACAO GERAL " * 5, "COMPONENTE ESPECIFICO " * 5])
    write_pdf(root / "2005" / "b2_gabarito.pdf", ["GABARITO " * 5])
    write_pdf(root / "2005" / "b3_padrao.pdf", ["PADRAO DE RESPOSTA " * 5])

    write_pdf(root / "2008" / "e1_prova.pdf", ["FORMACAO GERAL ENGENHARIA " * 5])

    write_pdf(root / "2011" / "1_prova.pdf", ["COMPUTACAO " * 5, "LICENCIATURA " * 5])
    write_pdf(root / "2011" / "2_gabarito.pdf", ["GABARITO " * 5])
    write_pdf(root / "2011" / "3_padrao.pdf", ["PADRAO " * 5])

    write_pdf(root / "2014" / "l2_gabarito.pdf", ["GABARITO SEM PROVA " * 5])
    write_pdf(root / "2014" / "x9_relatorio.pdf", ["ARQUIVO INESPERADO " * 5])

    (root / "misc").mkdir(parents=True, exist_ok=True)
    (root / "misc" / "readme.txt").write_text("not a year directory", encoding="utf-8")

    (root / "notes.txt").write_text("stray file at corpus root", encoding="utf-8")

    # A real .git directory would also sit at the root of a cloned corpus;
    # simulate just enough of it to prove the scanner ignores it.
    (root / ".git").mkdir(parents=True, exist_ok=True)
    (root / ".git" / "HEAD").write_text("ref: refs/heads/master\n", encoding="utf-8")

    return root


@pytest.fixture
def git_corpus(tmp_path: Path) -> Path:
    """A small *real* git clone-like corpus, for CLI tests that read git metadata."""
    root = tmp_path / "git_corpus"
    write_pdf(root / "2005" / "b1_prova.pdf", ["FORMACAO GERAL " * 5])
    write_pdf(root / "2005" / "b2_gabarito.pdf", ["GABARITO " * 5])
    write_pdf(root / "2005" / "b3_padrao.pdf", ["PADRAO " * 5])

    _git(["init", "-q"], root)
    _git(["config", "user.email", "test@example.invalid"], root)
    _git(["config", "user.name", "Test"], root)
    _git(["remote", "add", "origin", "https://example.invalid/geacc/enade.git"], root)
    _git(["add", "-A"], root)
    _git(["commit", "-q", "-m", "synthetic corpus for tests"], root)

    return root
