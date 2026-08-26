from django.db import migrations

def seed_ibisap_data(apps, schema_editor):
    IbiSAPConfiguration = apps.get_model('public_portal', 'IbiSAPConfiguration')
    IbiSAPScreenshot = apps.get_model('public_portal', 'IbiSAPScreenshot')
    IbiSAPComparisonRow = apps.get_model('public_portal', 'IbiSAPComparisonRow')

    # Seed Config
    IbiSAPConfiguration.objects.get_or_create(
        id=1,
        defaults={
            'hero_badge': 'Certified Nepal ERP • NRB & IRD CBMS Ready',
            'hero_title': "The Intelligent ERP for\nNepal's Regulated Enterprises",
            'hero_description': 'A high-performance, cost-effective alternative to SAP Business One. Built specifically for regulated Microfinance Institutions (MFIs), Cooperatives, Manufacturers, and Multi-Branch Retail Chains across Nepal.',
            'live_sandbox_url': 'https://ibisap.rajabhoj.com.np/login/?next=/',
            'live_sandbox_btn_text': 'Launch Live Cloud Sandbox',
            'metric_1_val': '80%',
            'metric_1_lbl': 'Lower TCO vs SAP B1',
            'metric_2_val': '100%',
            'metric_2_lbl': 'NRB IT Guidelines Compliant',
            'metric_3_val': 'v2.0',
            'metric_3_lbl': 'IRD CBMS Certified Sync',
            'metric_4_val': '2081',
            'metric_4_lbl': 'Native Nepali Miti (Bikram Sambat)',
            'enterprise_title': 'Enterprise IbiSAP',
            'enterprise_tagline': 'Engineered for Institutions Requiring Strict Data Sovereignty',
            'enterprise_desc': 'Designed for regulated microfinance institutions (MFIs), cooperatives, hospitals, and large enterprises requiring NRB IT compliance, dedicated PostgreSQL/SQL HANA database servers, and maker-checker workflows.',
            'enterprise_features': 'On-Premises & Private Cloud Deployment: Complete data sovereignty on your physical hardware or dedicated private virtual cluster.\nNRB IT Security Guidelines Compliant: Granular RBAC, dual-authorization (maker-checker), automated DRP backups, and immutable audit logs.\nNative Nepali Miti (Bikram Sambat) Engine: Dual-calendar fiscal accounting (Shrawan 1 to Ashadh 31) with bi-directional AD/BS conversion.\nCertified IRD CBMS Real-Time Invoicing: Direct REST API synchronization with the Inland Revenue Department with offline failover queues.\nDedicated PostgreSQL / SQL HANA Instance: Pessimistic row-level locking guaranteeing ledger transaction consistency.',
            'retail_title': 'Retail IbiSAP SaaS',
            'retail_tagline': 'Zero DevOps Overhead for Retail Chains & Distributors',
            'retail_desc': 'Built for retail stores, supermarkets, pharmacies, and distributors who want enterprise-grade billing, inventory, and accounting with instant 60-second onboarding and zero hardware maintenance.',
            'retail_features': 'Isolated Multi-Tenant Architecture: Centralized application master with isolated schema/database segregation for every registered tenant.\nHigh-Speed Point of Sale (POS) & Barcode: Sub-second barcode scanning, thermal slip printing, loyalty discounts, and integrated Fonepay QR.\nMulti-Branch Inventory & Expiry Alerts: Real-time stock valuation across warehouses with batch-level expiry monitoring and automated reorders.\nZero DevOps Maintenance & Automated Backups: Continuous encrypted cloud snapshots, 99.9% availability, and automatic seamless version upgrades.\nInstant 60-Second Onboarding: Sign up and start generating invoices immediately on any browser, tablet, or POS terminal.',
            'cta_headline': 'Request a Live Demo & Proposal',
            'cta_subheadline': 'Coordinate a live architectural walkthrough with sample dataset testing tailored to your institution.'
        }
    )

    # Seed Screenshots
    screenshots = [
        ('Executive Analytics Dashboard', 'Executive Analytics', 'Real-time liquidity monitoring, GL summaries, and branch performance indicators.', 'gallery/ibisap-dashboard.png', 1),
        ('Retail Cloud POS & High-Speed Billing', 'Retail Cloud POS', 'Fast thermal receipt printing, barcode scanning, and Fonepay QR integration.', 'gallery/ibisap-pos.png', 2),
        ('Nepali Miti & IRD CBMS Module', 'IRD Compliance', 'Shrawan 1 to Ashadh 31 fiscal periods with automated IRD API retry queues and bi-directional AD/BS conversion.', 'gallery/ibisap-nepali-miti.png', 3)
    ]
    for title, cat, desc, img, order in screenshots:
        IbiSAPScreenshot.objects.get_or_create(
            title=title,
            defaults={'category_tag': cat, 'description': desc, 'static_image_path': img, 'order': order, 'is_active': True}
        )

    # Seed Comparison Rows
    matrix = [
        ('Hosting & Topology', 'On-Premises Server or Dedicated Private Cloud', '100% Fully Managed Multi-Tenant Cloud SaaS', 1),
        ('Pricing & License Model', 'One-Time Perpetual License + Custom Annual SLA (Fraction of SAP B1)', 'Predictable Monthly / Annual Subscription per Branch', 2),
        ('Regulatory Compliance', 'Full NRB Unified Directives + Real-Time IRD CBMS Sync', 'Native Nepali Miti + IRD Approved Sales Invoicing', 3),
        ('Bespoke Customization', '100% Tailored Modules, Custom APIs & Legacy Migrations', 'Pre-configured modular settings with instant activation', 4),
        ('Database Engine', 'Dedicated PostgreSQL / SQL HANA instance with Row-Level Locking', 'Isolated Schema per Tenant (Automated Provisioning)', 5),
        ('Infrastructure Maintenance', 'Managed internally or via dedicated 24/7 SLA', 'Zero maintenance required; automatic rolling cloud updates', 6),
        ('Ideal Implementation', 'Regulated MFIs, Cooperatives, Hospitals, Mid-Enterprises', 'Retail Chains, Wholesalers, Distributors, Supermarkets', 7)
    ]
    for feat, ent, ret, order in matrix:
        IbiSAPComparisonRow.objects.get_or_create(
            feature_name=feat,
            defaults={'enterprise_value': ent, 'retail_value': ret, 'order': order}
        )


def reverse_seed(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('public_portal', '0010_ibisapcomparisonrow_ibisapconfiguration_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_ibisap_data, reverse_seed),
    ]
