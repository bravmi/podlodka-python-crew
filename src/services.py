import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

import models
import repositories
import serializers

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    pass


class NotFoundError(Exception):
    pass


class AuthError(Exception):
    pass


async def create_user(user_in: serializers.UserIn, session: AsyncSession) -> models.User:
    user = repositories.users.create_user(session, user_in)
    try:
        await session.commit()
    except IntegrityError:
        raise ServiceError("User already exists")
    return user


async def create_group(
    group_in: serializers.GroupIn, user: models.User, session: AsyncSession
) -> models.Group:
    group = await repositories.groups.create_group(session, group_in)
    group.members.append(user)
    await session.commit()
    return group


async def get_group(
    group_id: int, user: models.User, session: AsyncSession
) -> models.Group | None:
    """Get group and test for membership"""
    group = await repositories.groups.get_by_id(session, group_id)
    if not group:
        raise NotFoundError(f'Group id={group_id} not found')
    if user not in group.members:
        raise AuthError(f'User id={user.id} is not a member of group id={group.id}')
    return group


async def add_member(
    user_id: int, group_id: int, session: AsyncSession
) -> models.Group | None:
    pass


async def create_bill(
    bill_in: serializers.BillIn, user: models.User, session: AsyncSession
) -> models.Bill:
    group = await get_group(bill_in.group_id, user, session)
    payer = user
    if bill_in.payer_id:
        payer = await repositories.users.get_by_id(session, bill_in.payer_id)

    participants = [member for member in group.members if member is not payer]
    if bill_in.shares:
        participants = await repositories.users.get_by_ids(
            session, [share.user_id for share in bill_in.shares]
        )

    shares = bill_in.shares or []
    defined_shares = {share.user_id: share.amount for share in shares if share.amount}
    defined_amounts = sum(defined_shares.values())
    default_amount = (bill_in.total_amount - defined_amounts) / (
        len(participants) - len(defined_shares) + 1  # payer
    )

    bill = repositories.bills.create_bill(
        session,
        repositories.bills.Bill(
            description=bill_in.description,
            total_amount=bill_in.total_amount,
            payer_id=payer.id,
            group_id=group.id,
            shares={
                participant.id: defined_shares.get(participant.id, default_amount)
                for participant in participants
            },
        ),
    )
    await session.commit()
    await session.refresh(bill)
    return bill


async def get_bill(
    bill_id: int, user: models.User, session: AsyncSession
) -> models.Bill | None:
    pass


async def get_amount_owed(bill_id: int, user: models.User, session: AsyncSession):
    raise NotImplementedError()


async def create_transaction(
    transaction_in: serializers.TransactionIn, user: models.User, session: AsyncSession
):
    await get_bill(transaction_in.bill_id, user, session)
    transaction = await repositories.transactions.add_transaction(
        session, transaction_in, user
    )
    await session.commit()
    return transaction
