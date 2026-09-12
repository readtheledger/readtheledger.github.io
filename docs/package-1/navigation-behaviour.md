# Navigation, state and sharing — how the app behaves

Package 1 of the improvement roadmap. This is the documented contract; the
checks in `qa_package1.py` hold the app to it.

## Addresses

| View | Address | Title | Indexable |
|---|---|---|---|
| Front page | `/` | The Ledger — Finance, read properly | yes |
| A section | `/markets/`, `/central-banks/`, … | Markets — The Ledger | yes (a built page) |
| A Ledger story | `/story/<id>/` | *headline* — The Ledger | yes (a built page) |
| Newsstand | `/?view=newsstand` | Newsstand — The Ledger | no (`noindex`; `robots.txt` disallows `?view=`) |
| Saved | `/?view=saved` | Saved articles — The Ledger | no |
| A search | `/?q=term`, `/markets/?q=term` | Search: term — The Ledger | no (`?q=` disallowed) |
| A Newsstand preview | the address it was opened from | *headline* — The Ledger | — (no page of its own) |

Every topic in the strip and in the menu is an ordinary link to one of these
addresses. A plain click opens the view in place; a modified click (⌘/Ctrl,
middle button) opens it in a new tab.

A Newsstand item has no address of its own on this site, on purpose: its page
is the publisher's. Opening it does not change the address; **Read the original**
goes to the publisher, and **Share original** hands the system the publisher's
link, never a Ledger address. This is what keeps duplicate publisher-preview
pages out of search engines.

## Back, Forward, reload, new tab

- **Switching topic** replaces the address in place. Back does not walk through
  topics: it leaves the site, or closes an open story. This is how the tabs have
  always behaved and is unchanged.
- **Opening a story** pushes a history entry (a Ledger story at its own address,
  a Newsstand preview at the current one). **Back** closes it and restores the
  view you were in; **Forward** re-opens it. Escape and the reader's Back button
  go through history the same way.
- **Reload** lands on the same view: a section by its path, Newsstand or Saved
  by `?view=`, a search by `?q=` (the search box is open with the term in it),
  a Ledger story by its address.
- **New tab** on any of those addresses shows that view; a Saved view in a new
  tab shows *that device's* bookmarks, which is why it is not indexed.

## Sharing

`Share` hands the system share sheet the right link and reports what happened;
every message is in the toast (a live region), so it is read out as well as seen.

| Situation | What is shared | Message |
|---|---|---|
| Ledger story, share sheet completed | the story's own address | Shared this story's link — sent to the app you chose |
| Newsstand item, share sheet completed | the publisher's original link | Shared the original article's link — sent to the app you chose |
| Reader cancels the share sheet | — | Share cancelled |
| No share sheet (desktop browsers), or it fails | the link is copied | Sharing isn't available here — copied … instead |
| Copy fails too | — | Couldn't share or copy the link — it is *url* |

"Completed" means the reader chose an app and the sheet closed. It does not mean
anything was posted; the app cannot know that, and does not claim it.

`Copy` puts the article on the clipboard as plain text and says how many words.

## Refresh

The Newsstand is gathered by the site's build on a half-hour schedule that
GitHub runs when it can — a target, not a promise. Pull-to-refresh, the
Newsstand's **Check for a newer edition** button and the menu's **Check
Newsstand** all do the same thing and end in exactly one of three
messages:

- **Newer Newsstand edition loaded — gathered *time*** — a newer file was read.
- **No newer Newsstand edition — still the one gathered *time*** — the file has
  not changed since.
- **Couldn't reach the Newsstand — keeping the edition gathered *time*** — the
  file could not be read; nothing on show changed, and its time is still the
  true one.

A refresh never changes The Ledger's own articles: the edition line in the
masthead carries the publication's newest date separately from the Newsstand's
gathering time. **Reload app** (in the menu) is different — it clears this
device's cached copy of the app and loads it again.
