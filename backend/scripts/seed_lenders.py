import uuid

from sqlalchemy.orm import Session

from app.models.lender import Lender, LenderProgram, LenderCriteria
from app.db import SessionLocal


def seed_lenders(session: Session):
    """
    Seed multiple lender programs with diverse term and rate configurations.
    This demonstrates how different lenders offer different terms based on equipment age and credit quality.
    """
    
    # Clear existing lenders (for development)
    session.query(LenderCriteria).delete()
    session.query(LenderProgram).delete()
    session.query(Lender).delete()
    session.commit()
    
    # Lender 1: Premier Finance (Best rates, longest terms, strictest criteria)
    lender1 = Lender(name="Premier Finance")
    program1 = LenderProgram(
        name="Prime Equipment Finance",
        description="Best rates for prime borrowers with new equipment",
        lender=lender1,
        term_min=12,
        term_max=84,  # Up to 7 years for new equipment
        term_default=72,  # 6 years default
        term_used_equipment=60,  # 5 years for used
        interest_rate_min=5.99,
        interest_rate_max=9.99,
        interest_rate_default=7.49,
    )
    program1.criteria = [
        LenderCriteria(
            field_key="guarantor.fico",
            data_type="int",
            operator="range",
            value_min="720",
            value_max="850",
            description="Excellent personal credit (FICO 720+)",
        ),
        LenderCriteria(
            field_key="business.paynet_score",
            data_type="int",
            operator="range",
            value_min="750",
            value_max="900",
            description="Strong business credit (PayNet 750+)",
        ),
        LenderCriteria(
            field_key="loan.amount",
            data_type="int",
            operator="range",
            value_min="25000",
            value_max="500000",
            description="Loan amount $25K - $500K",
        ),
    ]
    session.add(lender1)
    
    # Lender 2: Advantage Capital (Moderate rates, flexible terms)
    lender2 = Lender(name="Advantage Capital")
    program2 = LenderProgram(
        name="Standard Equipment Financing",
        description="Competitive rates for qualified borrowers",
        lender=lender2,
        term_min=12,
        term_max=72,  # Up to 6 years
        term_default=60,  # 5 years default
        term_used_equipment=48,  # 4 years for used
        interest_rate_min=7.49,
        interest_rate_max=11.99,
        interest_rate_default=9.49,
    )
    program2.criteria = [
        LenderCriteria(
            field_key="guarantor.fico",
            data_type="int",
            operator="range",
            value_min="680",
            value_max="850",
            description="Good personal credit (FICO 680+)",
        ),
        LenderCriteria(
            field_key="business.paynet_score",
            data_type="int",
            operator="range",
            value_min="650",
            value_max="900",
            description="Acceptable business credit (PayNet 650+)",
        ),
        LenderCriteria(
            field_key="loan.amount",
            data_type="int",
            operator="range",
            value_min="15000",
            value_max="350000",
            description="Loan amount $15K - $350K",
        ),
    ]
    session.add(lender2)
    
    # Lender 3: Quick Capital (Higher rates, shorter terms, lenient criteria)
    lender3 = Lender(name="Quick Capital Solutions")
    program3 = LenderProgram(
        name="Fast Approval Program",
        description="Quick funding for near-prime borrowers",
        lender=lender3,
        term_min=12,
        term_max=48,  # Up to 4 years
        term_default=36,  # 3 years default
        term_used_equipment=36,  # Same for used
        interest_rate_min=10.99,
        interest_rate_max=16.99,
        interest_rate_default=13.49,
    )
    program3.criteria = [
        LenderCriteria(
            field_key="guarantor.fico",
            data_type="int",
            operator="range",
            value_min="640",
            value_max="850",
            description="Fair personal credit (FICO 640+)",
        ),
        LenderCriteria(
            field_key="business.paynet_score",
            data_type="int",
            operator="range",
            value_min="600",
            value_max="900",
            description="Fair business credit (PayNet 600+)",
        ),
        LenderCriteria(
            field_key="loan.amount",
            data_type="int",
            operator="range",
            value_min="10000",
            value_max="200000",
            description="Loan amount $10K - $200K",
        ),
    ]
    session.add(lender3)
    
    # Lender 4: Startup-friendly lender (accepts no business credit history)
    lender4 = Lender(name="Growth Capital Partners")
    program4 = LenderProgram(
        name="Startup & New Business Program",
        description="Financing for startups based on personal credit",
        lender=lender4,
        term_min=12,
        term_max=60,  # Up to 5 years
        term_default=48,  # 4 years default
        term_used_equipment=36,  # 3 years for used
        interest_rate_min=9.99,
        interest_rate_max=14.99,
        interest_rate_default=11.99,
    )
    program4.criteria = [
        LenderCriteria(
            field_key="guarantor.fico",
            data_type="int",
            operator="range",
            value_min="700",
            value_max="850",
            description="Good personal credit (FICO 700+)",
        ),
        LenderCriteria(
            field_key="loan.amount",
            data_type="int",
            operator="range",
            value_min="20000",
            value_max="250000",
            description="Loan amount $20K - $250K",
        ),
        # Note: No business credit requirement - good for startups
    ]
    session.add(lender4)
    
    # Lender 5: Regional lender with state restrictions
    lender5 = Lender(name="Midwest Equipment Finance")
    program5 = LenderProgram(
        name="Regional Standard Program",
        description="Serving Midwest businesses with competitive terms",
        lender=lender5,
        term_min=12,
        term_max=72,  # Up to 6 years
        term_default=60,  # 5 years default
        term_used_equipment=48,  # 4 years for used
        interest_rate_min=6.99,
        interest_rate_max=10.99,
        interest_rate_default=8.49,
    )
    program5.criteria = [
        LenderCriteria(
            field_key="guarantor.fico",
            data_type="int",
            operator="range",
            value_min="690",
            value_max="850",
            description="Good personal credit (FICO 690+)",
        ),
        LenderCriteria(
            field_key="business.paynet_score",
            data_type="int",
            operator="range",
            value_min="700",
            value_max="900",
            description="Good business credit (PayNet 700+)",
        ),
        LenderCriteria(
            field_key="application.state",
            data_type="string",
            operator="in",
            values=["MN", "WI", "IA", "IL", "IN", "MI", "OH", "ND", "SD", "NE", "KS", "MO"],
            description="Midwest states only",
        ),
        LenderCriteria(
            field_key="loan.amount",
            data_type="int",
            operator="range",
            value_min="25000",
            value_max="400000",
            description="Loan amount $25K - $400K",
        ),
    ]
    session.add(lender5)
    
    session.commit()
    print("✅ Seeded 5 lenders with 5 programs")
    print("   - Premier Finance: 5.99%-9.99%, up to 84 months (prime borrowers)")
    print("   - Advantage Capital: 7.49%-11.99%, up to 72 months (standard)")
    print("   - Quick Capital Solutions: 10.99%-16.99%, up to 48 months (near-prime)")
    print("   - Growth Capital Partners: 9.99%-14.99%, up to 60 months (startups)")
    print("   - Midwest Equipment Finance: 6.99%-10.99%, up to 72 months (regional)")


def main():
    session = SessionLocal()
    try:
        seed_lenders(session)
    finally:
        session.close()


if __name__ == "__main__":
    main()

