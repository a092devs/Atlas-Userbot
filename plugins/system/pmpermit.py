from db.core import db
from utils.respond import respond
from utils.logger import log_event

# -------------------------------------------------
# Plugin metadata
# -------------------------------------------------

__plugin__ = {
    "name": "PMPermit",
    "category": "system",
    "description": "Control and manage private message permissions",
    "commands": {
        "pm": "Enable or disable PM Permit",
        "pmlimit": "Set PM warning limit",
        "ausers": "List approved users",
        "dusers": "List unapproved users",
        "a": "Approve user (PM only)",
        "d": "Disapprove user (PM only)",
    },
}

# -------------------------------------------------
# DB keys & defaults
# -------------------------------------------------

pmpermit_enabled = "pmpermit.enabled"
pmpermit_limit = "pmpermit.limit"

DEFAULT_LIMIT = 5

# -------------------------------------------------
# Helpers
# -------------------------------------------------

def is_enabled():
    return db.get(pmpermit_enabled, "0") == "1"


def limit():
    return int(db.get(pmpermit_limit, DEFAULT_LIMIT))


def approve(uid: int):
    db.set(f"pmpermit.allow.{uid}", 1)
    db.delete(f"pmpermit.warns.{uid}")


def disapprove(uid: int):
    db.delete(f"pmpermit.allow.{uid}")


# -------------------------------------------------
# Main handler
# -------------------------------------------------

async def handler(event, args):
    text = (event.raw_text or "").strip()
    cmd = text.lstrip("./").split()[0].lower()
    params = args

    # -------------------------------------------------
    # pm
    # -------------------------------------------------
    if cmd == "pm":
        if not params:
            return await respond(
                event,
                f"PM Permit status\n"
                f"Status: {'enabled' if is_enabled() else 'disabled'}\n"
                f"Limit: {limit()}\n\n"
                "Usage:\n"
                ".pm on\n"
                ".pm off"
            )

        if len(params) != 1:
            return await respond(event, "Usage: .pm on | .pm off")

        action = params[0].lower()

        if action in ("on", "enable", "1", "yes", "true"):
            db.set(pmpermit_enabled, 1)
            log_event("PM Permit Enabled")
            return await respond(event, "PM Permit enabled")

        if action in ("off", "disable", "0", "no", "false"):
            db.set(pmpermit_enabled, 0)
            log_event("PM Permit Disabled")
            return await respond(event, "PM Permit disabled")

        return await respond(event, "Usage: .pm on | .pm off")

    # -------------------------------------------------
    # pmlimit
    # -------------------------------------------------
    if cmd == "pmlimit":
        if len(params) != 1 or not params[0].isdigit():
            return await respond(event, "Usage: .pmlimit <number>")

        db.set(pmpermit_limit, params[0])
        log_event("PM Permit Limit Changed", f"limit={params[0]}")
        return await respond(event, f"PM limit set to {params[0]}")

    # -------------------------------------------------
    # ausers
    # -------------------------------------------------
    if cmd == "ausers":
        keys = db.keys("pmpermit.allow.")
        if not keys:
            return await respond(event, "No approved users found")

        users = "\n".join(k.split(".")[-1] for k in keys)
        return await respond(event, f"Approved users:\n{users}")

    # -------------------------------------------------
    # dusers
    # -------------------------------------------------
    if cmd == "dusers":
        warn_keys = db.keys("pmpermit.warns.")
        allow_keys = set(db.keys("pmpermit.allow."))

        unapproved = [
            k.split(".")[-1]
            for k in warn_keys
            if f"pmpermit.allow.{k.split('.')[-1]}" not in allow_keys
        ]

        if not unapproved:
            return await respond(event, "No unapproved users found")

        users = "\n".join(unapproved)
        return await respond(event, f"Unapproved users:\n{users}")

    # -------------------------------------------------
    # a / d (PM only)
    # -------------------------------------------------
    if cmd in ("a", "d"):
        if not event.is_private:
            return await respond(event, "This command works in private messages only")

        uid = event.chat_id

        if cmd == "a":
            approve(uid)
            log_event("PM User Approved", str(uid))
            return await respond(event, "User approved")

        if cmd == "d":
            disapprove(uid)
            log_event("PM User Disapproved", str(uid))
            return await respond(event, "User disapproved")
