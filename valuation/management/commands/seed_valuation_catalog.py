from django.core.management.base import BaseCommand
from django.db import transaction

from valuation.models import ValuationCategory, ValuationMultiplier, ValuationProduct

MULTIPLY = ValuationMultiplier.MULTIPLY
VARIABLE_MULTIPLY = ValuationMultiplier.VARIABLE_MULTIPLY
ADD_PER_UNIT = ValuationMultiplier.ADD_PER_UNIT

INTL_TEAM = ('Equipe internacional', MULTIPLY, '1.2', '')
STUDENTS = ('Participação de estudantes', MULTIPLY, '1.1', '')
COMPANIES = ('Parceria com empresas', MULTIPLY, '1.15', '')
IMPACT_FACTOR = ('Impact Factor (informe o IF)', VARIABLE_MULTIPLY, None, '')
PRESENTED_WORKS = ('Número de trabalhos apresentados (n × 0,2)', ADD_PER_UNIT, '0.2', '')
AWARD_SUPERGOLD = ('Melhor do evento / SuperGold (×5)', MULTIPLY, '5', 'award_tier')
AWARD_GOLD = ('Melhor da sessão / Gold (×3)', MULTIPLY, '3', 'award_tier')
AWARD_SILVER = ('Menção honrosa / Silver / Bronze (×1)', MULTIPLY, '1', 'award_tier')

# Cada categoria: (nome, [produtos])
# Cada produto: dict com name, base_value (ou None), base_value_note, quantity_label,
# valuation_criteria, rationale e multipliers (lista das tuplas acima).
CATALOG = [
    ('Scientific Production', [
        dict(
            name='Original journal article',
            base_value='20120.00',
            valuation_criteria='Impact Factor',
            rationale='Average publication cost (~US$4K).',
            multipliers=[IMPACT_FACTOR, INTL_TEAM, STUDENTS],
        ),
        dict(
            name='Original international journal article (IF>3<10)',
            base_value='25000.00',
            valuation_criteria='Impact Factor',
            rationale='Average publication cost.',
            multipliers=[INTL_TEAM, COMPANIES],
        ),
        dict(
            name='Original international journal article (IF<3)',
            base_value='8000.00',
            valuation_criteria='Impact Factor',
            rationale='Average publication cost.',
            multipliers=[INTL_TEAM, COMPANIES],
        ),
        dict(
            name='Indexed original national article',
            base_value='4000.00',
            valuation_criteria='Impact Factor',
            rationale='Average publication cost.',
            multipliers=[INTL_TEAM, COMPANIES],
        ),
        dict(
            name='Review article',
            base_value='10060.00',
            valuation_criteria='Article type',
            rationale=(
                'Review articles tend to receive a high number of citations and contribute '
                'significantly to institutional recognition, although they generally have a lower '
                'direct impact on advancing scientific knowledge. Estimated valuation = 50% of the '
                'value assigned to an original article.'
            ),
            multipliers=[IMPACT_FACTOR, INTL_TEAM, STUDENTS],
        ),
        dict(
            name='Participation with presentation / invited talk in international events',
            base_value='15000.00',
            valuation_criteria='Text format / Event type',
            rationale='Reflects the estimated cost of promoting the Biopark brand through participation in the event (~US$3K).',
            multipliers=[INTL_TEAM, STUDENTS, PRESENTED_WORKS],
        ),
        dict(
            name='Participation with presentation / invited talk in national events',
            base_value='3000.00',
            valuation_criteria='Scientific event',
            rationale='Reflects the estimated cost of promoting the Biopark brand through participation in the event.',
            multipliers=[INTL_TEAM, STUDENTS, PRESENTED_WORKS],
        ),
        dict(
            name='Award or recognition for works in international events',
            base_value='15000.00',
            valuation_criteria='Award',
            rationale='Reflects the estimated cost of promoting the Biopark brand through participation in the event (~US$3K).',
            multipliers=[INTL_TEAM, STUDENTS, AWARD_SUPERGOLD, AWARD_GOLD, AWARD_SILVER],
        ),
        dict(
            name='Award or recognition for works in national events',
            base_value='3000.00',
            valuation_criteria='Award',
            rationale='Reflects the estimated cost of promoting the Biopark brand through participation in the event.',
            multipliers=[INTL_TEAM, STUDENTS, AWARD_SUPERGOLD, AWARD_GOLD, AWARD_SILVER],
        ),
        dict(
            name='Technical book with official registration',
            base_value='200000.00',
            valuation_criteria='ISBN',
            rationale=(
                'Long-term intellectual output requiring substantial effort, frequently used as an '
                'educational resource and technical reference. Estimated value based on that of an '
                'original research article published in a journal with an impact factor of 10.'
            ),
            multipliers=[INTL_TEAM, STUDENTS],
        ),
        dict(
            name='Book chapter',
            base_value='30180.00',
            valuation_criteria='ISBN',
            rationale=(
                'More limited scope and impact than complete books, but relevant to the consolidation '
                'and dissemination of specialized expertise. Estimated value considered equivalent to '
                'that of a review article published in a journal with an impact factor of 3.'
            ),
            multipliers=[INTL_TEAM, STUDENTS],
        ),
    ]),
    ('IP & Technology', [
        dict(
            name='International Patent Application with Biopark Educação as the Assignee',
            base_value='90000.00',
            valuation_criteria='Technological potential',
            rationale='Based on the average cost of technology development, patent drafting, and the potential for generating future economic assets.',
            multipliers=[INTL_TEAM, STUDENTS, COMPANIES],
        ),
        dict(
            name='National Patent Application with Biopark Educação as the Assignee',
            base_value='30000.00',
            valuation_criteria='Technological potential',
            rationale='Based on the average cost of technology development, patent drafting, and the potential for generating future economic assets.',
            multipliers=[INTL_TEAM, STUDENTS, COMPANIES],
        ),
        dict(
            name='Granted Patent with Biopark Educação as the Assignee',
            base_value=None,
            base_value_note='10% da valoração real de mercado do ativo tecnológico ao longo de um período de exploração de 5 anos. Preencha o valor já calculado.',
            valuation_criteria='Effective granting',
            rationale='The granting of a patent reduces legal uncertainty and significantly enhances the economic value of the technological asset.',
            multipliers=[INTL_TEAM, STUDENTS, COMPANIES],
        ),
        dict(
            name='Licensing or Technology Transfer of a Patent, Product, or Know-How to an Industrial Partner',
            base_value=None,
            base_value_note='Valor real do contrato + royalties sobre 5 anos de exploração (ou valor de desenvolvimento em licenciamento gratuito). Preencha o valor já calculado.',
            valuation_criteria='Royalties / Real value / Development value',
            rationale='The additional value represents the indirect institutional gains associated with enhanced reputation and the advancement of technological maturity.',
            multipliers=[INTL_TEAM],
        ),
        dict(
            name='Software registration',
            base_value='15000.00',
            valuation_criteria='Estimated cost of maintaining the registration over a ten-year period',
            rationale='Value based on the potential for practical application and the average cost of specialized software development.',
            multipliers=[INTL_TEAM, STUDENTS],
        ),
        dict(
            name='Registered cultivar',
            base_value='60000.00',
            valuation_criteria='Estimated cost of maintaining the registration over a ten-year period',
            rationale='High economic potential in the agricultural sector, associated with years of experimental development and intellectual property protection.',
            multipliers=[INTL_TEAM, STUDENTS, COMPANIES],
        ),
        dict(
            name='Documented know-how (validated methods, signed dossiers/reports)',
            base_value='20000.00',
            valuation_criteria='Estimated cost of maintaining the registration over a ten-year period',
            rationale='Represents the consolidation of technical knowledge that is difficult to replicate and has significant potential for technology transfer.',
            multipliers=[INTL_TEAM, STUDENTS, COMPANIES],
        ),
    ]),
    ('Funding', [
        dict(
            name='Approved Project in calls',
            base_value=None,
            base_value_note='100% do valor de financiamento aplicado ao Biopark (financeiro + in-kind). Preencha o valor já calculado.',
            valuation_criteria='Institutional return',
            rationale='Institutional return.',
            multipliers=[INTL_TEAM, STUDENTS, COMPANIES],
        ),
        dict(
            name='Company contract',
            base_value=None,
            base_value_note='100% do valor de financiamento aplicado ao Biopark (financeiro + in-kind). Preencha o valor já calculado.',
            valuation_criteria='Institutional return',
            rationale='Institutional return.',
            multipliers=[INTL_TEAM, STUDENTS],
        ),
        dict(
            name='International Cooperation agreement',
            base_value=None,
            base_value_note='R$30.000 (acordos até 2M) / R$60.000 (entre 2M e 10M) / R$90.000 (acima de 10M). Preencha o valor conforme a faixa.',
            valuation_criteria='Benchmark based on market value charged by specialized consulting companies',
            rationale='Value based on the reputational impact and the capacity to enhance internationalization through strategic partnerships.',
            multipliers=[],
        ),
    ]),
    ('Media Return', [
        dict(
            name='Media coverage',
            base_value=None,
            base_value_note='Valor real de clipping de mídia no período avaliado (busca por palavras-chave). Em validação com a vice-presidência.',
            valuation_criteria='Em validação com vice-presidência',
            rationale='Based on the real impact of media publications, as assessed by a specialized media monitoring and analysis company.',
            multipliers=[],
        ),
    ]),
    ('Event Organization', [
        dict(
            name='Event organization',
            base_value=None,
            base_value_note='Valor real captado para o evento (patrocínios, inscrições e outras receitas externas). Preencha o valor já calculado.',
            valuation_criteria='Scope and reach of the event',
            rationale="Reflects the institution's impact, networking opportunities, and contribution to strengthening the innovation ecosystem.",
            multipliers=[],
        ),
    ]),
    ('HR Development', [
        dict(
            name='Internship or Undergraduate Researcher (Scientific Initiation)',
            base_value='800.00',
            quantity_label='Número de meses de participação',
            valuation_criteria='Scientific training',
            rationale='Value associated with the effort invested in the initial stage of scientific training and research capacity building.',
            multipliers=[],
        ),
        dict(
            name='Master Researcher',
            base_value='2100.00',
            quantity_label='Número de meses de participação',
            valuation_criteria='',
            rationale='Development of highly qualified human resources with significant technical and scientific impact.',
            multipliers=[],
        ),
        dict(
            name='Doctorate Researcher',
            base_value='3100.00',
            quantity_label='Número de meses de participação',
            valuation_criteria='',
            rationale='Represents a substantial investment of time, technical expertise, and scientific effort in advanced research training.',
            multipliers=[INTL_TEAM],
        ),
        dict(
            name='Postdoctoral Researcher',
            base_value='5500.00',
            quantity_label='Número de meses de participação',
            valuation_criteria='Advanced specialization',
            rationale='Highly specialized training associated with the production of advanced scientific knowledge and research outputs.',
            multipliers=[],
        ),
    ]),
    ('Regulatory Impact', [
        dict(
            name='Regulatory product registration (ANVISA, MAPA)',
            base_value=None,
            base_value_note='Valoração real de mercado do ativo tecnológico ao longo de um período de exploração de 5 anos. Preencha o valor já calculado.',
            valuation_criteria='Approval',
            rationale='High technical and regulatory complexity, combined with significant strategic value for market entry.',
            multipliers=[],
        ),
    ]),
]


class Command(BaseCommand):
    help = 'Popula (ou atualiza) o catálogo de valoração de RD&I a partir da tabela da Biopark Educação.'

    @transaction.atomic
    def handle(self, *args, **options):
        for cat_order, (category_name, products) in enumerate(CATALOG):
            category, _ = ValuationCategory.objects.update_or_create(
                name=category_name, defaults={'order': cat_order}
            )
            for prod_order, product_data in enumerate(products):
                multipliers = product_data.pop('multipliers', [])
                product_data.setdefault('quantity_label', 'Quantidade')
                product_data.setdefault('base_value_note', '')
                product, _ = ValuationProduct.objects.update_or_create(
                    category=category,
                    name=product_data['name'],
                    defaults={**product_data, 'order': prod_order},
                )
                product.multipliers.all().delete()
                for mult_order, (label, factor_type, factor_value, group) in enumerate(multipliers):
                    ValuationMultiplier.objects.create(
                        product=product,
                        label=label,
                        factor_type=factor_type,
                        factor_value=factor_value,
                        exclusive_group=group,
                        order=mult_order,
                    )

        self.stdout.write(self.style.SUCCESS('Catálogo de valoração atualizado.'))
