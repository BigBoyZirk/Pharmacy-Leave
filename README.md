# Pharmacy annual leave

A small Flask app for a UK pharmacy: staff request leave with a 4-digit PIN, and an admin approves it.

## Run locally

```bash
cd pharmacy-leave
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

### Demo logins (first run)

| Role | How to log in |
| --- | --- |
| Staff | PIN `1001`, `1002`, or `1003` |
| Admin | Email and password from `.env` (`ADMIN_EMAIL` / `ADMIN_PASSWORD`) |

Change those values in `.env` before using this with real staff.

## Email

Leave requests still save if SMTP is not set. To send mail, fill `MAIL_*` in `.env`. Gmail needs an [app password](https://support.google.com/accounts/answer/185833), not the normal account password.

- New staff request → `NOTIFY_ADMIN_EMAIL`
- Approve / reject → the staff member’s email, if they have one

## Leave days

Each date in the booked range counts as one day, including weekends. Approved days in the current calendar year are subtracted from the staff member’s allowance (default 28).
