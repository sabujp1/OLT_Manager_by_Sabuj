import logging
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import User, UserRole
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)

async def seed_initial_data(db: AsyncSession) -> None:
    """Seeds the initial superuser if the database is empty."""
    try:
        # Check if any user exists
        result = await db.execute(select(User))
        user = result.scalars().first()
        
        if not user:
            logger.info("No users found in database. Seeding default super admin user...")
            
            default_admin = User(
                email="admin@oltnoc.local",
                full_name="NOC Administrator",
                hashed_password=get_password_hash("admin123"),
                role=UserRole.SUPER_ADMIN,
                is_active=True
            )
            db.add(default_admin)
            await db.commit()
            logger.info("Successfully seeded default super admin: admin@oltnoc.local / admin123")
        else:
            logger.info("Database already contains user accounts. Seeding skipped.")
            
    except Exception as e:
        logger.error(f"Error seeding initial database: {str(e)}")
        await db.rollback()
