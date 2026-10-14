import uvicorn # type: ignore

from api import app
from config import FASTAPI_PORT

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=FASTAPI_PORT)