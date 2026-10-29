import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test():
    e = create_async_engine('mysql+aiomysql://root:root@localhost:3306/edu_management?charset=utf8mb4')
    async with e.connect() as c:
        r = await c.execute(text('SELECT real_name FROM users WHERE id=1'))
        row = r.fetchone()
        val = row[0]
        print(f"repr: {repr(val)}")
        print(f"type: {type(val)}")
        print(f"print: {val}")
        print(f"utf8 bytes: {val.encode('utf-8')}")
        await c.commit()
    await e.dispose()

asyncio.run(test())
