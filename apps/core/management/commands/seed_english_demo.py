"""Fill the English (`_en`) columns for the demonstration catalogue (FR-136).

Kept out of ``seed_demo`` and out of the approved dataset on purpose. That
dataset is the approved Arabic content and is frozen — ``tests/test_route_contract``
asserts its shape — so the English copy lives here instead, as a separate,
idempotent pass that can be re-run or skipped without touching approved data.

This command reads no file: the translations are literals below, matched to
existing rows by their stable slug, key or legacy id.

    python manage.py seed_english_demo

Only rows that are still untranslated are written, so a real translation entered
in the admin is never overwritten by a re-run. Anything not listed keeps falling
back to Arabic, which is the designed behaviour, not a gap.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

CATEGORIES = {
    "fingerprint": ("Fingerprint locks", "Fast, secure fingerprint entry for home and office doors."),
    "keypad": ("Keypad locks", "Code entry with no key to carry or lose."),
    "smart-handle": ("Smart handles", "Smart handles for interior doors and home workspaces."),
    "accessories": ("Security accessories", "Viewers, bridges and add-ons that complete the setup."),
}

COLLECTIONS = {
    "best-sellers": ("Standout picks", "A curated set of ZAKEY smart locks and solutions.", "ZAKEY picks"),
    "featured": ("Featured products", "The products we put in front of first-time buyers.", "Featured"),
    "fingerprint-locks": ("Fingerprint locks", "Every ZAKEY lock that opens with a fingerprint.", "By entry method"),
    "smart-door-locks": ("Smart door locks", "Main-door locks with multiple ways in.", "For the main door"),
    "smart-home-solutions": ("Smart home solutions", "Bridges and hubs that connect the locks to the rest of the home.", "Whole home"),
    "security-accessories": ("Security accessories", "Viewers and add-ons that round out the entrance.", "Add-ons"),
}

PRODUCTS = {
    "zakey-apex-pro": (
        "ZAKEY Apex Pro",
        "A premium main-door lock with five ways in and a clear interior display.",
        "Most advanced",
    ),
    "zakey-nexus-elite": (
        "ZAKEY Nexus Elite",
        "A slim, quiet design with the fingerprint reader built into the handle.",
        "Premium",
    ),
    "zakey-vision-x": (
        "ZAKEY Vision X",
        "Camera and doorbell in one, so you see the entrance from a single interface.",
        "Clearer view",
    ),
    "zakey-pulse-f5": (
        "ZAKEY Pulse F5",
        "A balanced everyday fingerprint lock with an unmistakable battery warning.",
        "Practical choice",
    ),
    "zakey-orbit-k3": (
        "ZAKEY Orbit K3",
        "A compact keypad for interior doors and work units.",
        "",
    ),
    "zakey-nova-s2": (
        "ZAKEY Nova S2",
        "A straightforward fingerprint lock with a clear interface, for families and modern flats.",
        "Great value",
    ),
    "zakey-core-c1": (
        "ZAKEY Core C1",
        "A compact smart handle for interior doors and home workspaces.",
        "",
    ),
    "zakey-guard-view": (
        "ZAKEY Guard View",
        "A smart door viewer with an interior screen for a clearer look at who is there.",
        "Smart add-on",
    ),
    "zakey-bridge-mini": (
        "ZAKEY Bridge Mini",
        "A compact bridge linking the smart locks to the wider home system for smoother control.",
        "Home system",
    ),
}

NAVIGATION = {
    "الرئيسية": "Home",
    "المتجر": "Shop",
    "المنتجات": "Products",
    "عن زاكي": "About ZAKEY",
    "تواصل معنا": "Contact us",
    "البحث": "Search",
    "المفضلة": "Wishlist",
    "حسابي": "My account",
    "سلة التسوق": "Cart",
    "الشركة": "Company",
    "الدعم": "Support",
}

SHIPPING_METHODS = {
    "shipping-standard": ("Standard shipping", "Target delivery in 3 to 5 working days."),
    "shipping-free": ("Free shipping", "On orders of EGP 1,500 or more."),
    "shipping-same-day": ("Same-day delivery", "For eligible areas within Greater Cairo."),
}

PAYMENT_METHODS = {
    "payment-cod": ("Cash on delivery", "Pay for the order when it arrives.", "No order is created and no amount is collected yet."),
    "payment-instapay": ("InstaPay", "Instant transfer over the instant payments network.", "No InstaPay link or transfer is live yet."),
    "payment-vodafone-cash": ("Vodafone Cash", "Pay from your mobile wallet.", "No wallet or provider link is live yet."),
    "payment-etisalat-cash": ("e& Cash", "Pay from your mobile wallet.", "No wallet or provider link is live yet."),
    "payment-cashu": ("CashU", "A digital payment option for local transactions.", "No CashU integration, account or transaction is live yet."),
    "payment-installments": ("Instalments with an Egyptian bank card", "Planned instalment plans of up to 12 months.", "No bank link, credit approval or charge is live yet."),
}

GOVERNORATES = {
    "alexandria": "Alexandria", "aswan": "Aswan", "asyut": "Asyut", "beheira": "Beheira",
    "beni-suef": "Beni Suef", "cairo": "Cairo", "dakahlia": "Dakahlia", "damietta": "Damietta",
    "faiyum": "Faiyum", "gharbia": "Gharbia", "giza": "Giza", "ismailia": "Ismailia",
    "kafr-el-sheikh": "Kafr El Sheikh", "luxor": "Luxor", "matrouh": "Matrouh",
    "minya": "Minya", "monufia": "Monufia", "new-valley": "New Valley",
    "north-sinai": "North Sinai", "port-said": "Port Said", "qalyubia": "Qalyubia",
    "qena": "Qena", "red-sea": "Red Sea", "sharqia": "Sharqia", "sohag": "Sohag",
    "south-sinai": "South Sinai", "suez": "Suez",
}

INSTALLATION = "Installation service"

CURRENCY_LABEL = "EGP"

#: Feature chips, keyed by the stable `key` the storefront facets on.
FEATURES = {
    "app": ("Home control", "Manage every compatible lock from one place."),
    "auto-lock": ("Auto-lock", "The door locks itself once you are through."),
    "automation": ("Smart scenes", "Flexible routines for leaving and arriving."),
    "camera": ("Built-in camera", "A clear, live view of the entrance."),
    "card": ("Proximity card", "Quick entry with no key."),
    "doorbell": ("Built-in doorbell", "An immediate alert when a visitor arrives."),
    "fingerprint": ("Fast fingerprint", "One touch and you are in."),
    "low-battery": ("Battery warning", "A clear signal well before the power runs out."),
    "pin": ("Keypad", "Several entry codes."),
    "privacy": ("Privacy mode", "Extra privacy for rooms and interior spaces."),
}

#: Variant finish names.
FINISHES = {
    "أبيض": "White",
    "أسود": "Black",
    "أسود أوبسيديان": "Obsidian black",
    "برونزي": "Bronze",
    "جرافيت": "Graphite",
    "ذهبي شامبين": "Champagne gold",
    "فحمي": "Charcoal",
    "فضي": "Silver",
    "فضي ساتان": "Satin silver",
}

SPECIFICATION_GROUPS = {"المواصفات العامة": "General specifications"}

#: Specification rows are a small, closed vocabulary in this catalogue, so they
#: are translated by exact value rather than per row.
SPECIFICATION_LABELS = {
    "الاستخدام": "Usage",
    "التغذية": "Power",
    "التوافق": "Compatibility",
    "الشاشة": "Display",
    "الشاشة الداخلية": "Interior display",
    "زاوية الرؤية": "Field of view",
    "سُمك الباب المناسب": "Supported door thickness",
    "طاقة طوارئ": "Emergency power",
    "طرق الدخول": "Ways in",
    "مادة الهيكل": "Body material",
}

SPECIFICATION_VALUES = {
    "30–60 مم": "30–60 mm",
    "32–75 مم": "32–75 mm",
    "35–100 مم": "35–100 mm",
    "35–85 مم": "35–85 mm",
    "35–90 مم": "35–90 mm",
    "38–100 مم": "38–100 mm",
    "40–110 مم": "40–110 mm",
    "4 بوصات": "4 inches",
    "4.3 بوصة": "4.3 inches",
    "أقفال ZAKEY المدعومة": "Supported ZAKEY locks",
    "بصمة، رمز، بطاقة، مفتاح": "Fingerprint, code, card, key",
    "بصمة، رمز، بطاقة، مفتاح، واجهة ذكية": "Fingerprint, code, card, key, smart interface",
    "بصمة، رمز، مفتاح": "Fingerprint, code, key",
    "بصمة، مفتاح": "Fingerprint, key",
    "بطاريات جافة": "Dry-cell batteries",
    "بطارية قابلة للشحن": "Rechargeable battery",
    "رمز، بطاقة، مفتاح": "Code, card, key",
    "سبيكة معدنية": "Metal alloy",
    "داخلي": "Interior",
}

PARTNERS = {
    "المنازل الحديثة": "Modern homes",
    "الوحدات الفندقية": "Hotel units",
    "مشروعات التطوير": "Development projects",
    "مكاتب الأعمال": "Business offices",
}

DOCUMENT_LABELS = {
    "دليل الأبعاد": "Dimensions guide",
    "دليل الاستخدام": "User guide",
    "دليل القياس": "Sizing guide",
    "دليل المقاسات": "Size guide",
    "مخطط التركيب": "Installation drawing",
    "مخطط فتحة الباب": "Door cut-out drawing",
    "ورقة الأبعاد": "Dimensions sheet",
    "ورقة القياس": "Measurement sheet",
}

DOCUMENT_NOTICES = {
    "يؤكد فني التركيب الأبعاد النهائية بعد المعاينة.":
        "The installer confirms the final dimensions after the survey.",
    "تُفعّل خصائص الاتصال عند إطلاق الخدمة المتوافقة.":
        "Connectivity features are enabled when the compatible service launches.",
    "راجع فريق التركيب لتأكيد قياسات الباب النهائية.":
        "Check with the installation team to confirm the final door measurements.",
    "استعن بفريق التركيب لتأكيد ملاءمة المقاس قبل الشراء.":
        "Ask the installation team to confirm the fit before you buy.",
    "يؤكد فني التركيب توافق المخطط مع بابك قبل التنفيذ.":
        "The installer confirms the drawing matches your door before fitting.",
    "يؤكد فني التركيب توافق المخطط مع بابك.":
        "The installer confirms the drawing matches your door.",
    "راجع الأبعاد مع فريق التركيب قبل الشراء.":
        "Review the dimensions with the installation team before you buy.",
    "يؤكد فني التركيب الأبعاد النهائية بعد معاينة الباب.":
        "The installer confirms the final dimensions after surveying the door.",
    "راجع القياسات مع فريق التركيب قبل الشراء.":
        "Review the measurements with the installation team before you buy.",
}

#: The demonstration "reviews" are use-case cards rather than customer opinions,
#: so they are translated here. Real customer reviews are deliberately left
#: alone: a review is shown in the language it was written in unless a staff
#: member fills in the English column by hand.
REVIEWS = {
    "review-apex": ("For the family home", "Suggested use case",
        "Five ways in give everyone the method that suits them, with an interior display for a clearer view."),
    "review-elite": ("For modern entrances", "Suggested use case",
        "A slim design with the fingerprint reader in the handle, for anyone who wants technology that does not impose itself on the space."),
    "review-vision": ("To see your visitor", "Suggested use case",
        "Camera, doorbell and interior display bring the entrance together into one clear solution."),
    "review-pulse": ("For everyday use", "Suggested use case",
        "Fingerprint, PIN and a battery warning in a practical lock that is easy to rely on every day."),
    "review-orbit": ("For small offices", "Suggested use case",
        "A compact keypad and proximity cards that suit the movement of a team and its visitors through the day."),
    "review-nova": ("For modern flats", "Suggested use case",
        "A simple solution combining fingerprint and PIN with a clear battery warning."),
    "review-core": ("For interior rooms", "Suggested use case",
        "A compact smart handle that adds privacy without complicating the look of the door or how it is used."),
    "review-guard": ("To upgrade the door viewer", "Suggested use case",
        "A larger screen and a clearer camera, for anyone updating the entrance without replacing the lock entirely."),
    "review-bridge": ("For the connected home", "Suggested use case",
        "A small bridge that brings management of compatible locks and entry routines into one place."),
}

INSTALMENT_MESSAGES = {
    "خطط تقسيط حتى 12 شهرًا — تخضع لشروط البنك عند تفعيل الخدمة.":
        "Instalment plans of up to 12 months — subject to the bank's terms when the service goes live.",
    "خطط تقسيط حتى 9 أشهر — تخضع لشروط البنك عند تفعيل الخدمة.":
        "Instalment plans of up to 9 months — subject to the bank's terms when the service goes live.",
    "خطط تقسيط حتى 6 أشهر — تخضع لشروط البنك عند تفعيل الخدمة.":
        "Instalment plans of up to 6 months — subject to the bank's terms when the service goes live.",
    "خيارات التقسيط غير متاحة لهذا المنتج حاليًا.":
        "Instalment options are not available for this product yet.",
    "لا توجد خطة تقسيط لهذا الملحق حاليًا.":
        "There is no instalment plan for this accessory yet.",
}

#: Sparse English overlays for the authored page copy. Only the words are
#: listed — image paths, dimensions and ids stay Arabic-side, because
#: `HomeSection.resolved_data` deep-merges and anything omitted keeps its
#: original value.
PAGE_COPY = {
    "brand": {
        "name": "ZAKEY",
        "tagline": "Smarter security starts at your door",
        "logo": {"alt": "ZAKEY — smart locks"},
    },
    "announcement": {
        "message": "Free shipping planned on orders over EGP 1,500",
        "emphasis": "A choosing and installation guide before you buy",
    },
    "home": {
        "hero": {
            "eyebrow": "Smart security with a design worthy of your entrance",
            "heading": "Step into a safer world with ZAKEY",
            "description": "Discover smart locks that combine flexible entry with elegant design, for a home that feels easier every day.",
            "image": {"alt": "A ZAKEY smart lock on a modern home entrance"},
            "metrics": [
                {"label": "ways in", "value": "up to 5"},
                {"label": "planned installation coverage", "value": "3 governorates"},
                {"label": "planned free-shipping threshold", "value": "EGP 1,500+"},
            ],
            "primaryAction": {"label": "Shop the locks"},
            "secondaryAction": {"label": "Learn more"},
        },
        "promotion": {
            "heading": "Slimmer presence. Faster entry.",
            "description": "Explore the Nexus Elite, with its slim profile and the fingerprint reader built into the handle for quicker, easier entry.",
            "action": {"label": "See the product"},
            "image": {"alt": "The ZAKEY Nexus Elite in a light entrance space"},
        },
        "smartHome": {
            "eyebrow": "Smart home solutions",
            "heading": "One entrance, inside a connected home",
            "description": "Bring the lock, the camera and the entry accessories into one system for a clearer view and easier control of your entrance.",
            "image": {"alt": "A home entrance with a ZAKEY smart lock and camera"},
            "useCases": [
                {"title": "Family entry", "description": "Flexible ways in for everyone in the household."},
                {"title": "See your visitor", "description": "Built-in camera and doorbell, so you know who is at the door."},
                {"title": "Everyday security", "description": "Auto-locking and alerts that let you leave the house with confidence."},
            ],
        },
        "whyChoose": {
            "eyebrow": "Why ZAKEY?",
            "heading": "Considered detail, for a more confident decision",
            "items": [
                {"title": "A clear comparison", "description": "Price, size, entry methods and availability in one place."},
                {"title": "Built for Egypt", "description": "Arabic-language support, prices in pounds and local address options."},
                {"title": "Easy for everyone", "description": "Ordered information and clear steps, from comparison to choice."},
                {"title": "Design that suits your home", "description": "Modern finishes and considered detail to suit different entrances."},
            ],
        },
        "trustStrip": [
            {"title": "Security-led design", "description": "Clear information that helps you compare the ways in."},
            {"title": "A clear installation plan", "description": "Coverage targeted at launch in Cairo, Giza and Alexandria."},
            {"title": "A simple shipping policy", "description": "Free shipping planned for eligible orders when the service launches."},
            {"title": "Support in Arabic", "description": "Clear information before and after the sale, to help you choose the right solution."},
            {"title": "Choose with confidence", "description": "Specifications, prices and service options laid out before you decide."},
        ],
        "reviewsHeading": "Solutions that fit the detail of your day",
        "partnersHeading": "Solutions for every space",
        "newsletterHeading": "Everything new from ZAKEY, in one email",
    },
    "about": {
        "hero": {
            "eyebrow": "The ZAKEY story",
            "heading": "Making door security simpler and smarter",
            "description": "ZAKEY is a brand specialising in smart entry, combining practical technology with design that suits the detail of the Egyptian home.",
            "image": {"alt": "A modern home entrance expressing the ZAKEY vision"},
        },
        "stats": [
            {"label": "solutions in the catalogue", "value": "9"},
            {"label": "governorates in the address list", "value": "27"},
            {"label": "governorates targeted for installation", "value": "3"},
            {"label": "Arabic-language experience", "value": "100%"},
        ],
        "mission": {
            "eyebrow": "Our mission",
            "heading": "Technology you understand. Security you can rely on.",
            "body": "We select smart entry solutions that are easy to use, and present their specifications and installation options clearly, so every customer reaches the lock that suits their door and their needs.",
            "image": {"alt": "Smart lock detail on a wooden door"},
        },
        "teamHeading": "Expertise working towards one goal",
        "prototypeNotice": "We bring together product understanding, security needs, customer service and quality assurance to deliver one complete experience.",
    },
    "footer": {
        "copyright": "© 2026 ZAKEY. All rights reserved.",
        "description": "Smart lock solutions designed for a safer, easier home.",
        "legalLinks": [{"label": "Privacy policy"}, {"label": "Terms of use"}],
    },
    "contact": {
        "eyebrow": "Contact ZAKEY",
        "heading": "We are here to help",
        "description": "Tell us what you need, so we can walk you through choosing the right product before the support channels launch.",
        "hours": "Support hours will be announced at launch",
        "form": {
            "heading": "Send your enquiry",
            "submitLabel": "Review message",
            "successMessage": "Your message is ready. Actual sending is not available in the current preview build.",
            "fields": {
                "name": "Name",
                "email": "Email",
                "phone": "Egyptian mobile number",
                "message": "Your message",
                "subject": "Subject",
            },
        },
        "chatCard": {
            "heading": "Need a quick answer?",
            "actionLabel": "Start your enquiry",
            "description": "Start your enquiry and we will put together the information you need.",
        },
        "methodCards": [
            {"title": "Choosing a product", "detail": "Compare the lock that suits your door and your family's needs."},
            {"title": "Installation plan", "detail": "Learn the survey steps and the areas targeted for the service."},
            {"title": "After-sales information", "detail": "Usage and maintenance guidance, and the planned warranty policy."},
        ],
        "prototypeNotice": "The preview build does not send messages; what you type here will not be stored.",
    },
    "team": {
        "members": [
            {"name": "Product design", "role": "Technology that is easy to use",
             "bio": "We turn complex security features into a clear experience, down to the detail.",
             "image": {"alt": "The product design team"}},
            {"name": "Security solutions", "role": "A fit for every door",
             "bio": "We review the entry needs and the nature of the space to reach the most suitable solution.",
             "image": {"alt": "The security solutions team"}},
            {"name": "Customer service", "role": "Clear support in Arabic",
             "bio": "We help customers understand the options and the steps, before and after the purchase.",
             "image": {"alt": "The customer service team"}},
            {"name": "Quality assurance", "role": "Consistent information",
             "bio": "We look after the quality of the experience and the information, from page to product.",
             "image": {"alt": "The quality assurance team"}},
        ]
    },
}

#: FAQs, keyed by the stable legacy id.
FAQS = {
    "faq-door-fit": (
        "How do I know the lock fits my door?",
        "Compare your door's thickness and opening direction against the specifications. When the installation service launches, a survey will confirm the fit before fitting.",
    ),
    "faq-power": (
        "What happens when the battery gets low?",
        "The lock warns you well before the battery runs out, and each product page sets out the backup power option available for it.",
    ),
    "faq-installation": (
        "Where will the installation service be available?",
        "The coverage planned at launch includes specific addresses in Cairo, Giza and Alexandria, and requires confirmation.",
    ),
    "faq-camera": (
        "Are the camera images stored?",
        "Viewing and storage depend on the product and its settings. The current build of the site stores no images or recordings.",
    ),
    "faq-connectivity": (
        "How does the ZAKEY bridge work with the locks?",
        "The bridge is designed to manage compatible locks from one place. The actual connectivity features are enabled when the service launches.",
    ),
    "faq-unavailable": (
        "Can I buy a product that is unavailable?",
        "No. The product information stays visible for review while the purchase actions are clearly disabled.",
    ),
    "faq-shipping": (
        "When is shipping free?",
        "Shipping becomes free once the subtotal reaches EGP 1,500, under the policy shown.",
    ),
    "faq-payment": (
        "Are the payment methods shown active?",
        "No. Every payment method is a preview interface option and performs no transfer, charge or order.",
    ),
}


class Command(BaseCommand):
    help = "Fill the English (_en) columns for the demonstration catalogue."

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Replace existing English copy instead of only filling blanks.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        overwrite = options["overwrite"]
        written = 0

        def apply(instance, **values) -> bool:
            """Set the named `_en` fields, skipping any already translated."""
            changed = []
            for field, value in values.items():
                if not value:
                    continue
                if not overwrite and (getattr(instance, field, "") or "").strip():
                    continue
                setattr(instance, field, value)
                changed.append(field)
            if changed:
                instance.save(update_fields=changed)
            return bool(changed)

        from apps.catalog.models import Brand, Category, Collection, Product
        from apps.content.models import NavigationItem
        from apps.core.models import SiteSetting
        from apps.payments.models import PaymentMethod
        from apps.catalog.models import ProductVariant
        from apps.shipping.models import Governorate, InstallationService, ShippingMethod

        for slug, (name, description) in CATEGORIES.items():
            for category in Category.objects.filter(slug=slug):
                written += apply(category, name_en=name, description_en=description)

        for slug, (name, description, eyebrow) in COLLECTIONS.items():
            for collection in Collection.objects.filter(slug=slug):
                written += apply(
                    collection,
                    name_en=name,
                    description_en=description,
                    promotion_eyebrow_en=eyebrow,
                )

        for slug, (name, short, badge) in PRODUCTS.items():
            for product in Product.objects.filter(slug=slug):
                written += apply(
                    product,
                    name_en=name,
                    short_description_en=short,
                    badge_en=badge,
                    seo_title_en=name,
                    seo_description_en=short,
                )

        for brand in Brand.objects.all():
            # The brand is a Latin word already; the English column exists so the
            # page does not fall back and mix scripts mid-sentence.
            written += apply(brand, name_en=brand.name)

        for label, english in NAVIGATION.items():
            for item in NavigationItem.objects.filter(label=label):
                written += apply(item, label_en=english)

        for code, (label, description) in SHIPPING_METHODS.items():
            for method in ShippingMethod.objects.filter(code=code):
                written += apply(method, label_en=label, description_en=description)

        for code, (label, description, notice) in PAYMENT_METHODS.items():
            for method in PaymentMethod.objects.filter(code=code):
                written += apply(
                    method, label_en=label, description_en=description, notice_en=notice
                )

        for key, english in GOVERNORATES.items():
            for governorate in Governorate.objects.filter(key=key):
                written += apply(governorate, name_en=english)

        for service in InstallationService.objects.all():
            written += apply(service, name_en=INSTALLATION)

        from apps.catalog.models import ProductFeature, SpecificationGroup

        for key, (label, description) in FEATURES.items():
            for feature in ProductFeature.objects.filter(key=key):
                written += apply(
                    feature, label_en=label, description_en=description
                )

        for arabic, english in FINISHES.items():
            for variant in ProductVariant.objects.filter(finish_label=arabic):
                written += apply(variant, finish_label_en=english)

        for arabic, english in SPECIFICATION_GROUPS.items():
            for group in SpecificationGroup.objects.filter(label=arabic):
                written += apply(group, label_en=english)

        from apps.catalog.models import SpecificationItem

        for arabic, english in SPECIFICATION_LABELS.items():
            for item in SpecificationItem.objects.filter(label=arabic):
                written += apply(item, label_en=english)

        for arabic, english in SPECIFICATION_VALUES.items():
            for item in SpecificationItem.objects.filter(value=arabic):
                written += apply(item, value_en=english)

        for arabic, english in INSTALMENT_MESSAGES.items():
            for product in Product.objects.filter(instalment_message=arabic):
                written += apply(product, instalment_message_en=english)

        from apps.content.models import Partner

        for arabic, english in PARTNERS.items():
            for partner in Partner.objects.filter(name=arabic):
                written += apply(partner, name_en=english)

        from apps.reviews.models import Review

        for legacy_id, (author, title, body) in REVIEWS.items():
            for review in Review.objects.filter(legacy_id=legacy_id):
                written += apply(
                    review, author_name_en=author, title_en=title, body_en=body
                )

        from apps.catalog.models import ProductDocument

        for arabic, english in DOCUMENT_LABELS.items():
            for document in ProductDocument.objects.filter(label=arabic):
                written += apply(document, label_en=english)

        for arabic, english in DOCUMENT_NOTICES.items():
            for document in ProductDocument.objects.filter(notice=arabic):
                written += apply(document, notice_en=english)

        from apps.content.models import FAQ, HomeSection

        for legacy_id, (question, answer) in FAQS.items():
            for faq in FAQ.objects.filter(legacy_id=legacy_id):
                written += apply(faq, question_en=question, answer_en=answer)

        for key, overlay in PAGE_COPY.items():
            for section in HomeSection.objects.filter(key=key):
                if section.data_en and not overwrite:
                    continue
                section.data_en = overlay
                section.save(update_fields=["data_en"])
                written += 1

        setting = SiteSetting.objects.get_solo()
        written += apply(setting, currency_label_en=CURRENCY_LABEL)

        self.stdout.write(
            self.style.SUCCESS(f"English demo copy written to {written} record(s).")
        )
        self.stdout.write(
            "Anything still untranslated renders its Arabic source, which is the "
            "designed fallback. Fill the remaining '(إنجليزي)' fields in the admin."
        )
