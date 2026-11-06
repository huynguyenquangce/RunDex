# Data Sources (candidates)

Research date: 2026-11-06. Method: web searches (Vietnamese and English) plus a fetch of each candidate's `robots.txt`. `robots.txt` is a technical signal only: **Terms of Service were NOT reviewed** and must be checked before any source is enabled. Search tool coverage was limited; Facebook groups are not covered and are not a source (ADR 0003).

## Principle
- Organizer sites are the source of truth (trust tier T1/T2 in ADR 0003).
- Aggregator blogs and listings are used only for **discovery** of event names, then verified on the organizer's page (T3, always reviewed). Their content is not copied.
- The registration link always points to the organizer's official page (scam warning: fake fan pages exist, see plo.vn report on a Quy Nhon registration fraud).

## Candidates

| Source | Kind | Role | robots.txt (checked) | Status |
|---|---|---|---|---|
| vietnamtrailseries.com (Topas; VTM Moc Chau) | Organizer | T1/T2 official trail events | Allows all except `/wp-admin/`; sitemap at `/sitemap_index.xml` | Good first source |
| hcmcmarathon.com | Organizer | T2 official | not fetched | Check; page showed "updates coming" |
| rundanang.com (Danang International Marathon) | Organizer | T2 official | not fetched | Check |
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

Conclusions and policy for RunDex:
- No source grants permission to reuse content; none forbids it on the homepage either. Linked legal pages must still be read before automating a source.
- Collect only factual fields (name, date, location, distances, fee, deadline, status). Do not copy descriptions, photos, posters or logos.
- Always link to the organizer's own registration page and show the source; offer a takedown/correction contact.
- Respect robots.txt, identify the crawler with an honest User-Agent, rate-limit politely, cache raw pages.
- For the MVP, seed data is curated manually from public pages; automated adapters are enabled per source only after its terms are read (and, where unclear, after asking the organizer).

## Observed data conflicts (why review matters)
- Vietnam Trail Marathon 2027: 16/01 on one source vs 15–16/01 on another; Ahotu showed registration not open while the organizer said open.
- HCMC Marathon 2027 (17/01): third-party listing gave a registration close date (2026-12-09) while the official site only showed "updates coming".
- Vietnam Mountain Marathon 2026: 17–20/9 vs 18–19/9 across sources.
- Mai Chau Vietnam Ultra Marathon 2026 shown as cancelled on ITRA and werun.world.

## Upcoming events spotted (seed candidates, all unverified)
Vietnam Highlands Trail by UTMB (Da Lat, 8–10/01/2027); Bac Ninh Legacy Marathon (10/01); Mang Den Ultra Trail (15–17/01); Vietnam Trail Marathon (Moc Chau, 16/01); HCMC Marathon (17/01); Tet Run Mien Nam (24/01); Mang Den La La Trail (6–7/03); Dalat Ultra Trail (19–21/03); Manulife Danang International Marathon (21/03); Tien Phong Marathon (March, Bac Ninh); The Explorer Trail (17/04); VnExpress Marathon Quy Nhon (April); Tay Lau Mountain Trail (8/05); Summer Symphony Trail (26/06); That Son Trail (20/11).
Each must be verified on the organizer's page before it enters the catalog.

## Next steps
1. Read Terms of Service for the first sources (vietnamtrailseries.com, hcmcmarathon.com, rundanang.com, irace.vn).
2. Choose 3–5 sources for the MVP; record in the source registry and an ADR.
3. Use the verified list above as seed data (~40–60 events) for week 1.
