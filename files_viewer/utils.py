from pathlib import Path

from django.conf import settings
from django.http import Http404

PREVIEWABLE_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.gif', '.webp'}

EXTENSION_LABELS = {
    '.pdf': 'PDF',
    '.png': 'Imagem',
    '.jpg': 'Imagem',
    '.jpeg': 'Imagem',
    '.gif': 'Imagem',
    '.webp': 'Imagem',
    '.doc': 'Word',
    '.docx': 'Word',
    '.xls': 'Excel',
    '.xlsx': 'Excel',
}


def get_project(slug: str) -> dict:
    for project in settings.PROJECTS:
        if project['slug'] == slug:
            return project
    raise Http404('Projeto não encontrado.')


def resolve_safe_path(root: Path, relative_path: str) -> Path:
    """Resolve um caminho relativo dentro de root, impedindo path traversal."""
    candidate = (root / (relative_path or '')).resolve()

    if candidate != root and root not in candidate.parents:
        raise Http404('Caminho inválido.')

    if not candidate.exists():
        raise Http404('Arquivo ou pasta não encontrada.')

    return candidate
