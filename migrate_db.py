import asyncio
from backend.database import engine
from sqlalchemy import text

async def alter_table():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE email_logs ADD COLUMN paraphrased_content VARCHAR NULL;"))
            print("Successfully added paraphrased_content column.")
        except Exception as e:
            if 'already exists' in str(e).lower() or 'duplicate column' in str(e).lower():
                print("Column already exists.")
            else:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(alter_table())
