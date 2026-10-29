"""成绩 DAO"""
from app.model.score import Score
from app.model.score_log import ScoreLog
from app.dao.base_dao import BaseDAO
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal


class ScoreDAO(BaseDAO[Score]):
    def __init__(self):
        super().__init__(Score)

    async def log_change(self, db: AsyncSession, score_id: int, old_score: Decimal, new_score: Decimal, operator_id: int):
        log = ScoreLog(score_id=score_id, old_score=old_score, new_score=new_score, operator_id=operator_id)
        db.add(log)


score_dao = ScoreDAO()
