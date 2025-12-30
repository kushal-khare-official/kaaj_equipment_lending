-- SQL Script to insert lender programs from PDF documentation
-- Generated from: Citizens Bank, Advantage+ Financing, Apex Commercial Capital, Falcon Equipment Finance, Stearns Bank
--
-- Available field_keys for criteria (from feature_derivation.py):
--   guarantor.fico, guarantor.cdl_flag, guarantor.homeownership
--   business.paynet_score, business.revolving_utilization, business.time_in_business_years (derived from incorporation_date)
--   loan.amount, loan.term_months, loan.down_payment
--   equipment.X.age_years, equipment.X.mileage, equipment.X.type, equipment.X.titled, equipment.X.private_party
--   application.state
--
-- Operators: range (uses value_min/value_max), in/not_in (uses values JSON array), eq, gte, lte, contains, boolean
-- Data types: int, decimal, string, bool

-- ============================================================================
-- CLEAR EXISTING DATA (comment out if you want to append)
-- ============================================================================
DELETE FROM lender_criteria;
DELETE FROM lender_programs;
DELETE FROM lenders;

-- ============================================================================
-- 1. CITIZENS BANK - Equipment Finance Program 2025
-- Source: 112025 Rates - STANDARD.pdf
-- ============================================================================
INSERT INTO lenders (id, name, created_at, updated_at)
VALUES (
    'cb000001-0000-0000-0000-000000000001',
    'Citizens Bank',
    datetime('now'),
    datetime('now')
);

-- Tier 1: General Program - $75,000 App Only
INSERT INTO lender_programs (id, lender_id, name, description, term_min, term_max, term_default, term_used_equipment, interest_rate_min, interest_rate_max, interest_rate_default, created_at, updated_at)
VALUES (
    'cbp00001-0000-0000-0000-000000000001',
    'cb000001-0000-0000-0000-000000000001',
    'Tier 1 - General Program',
    'Application Only up to $75,000 total relationship. 2+ years TIB, 700+ FICO (Transunion), homeownership required, CDL required if needed.',
    24, 60, 60, 48,
    NULL, NULL, NULL,
    datetime('now'),
    datetime('now')
);

INSERT INTO lender_criteria (id, program_id, field_key, data_type, operator, value_min, value_max, "values", description, created_at, updated_at)
VALUES
    (lower(hex(randomblob(16))), 'cbp00001-0000-0000-0000-000000000001', 'guarantor.fico', 'int', 'range', '700', '850', NULL, 'Minimum 700+ Transunion FICO score', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'cbp00001-0000-0000-0000-000000000001', 'business.time_in_business_years', 'int', 'range', '2', '100', NULL, '2+ years time in business required', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'cbp00001-0000-0000-0000-000000000001', 'loan.amount', 'int', 'range', '1', '75000', NULL, 'Max $75,000 application only', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'cbp00001-0000-0000-0000-000000000001', 'guarantor.homeownership', 'bool', 'boolean', 'true', NULL, NULL, 'Homeownership required', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'cbp00001-0000-0000-0000-000000000001', 'application.state', 'string', 'not_in', NULL, NULL, '["CA"]', 'California not accepted', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'cbp00001-0000-0000-0000-000000000001', 'equipment.0.mileage', 'int', 'range', '0', '600000', NULL, 'Max 600,000 miles for Class 8 trucks', datetime('now'), datetime('now'));

-- Tier 2: Start-up Program - $50,000 App Only
INSERT INTO lender_programs (id, lender_id, name, description, term_min, term_max, term_default, term_used_equipment, interest_rate_min, interest_rate_max, interest_rate_default, created_at, updated_at)
VALUES (
    'cbp00002-0000-0000-0000-000000000002',
    'cb000001-0000-0000-0000-000000000001',
    'Tier 2 - Start-up Program',
    'Application Only up to $50,000 for startups. 700+ FICO, 5 years CDL for trucking or 5 years industry experience, homeownership required, GPS required.',
    24, 60, 60, 48,
    NULL, NULL, NULL,
    datetime('now'),
    datetime('now')
);

INSERT INTO lender_criteria (id, program_id, field_key, data_type, operator, value_min, value_max, "values", description, created_at, updated_at)
VALUES
    (lower(hex(randomblob(16))), 'cbp00002-0000-0000-0000-000000000002', 'guarantor.fico', 'int', 'range', '700', '850', NULL, 'Minimum 700+ Transunion FICO score', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'cbp00002-0000-0000-0000-000000000002', 'loan.amount', 'int', 'range', '1', '50000', NULL, 'Max $50,000 application only for startups', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'cbp00002-0000-0000-0000-000000000002', 'guarantor.homeownership', 'bool', 'boolean', 'true', NULL, NULL, 'Homeownership required', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'cbp00002-0000-0000-0000-000000000002', 'guarantor.cdl_flag', 'bool', 'boolean', 'true', NULL, NULL, 'Class A CDL for 5 years required for trucking', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'cbp00002-0000-0000-0000-000000000002', 'application.state', 'string', 'not_in', NULL, NULL, '["CA"]', 'California not accepted', datetime('now'), datetime('now'));

-- Tier 2: Non-Homeowner Program - $50,000 App Only
INSERT INTO lender_programs (id, lender_id, name, description, term_min, term_max, term_default, term_used_equipment, interest_rate_min, interest_rate_max, interest_rate_default, created_at, updated_at)
VALUES (
    'cbp00003-0000-0000-0000-000000000003',
    'cb000001-0000-0000-0000-000000000001',
    'Tier 2 - Non-Homeowner Program',
    'Application Only up to $50,000 for non-homeowners. 700+ FICO, 5 years at current residence, 2 years TIB required, GPS required.',
    24, 60, 60, 48,
    NULL, NULL, NULL,
    datetime('now'),
    datetime('now')
);

INSERT INTO lender_criteria (id, program_id, field_key, data_type, operator, value_min, value_max, "values", description, created_at, updated_at)
VALUES
    (lower(hex(randomblob(16))), 'cbp00003-0000-0000-0000-000000000003', 'guarantor.fico', 'int', 'range', '700', '850', NULL, 'Minimum 700+ Transunion FICO score', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'cbp00003-0000-0000-0000-000000000003', 'business.time_in_business_years', 'int', 'range', '2', '100', NULL, '2+ years time in business required', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'cbp00003-0000-0000-0000-000000000003', 'loan.amount', 'int', 'range', '1', '50000', NULL, 'Max $50,000 application only', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'cbp00003-0000-0000-0000-000000000003', 'application.state', 'string', 'not_in', NULL, NULL, '["CA"]', 'California not accepted', datetime('now'), datetime('now'));

-- Tier 3: Full Financials Program - $75,000 to $1,000,000
INSERT INTO lender_programs (id, lender_id, name, description, term_min, term_max, term_default, term_used_equipment, interest_rate_min, interest_rate_max, interest_rate_default, created_at, updated_at)
VALUES (
    'cbp00004-0000-0000-0000-000000000004',
    'cb000001-0000-0000-0000-000000000001',
    'Tier 3 - Full Financials Program',
    'Full financials required for $75,000-$1,000,000. Requires 2 years business and personal tax returns, PFS, debt schedule, 3 months bank statements.',
    24, 60, 60, 48,
    NULL, NULL, NULL,
    datetime('now'),
    datetime('now')
);

INSERT INTO lender_criteria (id, program_id, field_key, data_type, operator, value_min, value_max, "values", description, created_at, updated_at)
VALUES
    (lower(hex(randomblob(16))), 'cbp00004-0000-0000-0000-000000000004', 'loan.amount', 'int', 'range', '75000', '1000000', NULL, '$75,000 to $1,000,000 with full financials', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'cbp00004-0000-0000-0000-000000000004', 'application.state', 'string', 'not_in', NULL, NULL, '["CA"]', 'California not accepted', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'cbp00004-0000-0000-0000-000000000004', 'equipment.0.mileage', 'int', 'range', '0', '600000', NULL, 'Max 600,000 miles for Class 8 trucks', datetime('now'), datetime('now'));


-- ============================================================================
-- 2. ADVANTAGE+ FINANCING - Broker Program (Non-Trucking up to $75,000)
-- Source: 2025 Program Guidelines UPDATED.pdf
-- ============================================================================
INSERT INTO lenders (id, name, created_at, updated_at)
VALUES (
    'af000001-0000-0000-0000-000000000001',
    'Advantage+ Financing',
    datetime('now'),
    datetime('now')
);

-- Standard Program (2+ years TIB)
INSERT INTO lender_programs (id, lender_id, name, description, term_min, term_max, term_default, term_used_equipment, interest_rate_min, interest_rate_max, interest_rate_default, created_at, updated_at)
VALUES (
    'afp00001-0000-0000-0000-000000000001',
    'af000001-0000-0000-0000-000000000001',
    'Standard Program - Established Business',
    'Non-trucking equipment up to $75,000. Minimum 680 FICO (Equifax v5), 3 years industry experience, 10% down payment. No bankruptcies, judgements, foreclosures, or repossessions.',
    24, 60, 60, 48,
    NULL, NULL, NULL,
    datetime('now'),
    datetime('now')
);

INSERT INTO lender_criteria (id, program_id, field_key, data_type, operator, value_min, value_max, "values", description, created_at, updated_at)
VALUES
    (lower(hex(randomblob(16))), 'afp00001-0000-0000-0000-000000000001', 'guarantor.fico', 'int', 'range', '680', '850', NULL, 'Minimum 680 FICO v5 (Equifax)', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'afp00001-0000-0000-0000-000000000001', 'loan.amount', 'int', 'range', '10000', '75000', NULL, '$10,000 to $75,000 loan amount', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'afp00001-0000-0000-0000-000000000001', 'business.time_in_business_years', 'int', 'range', '2', '100', NULL, '2+ years time in business (tax returns not required)', datetime('now'), datetime('now'));

-- Start-Up Program
INSERT INTO lender_programs (id, lender_id, name, description, term_min, term_max, term_default, term_used_equipment, interest_rate_min, interest_rate_max, interest_rate_default, created_at, updated_at)
VALUES (
    'afp00002-0000-0000-0000-000000000002',
    'af000001-0000-0000-0000-000000000001',
    'Start-Up Program',
    'Non-trucking equipment up to $75,000 for startups. Minimum 700 FICO, 3 years industry experience, 10% down + 10% security deposit. Prior year personal taxes required.',
    24, 60, 60, 48,
    NULL, NULL, NULL,
    datetime('now'),
    datetime('now')
);

INSERT INTO lender_criteria (id, program_id, field_key, data_type, operator, value_min, value_max, "values", description, created_at, updated_at)
VALUES
    (lower(hex(randomblob(16))), 'afp00002-0000-0000-0000-000000000002', 'guarantor.fico', 'int', 'range', '700', '850', NULL, 'Minimum 700 FICO for startups', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'afp00002-0000-0000-0000-000000000002', 'loan.amount', 'int', 'range', '10000', '75000', NULL, '$10,000 to $75,000 loan amount', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'afp00002-0000-0000-0000-000000000002', 'business.time_in_business_years', 'int', 'range', '0', '2', NULL, 'Start-up business (less than 2 years)', datetime('now'), datetime('now'));


-- ============================================================================
-- 3. APEX COMMERCIAL CAPITAL - Equipment Finance
-- Source: Apex EF Broker Guidelines_082725.pdf
-- ============================================================================
INSERT INTO lenders (id, name, created_at, updated_at)
VALUES (
    'ax000001-0000-0000-0000-000000000001',
    'Apex Commercial Capital',
    datetime('now'),
    datetime('now')
);

-- A Rate Program - App Only up to $200,000
INSERT INTO lender_programs (id, lender_id, name, description, term_min, term_max, term_default, term_used_equipment, interest_rate_min, interest_rate_max, interest_rate_default, created_at, updated_at)
VALUES (
    'axp00001-0000-0000-0000-000000000001',
    'ax000001-0000-0000-0000-000000000001',
    'A Rate Program',
    'App-only up to $200,000. 5 years TIB, 660+ PayNet, 700+ FICO, 50% revolving available. Tax returns required over $200K.',
    24, 60, 60, 48,
    7.25, 7.75, 7.50,
    datetime('now'),
    datetime('now')
);

INSERT INTO lender_criteria (id, program_id, field_key, data_type, operator, value_min, value_max, "values", description, created_at, updated_at)
VALUES
    (lower(hex(randomblob(16))), 'axp00001-0000-0000-0000-000000000001', 'guarantor.fico', 'int', 'range', '700', '850', NULL, 'Minimum 700+ FICO', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00001-0000-0000-0000-000000000001', 'business.paynet_score', 'int', 'range', '660', '999', NULL, 'Minimum 660+ PayNet', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00001-0000-0000-0000-000000000001', 'business.time_in_business_years', 'int', 'range', '5', '100', NULL, '5+ years time in business', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00001-0000-0000-0000-000000000001', 'loan.amount', 'int', 'range', '10000', '500000', NULL, '$10,000 to $500,000 (app-only up to $200K)', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00001-0000-0000-0000-000000000001', 'business.revolving_utilization', 'decimal', 'range', '0', '50', NULL, '50% revolving available (max 50% utilization)', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00001-0000-0000-0000-000000000001', 'application.state', 'string', 'not_in', NULL, NULL, '["CA","NV","ND","VT"]', 'Does not lend in CA, NV, ND, VT', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00001-0000-0000-0000-000000000001', 'equipment.0.age_years', 'int', 'range', '0', '15', NULL, 'Equipment max 15 years old', datetime('now'), datetime('now'));

-- B Rate Program - App Only up to $100,000
INSERT INTO lender_programs (id, lender_id, name, description, term_min, term_max, term_default, term_used_equipment, interest_rate_min, interest_rate_max, interest_rate_default, created_at, updated_at)
VALUES (
    'axp00002-0000-0000-0000-000000000002',
    'ax000001-0000-0000-0000-000000000001',
    'B Rate Program',
    'App-only up to $100,000. 3 years TIB, 650+ PayNet, 670+ FICO, 50% revolving available. Tax returns required over $100K.',
    24, 60, 60, 48,
    8.25, 8.75, 8.50,
    datetime('now'),
    datetime('now')
);

INSERT INTO lender_criteria (id, program_id, field_key, data_type, operator, value_min, value_max, "values", description, created_at, updated_at)
VALUES
    (lower(hex(randomblob(16))), 'axp00002-0000-0000-0000-000000000002', 'guarantor.fico', 'int', 'range', '670', '850', NULL, 'Minimum 670+ FICO', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00002-0000-0000-0000-000000000002', 'business.paynet_score', 'int', 'range', '650', '999', NULL, 'Minimum 650+ PayNet', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00002-0000-0000-0000-000000000002', 'business.time_in_business_years', 'int', 'range', '3', '100', NULL, '3+ years time in business', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00002-0000-0000-0000-000000000002', 'loan.amount', 'int', 'range', '10000', '250000', NULL, '$10,000 to $250,000 (app-only up to $100K)', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00002-0000-0000-0000-000000000002', 'business.revolving_utilization', 'decimal', 'range', '0', '50', NULL, '50% revolving available (max 50% utilization)', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00002-0000-0000-0000-000000000002', 'application.state', 'string', 'not_in', NULL, NULL, '["CA","NV","ND","VT"]', 'Does not lend in CA, NV, ND, VT', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00002-0000-0000-0000-000000000002', 'equipment.0.age_years', 'int', 'range', '0', '15', NULL, 'Equipment max 15 years old', datetime('now'), datetime('now'));

-- C Rate Program
INSERT INTO lender_programs (id, lender_id, name, description, term_min, term_max, term_default, term_used_equipment, interest_rate_min, interest_rate_max, interest_rate_default, created_at, updated_at)
VALUES (
    'axp00003-0000-0000-0000-000000000003',
    'ax000001-0000-0000-0000-000000000001',
    'C Rate Program',
    'For businesses with 2 years TIB. 640+ PayNet, 640+ FICO. 3 months bank statements required with submission.',
    24, 60, 60, 48,
    11.00, 12.00, 11.50,
    datetime('now'),
    datetime('now')
);

INSERT INTO lender_criteria (id, program_id, field_key, data_type, operator, value_min, value_max, "values", description, created_at, updated_at)
VALUES
    (lower(hex(randomblob(16))), 'axp00003-0000-0000-0000-000000000003', 'guarantor.fico', 'int', 'range', '640', '850', NULL, 'Minimum 640+ FICO', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00003-0000-0000-0000-000000000003', 'business.paynet_score', 'int', 'range', '640', '999', NULL, 'Minimum 640+ PayNet', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00003-0000-0000-0000-000000000003', 'business.time_in_business_years', 'int', 'range', '2', '100', NULL, '2+ years time in business', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00003-0000-0000-0000-000000000003', 'loan.amount', 'int', 'range', '10000', '100000', NULL, '$10,000 to $100,000', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00003-0000-0000-0000-000000000003', 'application.state', 'string', 'not_in', NULL, NULL, '["CA","NV","ND","VT"]', 'Does not lend in CA, NV, ND, VT', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00003-0000-0000-0000-000000000003', 'equipment.0.age_years', 'int', 'range', '0', '15', NULL, 'Equipment max 15 years old', datetime('now'), datetime('now'));

-- Medical A Rate Program
INSERT INTO lender_programs (id, lender_id, name, description, term_min, term_max, term_default, term_used_equipment, interest_rate_min, interest_rate_max, interest_rate_default, created_at, updated_at)
VALUES (
    'axp00004-0000-0000-0000-000000000004',
    'ax000001-0000-0000-0000-000000000001',
    'Medical A Rate Program',
    'For licensed medical professionals (MD, DO, DMD, DDS, OD, DPM, DVM, VMD). 5 years licensed, 700+ FICO, essential use equipment.',
    24, 60, 60, 48,
    7.00, 7.25, 7.00,
    datetime('now'),
    datetime('now')
);

INSERT INTO lender_criteria (id, program_id, field_key, data_type, operator, value_min, value_max, "values", description, created_at, updated_at)
VALUES
    (lower(hex(randomblob(16))), 'axp00004-0000-0000-0000-000000000004', 'guarantor.fico', 'int', 'range', '700', '850', NULL, 'Minimum 700+ FICO', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00004-0000-0000-0000-000000000004', 'business.time_in_business_years', 'int', 'range', '5', '100', NULL, '5+ years licensed', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00004-0000-0000-0000-000000000004', 'loan.amount', 'int', 'range', '10000', '500000', NULL, '$10,000 to $500,000 (app-only up to $200K)', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00004-0000-0000-0000-000000000004', 'business.revolving_utilization', 'decimal', 'range', '0', '50', NULL, '50% revolving available (max 50% utilization)', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00004-0000-0000-0000-000000000004', 'application.state', 'string', 'not_in', NULL, NULL, '["CA","NV","ND","VT"]', 'Does not lend in CA, NV, ND, VT', datetime('now'), datetime('now'));

-- A+ Rate Program
INSERT INTO lender_programs (id, lender_id, name, description, term_min, term_max, term_default, term_used_equipment, interest_rate_min, interest_rate_max, interest_rate_default, created_at, updated_at)
VALUES (
    'axp00005-0000-0000-0000-000000000005',
    'ax000001-0000-0000-0000-000000000001',
    'A+ Rate Program',
    'Premium rates for select industries. 5 years TIB, 670+ PayNet, 720+ FICO. Max 5 year equipment age. No private party sales.',
    24, 60, 60, 48,
    6.50, 6.75, 6.50,
    datetime('now'),
    datetime('now')
);

INSERT INTO lender_criteria (id, program_id, field_key, data_type, operator, value_min, value_max, "values", description, created_at, updated_at)
VALUES
    (lower(hex(randomblob(16))), 'axp00005-0000-0000-0000-000000000005', 'guarantor.fico', 'int', 'range', '720', '850', NULL, 'Minimum 720+ FICO', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00005-0000-0000-0000-000000000005', 'business.paynet_score', 'int', 'range', '670', '999', NULL, 'Minimum 670+ PayNet', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00005-0000-0000-0000-000000000005', 'business.time_in_business_years', 'int', 'range', '5', '100', NULL, '5+ years time in business', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00005-0000-0000-0000-000000000005', 'loan.amount', 'int', 'range', '10000', '500000', NULL, '$10,000 to $500,000 (app-only up to $200K)', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00005-0000-0000-0000-000000000005', 'business.revolving_utilization', 'decimal', 'range', '0', '50', NULL, '50% revolving available (max 50% utilization)', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00005-0000-0000-0000-000000000005', 'application.state', 'string', 'not_in', NULL, NULL, '["CA","NV","ND","VT"]', 'Does not lend in CA, NV, ND, VT', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00005-0000-0000-0000-000000000005', 'equipment.0.age_years', 'int', 'range', '0', '5', NULL, 'Equipment max 5 years old', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00005-0000-0000-0000-000000000005', 'equipment.0.private_party', 'bool', 'boolean', 'false', NULL, NULL, 'No private party sales', datetime('now'), datetime('now'));

-- Corp Only Program
INSERT INTO lender_programs (id, lender_id, name, description, term_min, term_max, term_default, term_used_equipment, interest_rate_min, interest_rate_max, interest_rate_default, created_at, updated_at)
VALUES (
    'axp00006-0000-0000-0000-000000000006',
    'ax000001-0000-0000-0000-000000000001',
    'Corp Only Program',
    'No personal guarantee required. 5+ years TIB, $3MM+ annual sales, 2 years tax returns, 3 months bank statements, profitability required.',
    24, 60, 60, 48,
    7.00, 7.00, 7.00,
    datetime('now'),
    datetime('now')
);

INSERT INTO lender_criteria (id, program_id, field_key, data_type, operator, value_min, value_max, "values", description, created_at, updated_at)
VALUES
    (lower(hex(randomblob(16))), 'axp00006-0000-0000-0000-000000000006', 'business.time_in_business_years', 'int', 'range', '5', '100', NULL, '5+ years in business', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00006-0000-0000-0000-000000000006', 'loan.amount', 'int', 'range', '10000', '500000', NULL, '$10,000 to $500,000', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00006-0000-0000-0000-000000000006', 'application.state', 'string', 'not_in', NULL, NULL, '["CA","NV","ND","VT"]', 'Does not lend in CA, NV, ND, VT', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'axp00006-0000-0000-0000-000000000006', 'equipment.0.age_years', 'int', 'range', '0', '15', NULL, 'Equipment max 15 years old', datetime('now'), datetime('now'));


-- ============================================================================
-- 4. FALCON EQUIPMENT FINANCE - Rates & Programs November 2025
-- Source: EF Credit Box 4.14.2025.pdf (Falcon's file naming in docs)
-- ============================================================================
INSERT INTO lenders (id, name, created_at, updated_at)
VALUES (
    'fe000001-0000-0000-0000-000000000001',
    'Falcon Equipment Finance',
    datetime('now'),
    datetime('now')
);

-- A Credit Program
INSERT INTO lender_programs (id, lender_id, name, description, term_min, term_max, term_default, term_used_equipment, interest_rate_min, interest_rate_max, interest_rate_default, created_at, updated_at)
VALUES (
    'fep00001-0000-0000-0000-000000000001',
    'fe000001-0000-0000-0000-000000000001',
    'A Credit Program',
    '3+ years TIB, 680+ FICO, 660+ PayNet, 70% comparable credit. BK discharged 15+ years. App-only up to $250K commercial, $350K manufacturing.',
    24, 60, 60, 48,
    7.75, 9.00, 8.25,
    datetime('now'),
    datetime('now')
);

INSERT INTO lender_criteria (id, program_id, field_key, data_type, operator, value_min, value_max, "values", description, created_at, updated_at)
VALUES
    (lower(hex(randomblob(16))), 'fep00001-0000-0000-0000-000000000001', 'guarantor.fico', 'int', 'range', '680', '850', NULL, 'Minimum 680+ FICO', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'fep00001-0000-0000-0000-000000000001', 'business.paynet_score', 'int', 'range', '660', '999', NULL, 'Minimum 660+ PayNet', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'fep00001-0000-0000-0000-000000000001', 'business.time_in_business_years', 'int', 'range', '3', '100', NULL, '3+ years time in business', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'fep00001-0000-0000-0000-000000000001', 'loan.amount', 'int', 'range', '15000', '350000', NULL, '$15,000 to $350,000 (varies by industry)', datetime('now'), datetime('now'));

-- B Credit Program
INSERT INTO lender_programs (id, lender_id, name, description, term_min, term_max, term_default, term_used_equipment, interest_rate_min, interest_rate_max, interest_rate_default, created_at, updated_at)
VALUES (
    'fep00002-0000-0000-0000-000000000002',
    'fe000001-0000-0000-0000-000000000001',
    'B Credit Program',
    '3+ years TIB, 680+ FICO, 660+ PayNet. Similar to A but slightly higher rates.',
    24, 60, 60, 48,
    8.25, 9.75, 9.00,
    datetime('now'),
    datetime('now')
);

INSERT INTO lender_criteria (id, program_id, field_key, data_type, operator, value_min, value_max, "values", description, created_at, updated_at)
VALUES
    (lower(hex(randomblob(16))), 'fep00002-0000-0000-0000-000000000002', 'guarantor.fico', 'int', 'range', '680', '850', NULL, 'Minimum 680+ FICO', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'fep00002-0000-0000-0000-000000000002', 'business.paynet_score', 'int', 'range', '660', '999', NULL, 'Minimum 660+ PayNet', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'fep00002-0000-0000-0000-000000000002', 'business.time_in_business_years', 'int', 'range', '3', '100', NULL, '3+ years time in business', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'fep00002-0000-0000-0000-000000000002', 'loan.amount', 'int', 'range', '15000', '350000', NULL, '$15,000 to $350,000', datetime('now'), datetime('now'));

-- C Credit Program
INSERT INTO lender_programs (id, lender_id, name, description, term_min, term_max, term_default, term_used_equipment, interest_rate_min, interest_rate_max, interest_rate_default, created_at, updated_at)
VALUES (
    'fep00003-0000-0000-0000-000000000003',
    'fe000001-0000-0000-0000-000000000001',
    'C Credit Program',
    'Near-prime borrowers. Lower credit requirements with higher rates.',
    24, 60, 60, 48,
    9.00, 10.50, 10.00,
    datetime('now'),
    datetime('now')
);

INSERT INTO lender_criteria (id, program_id, field_key, data_type, operator, value_min, value_max, "values", description, created_at, updated_at)
VALUES
    (lower(hex(randomblob(16))), 'fep00003-0000-0000-0000-000000000003', 'guarantor.fico', 'int', 'range', '640', '850', NULL, 'Minimum 640+ FICO', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'fep00003-0000-0000-0000-000000000003', 'business.paynet_score', 'int', 'range', '620', '999', NULL, 'Minimum 620+ PayNet', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'fep00003-0000-0000-0000-000000000003', 'business.time_in_business_years', 'int', 'range', '3', '100', NULL, '3+ years time in business', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'fep00003-0000-0000-0000-000000000003', 'loan.amount', 'int', 'range', '15000', '150000', NULL, '$15,000 to $150,000', datetime('now'), datetime('now'));

-- D Credit Program
INSERT INTO lender_programs (id, lender_id, name, description, term_min, term_max, term_default, term_used_equipment, interest_rate_min, interest_rate_max, interest_rate_default, created_at, updated_at)
VALUES (
    'fep00004-0000-0000-0000-000000000004',
    'fe000001-0000-0000-0000-000000000001',
    'D Credit Program',
    'Sub-prime borrowers. Higher risk tolerance with elevated rates.',
    24, 60, 60, 48,
    10.00, 11.75, 11.00,
    datetime('now'),
    datetime('now')
);

INSERT INTO lender_criteria (id, program_id, field_key, data_type, operator, value_min, value_max, "values", description, created_at, updated_at)
VALUES
    (lower(hex(randomblob(16))), 'fep00004-0000-0000-0000-000000000004', 'guarantor.fico', 'int', 'range', '600', '850', NULL, 'Minimum 600+ FICO', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'fep00004-0000-0000-0000-000000000004', 'business.paynet_score', 'int', 'range', '580', '999', NULL, 'Minimum 580+ PayNet', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'fep00004-0000-0000-0000-000000000004', 'business.time_in_business_years', 'int', 'range', '3', '100', NULL, '3+ years time in business', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'fep00004-0000-0000-0000-000000000004', 'loan.amount', 'int', 'range', '15000', '150000', NULL, '$15,000 to $150,000', datetime('now'), datetime('now'));

-- E Credit Program
INSERT INTO lender_programs (id, lender_id, name, description, term_min, term_max, term_default, term_used_equipment, interest_rate_min, interest_rate_max, interest_rate_default, created_at, updated_at)
VALUES (
    'fep00005-0000-0000-0000-000000000005',
    'fe000001-0000-0000-0000-000000000001',
    'E Credit Program',
    'Highest risk tolerance program. Credit-challenged borrowers.',
    24, 60, 60, 48,
    12.00, 13.75, 13.00,
    datetime('now'),
    datetime('now')
);

INSERT INTO lender_criteria (id, program_id, field_key, data_type, operator, value_min, value_max, "values", description, created_at, updated_at)
VALUES
    (lower(hex(randomblob(16))), 'fep00005-0000-0000-0000-000000000005', 'guarantor.fico', 'int', 'range', '550', '850', NULL, 'Minimum 550+ FICO', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'fep00005-0000-0000-0000-000000000005', 'business.time_in_business_years', 'int', 'range', '3', '100', NULL, '3+ years time in business', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'fep00005-0000-0000-0000-000000000005', 'loan.amount', 'int', 'range', '15000', '150000', NULL, '$15,000 to $150,000', datetime('now'), datetime('now'));

-- Trucking Program (A/B Credits Only)
INSERT INTO lender_programs (id, lender_id, name, description, term_min, term_max, term_default, term_used_equipment, interest_rate_min, interest_rate_max, interest_rate_default, created_at, updated_at)
VALUES (
    'fep00006-0000-0000-0000-000000000006',
    'fe000001-0000-0000-0000-000000000001',
    'Trucking Program',
    'A/B Credits only. 5+ years TIB, 5+ trucks, 700+ FICO, 680+ PayNet. Class 8 10 years or newer, reefer trailers under 7 years.',
    24, 60, 60, 48,
    7.75, 9.75, 8.50,
    datetime('now'),
    datetime('now')
);

INSERT INTO lender_criteria (id, program_id, field_key, data_type, operator, value_min, value_max, "values", description, created_at, updated_at)
VALUES
    (lower(hex(randomblob(16))), 'fep00006-0000-0000-0000-000000000006', 'guarantor.fico', 'int', 'range', '700', '850', NULL, 'Minimum 700+ FICO for trucking', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'fep00006-0000-0000-0000-000000000006', 'business.paynet_score', 'int', 'range', '680', '999', NULL, 'Minimum 680+ PayNet for trucking', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'fep00006-0000-0000-0000-000000000006', 'business.time_in_business_years', 'int', 'range', '5', '100', NULL, '5+ years time in business', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'fep00006-0000-0000-0000-000000000006', 'loan.amount', 'int', 'range', '15000', '150000', NULL, '$15,000 to $150,000 app-only for trucking', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'fep00006-0000-0000-0000-000000000006', 'equipment.0.age_years', 'int', 'range', '0', '10', NULL, 'Class 8 trucks max 10 years old', datetime('now'), datetime('now'));


-- ============================================================================
-- 5. STEARNS BANK - Equipment Finance Credit Box
-- Source: EF Credit Box 4.14.2025.pdf
-- ============================================================================
INSERT INTO lenders (id, name, created_at, updated_at)
VALUES (
    'sb000001-0000-0000-0000-000000000001',
    'Stearns Bank',
    datetime('now'),
    datetime('now')
);

-- Tier 1 Program
INSERT INTO lender_programs (id, lender_id, name, description, term_min, term_max, term_default, term_used_equipment, interest_rate_min, interest_rate_max, interest_rate_default, created_at, updated_at)
VALUES (
    'sbp00001-0000-0000-0000-000000000001',
    'sb000001-0000-0000-0000-000000000001',
    'Tier 1 Program',
    'Best rates. 725+ FICO, 685+ PayNet, 3+ years TIB. No BK in last 7 years. Comparable debt required.',
    24, 60, 60, 48,
    NULL, NULL, NULL,
    datetime('now'),
    datetime('now')
);

INSERT INTO lender_criteria (id, program_id, field_key, data_type, operator, value_min, value_max, "values", description, created_at, updated_at)
VALUES
    (lower(hex(randomblob(16))), 'sbp00001-0000-0000-0000-000000000001', 'guarantor.fico', 'int', 'range', '725', '850', NULL, 'Minimum 725+ FICO', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'sbp00001-0000-0000-0000-000000000001', 'business.paynet_score', 'int', 'range', '685', '999', NULL, 'Minimum 685+ PayNet', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'sbp00001-0000-0000-0000-000000000001', 'business.time_in_business_years', 'int', 'range', '3', '100', NULL, '3+ years time in business', datetime('now'), datetime('now'));

-- Tier 2 Program
INSERT INTO lender_programs (id, lender_id, name, description, term_min, term_max, term_default, term_used_equipment, interest_rate_min, interest_rate_max, interest_rate_default, created_at, updated_at)
VALUES (
    'sbp00002-0000-0000-0000-000000000002',
    'sb000001-0000-0000-0000-000000000001',
    'Tier 2 Program',
    'Standard program. 710+ FICO, 675+ PayNet, 3+ years TIB. No BK in last 7 years.',
    24, 60, 60, 48,
    NULL, NULL, NULL,
    datetime('now'),
    datetime('now')
);

INSERT INTO lender_criteria (id, program_id, field_key, data_type, operator, value_min, value_max, "values", description, created_at, updated_at)
VALUES
    (lower(hex(randomblob(16))), 'sbp00002-0000-0000-0000-000000000002', 'guarantor.fico', 'int', 'range', '710', '850', NULL, 'Minimum 710+ FICO', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'sbp00002-0000-0000-0000-000000000002', 'business.paynet_score', 'int', 'range', '675', '999', NULL, 'Minimum 675+ PayNet', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'sbp00002-0000-0000-0000-000000000002', 'business.time_in_business_years', 'int', 'range', '3', '100', NULL, '3+ years time in business', datetime('now'), datetime('now'));

-- Tier 3 Program
INSERT INTO lender_programs (id, lender_id, name, description, term_min, term_max, term_default, term_used_equipment, interest_rate_min, interest_rate_max, interest_rate_default, created_at, updated_at)
VALUES (
    'sbp00003-0000-0000-0000-000000000003',
    'sb000001-0000-0000-0000-000000000001',
    'Tier 3 Program',
    'More flexible requirements. 700+ FICO, 665+ PayNet, 2+ years TIB. No BK in last 7 years.',
    24, 60, 60, 48,
    NULL, NULL, NULL,
    datetime('now'),
    datetime('now')
);

INSERT INTO lender_criteria (id, program_id, field_key, data_type, operator, value_min, value_max, "values", description, created_at, updated_at)
VALUES
    (lower(hex(randomblob(16))), 'sbp00003-0000-0000-0000-000000000003', 'guarantor.fico', 'int', 'range', '700', '850', NULL, 'Minimum 700+ FICO', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'sbp00003-0000-0000-0000-000000000003', 'business.paynet_score', 'int', 'range', '665', '999', NULL, 'Minimum 665+ PayNet', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'sbp00003-0000-0000-0000-000000000003', 'business.time_in_business_years', 'int', 'range', '2', '100', NULL, '2+ years time in business', datetime('now'), datetime('now'));

-- Tier 1 - No PayNet (higher FICO required)
INSERT INTO lender_programs (id, lender_id, name, description, term_min, term_max, term_default, term_used_equipment, interest_rate_min, interest_rate_max, interest_rate_default, created_at, updated_at)
VALUES (
    'sbp00004-0000-0000-0000-000000000004',
    'sb000001-0000-0000-0000-000000000001',
    'Tier 1 - No PayNet Program',
    'For businesses without PayNet score. 735+ FICO, 5+ years TIB. No BK in last 7 years.',
    24, 60, 60, 48,
    NULL, NULL, NULL,
    datetime('now'),
    datetime('now')
);

INSERT INTO lender_criteria (id, program_id, field_key, data_type, operator, value_min, value_max, "values", description, created_at, updated_at)
VALUES
    (lower(hex(randomblob(16))), 'sbp00004-0000-0000-0000-000000000004', 'guarantor.fico', 'int', 'range', '735', '850', NULL, 'Minimum 735+ FICO (no PayNet)', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'sbp00004-0000-0000-0000-000000000004', 'business.time_in_business_years', 'int', 'range', '5', '100', NULL, '5+ years time in business', datetime('now'), datetime('now'));

-- Tier 2 - No PayNet
INSERT INTO lender_programs (id, lender_id, name, description, term_min, term_max, term_default, term_used_equipment, interest_rate_min, interest_rate_max, interest_rate_default, created_at, updated_at)
VALUES (
    'sbp00005-0000-0000-0000-000000000005',
    'sb000001-0000-0000-0000-000000000001',
    'Tier 2 - No PayNet Program',
    'For businesses without PayNet score. 720+ FICO, 3+ years TIB. No BK in last 7 years.',
    24, 60, 60, 48,
    NULL, NULL, NULL,
    datetime('now'),
    datetime('now')
);

INSERT INTO lender_criteria (id, program_id, field_key, data_type, operator, value_min, value_max, "values", description, created_at, updated_at)
VALUES
    (lower(hex(randomblob(16))), 'sbp00005-0000-0000-0000-000000000005', 'guarantor.fico', 'int', 'range', '720', '850', NULL, 'Minimum 720+ FICO (no PayNet)', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'sbp00005-0000-0000-0000-000000000005', 'business.time_in_business_years', 'int', 'range', '3', '100', NULL, '3+ years time in business', datetime('now'), datetime('now'));

-- Tier 3 - No PayNet
INSERT INTO lender_programs (id, lender_id, name, description, term_min, term_max, term_default, term_used_equipment, interest_rate_min, interest_rate_max, interest_rate_default, created_at, updated_at)
VALUES (
    'sbp00006-0000-0000-0000-000000000006',
    'sb000001-0000-0000-0000-000000000001',
    'Tier 3 - No PayNet Program',
    'For businesses without PayNet score. 710+ FICO, 2+ years TIB. No BK in last 7 years.',
    24, 60, 60, 48,
    NULL, NULL, NULL,
    datetime('now'),
    datetime('now')
);

INSERT INTO lender_criteria (id, program_id, field_key, data_type, operator, value_min, value_max, "values", description, created_at, updated_at)
VALUES
    (lower(hex(randomblob(16))), 'sbp00006-0000-0000-0000-000000000006', 'guarantor.fico', 'int', 'range', '710', '850', NULL, 'Minimum 710+ FICO (no PayNet)', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'sbp00006-0000-0000-0000-000000000006', 'business.time_in_business_years', 'int', 'range', '2', '100', NULL, '2+ years time in business', datetime('now'), datetime('now'));

-- Corp Only - Tier 1
INSERT INTO lender_programs (id, lender_id, name, description, term_min, term_max, term_default, term_used_equipment, interest_rate_min, interest_rate_max, interest_rate_default, created_at, updated_at)
VALUES (
    'sbp00007-0000-0000-0000-000000000007',
    'sb000001-0000-0000-0000-000000000001',
    'Corp Only - Tier 1',
    'No personal guarantee. 700+ PayNet, 10+ years TIB. Strong business credit required.',
    24, 60, 60, 48,
    NULL, NULL, NULL,
    datetime('now'),
    datetime('now')
);

INSERT INTO lender_criteria (id, program_id, field_key, data_type, operator, value_min, value_max, "values", description, created_at, updated_at)
VALUES
    (lower(hex(randomblob(16))), 'sbp00007-0000-0000-0000-000000000007', 'business.paynet_score', 'int', 'range', '700', '999', NULL, 'Minimum 700+ PayNet', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'sbp00007-0000-0000-0000-000000000007', 'business.time_in_business_years', 'int', 'range', '10', '100', NULL, '10+ years time in business', datetime('now'), datetime('now'));

-- Corp Only - Tier 2
INSERT INTO lender_programs (id, lender_id, name, description, term_min, term_max, term_default, term_used_equipment, interest_rate_min, interest_rate_max, interest_rate_default, created_at, updated_at)
VALUES (
    'sbp00008-0000-0000-0000-000000000008',
    'sb000001-0000-0000-0000-000000000001',
    'Corp Only - Tier 2',
    'No personal guarantee. 690+ PayNet, 5+ years TIB.',
    24, 60, 60, 48,
    NULL, NULL, NULL,
    datetime('now'),
    datetime('now')
);

INSERT INTO lender_criteria (id, program_id, field_key, data_type, operator, value_min, value_max, "values", description, created_at, updated_at)
VALUES
    (lower(hex(randomblob(16))), 'sbp00008-0000-0000-0000-000000000008', 'business.paynet_score', 'int', 'range', '690', '999', NULL, 'Minimum 690+ PayNet', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'sbp00008-0000-0000-0000-000000000008', 'business.time_in_business_years', 'int', 'range', '5', '100', NULL, '5+ years time in business', datetime('now'), datetime('now'));

-- Corp Only - Tier 3
INSERT INTO lender_programs (id, lender_id, name, description, term_min, term_max, term_default, term_used_equipment, interest_rate_min, interest_rate_max, interest_rate_default, created_at, updated_at)
VALUES (
    'sbp00009-0000-0000-0000-000000000009',
    'sb000001-0000-0000-0000-000000000001',
    'Corp Only - Tier 3',
    'No personal guarantee. 680+ PayNet, 5+ years TIB.',
    24, 60, 60, 48,
    NULL, NULL, NULL,
    datetime('now'),
    datetime('now')
);

INSERT INTO lender_criteria (id, program_id, field_key, data_type, operator, value_min, value_max, "values", description, created_at, updated_at)
VALUES
    (lower(hex(randomblob(16))), 'sbp00009-0000-0000-0000-000000000009', 'business.paynet_score', 'int', 'range', '680', '999', NULL, 'Minimum 680+ PayNet', datetime('now'), datetime('now')),
    (lower(hex(randomblob(16))), 'sbp00009-0000-0000-0000-000000000009', 'business.time_in_business_years', 'int', 'range', '5', '100', NULL, '5+ years time in business', datetime('now'), datetime('now'));


-- ============================================================================
-- VERIFICATION QUERIES (run these after INSERT to verify data)
-- ============================================================================
-- SELECT 'Lenders:' as '';
-- SELECT name FROM lenders;
--
-- SELECT '' as '';
-- SELECT 'Programs per lender:' as '';
-- SELECT l.name as lender, COUNT(p.id) as programs
-- FROM lenders l
-- LEFT JOIN lender_programs p ON l.id = p.lender_id
-- GROUP BY l.name;
--
-- SELECT '' as '';
-- SELECT 'Criteria per program:' as '';
-- SELECT l.name as lender, p.name as program, COUNT(c.id) as criteria
-- FROM lenders l
-- JOIN lender_programs p ON l.id = p.lender_id
-- LEFT JOIN lender_criteria c ON p.id = c.program_id
-- GROUP BY l.name, p.name;
