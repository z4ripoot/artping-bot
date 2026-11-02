# Resources: design

## Intent

The community has messages and websites it points people to again and again, such as a hall of fame (`hof`).
Admins save each one under a short name, and anyone can then post it with `~<name>`, e.g. `~hof`, instead of
searching for the original message or link.

## Goals

- Admins set a resource with `~setresource (resource name) (link)`, where the link is a Discord message link
  or a website link.
- Everyone posts a resource with `~<resource name>`.
- For a Discord message link the resource is the message's **text**, copied once when the resource is set.
- Admins can remove resources, and everyone can list them.

## Non-goals

- No images, files or embeds from the linked message: the text is enough.
- No following later edits or deletion of the linked message. Running `~setresource` again with the same
  name refreshes the copy.
- No arguments to resource commands; anything after `~hof` is ignored.

## Anti-goals

- A resource must never hide or replace a built-in command.
- Posting a resource must never ping anyone, even if the copied message mentioned users or roles.

## Behavior (decided with the user)

- `~setresource hof <Discord message link>`: the bot fetches the message and stores its text in the
  database. `~hof` posts that stored text, as it was when set.
- `~setresource hof <website link>`: the link itself is stored, and `~hof` posts the link (Discord shows its
  usual preview).
- Setting a name that already exists replaces that resource.
- A resource name can't be the name of an existing command (`help`, `artping`, `setresource`, ...).
- Names ignore case: `~HOF` posts `hof`.
- `~setresource` is admin-only (silently ignored for non-admins, like the other admin commands); `~hof` works
  for everyone.
- `~removeresource (resource name)`, admins: removes a resource.
- The copied text doesn't ping anyone.

## Behavior (my calls, the user can override)

- **Listing:** `~resources`, for everyone, replies with the names alphabetically, e.g. `Resources: ~faq, ~hof`,
  or `No resources have been set yet`. It's in the art ping section of `~help`, the admin commands under
  `Admin Commands:`.
- **Replies:** `Resource hof has been set`, `Resource hof has been removed`, and refusals:
  - name taken by a command: `~help is a command, so it can't be a resource`
  - unknown name for `~removeresource`: `Resource hof doesn't exist`
  - not a link: `That isn't a link to a Discord message or a website`
  - a Discord message the bot can't fetch (deleted, a server the bot isn't in, or no permission to read the
    channel): `Couldn't read that message. Check the link, and that the bot can read that channel`
  - a message without text (e.g. only an image): `That message has no text`
- **Name format:** one word, as for every argument. A leading `~` is dropped, so `~setresource ~hof ...`
  works too. Names are stored as typed (not normalized, like currency names) and matched ignoring case;
  `~resources` shows them as stored. A name may only hold letters, digits, `_` and `-`, so names stay easy to
  type and can't contain mention syntax.
- **Link recognition:** a Discord message link is `https://discord.com/channels/<server>/<channel>/<message>`,
  also with `ptb.`/`canary.` and `discordapp.com`. Any other `http://` or `https://` link is a website link.
  The link must be the third word; more words are refused with the one-name hint, so a resource is never a
  free-form sentence.
- **Stored data:** the name, the posted content (the copied text, or the website link), and the source link,
  so admins can see where a resource came from later. `~resources` shows only names.
- **Dispatch:** `on_message` looks the first word up in the commands first and only then in the resources,
  so even if a command is added later with the same name as a resource, the command wins. The silence rules
  stay: unknown names still get no reply.
- **Mentions:** resource replies are sent with no mentions allowed at all (`discord.AllowedMentions.none()`),
  instead of the client's default that allows user mentions.
- **Cooldown:** the one every command has, posting a resource included.
- **Bots:** ignored, as for all messages.

## Database

`db/migrations/006_resources.sql`:

```sql
CREATE TABLE RESOURCE (
    NAME TEXT NOT NULL PRIMARY KEY COLLATE NOCASE,
    CONTENT TEXT NOT NULL,
    SOURCE TEXT NOT NULL
);
```

Setting an existing name replaces the whole row, so the name is stored as typed the last time.

The message's raw `content` is stored (mentions stay as `<@id>`, harmless with no mentions allowed). A
forwarded message has no text of its own and gets the "no text" refusal. "Letters" in names means ASCII
letters (`[A-Za-z0-9_-]+`).

## Fitting the architecture

- **model:** `model/resource.Resource` (`name`, `content`, `source`).
- **repository:** `repository/resource_repository.py`: get by name, get all names, set (insert or replace),
  remove.
- **service:** `service/resource_service.py` with the handlers `set_resource` (async: it fetches the message),
  `remove_resource`, `list_resources`, and a lookup the client uses for `~<name>`.
- **fetching:** `client.get_partial_messageable(channel_id).fetch_message(message_id)` needs no channel cache;
  `discord.NotFound`, `discord.Forbidden` and other `discord.HTTPException`s become the "Couldn't read" refusal.
- **commands:** `~resources` (everyone), `~setresource`, `~removeresource` (admin) in the `COMMANDS` table.
  The name check uses `COMMANDS_BY_NAME`, which lives in `commands.py`; the service needs it without a
  circular import (`commands.py` imports the services), e.g. by the client passing it, or by importing
  `commands` inside the function. Builder's call.
- **bot:** after a miss in `COMMANDS_BY_NAME`, `on_message` asks the resource service; on a hit it sends the
  content, split under the 2000-character limit, with no mentions allowed.

## Tests

- Service tests: setting from a message link (text stored, not the link), from a website link, replacing,
  name clash with a command (any casing, with and without `~`), invalid names and links, unfetchable message,
  message without text, removing, listing.
- `test_bot.py`: `~hof` posts the content, any casing; unknown names stay silent; a command wins over a
  resource of the same name; resource replies allow no mentions; non-admin `~setresource` is ignored.
- `test_database.py`: migration `006` applies.
- `tests/fakes.py`: `get_partial_messageable` on `FakeClient`, returning a channel whose `fetch_message`
  finds messages with `content`; the channel send records the `allowed_mentions` it was given.

## Left to the builder

- Exact wording beyond the replies listed above.
- How the service gets the command names (see Fitting the architecture).
- Update `README.md` (command table) and `CLAUDE.md` (architecture and schema), and the command handling spec
  for the resource lookup in dispatch.
