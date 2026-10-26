# Coliseum reminder: design

Describes the bot as built.

## Intent

Fire Emblem Heroes players get reminded before the weekly Coliseum (and Aether Raids) season closes, so they
can finish their battles in time.

## Behavior

- Coliseum closes on **Monday at 23:00 UTC**. On Mondays, at **18:00 and 22:00 UTC** (5 hours and 1 hour
  before), the bot posts in the configured channel:
  `Coliseum/Aether Raids closes <t:1761001200:R> at <t:1761001200:f>`.
  The `<t:...>` tags are Discord timestamps, which every reader sees in their own timezone ("in 5 hours",
  and the date and time).
- All scheduling is in UTC, whatever the host's timezone.
- The task runs daily at both times and does nothing on other weekdays.

## Configuration

`tasks.coliseum_notification_channel_id` (default empty). Empty turns the reminders off, with a warning in
the log at startup. The channel ID is read once, when the module is imported.

## Lifecycle

- `on_ready` starts the loop (`start_coliseum_notification`). `on_ready` fires again after reconnects, so the
  loop is started only when it isn't running yet.
- A configured channel the bot can't see is logged as an error at each reminder time, and the reminder is
  skipped.

## Non-goals

- No other games or events, and no reminders configurable from Discord.
- No catching up: a reminder time missed while the bot was offline is not sent later.

## Tests

`tests/fjormcord/bot/artping/test_coliseum.py`.
