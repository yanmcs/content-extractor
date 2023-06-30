import uvicorn
import sys


def start():
    if sys.platform == 'win32':
        uvicorn.run("app:app", host="localhost", port=5008, workers=1, reload=True)
    else:
        uvicorn.run("app:app", host="0.0.0.0", port=5008, workers=30)

if __name__ == "__main__":
    start() 