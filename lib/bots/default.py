import asyncio
import argparse
from .bot import Bot

async def main():
    parser = argparse.ArgumentParser(description="Codex")
    parser.add_argument("-u", "--url", type=str, help="Room URL", required=True)
    parser.add_argument("-t", "--token", type=str, help="Room token", required=True)
    parser.add_argument("-d", "--document", type=str, help="Document ID", required=True)

    args = parser.parse_args()
    bot = Bot(args.url, args.token, args.document)
    await bot.create_transport()
    await bot.create_pipeline()
    await bot.start()

if __name__ == "__main__":
    asyncio.run(main())