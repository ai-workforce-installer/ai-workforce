# If the mail search stops after one page

Read this only when a mailbox search returns a full page (as many threads as you asked for) and no next-page token. Some connections never return one, so the rest of the window can't be paged to: search it in slices instead, each small enough to fit on one page.

- **Hour bands, newest first:** the usual search with `newer_than:<n+w>h older_than:<n>h` in place of the dates (same exclusions), starting at n = 0, until a band reaches the window start (in hours ago, rounded up). Width w: aim for about 30 threads a band, so w = window hours × 30 ÷ the first search's estimate, rounded down, at least 1. Going newest first makes neighbouring bands overlap as time passes, so nothing falls between them; drop repeated thread IDs.
- **A band comes back full:** search it again as 1-hour bands. A full 1-hour band: search it twice, with `category:promotions` and with `-category:promotions`; together they are the whole hour. Still full: that hour is under Not checked.
- **No Unix-second dates, and no `category:primary` beside a date:** some connections answer those with nothing, which looks like an empty mailbox. An empty answer for a period that should have mail is a failed search, never "no mail".
- Use the summary view (sender, subject, newest message), so the slices also serve the quick pass, and record each slice's query and count.

The search is **complete** when every slice came back below a full page and the bands reach the window start: Completed through moves as usual, and Coverage says "comprehensive (<n> slices)".
