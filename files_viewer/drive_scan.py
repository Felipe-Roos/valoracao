"""Varredura da árvore de pastas sincronizada do Drive.

Duas estruturas são aceitas dentro de <root>/<ano>/:

  1. Com pasta de mês numerada (raiz compartilhada por vários projetos):
     <root>/2025/12. DEZEMBRO/EVIDÊNCIAS NOVEMBRO/09. revestimento de cateter/...
     A numeração da subpasta do projeto muda de mês para mês (ex: "revestimento
     de cateter" pode ser "09." em um mês e "10." no seguinte), então ela é
     localizada pelo texto depois do número, não pela posição/número.

  2. Pasta de evidências direto dentro do ano (raiz dedicada a um projeto só):
     <root>/2025/EVIDÊNCIAS ABRIL/arquivo.pdf
     Quando a pasta de evidências não tem nenhuma subpasta, todos os arquivos
     soltos nela são considerados do projeto (a raiz já é exclusiva dele).
"""

import re
import unicodedata
from pathlib import Path

_YEAR_RE = re.compile(r'^\d{4}$')
_LEADING_NUMBER_RE = re.compile(r'^\d+[.\s]+')


def _normalize(text: str) -> str:
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    return text.strip().casefold()


def _strip_leading_number(name: str) -> str:
    return _LEADING_NUMBER_RE.sub('', name).strip()


def _is_evidence_folder(entry: Path) -> bool:
    return entry.is_dir() and 'evid' in _normalize(entry.name)


def list_available_years(root: Path) -> list[int]:
    if not root or not root.is_dir():
        return []
    years = []
    for entry in root.iterdir():
        if entry.is_dir() and _YEAR_RE.match(entry.name):
            years.append(int(entry.name))
    return sorted(years, reverse=True)


def _list_evidence_folders(year_dir: Path) -> list[Path]:
    """Acha pastas de evidências direto no ano, ou uma pasta de mês abaixo."""
    evidence_folders = []
    for entry in sorted(year_dir.iterdir(), key=lambda e: e.name):
        if not entry.is_dir():
            continue
        if _is_evidence_folder(entry):
            evidence_folders.append(entry)
        elif _LEADING_NUMBER_RE.match(entry.name):
            for sub_entry in entry.iterdir():
                if _is_evidence_folder(sub_entry):
                    evidence_folders.append(sub_entry)
    return evidence_folders


def _find_project_subfolder(evidence_dir: Path, match_keyword: str) -> Path | None:
    keyword = _normalize(_strip_leading_number(match_keyword))
    if not keyword:
        return None
    for entry in evidence_dir.iterdir():
        if not entry.is_dir():
            continue
        candidate = _normalize(_strip_leading_number(entry.name))
        if candidate == keyword or keyword in candidate or candidate in keyword:
            return entry
    return None


def _has_subfolders(directory: Path) -> bool:
    return any(entry.is_dir() for entry in directory.iterdir())


def collect_year_files(
    root: Path, year: int, match_keyword: str, *, dedicated_root: bool = False
) -> list[dict]:
    """Agrega, em uma lista só, os arquivos do projeto em todo mês do ano.

    Quando `dedicated_root` é True, uma pasta de evidências sem subpastas tem
    seus arquivos soltos atribuídos direto ao projeto (a raiz é exclusiva
    dele). Quando False (raiz compartilhada por vários projetos), esses meses
    são ignorados por serem ambíguos — não dá pra saber de qual projeto é um
    arquivo solto sem a subpasta que o identifica.
    """
    year_dir = root / str(year)
    if not year_dir.is_dir():
        return []

    files = []
    for evidence_dir in _list_evidence_folders(year_dir):
        source_dir = _find_project_subfolder(evidence_dir, match_keyword)
        if source_dir is None and dedicated_root and not _has_subfolders(evidence_dir):
            source_dir = evidence_dir
        if source_dir is None:
            continue

        for file_path in sorted(source_dir.rglob('*')):
            if not file_path.is_file():
                continue
            files.append({
                'path': file_path,
                'rel_path': file_path.relative_to(root).as_posix(),
                'name': file_path.name,
                'month_label': evidence_dir.name,
            })
    return files
