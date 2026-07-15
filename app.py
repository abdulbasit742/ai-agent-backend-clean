from __future__ import annotations

import os

from dotenv import load_dotenv

from src import create_app

load_dotenv()
app = create_app()


if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("APP_ENV", "development").lower() == "development",
    )
