from app.infrastructure.email.reply_cleaner import clean_reply


def test_strips_gmail_style_quote_header():
    raw = (
        "No class today, sorry.\n\n"
        "On Wed, Aug 5, 2026 at 3:00 PM Course Rep <rep@example.com> wrote:\n"
        "> Is CSC803 holding today?\n"
    )
    assert clean_reply(raw) == "No class today, sorry."


def test_strips_signature_delimiter():
    raw = "We'll start by 5:30 today.\n\n--\nDr. Adeyemi\n+234 801 234 5678\n"
    assert clean_reply(raw) == "We'll start by 5:30 today."


def test_strips_outlook_original_message_block():
    raw = (
        "Move to Lab 2 please.\n\n"
        "-----Original Message-----\n"
        "From: Course Rep <rep@example.com>\n"
        "Sent: Wednesday, August 5, 2026 3:00 PM\n"
        "Subject: class today?\n"
    )
    assert clean_reply(raw) == "Move to Lab 2 please."


def test_plain_reply_with_no_quoting_passes_through():
    raw = "Yes, class is holding as scheduled."
    assert clean_reply(raw) == "Yes, class is holding as scheduled."


def test_strips_leading_gt_quote_markers():
    raw = "Confirmed, we're on.\n> original question here\n> more quoted text"
    assert clean_reply(raw) == "Confirmed, we're on."
