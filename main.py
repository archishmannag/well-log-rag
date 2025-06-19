import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        # "src.api.app:app",
        "tests.test_server.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=3,
        log_level="debug",
        use_colors=True,
    )
