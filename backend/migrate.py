import asyncio
from database import engine
from sqlalchemy import text

async def main():
    try:
        async with engine.begin() as conn:
            await conn.execute(text("ALTER TABLE audio_tasks ADD COLUMN user_id INT NOT NULL DEFAULT 0;"))
            await conn.execute(text("CREATE INDEX ix_audio_tasks_user_id ON audio_tasks (user_id);"))
            print("Successfully added user_id column.")
    except Exception as e:
        print(f"Error (maybe column already exists): {e}")

if __name__ == "__main__":
    asyncio.run(main())
