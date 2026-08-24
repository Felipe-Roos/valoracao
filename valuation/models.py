from django.db import models


class ValuationCategory(models.Model):
    name = models.CharField(max_length=120)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class ValuationProduct(models.Model):
    category = models.ForeignKey(ValuationCategory, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    base_value = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    base_value_note = models.CharField(
        max_length=255,
        blank=True,
        help_text='Explicação de como preencher o valor base quando ele não é um número fixo.',
    )
    quantity_label = models.CharField(max_length=80, default='Quantidade')
    rationale = models.TextField(blank=True)
    valuation_criteria = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class ValuationMultiplier(models.Model):
    MULTIPLY = 'multiply'
    VARIABLE_MULTIPLY = 'variable_multiply'
    ADD_PER_UNIT = 'add_per_unit'
    TYPE_CHOICES = [
        (MULTIPLY, 'Multiplicador fixo (ex: ×1.2)'),
        (VARIABLE_MULTIPLY, 'Multiplicador com valor informado (ex: Impact Factor)'),
        (ADD_PER_UNIT, 'Bônus somado por unidade (ex: +(n×0.2))'),
    ]

    product = models.ForeignKey(ValuationProduct, related_name='multipliers', on_delete=models.CASCADE)
    label = models.CharField(max_length=150)
    factor_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    factor_value = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    exclusive_group = models.CharField(
        max_length=50,
        blank=True,
        help_text='Multiplicadores com o mesmo grupo são mutuamente exclusivos (radio em vez de checkbox).',
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.product.name} — {self.label}'


class ProjectYearValuation(models.Model):
    project_slug = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project_slug', 'year')
        ordering = ['-year']

    def __str__(self):
        return f'{self.project_slug} — {self.year}'


class ValuationEntry(models.Model):
    project_year = models.ForeignKey(ProjectYearValuation, related_name='entries', on_delete=models.CASCADE)
    product = models.ForeignKey(ValuationProduct, related_name='+', on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    base_value = models.DecimalField(max_digits=14, decimal_places=2)
    applied_multipliers = models.JSONField(default=list, blank=True)
    final_value = models.DecimalField(max_digits=14, decimal_places=2)
    notes = models.CharField(max_length=255, blank=True)
    file_path = models.CharField(
        max_length=1024,
        blank=True,
        help_text='Caminho relativo (dentro da pasta do projeto) do arquivo usado como evidência.',
    )
    file_name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.product.name} ({self.final_value})'
