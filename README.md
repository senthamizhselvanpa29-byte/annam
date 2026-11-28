# Annam

A free calorie and nutrition tracker, in English, தமிழ் and हिंदी.

- Log food from about 1,600 Indian dishes and basic foods, with calories, protein, carbs, fat, fibre, vitamins and minerals
- Scan a packet barcode, make your own foods, keep favourites, copy yesterday's meal
- Track your weight with a graph, and back up your data to a file
- Add a meal photo
- See a weekly report with simple tips
- Snap a meal photo and let AI find the foods and calories
- Ask the AI helper about protein, dinner ideas and your week (works offline too, with simpler answers)
- Healthy Indian recipes you can log with one tap
- Install it on your phone from the browser ("Add to Home screen"); it works offline

Your data stays on your own phone (browser storage). Nothing is sent to a server.

The website is published with GitHub Pages from the `main` branch.

## Food data

All foods are stored in `foods.json` as values per 100 g (calories, protein, carbs, fat, fibre, sugars, saturated fat, cholesterol, calcium, iron, magnesium, potassium, sodium, zinc, vitamin C, folate, vitamin A) plus common servings in grams.

- **Annam dishes (66):** South Indian and everyday dishes (pongal, kuzhambu, kootu, avial, idiyappam, adai, pesarattu, ragi kali, bisibelebath, puliyodharai, chettinad chicken and more), calculated from IFCT 2017 ingredient values with a cooked-weight yield.
- **Basic foods (542):** Indian Food Composition Tables 2017 (ICMR-NIN), via the `@ifct2017/compositions` package, with Tamil and Hindi names. These are raw foods (fruits, vegetables, grains, dals, nuts, milk, eggs, meat and fish).
- **Indian dishes (955):** Indian Nutrient Databank (INDB): Vijayakumar A, et al. *Current Developments in Nutrition* 2024 (CC BY 4.0), https://github.com/lindsayjaacks/Indian-Nutrient-Databank-INDB- . Annam corrects two things in the original numbers:
  - deep-frying oil ("oil for frying", 240 to 480 ml) was counted in full; it is replaced by the oil the food absorbs (10 to 25% of the dough or batter weight), so 1 poori is about 110 kcal instead of 921;
  - per-100 g values were based on raw ingredient weight; they now use cooked weight (cooking yield, or standard household measures such as katori 150 g when the recipe leaves out water).
  59 dishes that failed sanity checks (energy density, macros not adding up) were left out.
- **About 70 hand-checked foods** in `index.html`, with vitamins and minerals linked from a matching dish.
- **Packaged foods:** looked up by barcode in Open Food Facts (open database, ODbL).

Daily targets for vitamins and minerals follow the ICMR-NIN 2020 RDA for adults. Sodium is shown against a 2,000 mg limit, total sugars against 18% of daily calories (the 90 g a day reference intake) and saturated fat against 10%. Vitamin A is stored but not shown yet, because IFCT and INDB values are not all on the same basis.

`tools/food-data/` has the scripts that build `foods.json` (Python 3, needs the INDB Excel files and `@ifct2017/compositions`).
