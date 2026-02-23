"""Seed script - populates DB with SNPs, ONDC categories, demo MSEs, and indexes Qdrant.

Run: python seed.py
"""

import asyncio
import json
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from src.config import settings
from src.core.logging import setup_logging, log
from src.db.base import get_engine, Base
from src.db.session import get_session_factory
from src.db.models.snp import SNP
from src.db.models.ondc_category import OndcCategory
from src.db.models.user import User, UserRole
from src.db.models.mse import MSE, OnboardingStatus
from src.db.models.product import Product, ProductStatus
from src.db.models.mse_match import MSEMatch, MatchStatus
from src.core.security import hash_password


DATA_DIR = Path(__file__).parent / 'src' / 'data'


async def create_tables():
    """Create all DB tables."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info('Tables created')


async def seed_snps(db):
    """Seed SNP data from snp_seed.json."""
    from sqlalchemy import select
    result = await db.execute(select(SNP).limit(1))
    if result.scalar_one_or_none():
        log.info('SNPs already seeded, skipping')
        return

    with open(DATA_DIR / 'snp_seed.json', encoding='utf-8') as f:
        data = json.load(f)

    for snp_data in data['snps']:
        snp_data.pop('qdrant_description', None)
        snp = SNP(id=uuid.uuid4(), **snp_data)
        db.add(snp)

    await db.flush()
    log.info(f'Seeded {len(data["snps"])} SNPs')


async def seed_ondc_categories(db):
    """Seed ONDC taxonomy from ondc_taxonomy.json."""
    from sqlalchemy import select
    result = await db.execute(select(OndcCategory).limit(1))
    if result.scalar_one_or_none():
        log.info('ONDC categories already seeded, skipping')
        return

    with open(DATA_DIR / 'ondc_taxonomy.json', encoding='utf-8') as f:
        data = json.load(f)

    for cat_data in data['categories']:
        cat = OndcCategory(id=uuid.uuid4(), **cat_data)
        db.add(cat)

    await db.flush()
    log.info(f'Seeded {len(data["categories"])} ONDC categories')


async def seed_demo_mses(db):
    """Seed 3 demo MSE profiles for demo."""
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.mobile == '9876543210'))
    if result.scalar_one_or_none():
        log.info('Demo MSEs already seeded, skipping')
        return

    demos = [
        {
            'user': {'mobile': '9876543210', 'role': 'mse'},
            'mse': {
                'udyam_number': 'UDYAM-MH-01-0012345',
                'business_name': 'Sharma Brass Works',
                'owner_name': 'Rajesh Sharma',
                'nic_code': '25910',
                'major_activity': 'manufacturing',
                'state': 'Maharashtra',
                'district': 'Pune',
                'address': 'Plot 12, MIDC Bhosari, Pune - 411026',
                'turnover': 5000000,
                'employee_count': 12,
                'transaction_type': 'b2c',
                'target_states': ['Maharashtra', 'Gujarat', 'Delhi'],
                'whatsapp_number': '919876543210',
                'onboarding_status': 'catalogue_ready',
            },
            'products': [
                {
                    'raw_description': 'Brass diya handmade, Rs 150, MOQ 10, 5cm diameter',
                    'product_name': 'Handmade Brass Diya',
                    'ondc_category_code': 'ONDC:RET16',
                    'subcategory': 'Brass Handicrafts',
                    'attributes': {'product_name': 'Handmade Brass Diya', 'mrp': 150, 'material': 'Brass', 'dimensions_cm': '5x5x3', 'colour': 'Golden', 'country_of_origin': 'India', 'moq': 10},
                    'compliance_score': 100.0,
                    'missing_fields': [],
                    'status': 'ready',
                },
                {
                    'raw_description': 'Brass puja thali set, Rs 450',
                    'product_name': 'Brass Puja Thali Set',
                    'ondc_category_code': 'ONDC:RET16',
                    'subcategory': 'Brass Puja Items',
                    'attributes': {'product_name': 'Brass Puja Thali Set', 'mrp': 450, 'material': 'Brass', 'country_of_origin': 'India'},
                    'compliance_score': 57.1,
                    'missing_fields': ['dimensions_cm', 'colour', 'moq'],
                    'status': 'draft',
                },
            ],
        },
        {
            'user': {'mobile': '9876543211', 'role': 'mse'},
            'mse': {
                'udyam_number': 'UDYAM-TN-05-0067890',
                'business_name': 'Priya Textiles',
                'owner_name': 'Priya Venkataraman',
                'nic_code': '13111',
                'major_activity': 'manufacturing',
                'state': 'Tamil Nadu',
                'district': 'Kanchipuram',
                'address': 'No. 45, Silk Weavers Colony, Kanchipuram - 631502',
                'turnover': 3500000,
                'employee_count': 8,
                'transaction_type': 'both',
                'target_states': ['Tamil Nadu', 'Karnataka', 'Andhra Pradesh'],
                'whatsapp_number': '919876543211',
                'onboarding_status': 'profile_complete',
            },
            'products': [
                {
                    'raw_description': 'Kanchipuram silk saree, red and gold, Rs 8500',
                    'product_name': 'Kanchipuram Silk Saree',
                    'ondc_category_code': 'ONDC:RET12',
                    'subcategory': 'Handloom Sarees',
                    'attributes': {'product_name': 'Kanchipuram Silk Saree', 'mrp': 8500, 'material_fabric': 'Pure Silk', 'colour': 'Red and Gold', 'country_of_origin': 'India'},
                    'compliance_score': 71.4,
                    'missing_fields': ['size', 'care_instructions'],
                    'status': 'draft',
                },
            ],
        },
    {
        'user': {'mobile': '9876543212', 'role': 'mse'},
        'mse': {
            'udyam_number': 'UDYAM-UP-09-0034567',
            'business_name': 'Organic Farms Co',
            'owner_name': 'Ramesh Kumar',
            'nic_code': '10750',
            'major_activity': 'manufacturing',
            'state': 'Uttar Pradesh',
            'district': 'Lucknow',
            'address': 'Village Mallpur, Lucknow - 226012',
            'turnover': 2000000,
            'employee_count': 5,
            'transaction_type': 'b2b',
            'target_states': ['Uttar Pradesh', 'Bihar', 'Madhya Pradesh', 'Delhi'],
            'whatsapp_number': '919876543212',
            'onboarding_status': 'snp_selected',
        },
        'products': [
            {
                'raw_description': 'Organic turmeric powder, 500g pack, Rs 120, FSSAI: 10013022000596',
                'product_name': 'Organic Turmeric Powder',
                'ondc_category_code': 'ONDC:RET10',
                'subcategory': 'Spices',
                'attributes': {'product_name': 'Organic Turmeric Powder', 'mrp': 120, 'net_weight_or_volume': '500g', 'fssai_license_no': '10013022000596', 'country_of_origin': 'India', 'manufacturer_name': 'Organic Farms Co', 'brand': 'OrganicFarms', 'expiry_date': '2026-12-31'},
                'compliance_score': 100.0,
                'missing_fields': [],
                'status': 'ready',
            },
            {
                'raw_description': 'Mango pickle in mustard oil, 500g, Rs 85, traditional recipe',
                'product_name': 'Mango Pickle in Mustard Oil',
                'ondc_category_code': 'ONDC:RET11',
                'subcategory': 'Pickles',
                'attributes': {'product_name': 'Mango Pickle in Mustard Oil', 'mrp': 85, 'net_weight': '500g', 'ingredients': 'Raw mango, mustard oil, spices, salt', 'country_of_origin': 'India', 'manufacturer_name': 'Organic Farms Co'},
                'compliance_score': 75.0,
                'missing_fields': ['fssai_license_no', 'expiry_date'],
                'status': 'draft',
            },
        ],
    },
    ]

    for demo in demos:
        user = User(
            id=uuid.uuid4(),
            mobile=demo['user']['mobile'],
            role=demo['user']['role'],
            hashed_password=hash_password('demo1234'),
            is_active=True,
        )
        db.add(user)
        await db.flush()

        mse = MSE(id=uuid.uuid4(), user_id=user.id, **demo['mse'])
        db.add(mse)
        await db.flush()

        for prod_data in demo['products']:
            product = Product(id=uuid.uuid4(), mse_id=mse.id, source='web', **prod_data)
            db.add(product)

    # Seed SNP user for demo
    snp_user = User(
        id=uuid.uuid4(),
        mobile='9000000001',
        role='snp',
        hashed_password=hash_password('snpdemo'),
        is_active=True,
    )
    db.add(snp_user)

    # Seed admin user
    admin_user = User(
        id=uuid.uuid4(),
        mobile='9000000002',
        role='admin',
        hashed_password=hash_password('admindemo'),
        is_active=True,
    )
    db.add(admin_user)

    await db.flush()
    log.info('Seeded 3 demo MSEs + SNP user + Admin user')


async def index_qdrant():
    """Index ONDC taxonomy and SNP knowledge into Qdrant."""
    from src.rag.qdrant_search import QdrantSearch, TAXONOMY_COLLECTION, SNP_COLLECTION, KNOWLEDGE_COLLECTION

    # Index ONDC taxonomy
    with open(DATA_DIR / 'ondc_taxonomy.json', encoding='utf-8') as f:
        taxonomy = json.load(f)

    taxonomy_chunks = []
    for cat in taxonomy['categories']:
        text = (
            f'ONDC Category: {cat["code"]} - {cat["name"]}\n'
            f'Description: {cat["description"]}\n'
            f'MSE Types: {", ".join(cat["mse_types"])}\n'
            f'Required Attributes: {", ".join(cat["required_attributes"])}\n'
            f'Example Products: {", ".join(cat["example_products"])}'
        )
        taxonomy_chunks.append({'content': text, 'source': cat['code'], 'index': 0})

    QdrantSearch.index_chunks(taxonomy_chunks, source='ondc_taxonomy', collection_name=TAXONOMY_COLLECTION)
    log.info(f'Indexed {len(taxonomy_chunks)} taxonomy chunks')

    # Index SNP knowledge
    with open(DATA_DIR / 'snp_seed.json', encoding='utf-8') as f:
        snps = json.load(f)

    snp_chunks = []
    for snp in snps['snps']:
        desc = snp.get('qdrant_description') or snp['description']
        snp_chunks.append({'content': desc, 'source': snp['name'], 'index': 0})

    QdrantSearch.index_chunks(snp_chunks, source='snp_knowledge', collection_name=SNP_COLLECTION)
    log.info(f'Indexed {len(snp_chunks)} SNP knowledge chunks')

    # Index TEAM/ONDC knowledge for FAQ RAG
    knowledge_chunks = [
        {'content': 'TEAM Initiative (Trade Enablement and Marketing) is a Rs. 277.35 Crore scheme by Ministry of MSME implemented by NSIC. Goal is to onboard 5 lakh MSEs onto ONDC (50% women-led). Duration: FY2024-25 to FY2026-27. Portal: team.msmemart.com', 'source': 'team_overview', 'index': 0},
        {'content': 'MSE Eligibility for TEAM: 1. Valid Udyam Registration Number required. 2. Major activity must be Manufacturing or Services (NOT Trading). 3. Not already a seller on ONDC. 4. Not previously benefited from similar government scheme.', 'source': 'team_eligibility', 'index': 1},
        {'content': 'ONDC - Open Network for Digital Commerce. Like UPI but for commerce. Seller lists products on ONE SNP - product becomes visible on ALL buyer apps (Paytm, PhonePe, Magicpin). SNP (Seller Network Participant) manages your ONDC catalogue. MSE pays nothing - SNPs are paid by government.', 'source': 'ondc_overview', 'index': 2},
        {'content': 'SNP Incentives from TEAM: Rs. 2500 per MSE onboarded (catalogue support). Rs. 50 per SKU up to 50 SKUs (B2C). Rs. 125 per SKU up to 20 SKUs (B2B). This is why SNPs offer free onboarding to MSEs.', 'source': 'snp_incentives', 'index': 3},
        {'content': 'ONDC Retail Categories: RET10 Grocery, RET11 Food and Beverages, RET12 Fashion, RET13 Beauty and Personal Care, RET14 Electronics, RET15 Appliances, RET16 Home and Decor, RET17 Toys and Games, RET18 Health and Wellness, RET19 Pharma.', 'source': 'ondc_categories', 'index': 4},
        {'content': 'Legal requirements for ONDC products: E-Commerce Rules 2020 requires accurate product description, MRP, country of origin. Legal Metrology Act 2011 requires net quantity, MRP, manufacturing date, manufacturer name. FSSAI license mandatory for food products (RET10, RET11).', 'source': 'legal_compliance', 'index': 5},
        {'content': 'VyapaarSetu AI capabilities: 1. Multilingual voice-enabled registration (Hindi/English/Hinglish). 2. AI product categorization to ONDC RET codes with compliance validation. 3. Intelligent MSE to SNP matching based on categories, geography, B2B/B2C preference.', 'source': 'vyapaarsetu_features', 'index': 6},
    ]

    QdrantSearch.index_chunks(knowledge_chunks, source='team_knowledge', collection_name=KNOWLEDGE_COLLECTION)
    log.info(f'Indexed {len(knowledge_chunks)} TEAM/ONDC knowledge chunks')


async def main():
    setup_logging()
    log.info('Starting VyapaarSetu seed script...')

    await create_tables()

    session_factory = get_session_factory()
    async with session_factory() as db:
        await seed_ondc_categories(db)
        await seed_snps(db)
        await seed_demo_mses(db)
        await db.commit()

    log.info('DB seeding complete')

    try:
        await index_qdrant()
        log.info('Qdrant indexing complete')
    except Exception as e:
        log.warning(f'Qdrant indexing failed (is Qdrant running?): {e}')

    log.info('==================================================')
    log.info('SEED COMPLETE! Demo credentials:')
    log.info('MSE 1 (Brass): mobile=9876543210 password=demo1234')
    log.info('MSE 2 (Textiles): mobile=9876543211 password=demo1234')
    log.info('MSE 3 (Organic): mobile=9876543212 password=demo1234')
    log.info('SNP: mobile=9000000001 password=snpdemo')
    log.info('Admin: mobile=9000000002 password=admindemo')
    log.info('==================================================')


if __name__ == '__main__':
    asyncio.run(main())
