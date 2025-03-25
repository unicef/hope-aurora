import logging

import djclick as click
from django.db.transaction import atomic

from aurora.core import registry
from aurora.core.models import CustomFieldType, FlexForm, OptionSet
from aurora.core.registry import field_registry
from aurora.registration.models import Registration
from testutils.factories import ProjectFactory  # Import ProjectFactory


logger = logging.getLogger(__name__)


class NotRunningInTTYError(Exception):
    pass


INTRO = """<h1>Instruction and consent</h1>
<ul>
<li>Welcome, this page is meant to help UNICEF and humanitarian partners to register
 families with children in Ukraine who need humanitarian assistance inside Ukraine</li>
<li>This survey is voluntary and the information you provide will remain strictly confidential.</li>
<li>Participating in this survey does not mean that you are entitled to assistance.
UNICEF and humanitarian partners will analyze the data for possible eligibility.</li>
<li>Only information that is necessary to facilitate your family potential access to humanitarian
 assistance will be collected, used, and processed. The information collected may also
be used for related purposes, such as monitoring and reporting on the quality of services</li>
<li>If you do not give your consent to treat your personal data, we cannot register you on this page.
 To seek humanitarian assistance you may approach UNICEF and its partners</li>
<li>Your answers to our questions as well as your personal data and photo may be shared with
 other humanitarian organization for assessment or assistance delivery purposes in accordance
  with your will.</li>
<li>The information you provide may be transferred to a secure storage location</li>
<li>UNICEF will keep your personal data for a maximum of 5 years after last use.</li>
<li>For the purpose of this registration A household consists of a person or a group of
 related or unrelated persons, who (i) live together in the same dwelling unit, (ii) who share
 common living arrangements, (iii) who acknowledge the same person as the household head, (iv)and
 who eat together Please list only individuals who belong to your household as per this definition.
</li>
<li>If you are sharing a space with other household please invite them to register as separate
 households.</li>
</ul>
"""

ADMIN1 = """0;0;------
UA01;UA;Avtonomna Respublika Krym;Автономна Республіка Крим;Автономная Республика Крым
UA05;UA;Vinnytska;Вінницька;Винницкая
UA07;UA;Volynska;Волинська;Волынская
UA12;UA;Dnipropetrovska;Дніпропетровська;Днепропетровская
UA14;UA;Donetska;Донецька;Донецкая
UA18;UA;Zhytomyrska;Житомирська;Житомирская
UA21;UA;Zakarpatska;Закарпатська;Закарпатская
UA23;UA;Zaporizka;Запорізька;Запорожская
UA26;UA;Ivano-Frankivska;Івано-Франківська;Ивано-Франковская
UA32;UA;Kyivska;Київська;Киевская
UA35;UA;Kirovohradska;Кіровоградська;Кировоградская
UA44;UA;Luhanska;Луганська;Луганская
UA46;UA;Lvivska;Львівська;Львовская
UA48;UA;Mykolaivska;Миколаївська;Николаевская
UA51;UA;Odeska;Одеська;Одесская
UA53;UA;Poltavska;Полтавська;Полтавская
UA56;UA;Rivnenska;Рівненська;Ровенская
UA59;UA;Sumska;Сумська;Сумская
UA61;UA;Ternopilska;Тернопільська;Тернопольская
UA63;UA;Kharkivska;Харківська;Харьковская
UA65;UA;Khersonska;Херсонська;Херсонская
UA68;UA;Khmelnytska;Хмельницька;Хмельницкая
UA71;UA;Cherkaska;Черкаська;Черкасская
UA73;UA;Chernivetska;Чернівецька;Черновицкая
UA74;UA;Chernihivska;Чернігівська;Черниговская
UA80;UA;Kyivska;Київська;Киевская
UA85;UA;Sevastopilska;Севастопільська;Севастопольский
"""

ADMIN2 = """UA0102;UA01;Bakhchysaraiskyi;Бахчисарайський;Бахчисарайский
UA0104;UA01;Bilohirskyi;Білогірський;Белогорский
UA0106;UA01;Dzhankoiskyi;Джанкойський;Джанкойский
UA0108;UA01;Yevpatoriiskyi;Євпаторійський;Евпаторийский
UA0110;UA01;Kerchynskyi;Керченський;Керченский
UA0112;UA01;Kurmanskyi;Курманський;Курманский
UA0114;UA01;Perekopskyi;Перекопський;Перекопский
UA0116;UA01;Simferopolskyi;Сімферопольський;Симферопольский
UA0118;UA01;Feodosiiskyi;Феодосійський;Феодосийский
UA0120;UA01;Yaltynskyi;Ялтинський;Ялтинский
UA0502;UA05;Vinnytskyi;Вінницький;Винницкий
UA0504;UA05;Haisynskyi;Гайсинський;Гайсинский
UA0506;UA05;Zhmerynskyi;Жмеринський;Жмеринский
UA0508;UA05;Mohyliv-Podilskyi;Могилів-Подільський;Могилев-Подольский
UA0510;UA05;Tulchynskyi;Тульчинський;Тульчинский
UA0512;UA05;Khmilnytskyi;Хмільницький;Хмельницкий
UA0702;UA07;Volodymyr-Volynskyi;Володимир-Волинський;Владимир-Волынский
UA0704;UA07;Kamin-Kashyrskyi;Камінь-Каширський;Камень-Каширский
UA0706;UA07;Kovelskyi;Ковельський;Ковельский
UA0708;UA07;Lutskyi;Луцький;Луцкий
UA1202;UA12;Dniprovskyi;Дніпровський;Днипровский
UA1204;UA12;Kamianskyi;Кам’янський;Каменский
UA1206;UA12;Kryvorizkyi;Криворізький;Криворожский
UA1208;UA12;Nikopolskyi;Нікопольський;Никопольский
UA1210;UA12;Novomoskovskyi;Новомосковський;Новомосковский
UA1212;UA12;Pavlohradskyi;Павлоградський;Павлоградский
UA1214;UA12;Synelnykivskyi;Синельниківський;Синельниковский
UA1402;UA14;Bakhmutskyi;Бахмутський;Бахмутский
UA1404;UA14;Volnovaskyi;Волноваський;Волновахский
UA1406;UA14;Horlivskyi;Горлівський;Горловский
UA1408;UA14;Donetskyi;Донецький;Донецкий
UA1410;UA14;Kalmiuskyi;Кальміуський;Кальмиусский
UA1412;UA14;Kramatorskyi;Краматорський;Краматорский
UA1414;UA14;Mariupolskyi;Маріупольський;Мариупольский
UA1416;UA14;Pokrovskyi;Покровський;Покровский
UA1802;UA18;Berdychivskyi;Бердичівський;Бердичевский
UA1804;UA18;Zhytomyrskyi;Житомирський;Житомирский
UA1806;UA18;Korostenskyi;Коростенський;Коростенский
UA1808;UA18;Novohrad-Volynskyi;Новоград-Волинський;Новоград-Волынский
UA2102;UA21;Berehivskyi;Берегівський;Береговский
UA2104;UA21;Mukachivskyi;Мукачівський;Мукачевский
UA2106;UA21;Rakhivskyi;Рахівський;Раховский
UA2108;UA21;Tiachivskyi;Тячівський;Тячевский
UA2110;UA21;Uzhhorodskyi;Ужгородський;Ужгородский
UA2112;UA21;Khustskyi;Хустський;Хустский
UA2302;UA23;Berdianskyi;Бердянський;Бердянский
UA2304;UA23;Vasylivskyi;Василівський;Васильевский
UA2306;UA23;Zaporizkyi;Запорізький;Запорожский
UA2308;UA23;Melitopolskyi;Мелітопольський;Мелитопольский
UA2310;UA23;Polohivskyi;Пологівський;Пологовский
UA2602;UA26;Verkhovynskyi;Верховинський;Верховинский
UA2604;UA26;Ivano-Frankivskyi;Івано-Франківський;Ивано-Франковский
UA2606;UA26;Kaluskyi;Калуський;Калушский
UA2608;UA26;Kolomyiskyi;Коломийський;Коломыйский
UA2610;UA26;Kosivskyi;Косівський;Косовский
UA2612;UA26;Nadvirnianskyi;Надвірнянський;Надворнянский
UA3200;UA32;Chornobylska zona vidchuzhennia;Чорнобильська зона відчуження;Чернобыльская зона отчуждения
UA3202;UA32;Bilotserkivskyi;Білоцерківський;Белоцерковский
UA3204;UA32;Boryspilskyi;Бориспільський;Бориспольский
UA3206;UA32;Brovarskyi;Броварський;Броварский
UA3208;UA32;Buchanskyi;Бучанський;Бучанский
UA3210;UA32;Vyshhorodskyi;Вишгородський;Вышгородский
UA3212;UA32;Obukhivskyi;Обухівський;Обуховский
UA3214;UA32;Fastivskyi;Фастівський;Фастовский
UA3502;UA35;Holovanivskyi;Голованівський;Голованевский
UA3504;UA35;Kropyvnytskyi;Кропивницький;Кропивницкий
UA3506;UA35;Novoukrainskyi;Новоукраїнський;Новоукраинский
UA3508;UA35;Oleksandriiskyi;Олександрійський;Александрийский
UA4402;UA44;Alchevskyi;Алчевський;Алчевская
UA4404;UA44;Dovzhanskyi;Довжанський;Должанский
UA4406;UA44;Luhanskyi;Луганський;Луганский
UA4408;UA44;Rovenkivskyi;Ровеньківський;Ровеньковский
UA4410;UA44;Svativskyi;Сватівський;Сватовский
UA4412;UA44;Sievierodonetskyi;Сєвєродонецький;Северодонецкий
UA4414;UA44;Starobilskyi;Старобільський;Старобельский
UA4416;UA44;Shchastynskyi;Щастинський;Счастьинский
UA4602;UA46;Drohobytskyi;Дрогобицький;Дрогобычский
UA4604;UA46;Zolochivskyi;Золочівський;Золочевский
UA4606;UA46;Lvivskyi;Львівський;Львовский
UA4608;UA46;Sambirskyi;Самбірський;Самборский
UA4610;UA46;Stryiskyi;Стрийський;Стрыйский
UA4612;UA46;Chervonohradskyi;Червоноградський;Червоноградский
UA4614;UA46;Yavorivskyi;Яворівський;Яворовский
UA4802;UA48;Bashtanskyi;Баштанський;Баштанский
UA4804;UA48;Voznesenskyi;Вознесенський;Вознесенский
UA4806;UA48;Mykolaivskyi;Миколаївський;Николаевский
UA4808;UA48;Pervomaiskyi;Первомайський;Первомайский
UA5102;UA51;Berezivskyi;Березівський;Березовский
UA5104;UA51;Bilhorod-Dnistrovskyi;Білгород-Дністровський;Белгород-Днестровский
UA5106;UA51;Bolhradskyi;Болградський;Болградский
UA5108;UA51;Izmailskyi;Ізмаїльський;Измаильский
UA5110;UA51;Odeskyi;Одеський;Одесский
UA5112;UA51;Podilskyi;Подільський;Подольский
UA5114;UA51;Rozdilnianskyi;Роздільнянський;Раздельнянский
UA5302;UA53;Kremenchutskyi;Кременчуцький;Кременчугский
UA5304;UA53;Lubenskyi;Лубенський;Лубенский
UA5306;UA53;Myrhorodskyi;Миргородський;Миргородский
UA5308;UA53;Poltavskyi;Полтавський;Полтавский
UA5602;UA56;Varaskyi;Вараський;Варашская
UA5604;UA56;Dubenskyi;Дубенський;Дубенский
UA5606;UA56;Rivnenskyi;Рівненський;Ровенский
UA5608;UA56;Sarnenskyi;Сарненський;Сарненский
UA5902;UA59;Konotopskyi;Конотопський;Конотопский
UA5904;UA59;Okhtyrskyi;Охтирський;Ахтырский
UA5906;UA59;Romenskyi;Роменський;Роменский
UA5908;UA59;Sumskyi;Сумський;Сумский
UA5910;UA59;Shostkynskyi;Шосткинський;Шосткинский
UA6102;UA61;Kremenetskyi;Кременецький;Кременецкий
UA6104;UA61;Ternopilskyi;Тернопільський;Тернопольский
UA6106;UA61;Chortkivskyi;Чортківський;Чортковский
UA6302;UA63;Bohodukhivskyi;Богодухівський;Богодуховский
UA6304;UA63;Iziumskyi;Ізюмський;Изюмский
UA6306;UA63;Krasnohradskyi;Красноградський;Красноградский
UA6308;UA63;Kupianskyi;Куп'янський;Купянский
UA6310;UA63;Lozivskyi;Лозівський;Лозовский
UA6312;UA63;Kharkivskyi;Харківський;Харьковский
UA6314;UA63;Chuhuivskyi;Чугуївський;Чугуевский
UA6502;UA65;Beryslavskyi;Бериславський;Бериславский
UA6504;UA65;Henicheskyi;Генічеський;Генический
UA6506;UA65;Kakhovskyi;Каховський;Каховский
UA6508;UA65;Skadovskyi;Скадовський;Скадовский
UA6510;UA65;Khersonskyi;Херсонський;Херсонский
UA6802;UA68;Kamianets-Podilskyi;Кам'янець-Подільський;Каменец-Подольский
UA6804;UA68;Khmelnytskyi;Хмельницький;Хмельницкий
UA6806;UA68;Shepetivskyi;Шепетівський;Шепетовский
UA7102;UA71;Zvenyhorodskyi;Звенигородський;Звенигородский
UA7104;UA71;Zolotoniskyi;Золотоніський;Золотоношский
UA7106;UA71;Umanskyi;Уманський;Уманский
UA7108;UA71;Cherkaskyi;Черкаський;Черкасский
UA7302;UA73;Vyzhnytskyi;Вижницький;Вижницкий
UA7304;UA73;Dnistrovskyi;Дністровський;Днестровский
UA7306;UA73;Cnernivetskyi;Чернівецький;Черновицкий
UA7402;UA74;Koriukivskyi;Корюківський;Корюковский
UA7404;UA74;Nizhynskyi;Ніжинський;Нежинский
UA7406;UA74;Novhorod-Siverskyi;Новгород-Сіверський;Новгород-Северский
UA7408;UA74;Prylutskyi;Прилуцький;Прилукский
UA7410;UA74;Chernihivskyi;Чернігівський;Черниговский
UA8000;UA80;Kyivska;Київська;Киевский
UA8500;UA85;Sevastopilska;Севастопільська;Севастопольский"""


def get_or_create_default_project():
    """Helper function to get or create a default project."""
    from aurora.core.models import Project

    project, created = Project.objects.get_or_create(name="UNICEF")
    return project


@click.command()  # noqa: C901
def upgrade(**kwargs):
    project = get_or_create_default_project()

    optionsets = [
        {
            "name": "ua_admin1",
            "data": ADMIN1.replace("\n", "\r\n"),
            "separator": ";",
            "columns": "pk,__,label",
        },
        {
            "name": "ua_admin2",
            "data": ADMIN2.replace("\n", "\r\n"),
            "separator": ";",
            "columns": "pk,parent,label",
        },
        {
            "name": "ua_admin3",
            "data": ADMIN3.replace("\n", "\r\n"),
            "separator": ";",
            "columns": "pk,parent,label",
        },
    ]
    for fld in optionsets:
        name = fld.pop("name")
        with atomic():
            OptionSet.objects.update_or_create(name=name, defaults=fld)

    custom_fields = [
        {
            "name": "MaritalStatus",
            "base_type": registry.forms.ChoiceField,
            "attrs": {"choices": ["Single", "Married", "Divorced", "Widowed", "Separated"]},
        },
        {
            "name": "ResidenceStatus",
            "base_type": registry.forms.ChoiceField,
            "attrs": {
                "choices": (
                    ("idp", "Displaced | Internally Displaced Person (IDP)"),
                    ("refugee", "Displaced | Refugee / Asylum Seeker"),
                    ("others_of_concern", "Displaced | Others of Concern"),
                    ("host", "Non-displaced | Hosting a displaced family"),
                    ("non_host", "Non-displaced | Not hosting a displaced family"),
                    ("returnee", "Returnee"),
                    ("repatriated", "Repatriate"),
                )
            },
        },
        {
            "name": "Gender",
            "base_type": registry.forms.ChoiceField,
            "attrs": {"choices": ["Female", "Male"]},
        },
        {
            "name": "ID Type",
            "base_type": registry.forms.ChoiceField,
            "attrs": {
                "choices": (
                    ("not_available", "Not Available"),
                    ("birth_certificate", "Birth Certificate"),
                    ("drivers_license", "Driver's License"),
                    ("electoral_card", "Electoral Card"),
                    ("unhcr_id", "UNHCR ID"),
                    ("national_id", "National ID"),
                    ("national_passport", "National Passport"),
                    ("scope_id", "WFP Scope ID"),
                    ("other", "Other"),
                )
            },
        },
        {
            "name": "Relationship",
            "base_type": registry.forms.ChoiceField,
            "attrs": {
                "choices": (
                    ("son_daughter", "Son / Daughter"),
                    ("wife_husband", "Wife / Husband"),
                    ("brother_sister", "Brother / Sister"),
                    ("mother_father", "Mother / Father"),
                    ("aunt_uncle", "Aunt / Uncle"),
                    ("grandmother_grandfather", "Grandmother / Grandfather"),
                    ("motherInLaw_fatherInLaw", "Mother-in-law / Father-in-law"),
                    ("daughterInLaw_sonInLaw", "Daughter-in-law / Son-in-law"),
                    ("sisterInLaw_brotherInLaw", "Sister-in-law / Brother-in-law"),
                    ("granddaugher_grandson", "Granddaughter / Grandson"),
                    ("nephew_niece", "Nephew / Niece"),
                    ("cousin", "Cousin"),
                )
            },
        },
        {
            "name": "Collector",
            "base_type": registry.forms.ChoiceField,
            "attrs": {
                "choices": (
                    ("primary", "Primary"),
                    ("alternate", "Alternate"),
                    ("no_role", "No"),
                )
            },
        },
        {
            "name": "Registration Method",
            "base_type": registry.forms.ChoiceField,
            "attrs": {
                "choices": (
                    ("hh_registration", "Household Registration"),
                    ("community", "Community-level Registration"),
                )
            },
        },
        {
            "name": "Data Sharing",
            "base_type": registry.fields.multi_checkbox.MultiCheckboxField,
            "attrs": {
                "choices": (
                    ("unicef", "UNICEF"),
                    ("humanitarian_partner", "Humanitarian partners"),
                    ("private_partner", "Private partners"),
                    ("government_partner", "Government partners"),
                )
            },
        },
    ]

    for fld in custom_fields:
        name = fld.pop("name")
        with atomic():
            custom_fld = CustomFieldType.build(name, fld)
            field_registry.register(custom_fld.get_class())

    base, __ = FlexForm.objects.get_or_create(name="Basic", project=project)
    hh, __ = FlexForm.objects.get_or_create(name="Household", project=project)
    ind, __ = FlexForm.objects.get_or_create(name="Individual", project=project)
    FlexForm.objects.get_or_create(name="Document", project=project)
    FlexForm.objects.get_or_create(name="Bank Account", project=project)

    base.add_formset(hh, extra=1, dynamic=False, max_num=1, min_num=1)
    base.add_formset(ind, extra=1, dynamic=True, min_num=1)

    base.add_field(
        "With whom may we share your information (select one or multiple among the following)?",
        registry.fields.MultiCheckboxField,
        choices=(
            ("unicef", "UNICEF"),
            ("priv_partner", "Private partners"),
            ("gov_partner", "Government partners"),
        ),
        name="enum_org",
    )
    base.add_field("Residence status", "aurora.core.models.ResidenceStatus")
    Registration.objects.get_or_create(name="Ucraina", defaults={"intro": INTRO, "flex_form": base, "project":project})

    hh.add_field("Admin 1", registry.fields.AjaxSelectField, datasource="ua_admin1")
    hh.add_field(
        "Admin 2",
        registry.fields.AjaxSelectField,
        datasource="ua_admin2",
        parent="ua_admin1",
    )
    hh.add_field(
        "Admin 3",
        registry.fields.AjaxSelectField,
        datasource="ua_admin3",
        parent="ua_admin2",
    )
    ind.add_field("First Name")
    ind.add_field("Last Name")

