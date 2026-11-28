# Annam

A free calorie and nutrition tracker, in English, தமிழ் and हिंदी.

- Log food from about 1,600 Indian dishes and basic foods, with calories, protein, carbs, fat, fibre, vitamins and minerals
- Scan a packet barcode, make your own foods, keep favourites, copy yesterday's meal
- Packet label: take a photo of the nutrition label, check the numbers (per 100 g or per serving), add the pack weight and how many grams you ate. The packet is saved in My foods with its exact numbers
- Search understands half-typed words ("samba w"), spelling slips and other spellings (sambhar, chapathi, biriyani, uppuma, daal) and Tamil or Hindi names
- Exact portions: small / medium / large, ¼ to 3 servings, exact grams, or weigh your plate before and after eating
- Log past days, log exercise (calories burned are added to your budget, or switch this off), set your own calorie goal, see your BMI (Indian cut-offs)
- Quick add: type only the calories (and protein, carbs, fat if you know them) for food you can't find, like a wedding meal
- Steps (typed from your phone or watch, with a step goal; walking above your usual day adds calories) and last night's sleep (hours and how well you slept)
- Body measurements (waist, hip, chest, arm, thigh, neck, body fat) with a waist check (Indian cut-offs: 90 cm men, 80 cm women), waist-to-height ratio, a body fat estimate from the tape (US Navy method) and a waist graph
- Goals: how fast to lose or gain (0.25 to 1 kg a week) with a "reach your goal weight around" date, a protein / carbs / fat split (balanced, high protein, low carb or your own %), a water goal and a step goal
- A calorie target for each meal (breakfast 25%, lunch 35%, snacks 10%, dinner 30%)
- Day score out of 100 (calories near goal, protein, fibre, water and regular meals), with tips; today is compared with what you need by that time of day
- Recipe maker: weigh your ingredients and the cooked pot, Annam works out one portion
- Track your weight with a graph, and back up your data to a file
- Add a meal photo
- Report for 7 or 30 days with simple tips, your top foods (and where most sugar and salt came from), activity and sleep, and badges
- Download your food diary and a daily summary (open in Excel or Google Sheets), print the report or save it as PDF for your doctor, and share your day on WhatsApp
- Snap a meal photo and let AI find the foods and calories
- Ask the AI helper about protein, dinner ideas and your week (works offline too, with simpler answers)
- Weekly diet plans (veg, egg or non-veg; South Indian, North Indian or mixed; balanced, high protein or diabetes friendly), sized to your calorie goal, with swap and one-tap logging
- Fasting timer (12 to 20 hours) with stages, streak and history
- Reminders for meals, water and weekly weigh-in, plus Google Calendar links and a calendar file for reminders that always come
- Diabetes mode: sugar log with targets, carbs per meal, sweet and high-fibre food tags, 14-day sugar chart. It is not medical advice; follow your doctor
- Type or speak several foods at once, in English, Tamil or Hindi ("2 idli and 1 bowl sambar", "இரண்டு இட்லி ஒரு கிண்ணம் சாம்பார்", "दो रोटी और एक कटोरी दाल")
- Save a meal you eat often (My meals) and add it again with one tap
- Healthy Indian recipes you can log with one tap (in Plans)
- Install it on your phone from the browser ("Add to Home screen"); it works offline

Your food log, sugar readings and settings stay on your own phone (browser storage). Only what you choose to send goes out: a meal photo or a question for the AI helper goes to the Annam AI server, a barcode goes to Open Food Facts, and the mic uses your phone browser's own speech service.

The website is published with GitHub Pages from the `main` branch.

## Food data

All foods are stored in `foods.json` as values per 100 g (calories, protein, carbs, fat, fibre, sugars, saturated fat, cholesterol, calcium, iron, magnesium, potassium, sodium, zinc, vitamin C, folate, vitamin A) plus common servings in grams.

- **Annam dishes (98):** South Indian and everyday dishes (pongal, kuzhambu, kootu, avial, idiyappam, adai, pesarattu, ragi kali, bisibelebath, puliyodharai, chettinad chicken and more), calculated from IFCT 2017 ingredient values with a cooked-weight yield. This includes samba wheat (broken wheat) rava and its upma, pongal, kanji, dosa and payasam; 13 kinds of sambar (drumstick, brinjal, bottle gourd, ash gourd, pumpkin, radish, okra, small onion, mixed vegetable, tiffin, no oil, no dal, arachuvitta); cooked seeraga samba, basmati, sona masoori, ponni, matta, mappillai samba and kavuni rice; and seeraga samba biryani (chicken, mutton, egg, veg). IFCT has no separate entry for most rice types, so each uses the nearest IFCT rice (raw milled, parboiled milled, or brown rice for the red and black rices) and a typical cooked yield. Each dish also lists the other names people use for it (for example samba godumai, dalia, sorakkai sambar).
- **Basic foods (542):** Indian Food Composition Tables 2017 (ICMR-NIN), via the `@ifct2017/compositions` package, with Tamil and Hindi names. These are raw foods (fruits, vegetables, grains, dals, nuts, milk, eggs, meat and fish).
- **Indian dishes (955):** Indian Nutrient Databank (INDB): Vijayakumar A, et al. *Current Developments in Nutrition* 2024 (CC BY 4.0), https://github.com/lindsayjaacks/Indian-Nutrient-Databank-INDB- . Annam corrects two things in the original numbers:
  - deep-frying oil ("oil for frying", 240 to 480 ml) was counted in full; it is replaced by the oil the food absorbs (10 to 25% of the dough or batter weight), so 1 poori is about 110 kcal instead of 921;
  - per-100 g values were based on raw ingredient weight; they now use cooked weight (cooking yield, or standard household measures such as katori 150 g when the recipe leaves out water).
  59 dishes that failed sanity checks (energy density, macros not adding up) were left out.
- **About 70 hand-checked foods** in `index.html`, with vitamins and minerals linked from a matching dish.
- **Packaged foods:** looked up by barcode in Open Food Facts (open database, ODbL).

Daily targets for vitamins and minerals follow the ICMR-NIN 2020 RDA for adults. Sodium is shown against a 2,000 mg limit, total sugars against 18% of daily calories (the 90 g a day reference intake) and saturated fat against 10%. Vitamin A is stored but not shown yet, because IFCT and INDB values are not all on the same basis.

`tools/food-data/` has the scripts that build `foods.json` (Python 3, needs the INDB Excel files and `@ifct2017/compositions`).
