# Homework: Your Own AI Customer Service Agent, with a Database and Tools (Unit G)

## 1. What to build: a customer service agent that answers from a database through tools

Choose a **shop or an office**, and build an **AI text customer service agent** (客服 Agent) for it,
with a chat screen that customers can use.

Your agent works like the class example in **Unit G-3 (customer service agent)**:
every customer question goes to the agent first, and the agent decides which **tool** (工具) to call.
The tools read your **SQLite database** (資料庫) or do calculations in your code.
The model never answers from memory.

![What you build: your own customer service agent](images/homework-architecture-en.png)

You may build the chat screen in any of these ways:

| Way | Examples | Notes |
|---|---|---|
| **Gradio** (recommended) | Start from `app-gradio.py` in Unit G-3 | We use it in class. It is the fastest way. |
| **Any other web framework** (網頁框架) | Streamlit; Django; a Flask or FastAPI back end (後端) with an HTML and JavaScript front end (前端); React, Vue or Next.js | Use what you already know or want to learn. |
| **A mobile app** (手機 App, try it if you like) | React Native, Flutter, Android (Kotlin) or iOS (Swift) | An extra challenge. Screenshots from a phone or an emulator (模擬器) are fine. |

All three ways have the same basic rules (part 3) and are graded the same way.

> **Keep the back end on the server:** if you build a web front end or a mobile app,
> the **API key, the agent loop, the tools and the database all stay in your back end** (a server program).
> **Never put your API key in the front-end or app code.** Anyone who opens your page or app can read it.
> The front end only sends the customer's message to your back end and shows the answer.

Some ideas: a restaurant, a coffee shop, a bookstore, a gym, a hotel (飯店) or a guesthouse (民宿),
a cram school (補習班), a clinic front desk (診所掛號櫃台), or an office at our school.
**Do not hand in the fast food example from class.** Design your own shop or office.

> **Cowork with AI: this is required.** Build this agent **together with an AI tool** (與 AI 協作, cowork),
> for example Claude Code, Codex or Gemini CLI in a console, GitHub Copilot (agent mode) in VS Code,
> or ChatGPT, Claude or Gemini in a web page. Use it to plan your tables and tools, write and fix code,
> and test your agent. **You are still responsible for the result:** read the code the AI writes,
> run it, and check every answer of your agent. Part 6 of the report template tells us how you worked with AI.
> Never paste your API key into an AI chat.

## 2. Start from the class example, and change everything that belongs to your own shop

You may start from the files in Unit G-3: `app-gradio.py`, `shop_info.csv` and `menu.csv`.
The notebook `1-Agent-Tool-Calling.ipynb` explains every part step by step.
Keep the **method**, and replace everything that belongs to the shop:

| Part of the class example | What you must change |
|---|---|
| `shop_info.csv` (opening hours, address, delivery, parking ...) | Your own information table: the facts your customers ask about |
| `menu.csv` (items, prices, available or not) | Your own records table: your services, rooms, classes or products |
| The tools (`get_shop_info`, `get_price`, `calculate_total`, `transfer_to_human`) | Your own tools, with names, descriptions and code that fit your shop. **Your calculation tool must fit your shop**, not only add up a food order |
| The system prompt (role and rules) | Your own role and rules |
| The sample questions on the chat page | Questions your own customers would ask |

## 3. Basic rules: what every agent must have

### 3.1 A SQLite database with at least two tables, built from your own CSV files

1. **An information table** (資訊表), like `shop_info` in class: one row per topic, with the columns `topic` and `content`.
   It has **at least 8 topics**. Include the questions your customers ask most often,
   such as opening hours, address, payment, delivery or parking. If customers ask something all the time,
   it belongs in this table.
2. **A records table** (紀錄表), like `menu` in class: one row per service, room, class or product.
   It has **at least 15 rows**. Each row has at least a name, a number (a price or a fee),
   and whether it is available. Not every shop sells food, so use the columns that fit yours.
3. Your program **builds the tables from CSV files when it starts** (see Step 3 of the Unit G-3 notebook).
   You hand in the CSV files, not the `.db` file.

### 3.2 At least four tools, one of each kind

| Kind of tool | In class | Ideas for your shop | A customer might ask |
|---|---|---|---|
| Look up information | `get_shop_info(topic)` | opening hours of a clinic, the rules of a gym | "Is there parking?" |
| Look up records | `get_price` | find a class, a room or a product; check if it is available | "Is the Friday yoga class full?" |
| Calculate (in code) | `calculate_total(items)` | nights × room price, a monthly fee with a student discount, a shipping fee | "How much are three nights in a double room?" |
| Hand over to a person | `transfer_to_human()` | complaints, or questions your data cannot answer | "I want to speak to the manager." |

Follow the four rules for tools from class:

- **Return data, not sentences.** The model writes the sentences.
- **Say clearly when nothing is found.** Otherwise the model makes something up.
- **Do the maths in the tool.** Never let the model add up the bill.
- **Take parameters, never free SQL.** Your code builds the query; the model only fills in the values.

### 3.3 An agent loop that is safe and visible

- The loop stops after `max_steps` model calls, so a confused model cannot loop forever.
- It runs **only your own tools**. If the model asks for a tool name you did not write, the loop refuses.
- The chat page **shows the tool trace** (工具軌跡): which tool was called, with which arguments,
  and what came back, like the "Tools used" panel of `app-gradio.py`.
  Your screenshots in the report must show this trace.

### 3.4 A system prompt with a role and four kinds of rules

| Kind of rule | What it does | Example from class |
|---|---|---|
| Grounding (接地) | Answer only from tool results; say so when nothing is found | "Answer only from tool results. Never invent anything." |
| Scope (範圍) | Stay with the shop; politely refuse other topics | "Only talk about this shop." |
| Routing (分派) | Which tool to use for which question | "Shop questions -> get_shop_info." |
| Language and format | How to answer | "Answer in the customer's language, in three sentences or less." |

### 3.5 A chat screen that remembers the conversation

It sends the **chat history** with each new question, shows a **greeting**, and offers **sample questions**.

## 4. Test that your agent picks the right tool and stays inside its job

Making the agent answer is easy. **Making it pick the right tool and stay inside its job is the hard part.**

1. **Four kinds of question.** Ask at least one of each kind (see Step 9 of the Unit G-3 notebook).
   In your report, you show one conversation of each kind, with a screenshot of the tool trace:

   | Kind | A good answer |
   |---|---|
   | In the data | The right tool, and the exact value from the database |
   | Needs maths | The calculation tool gives the number, not the model |
   | Not in the data | "I don't have that information" and a hand-over to a person. Never invent |
   | Not our job | A polite refusal, and back to the shop |

2. **A tool-choice test** (工具選擇測試) with **at least 10 questions**. For each question, write the tool or tools
   you would accept, run the test, and report the score, like Step 9 of the Unit G-3 notebook.
   When a question misses, tell us what you changed (usually the tool description or a rule) and test again.

> **If customers often ask something that is not in your data, add it to the data, not to the rules.**
> In class, delivery and parking became topics in `shop_info.csv` for this reason.

## 5. Describe your agent clearly: who it serves, and why it fits them

There is no single right answer here. We want you to explain your own agent well,
in about 150 to 250 words. Answer three questions:

- **Who does it serve?** For example, new customers, members, students or patients.
- **What problem does it solve for them?** What do they usually want to know or get done?
- **Why does it fit them better than what they use now?** For example, phone calls,
  the FAQ page of a website, a general chatbot like ChatGPT, or the auto-reply of a LINE official account.

## 6. Extra credit: optional features that make your agent more useful

Choose any of these if you have time. Tell us in your report which ones you did.

| Feature | What it means | Where to learn it |
|---|---|---|
| A tool that changes data | For example `make_booking`: the agent shows a summary, the customer confirms, and only then your code writes to the database | Your own design |
| Two languages | A Chinese name column (`name_zh`), and your program decides the reply language | Steps 4 and 6 of the Unit G-3 notebook |
| Forgiving names | Customers do not have to type the exact name in your database, for example "large Coke" | Step 6 of the Unit G-3 notebook finds part of a name; go further, for example with a list of other names (aliases) |

RAG (searching long documents, 檢索長文件) comes in the next unit (Unit H). You do not need it for this homework.

## 7. What to hand in

You hand in **two things, and both are required**: a PDF report, and your code on GitHub.

![How to hand in this week's homework](images/submit-en.png)

### 7.1 The PDF report (required, used for grading)

Fill in the Word template **`Report-Template-EN.docx`** in this folder.
When you finish, choose "Save As" in Word, save it as a PDF,
and upload it to the course site. Name it **`ID_Name_CustomerService.pdf`** (學號_姓名_CustomerService.pdf).
The template already has these parts. Follow the grey hints:

- **Basic information**: student ID, name, your shop, the model, how you built the chat screen, and your GitHub link.
1. **Where your agent is used**: who it serves, what problem it solves, and why it fits them better
   than what they use now (about 150 to 250 words).
2. **Your database**: each table, its CSV file, its columns and the number of rows.
   You do not paste the CSV files; we read them on GitHub.
3. **Your tools**: each tool, its kind, what it reads or calculates, its parameters, and how a customer might ask.
   Then explain your calculation tool in two or three sentences.
4. **Your system prompt**: the role and your rules sorted into the four kinds, and why you wrote each one.
   You do not paste the whole prompt; we read it in your code on GitHub.
5. **Your agent in action**: four conversations, one for each kind of question (in the data, needs maths,
   not in the data, not our job), with screenshots that show the tool trace.
   Then your tool-choice score and what you fixed.
6. **How you coworked with AI, and the problems you met** (required): which AI tools you used, where,
   about how many hours, and what for; then the problems you met while building your agent and how you solved them.
7. **Extra credit** (optional): which features you added.
8. **Checklist**: check every item before you hand in.

### 7.2 Your code on GitHub (required)

Put your project on GitHub. **GitHub is the only way to hand in your code.** We do not accept ZIP files.

If you have never used GitHub, read **`(FYR) GitHub-Guide-EN.md`** in the folder `(FYR) GitHub Guide and README Template`
(for your reference). It shows how to make a GitHub account,
how to upload your project from your own computer, and how to ask an AI tool to upload it for you.

Your repository must have these files:

| File | What it is |
|---|---|
| Your program code | Gradio: only your Gradio app, such as `app.py` (or a name like `app-gradio.py`), and any Python files it imports. Other frameworks or apps: all your front-end and back-end source folders |
| Your CSV files | At least two: your information table and your records table. Your program builds the database from them |
| `.env.example` | A sample settings file with an empty key, such as `API_KEY=` |
| A list of the packages to install | Python: `requirements.txt` (such as `gradio`, `openai`, `python-dotenv`). JavaScript: `package.json`. Flutter: `pubspec.yaml` |
| `README.md` | The first page people see in your repository. Use the template below |
| `.gitignore` | Tells git which files must not be uploaded (see rule 2 below) |

**Only the app is needed.** You do not have to upload a notebook (`.ipynb`) that you used to try things out
or to show the steps. We run your app, so the app and its CSV files must be complete on their own.

Follow these rules:

1. Make the repository **public**, so we can see it. Before you hand in the link,
   open it in a private (incognito) browser window to check that it works without logging in.
2. Your **`.gitignore`** file must have at least these lines. `*.db` keeps the database file out of GitHub,
   because your program builds it again from the CSV files:

   ```text
   .env
   *.db
   __pycache__/
   venv/
   .venv/
   node_modules/
   build/
   dist/
   ```

3. Write the **link** on page 1 of your PDF.
   We grade the version in your repository at the deadline. Changes made after the deadline do not count.

**Write your README.md from the template.** GitHub shows `README.md` on the front page of your repository,
so it is the first thing we read. Copy **`(FYR) README-Template.md`** from the folder `(FYR) GitHub Guide and README Template` into your project,
rename it to `README.md`, and fill in every part: what your agent does, who it serves, its tools and tables,
a screenshot, and how to install and run it, step by step.

> **Keep your key safe:** `.env` holds your API key (金鑰). **Never push it to GitHub.**
> A key on the internet can be found and stolen within hours.
> If you upload it by mistake, delete the key at once and make a new one.
> **Deleting the file from GitHub is not enough**, because git keeps it in the history.
> Points will be taken off if your repository contains a key.

> **Notes on the API:**
> Your API settings go in a `.env` file. Copy `.env.example` to `.env`, then put your key after `API_KEY=`.
> Tool calling needs an endpoint and a model that support `tools`; if Step 5 of the Unit G-3 notebook shows no tool call, your endpoint or model does not support tools.
> Error 429 means too many calls in a short time (呼叫太頻繁). A free plan may allow only about 15 calls a minute,
> and one tool question uses two or more calls, so add `time.sleep()` between test questions.
