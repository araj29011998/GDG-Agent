import os
import platform
import subprocess
import json
import datetime

from flask import Flask, request, jsonify, render_template
import ollama

# --------- Config ---------
DRAFTS_DIR = "drafts"
MODEL_NAME = "llama3.2"

app = Flask(__name__)

# Keep track of last created file for "open last / close last"
last_created_path = None


# ---------- Utility functions for files ----------

def ensure_drafts_dir():
    os.makedirs(DRAFTS_DIR, exist_ok=True)


def create_draft_file(title, content):
    """Create a .txt file with the LinkedIn post content and return its path."""
    safe_title = "".join(
        c for c in title if c.isalnum() or c in ("-", "_", " ")
    ).strip()
    if not safe_title:
        safe_title = "linkedin_post"

    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{safe_title.replace(' ', '_')}_{timestamp}.txt"
    path = os.path.join(DRAFTS_DIR, filename)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return path


def open_file(path):
    """Open a file with the default editor on the current OS."""
    system = platform.system()
    if system == "Windows":
        os.startfile(path)  # type: ignore[attr-defined]
    elif system == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def list_drafts():
    """Return list of .txt files in the drafts folder."""
    ensure_drafts_dir()
    return [f for f in os.listdir(DRAFTS_DIR) if f.endswith(".txt")]


# ---------- LLM helpers ----------

def call_llm(messages, model=MODEL_NAME):
    """Call the local Ollama model with a list of messages."""
    response = ollama.chat(model=model, messages=messages)
    return response["message"]["content"]


def generate_linkedin_post(title, topic_description):
    """Ask the LLM to write a full LinkedIn post."""
    system_msg = (
        "You are an expert LinkedIn content writer. "
        "Write engaging, professional posts with a clear hook, body, and call-to-action. "
        "End with 4-7 relevant hashtags."
    )

    user_msg = (
        f"Create a LinkedIn post.\n\n"
        f"Title or context: {title}\n"
        f"Topic description: {topic_description}\n\n"
        f"Tone: professional, enthusiastic, concise."
    )

    content = call_llm(
        [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]
    )
    return content.strip()


def ask_agent_for_tool(user_command):
    """
    Ask the agent which tool to use.
    Agent must respond with strict JSON.
    """
    system_prompt = """
You are a LinkedIn Draft Agent that can take high-level commands from the user
and choose tools to act on their local machine.

TOOLS YOU CAN CHOOSE:

1) create_post_file(title, topic_description)
   - Use when the user wants to create a new LinkedIn post draft.
   - 'title': short title for the draft (string).
   - 'topic_description': what the post should talk about (string).

2) open_file(filename)
   - Use when the user wants to open a specific draft file, or the last created file.
   - 'filename': can be 'last' or an exact filename from the drafts folder.

3) list_files()
   - Use when the user wants to see all available draft files.

4) close_file(filename)
   - Conceptually closes a file. Since we cannot force-close the editor,
     interpret this as telling the user to manually close it and forgetting
     which file is 'last'.
   - 'filename': can be 'last' or a specific filename.

RESPONSE FORMAT (VERY IMPORTANT):
You must ALWAYS respond only in VALID JSON (no extra text, no markdown, no commentary).

If no tool is needed and you just want to answer:
{
  "tool": "none",
  "args": {},
  "message": "Your plain text answer here."
}

Only output a single JSON object.
"""

    content = call_llm(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_command},
        ]
    )

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        data = {
            "tool": "none",
            "args": {},
            "message": f"(Agent output not valid JSON) Raw content: {content}",
        }

    return data


# ---------- Flask routes ----------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/command", methods=["POST"])
def handle_command():
    global last_created_path

    data = request.get_json(force=True)
    user_command = data.get("command", "").strip()
    if not user_command:
        return jsonify({"log": ["Agent: Please type a command."]})

    log = []
    log.append(f"You: {user_command}")
    log.append("Agent: Thinking which tool to use...")

    tool_call = ask_agent_for_tool(user_command)

    tool = tool_call.get("tool", "none")
    args = tool_call.get("args", {}) or {}
    message = tool_call.get("message", "")

    if message:
        log.append(f"Agent: {message}")

    # ---- Handle tool calls ----
    if tool == "create_post_file":
        title = args.get("title", "LinkedIn Post")
        topic_description = args.get("topic_description", user_command)

        log.append("Agent: Generating LinkedIn post content...")
        post_text = generate_linkedin_post(title, topic_description)

        ensure_drafts_dir()
        path = create_draft_file(title, post_text)
        last_created_path = path

        log.append(f"Agent: Draft created at: {path}")
        log.append("Agent: You can now ask me to open the last draft.")

    elif tool == "open_file":
        filename = args.get("filename", "last")

        if filename == "last":
            if last_created_path and os.path.exists(last_created_path):
                open_file(last_created_path)
                log.append(f"Agent: Opened last draft: {last_created_path}")
            else:
                log.append("Agent: I don't have a 'last' draft remembered yet.")
        else:
            path = os.path.join(DRAFTS_DIR, filename)
            if os.path.exists(path):
                open_file(path)
                last_created_path = path
                log.append(f"Agent: Opened draft: {path}")
            else:
                log.append(f"Agent: File '{filename}' not found in drafts folder.")

    elif tool == "list_files":
        files = list_drafts()
        if not files:
            log.append("Agent: No drafts found yet.")
        else:
            log.append("Agent: Here are your drafts:")
            for f in files:
                log.append(f"  - {f}")

    elif tool == "close_file":
        target = args.get("filename", "last")
        if target == "last" and last_created_path:
            log.append("Agent: I'll forget the last opened draft. Please close the editor window manually.")
            last_created_path = None
        else:
            log.append("Agent: I can't force-close the editor. Please close any open windows manually.")

    elif tool == "none":
        # Just a text response; nothing to execute.
        pass
    else:
        log.append(f"Agent: I don't recognize the tool '{tool}'. Doing nothing.")

    return jsonify({"log": log})


if __name__ == "__main__":
    ensure_drafts_dir()
    app.run(host="127.0.0.1", port=5000, debug=True)
