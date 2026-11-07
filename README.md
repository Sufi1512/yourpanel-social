# yourpanel-social

Public image assets for YourPanel's social media posts.

- `posts/<date>-<slug>/` holds the JPEG slides for one post.
- `posts/calendar.json` is the posting calendar. A daily scheduled task publishes
  the entry dated today, but only when its `status` is `approved`, then marks it
  `published` with the Instagram media id and link.
