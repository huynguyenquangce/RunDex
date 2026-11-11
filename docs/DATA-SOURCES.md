# Data Sources (candidates)

Research date: 2026-11-06. Method: web searches (Vietnamese and English) plus a fetch of each candidate's `robots.txt`. `robots.txt` is a technical signal only: **Terms of Service were NOT reviewed** and must be checked before any source is enabled. Search tool coverage was limited; Facebook groups are not covered and are not a source (ADR 0003).

## Principle
- Organizer sites are the source of truth (trust tier T1/T2 in ADR 0003).
- Aggregator blogs and listings are used only for **discovery** of event names, then verified on the organizer's page (T3, always reviewed). Their content is not copied.
- The registration link always points to the organizer's official page (scam warning: fake fan pages exist, see plo.vn report on a Quy Nhon registration fraud).

## Candidates

| Source | Kind | Role | robots.txt (checked) | Status |
|---|---|---|---|---|
| vietnamtrailseries.com (Topas; VTM Moc Chau) | Organizer | T1/T2 official trail events | Allows all except `/wp-admin/`; sitemap at `/sitemap_index.xml` | robots OK, but Service Agreement restricts use: authorization from Topas Travel needed before any automated use |
| hcmcmarathon.com | Organizer | T2 official | No paths blocked; sitemap `/sitemap_index.xml` | No terms found; ask permission; page showed "updates coming" |
| rundanang.com (Danang International Marathon) | Organizer | T2 official | Blocks only `/wp-admin/`; sitemap `/wp-sitemap.xml` | No retrievable terms; ask permission |
| irace.vn event pages (e.g. Vietnam Trail Marathon) | Ticketing platform | T2 for events it sells | Blocks ~90 named bots and some `/go` paths; generic agents only barred from one JSON file | ToS must be checked; use respectfully |
| asiatrailmaster.com, ahotu.com, marathonscout.com, finishers.com | International listings | T3 discovery | ahotu returned 403; others not fetched | Likely restrictive; low priority |
| itra.run | Trail race registry | T3 for UTMB/ITRA events | robots not retrievable (404/empty) | Check ToS; low priority |
| thegioichaybo.vn, tikpik.vn, linh.academy, happyrun.vn, pace8.vn, cityguide.vn | Third-party blogs/listings | T3 discovery only | thegioichaybo: `/search`, `/cart` etc. disallowed, sitemap present, crawl-delay for some bots; tikpik 404; others not fetched | Content is third-party; do not copy; verify on organizer pages |
| Official news sites (VnExpress, Tien Phong, baolaocai.vn, etc.) | News | T3 for announcements | not fetched | Slow-moving but good for new-event discovery |

## Terms review (2026-11-06, homepage level only)
Method: fetched each site's homepage and looked for legal pages. The text of linked legal pages was NOT read, so this is a first pass, not legal advice.

| Site | Findings | Registration URL(s) found |
|---|---|---|
| vietnamtrailseries.com (Topas) | Has Service Agreement, General Trading Conditions, Privacy Policy, Race Rules, per-event T&Cs (linked, unread). Footer: "All Rights Reserved". No statement on reuse/scraping on the homepage. | https://vietnamtrailseries.com/trail-marathon/vtm-book-now/ and https://vietnamtrailseries.com/registration-payment/ |
| hcmcmarathon.com (Pulse Active) | No terms/privacy found. Footer: copyright Pulse Active. Date shown: 17 Jan 2027, start/finish 30/4 Park, Le Duan. Fees and deadline not on homepage. | https://hcmcmarathon.com/register/ (EN), https://hcmcmarathon.com/vi/dang-ky/ (VI) |
| rundanang.com (Pulse Active) | Footer label "Term Condition / Privacy Policy" with no retrievable link. Copyright Pulse Active. Date only as a countdown. | https://rundanang.com/dang-ky/ |
| irace.vn | No legal page found on the homepage (FAQ/user manual exist, unread). | n/a (ticketing platform; event pages) |

### Vietnam Trail Series legal pages (read 2026-11-06)
- Service Agreement (operator: Phu Thinh Ltd. Co / Topas Travel): the site "is protected by copyright law", is "for informational purposes and online registration for races only", "not for any other commercial use", and research, reference and information sharing must be "authorized by Topas Travel and clearly cited".
- General Trading Conditions and Privacy Policy: no clause on content reuse or automated access (they cover fees/participation and registrants' personal data).
- Consequence: republishing their event information in RunDex, and any automated collection, should be authorized by Topas Travel and cited. Because of this, keep automated collection from this source off by default; use manually curated, clearly cited facts and link to the official page.
- The other sites (Pulse Active: hcmcmarathon.com, rundanang.com; irace.vn) show no retrievable terms; that is not permission. Ask first as well.
- Owner decision (2026-11-06): RunDex is a personal, non-commercial project, so permission requests to organizers are optional and will not be sent for now. Revisit if the app or repo is ever published commercially, in an app store, or promoted beyond personal/challenge use.
- Not legal advice.

Conclusions and policy for RunDex:
- No source grants permission to reuse content; none forbids it on the homepage either. Linked legal pages must still be read before automating a source.
- Collect only factual fields (name, date, location, distances, fee, deadline, status). Do not copy descriptions, photos, posters or logos.
- Always link to the organizer's own registration page and show the source; offer a takedown/correction contact.
- Respect robots.txt, identify the crawler with an honest User-Agent, rate-limit politely, cache raw pages.
- For the MVP, seed data is curated manually from public pages; automated adapters are enabled per source only after its terms are read (and, where unclear, after asking the organizer).

## pace8.vn (evaluated 2026-11-11)
Ticketing and registration portal of PaceX Viet Nam JSC ("cổng thông tin các giải chạy", also e-waiver and racekit check-in). Checked by hand: robots.txt, sitemap, the event listing, and one event page (Vietnam Trail Marathon 2027). Five polite requests, honest User-Agent.

- **robots.txt:** allows everything except `/users/`, `/portal/`, `/crons/`, `/scripts/`, `/frames/`; no crawl-delay; points to `https://pace8.vn/sitemap.xml`.
- **Terms:** `/dieu-khoan-su-dung.html` exists but its text could not be retrieved by our fetch; no reuse clause seen; footer "©2026 CÔNG TY CỔ PHẦN PACEX VIỆT NAM". Same stance as the other sources: facts only, cite the source, link to the registration page.
- **Coverage:** the sitemap lists 439 URLs, about 197 single event pages, all with `lastmod` (recent months: Oct 2026 17, Nov 2026 11). The `/su-kien` listing shows ROAD 23, TRAIL 8, TRIATHLON 1 (about 32 events currently on sale; the page also says "100+"). It only covers events sold through pace8 (e.g. Vietnam Trail Marathon, Dalat Ultra Trail, Mang Den LaLa Trail, Cuc Phuong Jungle Paths, HCMC Marathon 2027, Can Tho Heritage, Tet Run), not every event in Vietnam.
- **The listing cards are not in the static HTML** (no event links in the downloaded page), so discovery should use the sitemap, not the listing.
- **Structured data:** every event page carries a schema.org `Event` block (JSON-LD) with `name`, `startDate`, `endDate` (ISO with +07:00), `eventStatus`, `location` (text such as "Mộc Châu, Sơn La"), `organizer` (name and pace8 organizer page), and `offers`: one per distance with `name` (e.g. "21Km"), `price` (VND), `availability` (InStock / SoldOut), `validFrom`, `url`. Example: VTM 2027 lists 5 Km trẻ em 1,000,000; 5 Km 1,700,000; 10 Km 1,900,000; 21 Km 3,300,000; 50 Km 4,100,000; 70 Km 4,400,000; all SoldOut.
- **Not on the page:** start time per distance, elevation, cut-off, registration deadline (`validThrough` is empty), slots. The ticket link is the pace8 event page itself, and the button shows "Hết vé" when sold out.
- **Why it matters:** the data is machine-readable, so it can be parsed by rules instead of an LLM (no extraction step, no invented values), and it fills the fees and sold-out state that the blog sources lack. Proposed: sitemap source filtered to `/su-kien/<slug>`, a JSON-LD extractor feeding the normal verify, validate, diff, tier path, `SoldOut` on every offer mapped to `registration_closed`. Tier to decide (ticketing platform, not the organizer: tier 1 auto-apply, or tier 2 so date changes are reviewed).
- **Status (2026-11-11): integrated** as source `pace8` (tier 2, sitemap filtered to `/su-kien/<slug>`, `extractor: jsonld`, see ADR 0007). Fees per distance and sold-out state are filled; start time, elevation and cut-off stay empty. Date, status and link changes are reviewed by a person.
- Caveats: slugs can redirect (`/su-kien/hcmc-marathon-2027` answered 301), the sitemap contains past events and non-event pages (`ket-thuc-dang-ky`, `flash-sale`, group registration pages), and prices are for the pace8 sales channel.

## Observed data conflicts (why review matters)
- Vietnam Trail Marathon 2027: 16/01 on one source vs 15–16/01 on another; Ahotu showed registration not open while the organizer said open.
- HCMC Marathon 2027 (17/01): third-party listing gave a registration close date (2026-12-09) while the official site only showed "updates coming".
- Vietnam Mountain Marathon 2026: 17–20/9 vs 18–19/9 across sources.
- Mai Chau Vietnam Ultra Marathon 2026 shown as cancelled on ITRA and werun.world.

## Upcoming events spotted (seed candidates, all unverified)
Vietnam Highlands Trail by UTMB (Da Lat, 8–10/01/2027); Bac Ninh Legacy Marathon (10/01); Mang Den Ultra Trail (15–17/01); Vietnam Trail Marathon (Moc Chau, 16/01); HCMC Marathon (17/01); Tet Run Mien Nam (24/01); Mang Den La La Trail (6–7/03); Dalat Ultra Trail (19–21/03); Manulife Danang International Marathon (21/03); Tien Phong Marathon (March, Bac Ninh); The Explorer Trail (17/04); VnExpress Marathon Quy Nhon (April); Tay Lau Mountain Trail (8/05); Summer Symphony Trail (26/06); That Son Trail (20/11).
Each must be verified on the organizer's page before it enters the catalog.

## Next steps
1. Permission requests are optional (owner decision); template kept in docs/ORGANIZER-OUTREACH.md in case it is needed later.
2. Choose 3–5 sources for the MVP; record in the source registry and an ADR.
3. Use the verified list above as seed data (~40–60 events) for week 1.
