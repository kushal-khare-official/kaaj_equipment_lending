import uuid

from sqlalchemy.orm import Session

from app.models.lender import Lender, LenderProgram, LenderCriteria
from app.db import SessionLocal


def seed_example(session: Session):
    lender = Lender(name="Sample Lender")
    program = LenderProgram(
        name="Standard",
        description="Sample program",
        lender=lender,
        term_min=12,
        term_max=84,
        term_default=60,
        term_used_equipment=48,
        interest_rate_min=6.5,
        interest_rate_max=12.5,
        interest_rate_default=8.5,
    )
    program.criteria = [
        LenderCriteria(
            field_key="guarantor.fico",
            data_type="int",
            operator="range",
            value_min="680",
            value_max="850",
            description="FICO between 680 and 850",
        ),
        LenderCriteria(
            field_key="business.paynet_score",
            data_type="int",
            operator="range",
            value_min="650",
            value_max="850",
            description="PayNet floor",
        ),
        LenderCriteria(
            field_key="application.state",
            data_type="string",
            operator="not_in",
            values=["CA"],
            description="Exclude CA",
        ),
    ]
    session.add(lender)
    session.commit()


def main():
    session = SessionLocal()
    try:
        seed_example(session)
        print("Seeded sample lender/program/criteria.")
    finally:
        session.close()


if __name__ == "__main__":
    main()

