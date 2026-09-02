import uuid

from sqlalchemy.orm import Session as DbSession

from ..models import User


def upsert(db: DbSession, user_id: uuid.UUID) -> None:
    """Add the user row if it is new. The caller owns the transaction.

    Flushed, not committed: the same transaction goes on to insert rows that
    reference this one, and the unit of work has no relationship() between the
    models to order the inserts from -- it would emit them alphabetically and
    trip the foreign key. A rollback still takes this row with it.
    """
    if not db.get(User, user_id):
        db.add(User(id=user_id))
        db.flush()
