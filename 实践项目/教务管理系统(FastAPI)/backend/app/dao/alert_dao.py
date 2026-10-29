"""学业预警 DAO"""
from app.model.alert_record import AlertRecord
from app.dao.base_dao import BaseDAO


class AlertDAO(BaseDAO[AlertRecord]):
    def __init__(self):
        super().__init__(AlertRecord)


alert_dao = AlertDAO()
