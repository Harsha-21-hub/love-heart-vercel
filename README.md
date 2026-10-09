# Love Heart — Vercel + FastAPI (Python)

This project is set up for Vercel's Python runtime and works in modern mobile and desktop browsers. The `app.py` entrypoint exposes the FastAPI app, and `main.py` generates the heart's SVG from Python and serves the mobile-friendly page.

## Important note about the supplied `love.py`

`love.py` is preserved **byte-for-byte** from the uploaded file. The original script uses `turtle` and `tkinter` to open and animate a desktop GUI window. Vercel Functions run headlessly and cannot show that desktop window to visitors, so importing/running that script unchanged is not a workable way to render the website. FastAPI does not bridge a Tkinter window into a browser.

For the live website, `main.py` retains the original composition's core design in Python (the parametric heart, multilingual phrases, colors, phrase placement, and animation timing) and serves a browser-renderable animated SVG. The browser does not need to run Python locally, so it works on Android over Wi-Fi or mobile data.

## Deploy to Vercel

1. Extract this ZIP.
2. Push all five files (`app.py`, `main.py`, `love.py`, `requirements.txt`, `vercel.json`, plus this README) to a GitHub repository.
3. In <https://vercel.com/>, choose **Add New → Project**, import that repository, and deploy with the defaults. Vercel's Python runtime supports FastAPI.
4. Open the generated `https://<project-name>.vercel.app` address on Android or share it.

No custom domain is required. To test the backend after deployment, open `/healthz`; it should return `{"status":"ok"}`. `/api/info` gives a little more detail about the generated animation.

## Local test

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app:app --reload
```

Then open <http://127.0.0.1:8000>.
