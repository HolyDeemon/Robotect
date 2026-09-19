import asyncio
import os
from dotenv import load_dotenv
from subprocess import Popen
import uvicorn

def shutdown_rest_of_app(_, __):
    raise KeyboardInterrupt

def main():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        load_dotenv()

        PORT = int(os.getenv("LOGIN_PORT", 6000))

        web_config = uvicorn.Config(
            "LOGIN.main_login:app",
            host = "127.0.0.1",
            port=PORT,
            loop="asyncio",
            workers=4,
         )
        web_server = uvicorn.Server(config=web_config)
        loop.create_task(web_server.serve())
        loop.run_forever()
    except KeyboardInterrupt:
        print("Caught Ctrl+C. Exiting gracefully.")


if __name__ == "__main__":
    main()