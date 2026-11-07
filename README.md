# yourpanel-social

Public image assets for YourPanel's social media posts.

- `posts/<date>-<slug>/` holds the JPEG slides for one post.
- `posts/calendar.json` is the posting calendar. A daily scheduled task publishes
  the entry dated today, but only when its `status` is `approved`, then marks it
  `published` with the Instagram media id and link.

## aiwithsufi (separate Instagram page)

- `aiwithsufi/reels/<date>-<slug>/reel.mp4` — explainer Reels.
- `aiwithsufi/news/<date>/NN.jpg` — daily AI news carousels.
- `aiwithsufi/tools/news_carousel.py` — renders the news carousel (Charcoal & Gold, Montserrat).
The aiwithsufi folder is not part of YourPanel's calendar or its daily posting task.
