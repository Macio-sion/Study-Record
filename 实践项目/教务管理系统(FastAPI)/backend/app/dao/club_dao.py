"""社团 DAO"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.model.club import Club
from app.model.club_member import ClubMember
from app.dao.base_dao import BaseDAO


class ClubDAO(BaseDAO[Club]):
    def __init__(self):
        super().__init__(Club)

    async def get_member(self, db: AsyncSession, club_id: int, student_id: int) -> ClubMember | None:
        result = await db.execute(
            select(ClubMember).where(ClubMember.club_id == club_id, ClubMember.student_id == student_id)
        )
        return result.scalar_one_or_none()


class ClubMemberDAO(BaseDAO[ClubMember]):
    def __init__(self):
        super().__init__(ClubMember)

    async def get_by_club(self, db: AsyncSession, club_id: int, page: int = 1, page_size: int = 20) -> tuple[list[ClubMember], int]:
        filters = [ClubMember.club_id == club_id]
        return await self.get_all(db, page=page, page_size=page_size, filters=filters, order_by=ClubMember.joined_at)


club_dao = ClubDAO()
club_member_dao = ClubMemberDAO()
