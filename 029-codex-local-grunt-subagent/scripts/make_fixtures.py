#!/usr/bin/env python3
"""Write the two #029 fixtures (synthetic text written for this experiment) and their answer keys (kept outside the fixture dirs)."""
import json, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = [("The battery easily lasts two days and charging is quick.", "positive"),
("Stopped working after a week. Waste of money.", "negative"),
("Exactly as described, arrived early, very happy.", "positive"),
("The strap broke the first time I used it.", "negative"),
("Not bad at all for the price; I'd buy it again.", "positive"),
("I wanted to love it, but the screen is too dim to read outdoors.", "negative"),
("Customer support replaced it without any fuss. Great service.", "positive"),
("Smells of cheap plastic and the lid doesn't close properly.", "negative"),
("Oh great, another charger that dies in a month. Brilliant.", "negative"),
("Fits perfectly and the colour is even nicer in person.", "positive"),
("It's fine, I guess, but it stopped pairing with my phone twice already, so I'm returning it.", "negative"),
("Never had a kettle boil this fast. Love it.", "positive"),
("The instructions were useless and two screws were missing.", "negative"),
("I was sceptical, but it genuinely improved my sleep.", "positive"),
("Couldn't be happier with this purchase.", "positive"),
("Couldn't be more disappointed with this purchase.", "negative"),
("Sound quality is crisp and the bass is not overdone.", "positive"),
("Looks nice in photos; in reality it feels flimsy and wobbles.", "negative"),
("No complaints after six months of daily use.", "positive"),
("Arrived late, box crushed, and the glass was cracked.", "negative"),
("Does what it says, nothing more, nothing less, and I'm happy with that.", "positive"),
("Five stars for the design, zero for the battery, which barely lasts an hour.", "negative"),
("My kids use it every day and it still looks new.", "positive"),
("I wouldn't recommend it to anyone.", "negative")]
D = [("The meeting was moved to 3 March 2025.", "2025-03-03"),
("Invoice dated 12/07/2024 (day/month/year).", "2024-07-12"),
("Deadline: July 4, 2026.", "2026-07-04"),
("The shop reopened on the 21st of September 2023.", "2023-09-21"),
("Released 2019-11-05 in Europe.", "2019-11-05"),
("We met on Feb. 29, 2024.", "2024-02-29"),
("Shipped 01.10.2025 (European format, day first).", "2025-10-01"),
("Her flight leaves on Sunday, 8 June 2025.", "2025-06-08"),
("The lease ends 31-Dec-2027.", "2027-12-31"),
("Report filed on 5/14/2022 (US format).", "2022-05-14"),
("The bridge opened on 27 May 1937.", "1937-05-27"),
("Payment received Jan 2nd, 2026.", "2026-01-02"),
("Warranty valid until 2028/02/15.", "2028-02-15"),
("The concert is on the 1st of November, 2025.", "2025-11-01"),
("Exam scheduled for 09 Aug 2024.", "2024-08-09"),
("He was born on April 23rd 1990.", "1990-04-23"),
("Version 2 shipped on 3rd Oct 2021.", "2021-10-03"),
("Membership started 06/30/2023 (US format).", "2023-06-30"),
("The festival begins 15 Jan. 2026.", "2026-01-15"),
("Closing date: 2025.12.01 (year.month.day).", "2025-12-01")]
F = os.path.join(HERE, "fixtures"); K = os.path.join(HERE, "keys")
with open(f"{F}/G01_sentiment/reviews.txt", "w") as f:
    for i, (t, _) in enumerate(R, 1): f.write(f"{i}\t{t}\n")
with open(f"{F}/G02_dates/sentences.txt", "w") as f:
    for i, (t, _) in enumerate(D, 1): f.write(f"{i}\t{t}\n")
json.dump({str(i): l for i, (_, l) in enumerate(R, 1)}, open(f"{K}/G01_sentiment.json", "w"))
json.dump({str(i): l for i, (_, l) in enumerate(D, 1)}, open(f"{K}/G02_dates.json", "w"))
open(f"{F}/G01_sentiment/TASK.md", "w").write("Write `labels.csv` with header `id,label` and one row per line of `reviews.txt` (tab-separated id and text); label is `positive` or `negative`.\n")
open(f"{F}/G02_dates/TASK.md", "w").write("Write `dates.csv` with header `id,date` and one row per line of `sentences.txt` (tab-separated id and text); date is the date in the sentence as ISO `YYYY-MM-DD`.\n")
print("ok")
