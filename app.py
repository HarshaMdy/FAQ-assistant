from index import app, application

# Alias for Vercel auto-detection of app.py
if __name__ == "__main__":
    from index import run_server
    run_server()
