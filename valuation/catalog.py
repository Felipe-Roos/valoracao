from .models import ValuationCategory


def catalog_as_data():
    """Serializa o catálogo (categorias > produtos > multiplicadores) para uso em JS."""
    categories = []
    for category in ValuationCategory.objects.prefetch_related('products__multipliers'):
        products = []
        for product in category.products.all():
            multipliers = [
                {
                    'id': m.id,
                    'label': m.label,
                    'factor_type': m.factor_type,
                    'factor_value': float(m.factor_value) if m.factor_value is not None else None,
                    'exclusive_group': m.exclusive_group,
                }
                for m in product.multipliers.all()
            ]
            products.append({
                'id': product.id,
                'name': product.name,
                'base_value': float(product.base_value) if product.base_value is not None else None,
                'base_value_note': product.base_value_note,
                'quantity_label': product.quantity_label,
                'valuation_criteria': product.valuation_criteria,
                'multipliers': multipliers,
            })
        categories.append({'name': category.name, 'products': products})
    return categories
