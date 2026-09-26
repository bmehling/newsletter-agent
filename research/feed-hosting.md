# Private Feed hosting options

Research for [#3](https://github.com/bmehling/newsletter-agent/issues/3), part of map [#1](https://github.com/bmehling/newsletter-agent/issues/1). Facts only; the choice is a separate ticket. Sources checked 2026-09-26.

## Summary

- **Cloudflare R2 fits the free-tier numbers best.** It gives 10 GB-month storage and free egress. Our load is under 1 GB. It needs a Cloudflare account with a payment method, and the `r2.dev` URL is rate-limited and "for development only". Production use needs a custom domain on Cloudflare.
- **Object storage cannot check a password by itself.** For a public bucket, privacy means an unguessable URL. HTTP basic auth needs a small proxy in front of the bucket (for example, a Cloudflare Worker) or a self-hosted server.
- **Basic auth support in apps is uneven.** AntennaPod supports it in code. Overcast documents it. Pocket Casts calls its support "limited". Apple does not document it for listeners. An unguessable URL works in every app because it is just a URL.
- **Overcast and Pocket Casts fetch the Feed from their own servers.** The Feed URL, and any credentials in it, go to those vendors. AntennaPod fetches from the phone.
- **Static site hosts are a poor fit.** GitHub Pages sites are public and need a git commit per Episode. Cloudflare Pages caps each file at 25 MiB, which a 30-min MP3 at 128 kbps exceeds.

## Load estimate

30 min = 1,800 s. MP3 size = bitrate × seconds ÷ 8.

| Bitrate | Per Episode | 22 Episodes/month |
|---|---|---|
| 64 kbps mono (speech) | 14.4 MB | ~317 MB |
| 96 kbps | 21.6 MB | ~475 MB |
| 128 kbps | 28.8 MB | ~634 MB |

With one listener and 30-day retention, storage and egress are each under 1 GB/month. Feed polls (say hourly, plus server crawls from Overcast or Pocket Casts) add a few thousand small GET requests per month.

## Comparison

| Option | Free allowance | Cost at our load | Basic auth? | Unguessable URL? | Retention tooling | Setup for a non-expert | Notes |
|---|---|---|---|---|---|---|---|
| **Cloudflare R2** (public bucket) | 10 GB-month, 1M Class A, 10M Class B ops, egress free [1] | $0 | Not native. Needs a Worker (free plan: 100k requests/day) [5] | Yes. Public buckets do not list contents [2] | Lifecycle rule: delete by prefix after N days, usually within 24 h [4] | Medium. Account + payment method to enable R2 [3], bucket, API token, public access | `r2.dev` is rate-limited and "should only be used for development purposes"; custom domain needed for production [2] |
| **Backblaze B2** (public bucket) | 10 GB storage free; egress free up to 3× average stored; Class A/B/C calls free [6] | $0 | Not native. Needs a proxy | Yes | Lifecycle rules by `fileNamePrefix` (hide, then delete) [8] | Medium. First public bucket needs verified email and a payment history or small prepaid fee [7] | Bucket docs say public downloads beyond 1 GB/day are charged [9]. URL form `https://f000.backblazeb2.com/file/<bucket>/<file>` [7] |
| **Amazon S3** | New accounts: up to $200 credits; free plan 6 months [10] | ~$0.02/month storage; first 100 GB/month egress free [10] | Not native. Needs CloudFront/Lambda or similar | Yes | S3 lifecycle rules | Hard. IAM, bucket policy, block-public-access settings | Not near-free after credits expire, but still cents at this load |
| **Presigned URLs** (R2/S3) | n/a | n/a | n/a | Token in query string | n/a | n/a | R2 presigned URLs expire after at most 7 days [11]. Old Episodes and the Feed URL itself would break. Not suitable for a Feed |
| **GitHub Pages** | 1 GB site, 100 GB/month soft bandwidth [12] | $0 | No | Only by obscurity. Site is public even from a private repo, and private-repo Pages needs Pro [13] | Git commits; deleted MP3s stay in repo history | Easy for developers, awkward for audio | MP3s in git grow the repo past the 1 GB limit over time |
| **Cloudflare Pages** | 20,000 files, 500 builds/month [14] | $0 | Via Cloudflare Access or a Function | Yes | Redeploy | Medium | 25 MiB max file size [14]. A 128 kbps 30-min MP3 (28.8 MB) does not fit |
| **Self-host on the Mac** + Tailscale Funnel | Funnel on all Tailscale plans [15] | $0 | Yes. The agent's own HTTP server can require it | Yes | Agent deletes files | Medium. Install Tailscale, enable MagicDNS, HTTPS, Funnel policy [15] | Mac must be awake and online whenever an app fetches. Funnel has "non-configurable bandwidth limits" [15]. Ports 443/8443/10000 only |
| **Paid private-podcast hosts** | n/a | Not priced here | Varies | Varies | Built in | Easy | Assumed outside the near-free target; not researched |

## Privacy methods and app support

| Method | How it works | Where it works |
|---|---|---|
| **Unguessable URL** (random path, e.g. 128-bit token in the path) | Anyone with the link can read it. No listing on R2 public buckets [2] | Every app, since it is a plain URL. Pocket Casts documents this pattern for private feeds (its example is a Patreon `?auth=` token) [17] |
| **Token query string** | Same as above, but the server (Worker/self-host) checks the token | Every app. Needs a server-side check; bare object storage ignores it |
| **HTTP basic auth** | Server returns 401; app sends `Authorization: Basic` | See next table |

| App | Basic auth support | Who fetches the Feed | Source |
|---|---|---|---|
| **AntennaPod** (reference) | Yes. Prompts "Authentication required" on 401 when adding a Feed; sends credentials via `BasicAuthorizationInterceptor`. Past bugs with special characters in passwords and with streaming were fixed (issues closed 2020–2022) | The phone | [18], [19], [20], [21] |
| **Overcast** | Yes, via `https://user:password@host/...` in the URL. Treated as private: excluded from search and sharing. Basic-auth feeds cannot use the ping API | Overcast crawl servers fetch the Feed; the phone downloads the audio | [16] |
| **Pocket Casts** | "Limited". Embed `https://username:password@...`, URL-encode special characters, submit as Private | Pocket Casts servers fetch the Feed | [17], [22] |
| **Apple Podcasts** | Not documented by Apple for listeners. Apple documents "Follow a Show by URL" [23] but says nothing about passwords. Its creator rules require directory feeds to be public [24], which does not apply to a Feed added by URL. Community reports say it prompts for credentials; unverified | Not documented | [23], [24] |

Also: Overcast treats any Feed with `<itunes:block>` as private [16]. Adding `<itunes:block>Yes</itunes:block>` is cheap insurance against directory listing.

## Required Feed tags

RSS 2.0 core [25]:

- `<channel>`: `title`, `link`, `description`.
- `<item>` `<enclosure>`: `url`, `length` (bytes), `type` (MIME, `audio/mpeg`).
- `<guid>`: stable per Episode. `isPermaLink="false"` if it is not a URL.

Apple Podcasts requirements [24], [26] (other apps accept the same tags):

- Channel: `title`, `language`, `itunes:image` (artwork), `itunes:category`, `itunes:explicit` (`true`/`false`).
- Item: `title`, `enclosure`, `guid` that never changes, `pubDate` in RFC 2822 format.
- Server must answer HTTP `HEAD` and byte-range requests for streaming and artwork [24].
- ASCII-only file names and URLs [24].

Note: R2, B2 and S3 serve byte ranges and HEAD by default as S3-compatible stores; a self-hosted server must implement them.

## Retention and cleanup

- R2: lifecycle rule `Expiration: { Days: N }` on a prefix; removal usually within 24 h [4].
- B2: `daysFromUploadingToHiding` + `daysFromHidingToDeleting` on a `fileNamePrefix` [8].
- Either way, the agent must also drop expired items from the Feed XML, or apps will list Episodes whose files return 404.

## Shortlist (facts for the decision ticket)

1. **Cloudflare R2, public bucket, unguessable path.** $0 at this load. Works in every app. Weak points: needs a payment method on file; production use needs a custom domain on Cloudflare (domain cost); the Feed URL is the only secret, and Overcast/Pocket Casts servers will see it.
2. **Cloudflare R2 + Worker for basic auth or token check.** Same storage cost; Worker free plan (100k requests/day) covers the load [5]. Adds real access control and lets credentials be rotated without moving files. More setup and code.
3. **Backblaze B2, public bucket, unguessable path.** $0 at this load. Needs a small prepaid fee to unlock public buckets. B2 docs give two different free-egress rules (3× storage [6] vs 1 GB/day [9]); both cover one listener.
4. **Self-host on the Mac via Tailscale Funnel.** $0, no third-party storage, basic auth under our control. Fails if the Mac is asleep or offline when the app fetches, which conflicts with a pre-6:30 AM Episode unless the Mac stays awake.

Ruled out: presigned URLs (7-day expiry), GitHub Pages (public, git bloat), Cloudflare Pages (25 MiB file cap), Spotify (no private RSS; per map #1).

## Sources

1. Cloudflare R2 pricing: https://developers.cloudflare.com/r2/pricing/
2. Cloudflare R2 public buckets: https://developers.cloudflare.com/r2/buckets/public-buckets/
3. Cloudflare R2 get started: https://developers.cloudflare.com/r2/get-started/
4. Cloudflare R2 object lifecycles: https://developers.cloudflare.com/r2/buckets/object-lifecycles/
5. Cloudflare Workers limits: https://developers.cloudflare.com/workers/platform/limits/
6. Backblaze B2 pricing: https://www.backblaze.com/cloud-storage/pricing
7. Backblaze, deliver public B2 content through Cloudflare CDN: https://www.backblaze.com/docs/cloud-storage-deliver-public-backblaze-b2-content-through-cloudflare-cdn
8. Backblaze lifecycle rules: https://www.backblaze.com/docs/cloud-storage-lifecycle-rules
9. Backblaze buckets: https://www.backblaze.com/docs/cloud-storage-buckets
10. Amazon S3 pricing: https://aws.amazon.com/s3/pricing/
11. Cloudflare R2 presigned URLs: https://developers.cloudflare.com/r2/api/s3/presigned-urls/
12. GitHub Pages limits: https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits
13. GitHub Pages, creating a site (public even if repo is private; plan availability): https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site
14. Cloudflare Pages limits: https://developers.cloudflare.com/pages/platform/limits/
15. Tailscale Funnel: https://tailscale.com/kb/1223/funnel
16. Overcast podcaster info: https://overcast.fm/podcasterinfo
17. Pocket Casts, private or members-only feeds: https://support.pocketcasts.com/knowledge-base/private-or-members-only-feeds/
18. AntennaPod source, `BasicAuthorizationInterceptor`: https://github.com/AntennaPod/AntennaPod/blob/develop/net/common/src/main/java/de/danoeh/antennapod/net/common/BasicAuthorizationInterceptor.java
19. AntennaPod source, `OnlineFeedViewActivity` (auth prompt): https://github.com/AntennaPod/AntennaPod/blob/develop/app/src/main/java/de/danoeh/antennapod/ui/screen/onlinefeedview/OnlineFeedViewActivity.java
20. AntennaPod issue #3866, auth not used when streaming (closed 2020-02-17): https://github.com/AntennaPod/AntennaPod/issues/3866
21. AntennaPod issues #5715 (special characters, closed 2022-02-26) and #5855 (add by URL with credentials, closed 2022-04-26): https://github.com/AntennaPod/AntennaPod/issues/5715, https://github.com/AntennaPod/AntennaPod/issues/5855
22. Pocket Casts, password-protected feeds: https://support.pocketcasts.com/knowledge-base/password-protected-podcasts/
23. Apple Support, follow shows in Podcasts on Mac: https://support.apple.com/guide/podcasts/follow-or-unfollow-shows-podf17151dc/mac
24. Apple Podcasts for Creators, RSS feed requirements: https://podcasters.apple.com/support/823-podcast-requirements
25. RSS 2.0 specification: https://www.rssboard.org/rss-specification
26. Apple Podcasts for Creators, explicit content and categories: https://podcasters.apple.com/support/5440-explicit-content, https://podcasters.apple.com/support/1691-apple-podcasts-categories
