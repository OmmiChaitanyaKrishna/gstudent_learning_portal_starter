# G-Student Learning Portal (local starter)

## Features
- Student registration using registration number and password
- Admin approval / rejection
- Student dashboard inspired by the supplied G-Student screenshot
- Topic-wise quizzes read from an Excel file
- Starter chatbot endpoint (rule-based demo, not a full generative AI model)
- MySQL storage with hashed passwords

## 1. Install software
Install Python 3.11+ (or a compatible recent Python), VS Code, MySQL Server 8, and MySQL Workbench. PyCharm is optional; it can open this same project.

## 2. Create database
1. Open MySQL Workbench and connect to your local MySQL server.
2. Open `schema.sql` in Workbench.
3. Execute the whole script.

## 3. Configure database credentials
In `app.py`, replace `YOUR_MYSQL_PASSWORD` with your local MySQL root password, or preferably set environment variables:
- `DB_HOST=localhost`
- `DB_USER=root`
- `DB_PASSWORD=your_password`
- `DB_NAME=gstudent_portal`
- `FLASK_SECRET_KEY=a-long-random-secret`

Never commit real passwords or API keys to a public repository.

## 4. Install Python dependencies
Open the project folder in VS Code. In the terminal:

Windows:
```powershell
py -m venv .venv
.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
```

macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, use Command Prompt and run `.venv\\Scripts\\activate.bat`, or configure the terminal environment without changing global security policy.

## 5. Run
```bash
python app.py
```
Open `http://127.0.0.1:5000`.

## 6. Create the first admin
1. Register a normal account from the registration page.
2. In MySQL Workbench execute this statement, replacing the sample registration number:
```sql
UPDATE users SET role='admin', status='approved' WHERE reg_no='YOUR_REGISTRATION_NO';
```
3. Log out and log in again using that account. The admin portal appears.
4. Register a separate student account and approve it from the admin portal.

## 7. Excel question dataset
The starter `data/questions.xlsx` file is included. Its column names must be:
`topic, question, option_a, option_b, option_c, option_d, answer, explanation`

`answer` must be A, B, C or D. Add rows in Excel to create more questions and topics. Restart the app if needed after editing the file.

## 8. AI chatbot
The included `/api/chat` is a rule-based demo so the project runs without an API key. To make it a true AI chatbot, add a backend call to an AI provider, store its API key in an environment variable, validate user input, and never expose the key in JavaScript/browser code.

## Important
This is a learning-project starter, not an official GITAM service. The dashboard tiles are visual/demo links; connect them to authorized real data or implement their pages before production. Use HTTPS, CSRF protection, rate limiting, secure secrets, backups, and appropriate access controls before public deployment.
