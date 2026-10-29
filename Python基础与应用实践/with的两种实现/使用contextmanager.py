"""
@Author : Administrator
@Company : 
@Date : 2026/7/13 10:32
@Desc :
@Version : 1.0
"""
# 模拟cm管理session
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

engine = create_engine(
                url='mysql+pymysql://root:root@localhost:3306/test2026?charset=utf8mb4',
                pool_size=5,  # 初始池大小
                max_overflow=10,  # 最大池数量
                pool_timeout=30,  # 单服务超时时间，秒为单位。
                pool_recycle=3600,  # 峰值延缓恢复时间
                pool_pre_ping=True,  # 服务前测试单的网络连接是否存活
                echo=False  # 是否打印操作日志
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

@contextmanager
def get_session():
    print("获取session")
    session1 = SessionLocal()
    try:
        print("execute")
        yield session1
        session1.commit()
    except Exception as e:
        session1.rollback()
        raise e
    finally:
        print("session close")
        session1.close()

if __name__ == '__main__':
    with get_session() as session:
        session.execute(text("update bank_account set balance= balance - 100 where id=:id"), {
            "id": 1,
        })
        print("success")
        raise Exception("failed")
        session.execute(text("update bank_account set balance= balance + 100 where id=:id"), {
            "id": 2,
        })
        print("success")

    print("close Done")

