"""Rebuild Annam's INDB food file with cooked weights and fixed frying oil.

INDB (Vijayakumar et al. 2024, CC BY 4.0) sums raw ingredients. Two problems:
1. Deep-frying oil ("for frying", 240-480 ml) is counted in full. A poori comes
   out at 921 kcal. We replace it with the oil the food really absorbs.
2. Per-100 g values use raw ingredient weight (water often not listed), so
   grams per serving are wrong for cooked food. We use standard cooked
   household measures (ICMR-NIN style: katori 150 g etc.) for bowls, plates
   and glasses, and the recipe's own weight for countable pieces.
"""
import json, re, sys

D = json.load(open('indb.json'))
S = json.load(open('serv.json'))
R = json.load(open('recipes.json'))

NUT = ['energy_kcal', 'protein_g', 'carb_g', 'fat_g', 'fibre_g', 'freesugar_g', 'sfa_mg',
       'cholesterol_mg', 'calcium_mg', 'iron_mg', 'magnesium_mg', 'potassium_mg', 'sodium_mg',
       'zinc_mg', 'vitc_mg', 'folate_ug', 'vita_ug']
# sunflower oil per 100 g (UK CoFID 17-045, as used by INDB code T508)
OIL = {'energy_kcal': 899, 'fat_g': 99.9, 'sfa_mg': 12000, 'iron_mg': 0.1}

def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0

# ---------- frying oil per recipe (grams, as INDB converted them) ----------
fry = {}
for r in R:
    txt = str(r['amount_org'] or '').lower()
    if r['food_code'] == 'T508' and re.search(r'fr[yi]', txt):
        a, u = num(r['amount']), r['unit']
        g = a * 240 if u == 'C' else a * 13.5 if u == 'tbsp' else a * 4 if u == 'tsp' else a
        if g >= 60:  # deep frying; small "2 tbsp for frying" is shallow and stays counted
            fry[r['recipe_code']] = fry.get(r['recipe_code'], 0) + g
nonabs = {}
for r in R:
    t = (str(r['ingredient_name_org']) + ' ' + str(r['amount_org'])).lower()
    if r['food_code'] == 'K505' and re.search(r'for soaking|for steaming', t):
        a = num(r['amount']); nonabs[r['recipe_code']] = nonabs.get(r['recipe_code'], 0) + (a * 240 if r['unit'] == 'C' else a)
has_water = {r['recipe_code'] for r in R if r['food_code'] == 'K505'}
ing_w = {}
for r in R:  # rough own weight sum, only used when INDB has no serving data
    a, u = num(r['amount']), r['unit']
    g = {'g': a, 'ml': a, 'tsp': a * 4, 'tbsp': a * 13, 'C': a * 200, 'sprig': a * 2}.get(u, a * 3)
    ing_w[r['recipe_code']] = ing_w.get(r['recipe_code'], 0) + g

def absorb_rate(name):
    n = name.lower()
    if re.search(r'chips|crisp|wafer|papad|sev|namak para|mathri|chakli|murukku', n): return 0.25
    if re.search(r'samosa|kachori|gujiya|gunjia|puff|shakarpara|karanji', n): return 0.20
    if re.search(r'cutlet|tikki|kabab|kebab|chop|patty|croquette|fish|chicken|mutton|egg|paneer', n): return 0.10
    if re.search(r'jamun|jalebi|imarti|malpua|balushahi', n): return 0.12
    return 0.15  # poori, bhatura, vada, pakora, bonda, bajji ...

# ---------- cooked household grams per serving unit ----------
UNIT_G = {
    'bowl': 150, 'curry bowl': 150, 'small bowl': 100, 'soup bowl': 200, 'plate': 250,
    'small plate': 150, 'cup': 150, 'tea cup': 150, 'glass': 200, 'tall glass': 300,
    'juice glass': 200, 'tall stemmed glass': 200, 'sundae glass': 150, 'half-pints': 280,
    'ice cream cup': 80, 'ice-cream cup': 80, 'tablespoon': 15, 'teaspoon': 5,
    'idli': 40, 'dosa': 85, 'uttapam': 120, 'appam': 60, 'pesarattu': 90, 'puttu': 120,
    'parantha': 90, 'roti': 50, 'chapati': 40, 'naan': 90, 'thepla': 40, 'khakhra': 20,
    'cheela': 70, 'pancake': 70, 'dhokla': 30, 'slice': 30, 'toast': 35, 'sandwich': 120,
    'triangle': 40, 'toasted triangle': 30, 'gm': 1, 'ml': 1,
}
NAME_G = [  # (regex on name, unit or None, grams) - first match wins
    (r'masala dosa', 'dosa', 150), (r'rava dosa|semolina dosa', 'dosa', 75),
    (r'stuffed|aloo|potato|gobhi|cauliflower|mooli|radish|paneer|keema|dal par|matar|pea', 'parantha', 110),
    (r'porridge|daliya|dalia|cornflakes|flakes|muesli|oat|murmura|puffed', 'bowl', 200),
    (r'kheer|payasam|custard|halwa|halva|sheera|kesari', 'bowl', 120),
    (r'raita', 'bowl', 120), (r'salad', 'bowl', 100),
    (r'bhel|chaat|chat|papdi', 'plate', 150), (r'biryani|biriyani|pulao|pulav|rice|chawal|khichdi|khichri|bhaat|sadam|pongal|bisi', 'plate', 250),
    (r'chutney|pickle|achaar|achar|dip', 'small bowl', 30),
]

STD_PIECE = {'idli': 40, 'dosa': 85, 'chapati': 40, 'roti': 45, 'parantha': 75, 'poori': 30, 'bhatura': 70,
             'vada': 45, 'bonda': 50, 'uttapam': 120, 'appam': 60, 'pesarattu': 90, 'puttu': 120,
             'thepla': 40, 'cheela': 70, 'naan': 90, 'samosa': 60, 'kachori': 45, 'dhokla': 30, 'egg': 50,
             'omelette': 60, 'cutlet': 50, 'tikki': 50, 'pakora': 20, 'gulab jamun': 40, 'ladoo': 35, 'burfi': 30}
STD_NAME = [('dosa', r'masala dosa|dosa.*fill', 150), ('dosa', r'rava dosa|semolina dosa', 75), ('vada', r'dahi vada|dahi bhalla', 70),
            ('parantha', r'stuffed|aloo|potato|gobhi|cauliflower|mooli|radish|paneer|keema|dal|matar|pea', 100)]
VOLUME = {'bowl': 'bowl', 'curry bowl': 'bowl', 'small bowl': 'bowl', 'soup bowl': 'bowl', 'plate': 'plate',
          'small plate': 'plate', 'cup': 'cup', 'tea cup': 'cup', 'glass': 'glass', 'tall glass': 'glass',
          'juice glass': 'glass', 'tall stemmed glass': 'glass', 'tablespoon': 'spoon', 'teaspoon': 'spoon'}
FAMILY = {'bowl': [('small bowl', 100), ('bowl', 150), ('large bowl', 250)],
          'plate': [('small plate', 150), ('plate', 250)],
          'cup': [('cup', 150)], 'glass': [('glass', 200), ('tall glass', 300)],
          'spoon': [('teaspoon', 5), ('tablespoon', 15)]}

PIECE = {'piece', 'biscuit', 'cookie', 'cookies', 'egg', 'cutlet', 'poori', 'ladoo', 'vada', 'burfi',
         'tart', 'pie', 'pastry', 'large slice', 'kabab', 'kebab', 'samosa', 'patty', 'pakora',
         'omelette', 'kofta', 'fillet', 'kachori', 'roll', 'gunjia', 'puff', 'swiss roll', 'cake',
         'bhatura', 'kaathi roll', 'gulab jamun', 'bonda', 'tikki', 'burger', 'spring roll',
         'muthia', 'square', 'finger', 'mulik/fritter', 'chop', 'chops', 'bun', 'bread roll',
         'meringue', 'candy', 'potato', 'capsicum', 'brinjal', 'tomato', 'stuffed tomato', 'kulfi',
         'flan', 'horn', 'éclair', 'pancake', 'small mould', 'souffle cup', 'portion', 'jar',
         'dish', 'souffle dish', 'casserole dish', 'shallow dish', 'small casserole dish'}
YIELD_PIECE = 0.85  # fried/baked pieces lose some water


DRY = re.compile(r'chutney|powder|podi|pickle|achaar|achar|ladoo|laddu|burfi|barfi|chikki|halwa|biscuit|cookie|cake|mathri|namkeen|mix|sev|bhujia|candy|toffee|fudge|brittle|sweet|mithai|peda|sandesh|dressing|sauce|jam|butter|icing|nuts|roasted|khakhra|chivda|chiwda|trail|granola|panjiri|gajak')
def cook_yield(name, unit, fried):
    n = name.lower()
    if fried: return 0.85
    if re.search(r'idli|dhokla|steam|puttu|idiyappam|modak|kozhukattai|momo|salad|raita|chutney|dip|juice|shake|lassi|sharbat|smoothie|milk|buttermilk|chaas|cold|iced|lemonade|squash|sandwich|ice cream|kulfi|mousse|dressing', n): return 1.0
    if unit in ('glass', 'tall glass', 'juice glass', 'tall stemmed glass'): return 1.0
    if re.search(r'tea|coffee|chai|cocoa|rasam|soup|stock|consomme|canjee|kanji', n): return 0.85
    if re.search(r'rice|pulao|pulav|biryani|biriyani|khichdi|khichri|khitchdi|pongal|bhaat|chawal|sadam|bisi', n): return 0.95
    if re.search(r'dal|sambar|curry|kadhi|gravy|stew|kootu|kuzhambu|korma|makhani|rajma|chole|channa|chana|keema|masala|porridge|daliya|kheer|payasam|halwa|halva|kesari|sheera|upma', n): return 0.8
    if re.search(r'cake|biscuit|cookie|bread|pie|tart|bake|naan|roti|chapati|paratha|parantha|dosa|cheela|chilla|uttapam|pancake|thepla|toast|pizza|bun|puff|pastry|souffle', n): return 0.85
    return 0.9

def household(name, unit):
    n = name.lower()
    for rx, u, g in NAME_G:
        if (u is None or u == unit) and re.search(rx, n):
            return g
    return UNIT_G.get(unit)

def clean_name(n):
    n = re.sub(r'\s+', ' ', n.strip())
    m = re.match(r'^(.*?)\s*\((.*)\)\s*$', n)
    return (m.group(1).strip(), m.group(2).strip()) if m else (n, '')

out, flags = [], []
for d in D:
    code, name = d['food_code'], d['food_name']
    s = S.get(code, {})
    nserv = num(s.get('no_of_servings')); size = num(s.get('size_of_servings')) or 1
    unit = (s.get('servings_unit') or d.get('servings_unit') or '').strip()
    p100 = {k: num(d[k]) for k in NUT}
    if p100['energy_kcal'] <= 0:
        flags.append((code, name, 'no energy')); continue
    if nserv and d['unit_serving_energy_kcal']:
        W = num(d['unit_serving_energy_kcal']) * nserv * size / p100['energy_kcal'] * 100
    else:
        W = ing_w.get(code, 0)
    tot = {k: p100[k] * W / 100 for k in NUT}
    W -= min(nonabs.get(code, 0), W * 0.8)
    oil = fry.get(code, 0)
    if oil and W > oil:
        nonoil = W - oil
        ab = absorb_rate(name) * nonoil
        for k, v in OIL.items():
            tot[k] -= (oil - ab) * v / 100
        tot['fat_g'] = max(tot['fat_g'], 0)
        W = nonoil + ab
    pieces = nserv * size if nserv else 0
    hg = household(name, unit) if unit else None
    ab = absorb_rate(name) * (W - oil) if oil else 0  # absorbed oil already inside W
    raw_density = tot['energy_kcal'] / W * 100 if W else 0
    water = code in has_water
    g_unit = None
    if pieces:
        W_ps = W / pieces
        y = cook_yield(name, unit, bool(oil))
        g_yield = (W_ps - ab / pieces) * y + ab / pieces
        # water left out of the recipe (soaked poha, dosa batter, dals): raw weight is
        # far too small, so use the cooked household measure instead
        if hg and not water and not oil and raw_density > 200 and not DRY.search(name.lower()):
            g_unit = max(hg, g_yield)
        else:
            g_unit = g_yield
    if pieces and g_unit:
        per_unit = {k: tot[k] / pieces for k in NUT}
        per100 = {k: per_unit[k] / g_unit * 100 for k in NUT}
    else:  # no serving info: raw-basis density (after oil fix), yield-adjusted
        y = cook_yield(name, unit, bool(oil))
        per100 = {k: tot[k] / (W * y) * 100 for k in NUT} if W else p100
    kcal = per100['energy_kcal']
    # sanity: energy from macros should match stated energy; density in a sane range
    macro = 4 * per100['protein_g'] + 4 * per100['carb_g'] + 9 * per100['fat_g'] + 2 * per100['fibre_g']
    bad = []
    if not (5 <= kcal <= 650): bad.append(f'density {kcal:.0f}')
    if macro and abs(macro - kcal) / max(kcal, 1) > 0.25: bad.append(f'macro {macro:.0f} vs {kcal:.0f}')
    if pieces and g_unit and per_unit['energy_kcal'] > 1200: bad.append(f'unit {per_unit["energy_kcal"]:.0f}')
    if bad:
        flags.append((code, name, '; '.join(bad)))
        if not (5 <= kcal <= 650) or (macro and abs(macro - kcal) > 40 and abs(macro - kcal) / max(kcal, 1) > 0.3) or (pieces and g_unit and per_unit['energy_kcal'] > 1200):
            continue  # drop clearly broken rows
    en, local = clean_name(name)
    units = []
    if g_unit:
        std = STD_PIECE.get(unit)
        if std:
            for uu, rx, gg in STD_NAME:
                if uu == unit and re.search(rx, name.lower()): std = gg; break
        if unit in VOLUME:
            fam = VOLUME[unit]
            hgv = household(name, unit) or UNIT_G.get(unit)
            units.append([unit, hgv])
            for lab, gg in FAMILY[fam]:
                if lab != unit and abs(gg - hgv) > 10: units.append([lab, gg])
        elif std:
            units.append([unit, std])
        else:
            units.append([unit, max(1, round(g_unit))])
    units.append(['100 g', 100])
    out.append({'id': code, 'n': en, 'l': local, 'u': units,
                'v': [round(per100[k], 2 if k in ('iron_mg', 'zinc_mg') else 1) for k in NUT],
                'fried': bool(oil)})

print('kept', len(out), 'flagged', len(flags), 'fry-fixed', sum(1 for o in out if o['fried']))
json.dump(out, open('indb_fixed.json', 'w'), ensure_ascii=False)
json.dump(flags, open('indb_flags.json', 'w'), ensure_ascii=False, indent=0)
