import mimetypes
from decimal import Decimal

from django.conf import settings
from django.db.models import Count, Sum
from django.http import FileResponse, Http404
from django.shortcuts import render
from django.utils import timezone

from valuation.catalog import catalog_as_data
from valuation.models import ValuationEntry

from .drive_scan import collect_year_files, list_available_years
from .utils import EXTENSION_LABELS, PREVIEWABLE_EXTENSIONS, get_project, resolve_safe_path


def project_list(request):
    projects = [
        {**project, 'folder_configured': bool(project['root'] and project['root'].exists())}
        for project in settings.PROJECTS
    ]
    return render(request, 'files_viewer/project_list.html', {'projects': projects})


def file_list(request, project_slug):
    project = get_project(project_slug)
    root = project['root']
    folder_configured = bool(root and root.exists())

    available_years = list_available_years(root) if folder_configured else []

    year_raw = request.GET.get('year', '').strip()
    if year_raw.isdigit():
        selected_year = int(year_raw)
    elif available_years:
        selected_year = available_years[0]
    else:
        selected_year = timezone.now().year

    entries = []

    if folder_configured:
        for file in collect_year_files(
            root, selected_year, project['match'], dedicated_root=project['dedicated_root']
        ):
            ext = file['path'].suffix.lower()
            entries.append({
                'name': file['name'],
                'rel_path': file['rel_path'],
                'month_label': file['month_label'],
                'label': EXTENSION_LABELS.get(ext, ext.lstrip('.').upper() or 'Arquivo'),
                'previewable': ext in PREVIEWABLE_EXTENSIONS,
            })

        file_paths = [e['rel_path'] for e in entries]
        valuations_by_file = {}
        if file_paths:
            qs = (
                ValuationEntry.objects.filter(
                    project_year__project_slug=project_slug,
                    project_year__year=selected_year,
                    file_path__in=file_paths,
                )
                .values('file_path')
                .annotate(total=Sum('final_value'), count=Count('id'))
            )
            valuations_by_file = {row['file_path']: row for row in qs}

        for entry in entries:
            info = valuations_by_file.get(entry['rel_path'])
            entry['valuation_total'] = info['total'] if info else None
            entry['valuation_count'] = info['count'] if info else 0

    year_total = (
        ValuationEntry.objects.filter(
            project_year__project_slug=project_slug, project_year__year=selected_year
        ).aggregate(total=Sum('final_value'))['total']
        or Decimal('0')
    )

    context = {
        'project': project,
        'entries': entries,
        'folder_configured': folder_configured,
        'folder_path': str(root) if root else '(não configurado)',
        'available_years': available_years,
        'selected_year': selected_year,
        'year_total': year_total,
        'valuation_catalog': catalog_as_data(),
    }
    return render(request, 'files_viewer/file_list.html', context)


def _serve_file(project_slug, rel_path, *, as_attachment):
    project = get_project(project_slug)
    if not project['root']:
        raise Http404('Pasta do projeto não configurada.')

    file_path = resolve_safe_path(project['root'], rel_path)
    if not file_path.is_file():
        raise Http404('Essa entrada não é um arquivo.')

    content_type, _ = mimetypes.guess_type(file_path.name)
    return FileResponse(
        open(file_path, 'rb'),
        content_type=content_type or 'application/octet-stream',
        filename=file_path.name,
        as_attachment=as_attachment,
    )


def file_preview(request, project_slug, rel_path):
    return _serve_file(project_slug, rel_path, as_attachment=False)


def file_download(request, project_slug, rel_path):
    return _serve_file(project_slug, rel_path, as_attachment=True)
