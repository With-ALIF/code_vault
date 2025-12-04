import re
import asyncio
import time
import json
import os
import logging
from collections import deque
from io import BytesIO
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import RetryAfter, BadRequest, Forbidden

# ================= BOT TOKEN =================
BOT_TOKEN = '8279532303:AAE7YuydI5MRB68P7aRnI74d6RFlom2sJas'
# =============================================

# --------- CLEAN LOGGING (NO CONSOLE NOISE) ----------
logging.basicConfig(level=logging.ERROR, format="%(message)s")
logger = logging.getLogger(__name__)
# -----------------------------------------------------

DELAY_BETWEEN_POLLS = 3
POLLS_PER_BATCH = 20
BREAK_BETWEEN_BATCHES = 5
RETRY_ATTEMPTS = 3
DATA_FILE = "sot_bot_user_data.json"

# safe limits for fallback truncation (you can tune)
FALLBACK_QUESTION_LIMIT = 1000
FALLBACK_OPTION_LIMIT = 300
FALLBACK_EXPLANATION_LIMIT = 2000

class PollBot:
    def __init__(self, token):
        self.token = token
        self.app = Application.builder().token(token).build()

        self.poll_queue = deque()
        self.is_processing = False
        self.current_user_id = None
        self.last_poll_time = 0

        self.user_channels = {}
        self.user_format = {}

        self._load_data()
        self.setup_handlers()

    # ---------------------- Load & Save ----------------------
    def _load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.user_channels = {int(k): v for k, v in data.get("user_channels", {}).items()}
                self.user_format = {int(k): v for k, v in data.get("user_format", {}).items()}
            except Exception as e:
                logger.error(f"_load_data error: {e}")

    def _save_data(self):
        try:
            data = {
                "user_channels": {str(k): v for k, v in self.user_channels.items()},
                "user_format": {str(k): v for k, v in self.user_format.items()}
            }
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"_save_data error: {e}")

    # ---------------------- Helpers ----------------------
    def normalize_chat_id(self, raw):
        try:
            return int(str(raw).strip())
        except:
            return raw

    # ---------------------- Parsing (your original functions kept intact) ----------------------
    def parse_mcq_text(self, text):
        """
        Supports:
         - Old format: Question 1: ... A. ... B. ... Correct Answer: A Explanation: ...
         - New format: Question. ... A) ... B) ... Ans: A Explanation ...
         - Mixed/variants: A. or A) or 'A )' etc. 'Correct Answer', 'Ans', 'Answer' accepted.
        Returns list of polls: {question, options(list of 4), correct_answer(int 0-3), explanation}
        """

        polls = []

        # Normalize some characters & unify line endings
        t = text.replace('\r\n', '\n').replace('\r', '\n')

        # Split into blocks by headers like:
        # "Question 1:" or "Question:" or "Question." (case-insensitive)
        blocks = re.split(r'(?i)Question\s*\d*\s*[:.]', t)
        # If split produced an empty leading block (text before first Question), ignore it
        for block in blocks:
            if not block or not block.strip():
                continue

            q_text = block.strip()

            try:
                # 1) Extract question text: everything up to the first option (A. or A) or A ))
                q_match = re.search(r'^(.*?)(?=\n\s*A[\.\)]|\n\s*A\s*\))', q_text, re.DOTALL | re.IGNORECASE)
                if q_match:
                    question = q_match.group(1).strip()
                else:
                    # If not found, maybe format is "Question.\nA) ..." and question is missing
                    # Try to take the part before "A" line or first blank line
                    lines = q_text.splitlines()
                    if lines and not re.match(r'^\s*A[\.\)]', lines[0], re.IGNORECASE):
                        question = lines[0].strip()
                    else:
                        question = ""  # fallback

                # 2) Extract options A-D with flexible separators (., ), or ) with spaces)
                option_a = re.search(r'A[\.\)]\s*(.*?)(?=\n\s*B[\.\)]|\n\s*C[\.\)]|\n\s*D[\.\)]|$)', q_text, re.DOTALL | re.IGNORECASE)
                option_b = re.search(r'B[\.\)]\s*(.*?)(?=\n\s*C[\.\)]|\n\s*D[\.\)]|$)', q_text, re.DOTALL | re.IGNORECASE)
                option_c = re.search(r'C[\.\)]\s*(.*?)(?=\n\s*D[\.\)]|$)', q_text, re.DOTALL | re.IGNORECASE)
                option_d = re.search(r'D[\.\)]\s*(.*?)(?=\n|$)', q_text, re.DOTALL | re.IGNORECASE)

                if not all([option_a, option_b, option_c, option_d]):
                    # If options are on same line or different structure, try stricter pattern:
                    # Look for lines that start with 'A' optionally followed by '.' or ')'
                    lines = q_text.splitlines()
                    opts = {}
                    for line in lines:
                        m = re.match(r'^\s*([A-D])\s*[\.\)]\s*(.*)', line, re.IGNORECASE)
                        if m:
                            opts[m.group(1).upper()] = m.group(2).strip()
                    if all(k in opts for k in ['A', 'B', 'C', 'D']):
                        option_a_text = opts['A']
                        option_b_text = opts['B']
                        option_c_text = opts['C']
                        option_d_text = opts['D']
                    else:
                        # Can't parse options -> skip this block
                        continue
                else:
                    option_a_text = option_a.group(1).strip()
                    option_b_text = option_b.group(1).strip()
                    option_c_text = option_c.group(1).strip()
                    option_d_text = option_d.group(1).strip()

                # 3) Correct answer: accept "Correct Answer:", "Correct answer:", "Ans:", "Answer:", etc.
                corr = re.search(r'(?i)(?:Correct\s*Answer|Correct\s*answer|Answer|Ans)\s*[:.]?\s*([A-D])', q_text)
                if not corr:
                    # try one-line variant: "Ans.\nA" or "Ans\nA"
                    corr = re.search(r'(?i)Ans\s*[:.]?\s*\n?\s*([A-D])', q_text)
                if not corr:
                    # If still not found, skip this block (we require correct answer)
                    continue

                correct_letter = corr.group(1).upper()
                correct_index = ord(correct_letter) - ord('A')
                if correct_index < 0 or correct_index > 3:
                    continue

                # 4) Explanation: optional, everything after 'Explanation' keyword
                expl = ""
                expl_match = re.search(r'(?i)Explanation\s*[:.]?\s*(.*)', q_text, re.DOTALL)
                if expl_match:
                    expl = expl_match.group(1).strip()

                polls.append({
                    "question": question if question else "(No question text)",
                    "options": [
                        option_a_text,
                        option_b_text,
                        option_c_text,
                        option_d_text
                    ],
                    "correct_answer": correct_index,
                    "explanation": expl
                })

            except Exception as e:
                # skip problematic block but continue parsing others
                logger.error(f"parse error: {e}")
                continue

        return polls

    def parse_csv_text(self, text, strip_html=False):
        """
        Read CSV text and convert rows to poll dicts compatible with existing logic.
        Handles headers (case-insensitive) like:
        questions,option1,option2,option3,option4,option5,answer,explanation,type,section

        - answer can be A/B/C... or 1/2/3...
        - supports quoted fields with commas
        - returns list of polls: {question, options(list), correct_answer (0-based int), explanation}
        - strip_html: if True, HTML tags will be removed from question/explanation/options
        """
        import csv
        from io import StringIO

        polls = []

        def clean_html(s):
            if s is None:
                return ""
            s = str(s).strip()
            if not s:
                return ""
            if strip_html:
                return re.sub(r'<[^>]+>', '', s).strip()
            return s

        f = StringIO(text)
        try:
            reader = csv.DictReader(f)
        except Exception:
            # fallback to simple parsing
            f.seek(0)
            simple = csv.reader(f)
            for row in simple:
                if len(row) < 6:
                    continue
                q = clean_html(row[0])
                opts = [clean_html(row[i]) for i in range(1, min(6, len(row)))]
                # ensure at least 4 options
                while len(opts) < 4:
                    opts.append("")
                ans_raw = row[6].strip() if len(row) > 6 else ""
                expl = clean_html(row[7]) if len(row) > 7 else ""

                # normalize answer
                correct_index = None
                if ans_raw:
                    if ans_raw.isdigit():
                        try:
                            correct_index = int(ans_raw) - 1
                        except:
                            correct_index = None
                    else:
                        a = ans_raw.strip().upper()
                        if a and a[0] in "ABCDE":
                            correct_index = ord(a[0]) - ord('A')
                if correct_index is None or correct_index < 0 or correct_index >= len(opts):
                    continue

                polls.append({
                    "question": q or "(No question text)",
                    "options": opts[:4],
                    "correct_answer": correct_index,
                    "explanation": expl
                })

            return polls

        # If using DictReader
        fieldnames = {fn.lower().strip(): fn for fn in (reader.fieldnames or [])}

        # helper lists for header keys
        q_keys = ['questions', 'question', 'q']
        opt_keys = [f'option{i}' for i in range(1, 6)]
        ans_keys = ['answer', 'ans', 'correct', 'correct answer', 'correct_answer']
        expl_keys = ['explanation', 'explain', 'explanation_text', 'explaination']

        for row in reader:
            # find question column
            q_col = None
            for k in q_keys:
                if k in fieldnames:
                    q_col = fieldnames[k]
                    break
            if not q_col:
                # fallback to first column
                if reader.fieldnames and len(reader.fieldnames) > 0:
                    q_col = reader.fieldnames[0]
                else:
                    continue

            question = clean_html(row.get(q_col, "") or "")

            # gather options
            opts = []
            for i in range(1, 6):
                name = f'option{i}'
                candidate = fieldnames.get(name)
                if candidate:
                    val = clean_html(row.get(candidate, "") or "")
                    opts.append(val)

            # positional fallback if no option headers matched
            if not any(opts):
                try:
                    cols = reader.fieldnames
                    q_idx = cols.index(q_col)
                    for j in range(q_idx + 1, min(q_idx + 6, len(cols))):
                        opts.append(clean_html(row.get(cols[j], "") or ""))
                except Exception:
                    pass

            # ensure at least 4 options
            while len(opts) < 4:
                opts.append("")

            # find answer
            ans_col = None
            for k in ans_keys:
                if k in fieldnames:
                    ans_col = fieldnames[k]
                    break

            ans_raw = (row.get(ans_col, "") or "").strip() if ans_col else ""

            # heuristic: if ans_raw empty, try to find any small cell that looks like answer
            if not ans_raw:
                for fn in reader.fieldnames:
                    v = (row.get(fn, "") or "").strip()
                    if v and (v.isdigit() or (len(v) <= 3 and any(ch.isalpha() for ch in v))):
                        if len(v) < 6:
                            ans_raw = v
                            break

            correct_index = None
            if ans_raw:
                a = ans_raw.strip().upper()
                m = re.match(r'^([A-E])', a)
                if m:
                    correct_index = ord(m.group(1)) - ord('A')
                else:
                    digits = re.search(r'\d+', a)
                    if digits:
                        try:
                            correct_index = int(digits.group(0)) - 1
                        except:
                            correct_index = None

            expl_col = None
            for k in expl_keys:
                if k in fieldnames:
                    expl_col = fieldnames[k]
                    break
            explanation = clean_html(row.get(expl_col, "") or "") if expl_col else ""

            if correct_index is None or correct_index < 0 or correct_index >= len(opts):
                continue

            polls.append({
                "question": question or "(No question text)",
                "options": opts[:4],
                "correct_answer": correct_index,
                "explanation": explanation
            })

        return polls

    # ---------------------- Formatting ----------------------
    def format_question(self, q, uid):
        prefix = self.user_format.get(uid, {}).get("prefix", "")
        return f"{prefix}\n\n{q}" if prefix else q

    def format_explanation(self, e, uid):
        suffix = self.user_format.get(uid, {}).get("suffix", "")
        if e:
            return f"{e}\n\n{suffix}" if suffix else e
        return suffix if suffix else ""

    # ---------------------- Poll Sending ----------------------
    async def send_single_poll(self, ctx, poll, idx, total, chat, uid):
        """
        Attempt to send poll preserving original message content.
        If Telegram rejects due to length or entities, fallback:
         - upload the ORIGINAL full text as a .txt document to the same chat (so nothing is lost)
         - send a safe/truncated poll so the channel still gets a poll
        """
        # Keep original unmodified texts
        q_original = self.format_question(poll["question"], uid)
        ex_original = self.format_explanation(poll.get("explanation", ""), uid)
        original_opts = list(poll["options"])

        # make options list (non-empty)
        opts = [o for o in original_opts if o is not None and str(o).strip() != ""]
        if len(opts) < 2:
            logger.error("Not enough non-empty options to send poll")
            return False

        # compute mapping for correct option
        orig_correct = poll.get("correct_answer", 0)
        non_empty_indices = [i for i, o in enumerate(original_opts) if o and str(o).strip()]
        if orig_correct in non_empty_indices:
            new_correct = non_empty_indices.index(orig_correct)
        else:
            new_correct = 0

        # Try to send as-is (no forced parse mode) to avoid entity parse errors.
        # This preserves the exact text the user provided (including HTML tags).
        for attempt in range(RETRY_ATTEMPTS):
            try:
                # rate limiting between polls
                d = time.time() - self.last_poll_time
                if d < DELAY_BETWEEN_POLLS:
                    await asyncio.sleep(DELAY_BETWEEN_POLLS - d)

                await ctx.bot.send_poll(
                    chat_id=chat,
                    question=q_original,
                    options=opts,
                    type="quiz",
                    correct_option_id=new_correct,
                    explanation=ex_original or None,
                    is_anonymous=True,
                    # do NOT set explanation_parse_mode so Telegram won't try to parse HTML entities –
                    # that way we keep the literal text intact (tags appear as plain text).
                    explanation_parse_mode=None
                )

                self.last_poll_time = time.time()
                return True

            except RetryAfter as e:
                await asyncio.sleep(e.retry_after + 1)
            except BadRequest as e:
                err = str(e)
                logger.error(f"send_single_poll BadRequest: {err}")

                # If message too long or can't parse entities -> fallback
                if 'Message is too long' in err or "Can't parse entities" in err or 'unsupported start tag' in err:
                    # 1) Upload the original content as a .txt file to the target chat so nothing is lost.
                    try:
                        combined = "QUESTION:\n" + q_original + "\n\nOPTIONS:\n"
                        for i, o in enumerate(original_opts):
                            label = chr(ord('A') + i)
                            combined += f"{label}. {o}\n"
                        combined += "\nEXPLANATION:\n" + (ex_original or "")
                        bio = BytesIO(combined.encode('utf-8'))
                        bio.name = "original_poll.txt"
                        await ctx.bot.send_document(chat_id=chat, document=bio, caption="Full original poll content (raw).")
                    except Exception as doc_e:
                        logger.error(f"Failed to send original content as document: {doc_e}")

                    # 2) Prepare safe truncated versions for poll (so poll can be posted)
                    q_safe = q_original
                    ex_safe = ex_original
                    safe_opts = list(opts)

                    if len(q_safe) > FALLBACK_QUESTION_LIMIT:
                        q_safe = q_safe[:FALLBACK_QUESTION_LIMIT-12].rstrip() + "\n\n[...truncated...]"
                    # truncate options if required
                    for i, o in enumerate(safe_opts):
                        if len(o) > FALLBACK_OPTION_LIMIT:
                            safe_opts[i] = o[:FALLBACK_OPTION_LIMIT-12].rstrip() + "..."
                    if ex_safe and len(ex_safe) > FALLBACK_EXPLANATION_LIMIT:
                        ex_safe = ex_safe[:FALLBACK_EXPLANATION_LIMIT-12].rstrip() + "\n\n[...truncated...]"

                    # Try sending truncated poll (still without parse_mode)
                    try:
                        await ctx.bot.send_poll(
                            chat_id=chat,
                            question=q_safe,
                            options=safe_opts,
                            type="quiz",
                            correct_option_id=new_correct if new_correct < len(safe_opts) else 0,
                            explanation=ex_safe or None,
                            is_anonymous=True,
                            explanation_parse_mode=None
                        )
                        self.last_poll_time = time.time()
                        return True
                    except Exception as inner_e:
                        logger.error(f"Fallback truncated poll failed: {inner_e}")
                        return False
                else:
                    # other BadRequest types (e.g., chat not found, poll not allowed)
                    logger.error(f"Unhandled BadRequest: {err}")
                    return False
            except Forbidden as e:
                logger.error(f"Forbidden: {e}")
                return False
            except Exception as e:
                logger.error(f"send_single_poll error: {e}")
                return False

        return False

    # ---------------------- Queue Processor ----------------------
    async def process_queue(self, ctx, uid):

        if self.is_processing:
            return

        self.is_processing = True
        self.current_user_id = uid

        my_polls = []
        others = deque()

        # Collect polls belonging to this user; keep others in queue
        while self.poll_queue:
            item = self.poll_queue.popleft()
            if item.get("owner_user_id") == uid:
                my_polls.append(item["poll_data"])
            else:
                others.append(item)

        self.poll_queue = others

        if not my_polls:
            try:
                await ctx.bot.send_message(uid, "❌ আপনার কিউতে কোনো পোল নেই।")
            except Exception:
                pass
            self.is_processing = False
            self.current_user_id = None
            return

        target = self.user_channels.get(uid)
        if not target:
            try:
                await ctx.bot.send_message(uid, "❌ কোনো চ্যানেল সেট করা নেই। /setchannel ব্যবহার করুন।")
            except Exception:
                pass
            self.is_processing = False
            self.current_user_id = None
            return

        total = len(my_polls)
        sent = 0

        # Inform start of sending
        try:
            await ctx.bot.send_message(uid, "Starting to send...")
        except Exception:
            pass

        # Send in batches
        while my_polls:
            batch = my_polls[:POLLS_PER_BATCH]
            my_polls = my_polls[POLLS_PER_BATCH:]

            for poll in batch:
                ok = await self.send_single_poll(ctx, poll, sent + 1, total, target, uid)
                if ok:
                    sent += 1

            if my_polls:
                try:
                    await ctx.bot.send_message(uid, f"⏸ {BREAK_BETWEEN_BATCHES}s বিরতি...")
                except Exception:
                    pass
                await asyncio.sleep(BREAK_BETWEEN_BATCHES)

        try:
            await ctx.bot.send_message(
                uid,
                f"✅ All done! Successfully sent {sent}/{total} polls to the channel."
            )
        except Exception:
            pass

        self.is_processing = False
        self.current_user_id = None

    # ---------------------- Commands ----------------------
    async def start(self, u: Update, c: ContextTypes.DEFAULT_TYPE):
        welcome = """
🤖 ALIF Poll Bot

প্রথমে টার্গেট চ্যানেল সেট করুন:
 /setchannel <channel_id_or_username>

উদাহরণ:
 /setchannel -1001234567890
 /setchannel @mychannel

(চ্যানেলে বটকে অ্যাড করে এবং পোস্ট করার অনুমতি দিন)

এখানে ফরম্যাট সেট করুন (ঐচ্ছিক):
 /setformat <prefix> || <suffix>

উদাহরণ:
 /setformat [SOT] || [@SOT_Academy]

তারপর MCQ টেক্সট পাঠান — বট নিম্নোক্ত দুই ফরম্যাটই পার্স করবে:

ফরম্যাট-১ -
Question 1:
প্রশ্ন
A. ...
B. ...
C. ...
D. ...
Correct Answer: A
Explanation: ...

ফরম্যাট-২ -
Question.
প্রশ্ন
A)
B)
C)
D)

Ans: A
Explanation: ...

অথবা CSV ফরম্যাটও পাঠাতে পারেন:
Question,Option1,Option2,Option3,Option4,Option5,Answer,Explanation
"""
        if u.message:
            await u.message.reply_text(welcome)
        else:
            # fallback if message absent
            if u.effective_user and u.effective_user.id:
                await c.bot.send_message(u.effective_user.id, "Bot started. Use /start for instructions.")

    async def setchannel(self, u: Update, c: ContextTypes.DEFAULT_TYPE):
        uid = u.effective_user.id if u.effective_user else None
        if uid is None:
            return
        if not c.args:
            if u.message:
                await u.message.reply_text("ব্যবহার: /setchannel <channel_id_or_username>")
            return
        raw = c.args[0]
        self.user_channels[uid] = self.normalize_chat_id(raw)
        self._save_data()
        if u.message:
            await u.message.reply_text(f"✅ Channel set: {raw}")

    async def setformat(self, u: Update, c: ContextTypes.DEFAULT_TYPE):
        uid = u.effective_user.id if u.effective_user else None
        if uid is None:
            return
        text = " ".join(c.args).strip()

        if "||" not in text:
            if u.message:
                await u.message.reply_text("ব্যবহার: /setformat <prefix> || <suffix>")
            return

        prefix, suffix = text.split("||", 1)
        self.user_format[uid] = {"prefix": prefix.strip(), "suffix": suffix.strip()}
        self._save_data()

        if u.message:
            await u.message.reply_text("✅ Format saved!")

    async def handle_text(self, u: Update, c: ContextTypes.DEFAULT_TYPE):
        # robust uid and text extraction
        uid = u.effective_user.id if u.effective_user else None

        text = ""
        if u.message and u.message.text:
            text = u.message.text
        elif u.edited_message and u.edited_message.text:
            text = u.edited_message.text
        else:
            if u.message:
                await u.message.reply_text("No text found in update.")
            return

        # ---------------- CSV detection ----------------
        first_line = text.splitlines()[0] if text.strip() else ""
        if first_line:
            lower_first = first_line.lower()
            if (',' in first_line and (any(h in lower_first for h in ['question', 'questions', 'option1']) or lower_first.startswith('questions'))):
                polls = self.parse_csv_text(text, strip_html=False)
                if not polls:
                    if u.message:
                        await u.message.reply_text("❌ CSV পার্স করা যায়নি — ফরম্যাট পরীক্ষা করুন।")
                    return

                for p in polls:
                    # do NOT modify the original texts — keep them as-is
                    self.poll_queue.append({"owner_user_id": uid, "poll_data": p})

                total = len(polls)
                batches = (total - 1) // POLLS_PER_BATCH + 1
                est_seconds = total * DELAY_BETWEEN_POLLS + max(0, batches - 1) * BREAK_BETWEEN_BATCHES
                est_min = est_seconds // 60
                est_sec = est_seconds % 60

                if u.message:
                    await u.message.reply_text(
                        f"📁 CSV detected!\n✓ Loaded {total} polls.\nAdded to queue!\nWill be sent in {batches} batch(es)\n⏱ Estimated time: ~{est_min} min {est_sec} sec\nStarting to send..."
                    )

                await self.process_queue(c, uid)
                return

        # quick sanity check for required keywords (either style)
        if not re.search(r'(?i)Question', text) or not re.search(r'(?i)(Correct\s*Answer|Ans|Answer)', text):
            if u.message:
                await u.message.reply_text("❌ MCQ ফরম্যাট সঠিক নয় — 'Question' ও 'Ans/Correct Answer' থাকার কথা।")
            return

        polls = self.parse_mcq_text(text)
        if not polls:
            if u.message:
                await u.message.reply_text("❌ পোল তৈরি হয়নি (পার্সিং ব্যর্থ)। অনুগ্রহ করে ফরম্যাট পরীক্ষা করুন।")
            return

        # Append polls to queue (no modification of original messages)
        for p in polls:
            self.poll_queue.append({"owner_user_id": uid, "poll_data": p})

        total = len(polls)
        batches = (total - 1) // POLLS_PER_BATCH + 1
        est_seconds = total * DELAY_BETWEEN_POLLS + max(0, batches - 1) * BREAK_BETWEEN_BATCHES
        est_min = est_seconds // 60
        est_sec = est_seconds % 60

        if u.message:
            await u.message.reply_text(
                f"📊 Processing your polls...\n"
                f"✓ Found {total} polls.\n\n"
                f"Added to queue! 📦\n"
                f"Will be sent in {batches} batch(es) of up to {POLLS_PER_BATCH} polls each\n"
                f"⏱ Estimated time: ~{est_min} min {est_sec} sec\n"
                f"Starting to send..."
            )

        # start processing
        await self.process_queue(c, uid)

    # ---------------------- Setup ----------------------
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        # central error handler so Telegram exceptions don't crash your bot
        try:
            logger.error(f"Exception while handling an update: {context.error}")
            # optionally notify admin
        except Exception as ex:
            logger.error(f"Error in error_handler: {ex}")

    def setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("setchannel", self.setchannel))
        self.app.add_handler(CommandHandler("setformat", self.setformat))

        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))

        # global error handler
        self.app.add_error_handler(self.error_handler)

    # ---------------------- Run ----------------------
    def run(self):
        print("Bot is running...")
        self.app.run_polling()


def main():
    PollBot(BOT_TOKEN).run()


if __name__ == "__main__":
    main()
