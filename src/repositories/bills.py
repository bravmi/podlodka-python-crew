from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import functions

import models


class Bill(BaseModel):
    description: str
    total_amount: float

    payer_id: int
    group_id: int

    shares: dict[int, float]


def create_bill(session: AsyncSession, bill_in: Bill) -> models.Bill:
    bill = models.Bill(
        description=bill_in.description,
        total_amount=bill_in.total_amount,
        payer_id=bill_in.payer_id,
        group_id=bill_in.group_id,
    )
    for user_id, amount in bill_in.shares.items():
        bill.shares.append(models.BillShare(user_id=user_id, amount=amount))
    session.add(bill)
    return bill


async def get_bill(session: AsyncSession, bill_id: int) -> models.Bill | None:
    pass
