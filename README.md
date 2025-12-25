Demo- https://drive.google.com/file/d/1RfG3tZSBw7dEEFz4bVVh0yGYZiAqTp9A/view?usp=sharing

Got it. Based on your repo structure and what you’re saying (“**python app.py worked**”), your project is being run as a **Flask app**, not Streamlit (even if we tried Streamlit earlier). Your screenshot of `app = Flask(__name__)` also matches Flask.

So here is the clean, correct, end-to-end checklist to run **GDG Agent (Ollama + LinkedIn Draft Generator)** exactly the way you’ve been running it.

---

## GDG Agent — Setup + Run Steps (Clean Summary)

### 0) Pre-req: Ollama must be running

1. Install Ollama (once).
2. Pull your model (once), example:

```bash
ollama pull llama3
```

3. Quick test:

```bash
ollama run llama3
```

If the model responds, Ollama side is fine.

---

## 1) Go to your project root

From your screenshots your project is inside `demo/` and code is in `GDG-Agent/`.

```bash
cd ~/Desktop/demo/GDG-Agent
```

Confirm you see:

* `app.py`
* `agent.py`
* `pipeline.py`
* `drafts/`
* `templates/`
* `static/`

---

## 2) Activate the existing venv (the one you already use)

You said your venv is created at `demo/.venv` (one level above GDG-Agent).

So activate it like this:

```bash
cd ~/Desktop/demo
source .venv/bin/activate
cd GDG-Agent
```

Your terminal should show:

```bash
(.venv) ... GDG-Agent %
```

---

## 3) Install dependencies in that same environment (one time)

Run these inside `(.venv)`:

```bash
pip install flask ollama
```

If your project uses extra packages (sometimes requests/dotenv), safest minimal add-ons:

```bash
pip install python-dotenv requests
```

Optional verification:

```bash
python -c "import flask; import ollama; print('OK')"
```

---

## 4) Run the application (the way you said works)

You said this works for you:

```bash
python app.py
```

If it’s a Flask app, it will print something like:

* Running on `http://127.0.0.1:5000` (or similar)

Open that URL in the browser.

---

## 5) What happens when you use the UI

* You enter your LinkedIn prompt/topic in the UI
* The backend calls:

  * `pipeline.py` (orchestrates)
  * which uses `agent.py` (talks to Ollama)
* Final output is saved to:

  * `drafts/` folder (you already confirmed this is happening)

---

## 6) Quick troubleshooting checklist (most common)

### A) If Ollama errors / model not found

Run:

```bash
ollama list
```

Then ensure your app is using a model that exists (e.g., `llama3`).

### B) If Flask module missing

```bash
pip install flask
```

### C) If port already in use

Mac will often keep 5000 busy. Run on another port:

```bash
export PORT=5001
python app.py
```

(Only if your `app.py` reads PORT; if not, we’ll change one line.)

### D) If drafts folder missing

Create it once:

```bash
mkdir -p drafts
```

---

## The exact “daily run” sequence (copy-paste)

This is the minimal sequence you will use every time:

```bash
cd ~/Desktop/demo
source .venv/bin/activate
cd GDG-Agent
python app.py
```
