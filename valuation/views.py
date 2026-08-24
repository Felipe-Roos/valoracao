import json
from decimal import Decimal, InvalidOperation

from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from files_viewer.drive_scan import list_available_years
from files_viewer.utils import get_project

from .models import ProjectYearValuation, ValuationCategory, ValuationEntry, ValuationProduct


def _to_decimal(value, default=None):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError):
        return default


def year_list(request, project_slug):
    project = get_project(project_slug)
    folder_configured = bool(project['root'] and project['root'].exists())
    disk_years = list_available_years(project['root']) if folder_configured else []

    totals_by_year = dict(
        ProjectYearValuation.objects.filter(project_slug=project_slug)
        .annotate(total=Sum('entries__final_value'))
        .values_list('year', 'total')
    )

    all_years = sorted(set(disk_years) | set(totals_by_year), reverse=True)
    years = [
        {'year': year, 'total': totals_by_year.get(year) or Decimal('0')}
        for year in all_years
    ]

    context = {
        'project': project,
        'years': years,
        'folder_configured': folder_configured,
    }
    return render(request, 'valuation/year_list.html', context)


@require_POST
def year_create(request, project_slug):
    get_project(project_slug)
    year_raw = request.POST.get('year', '').strip()
    if year_raw.isdigit():
        year = int(year_raw)
        ProjectYearValuation.objects.get_or_create(project_slug=project_slug, year=year)
        return redirect('valuation:year_detail', project_slug=project_slug, year=year)
    return redirect('valuation:year_list', project_slug=project_slug)


def year_detail(request, project_slug, year):
    project = get_project(project_slug)
    project_year, _ = ProjectYearValuation.objects.get_or_create(project_slug=project_slug, year=year)

    categories = ValuationCategory.objects.prefetch_related('products__multipliers')
    entries = project_year.entries.select_related('product').all()
    total = project_year.entries.aggregate(total=Sum('final_value'))['total'] or Decimal('0')

    context = {
        'project': project,
        'project_year': project_year,
        'categories': categories,
        'entries': entries,
        'total': total,
    }
    return render(request, 'valuation/year_detail.html', context)


@require_POST
def entry_create(request, project_slug, year):
    get_project(project_slug)
    project_year, _ = ProjectYearValuation.objects.get_or_create(project_slug=project_slug, year=year)

    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({'error': 'JSON inválido.'}, status=400)

    product = get_object_or_404(ValuationProduct, pk=payload.get('product_id'))
    quantity = _to_decimal(payload.get('quantity'), Decimal('1')) or Decimal('1')
    base_value = _to_decimal(payload.get('base_value'))
    final_value = _to_decimal(payload.get('final_value'))
    notes = (payload.get('notes') or '')[:255]
    applied_multipliers = payload.get('applied_multipliers') or []
    file_path = (payload.get('file_path') or '')[:1024]
    file_name = (payload.get('file_name') or '')[:255]

    if base_value is None or final_value is None:
        return JsonResponse({'error': 'Valor base e valor final são obrigatórios.'}, status=400)

    entry = ValuationEntry.objects.create(
        project_year=project_year,
        product=product,
        quantity=quantity,
        base_value=base_value,
        applied_multipliers=applied_multipliers,
        final_value=final_value,
        notes=notes,
        file_path=file_path,
        file_name=file_name,
    )

    total = project_year.entries.aggregate(total=Sum('final_value'))['total'] or Decimal('0')

    return JsonResponse({
        'id': entry.id,
        'product_name': product.name,
        'category_name': product.category.name,
        'quantity': str(entry.quantity),
        'base_value': str(entry.base_value),
        'final_value': str(entry.final_value),
        'notes': entry.notes,
        'file_path': entry.file_path,
        'file_name': entry.file_name,
        'total': str(total),
    })


@require_POST
def entry_delete(request, project_slug, year, entry_id):
    get_project(project_slug)
    project_year = get_object_or_404(ProjectYearValuation, project_slug=project_slug, year=year)
    entry = get_object_or_404(ValuationEntry, pk=entry_id, project_year=project_year)
    entry.delete()

    total = project_year.entries.aggregate(total=Sum('final_value'))['total'] or Decimal('0')
    return JsonResponse({'deleted': True, 'total': str(total)})
