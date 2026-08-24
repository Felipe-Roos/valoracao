from django.contrib import admin

from .models import (
    ProjectYearValuation,
    ValuationCategory,
    ValuationEntry,
    ValuationMultiplier,
    ValuationProduct,
)


class ValuationMultiplierInline(admin.TabularInline):
    model = ValuationMultiplier
    extra = 0


@admin.register(ValuationCategory)
class ValuationCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')


@admin.register(ValuationProduct)
class ValuationProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'base_value', 'order')
    list_filter = ('category',)
    inlines = [ValuationMultiplierInline]


@admin.register(ProjectYearValuation)
class ProjectYearValuationAdmin(admin.ModelAdmin):
    list_display = ('project_slug', 'year', 'created_at')
    list_filter = ('project_slug', 'year')


@admin.register(ValuationEntry)
class ValuationEntryAdmin(admin.ModelAdmin):
    list_display = ('product', 'project_year', 'quantity', 'base_value', 'final_value', 'created_at')
    list_filter = ('project_year__project_slug', 'project_year__year')
