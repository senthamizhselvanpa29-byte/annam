"""Merge Annam dishes + IFCT 2017 basic foods + fixed INDB dishes into foods.json."""
import json, re, sys
OUT = sys.argv[1]
dishes = json.load(open('dishes.json'))
raw = json.load(open('ifct_raw.json'))
indb = json.load(open('indb_fixed.json'))

NONVEG = re.compile(r'chicken|mutton|fish|egg|meat|keema|kheema|prawn|shrimp|crab|beef|pork|lamb|ham\b|bacon|salami|'
                    r'sausage|anchov|tuna|sardine|liver|goat|sheep|lobster|squid|omelette|omlet|gushtaba|rogan|kabab|kebab|seekh|'
                    r'gelatin|souffle|mayonnaise|meringue|custard|cake|cookie|pastry', re.I)
EGGISH = re.compile(r'souffle|mayonnaise|meringue|custard|cake|cookie|pastry', re.I)  # may contain egg: unknown
NONVEG_GRP = {'Animal Meat', 'Poultry', 'Marine Fish', 'Fresh Water Fish and Shellfish', 'Marine Shellfish',
              'Marine Mollusks', 'Egg and Egg Products'}
def vg(name):
    if EGGISH.search(name) and not re.search(r'eggless|without egg', name, re.I): return -1
    if re.search(r'eggless|without egg', name, re.I): return 1
    return 0 if NONVEG.search(name) else 1

foods = []
for d in dishes:
    foods.append([d['id'], d['n'], d['ta'], d['hi'], '', 'annam', d['veg'], d['u'], d['v']])
for r in raw:
    foods.append([r['id'], r['n'], '', '', ' '.join(x for x in (r['ta'], r['hi']) if x), 'ifct',
                  0 if r['grp'] in NONVEG_GRP else 1, r['u'], r['v']])
for r in indb:
    v = list(r['v']); v[6] = round(v[6] / 1000, 1)  # sat fat mg -> g
    foods.append([r['id'], r['n'], '', '', r['l'], 'indb', vg(r['n'] + ' ' + r['l']), r['u'], v])
# sanity: no NaN / negative
for f in foods:
    f[8] = [max(0, x) if x == x else 0 for x in f[8]]
byid = {f[0]: f for f in foods}
byname = {}
for f in foods:
    byname.setdefault(f[1].lower(), f)

# micronutrient reference for Annam's 67 hand-checked foods (per gram, from a matching dish/food)
REF = {'idli': 'Idli', 'dosa': 'Plain dosa', 'masaladosa': 'Masala dosa', 'sambar': 'AN_sambar_home',
       'chutney': 'AN_coconut_chutney_home', 'pongal': 'AN_ven_pongal', 'upma': 'Semolina upma', 'poha': 'AN_aval_upma',
       'vada': 'AN_medu_vada', 'chapati': 'Chapati/Roti', 'paratha': 'Plain parantha/paratha', 'rice': 'AN_white_rice',
       'brownrice': 'AN_brown_rice', 'curdrice': 'Curd rice', 'lemonrice': 'Lemon rice', 'ragi': 'AN_ragi_kali',
       'oats': 'Oatmeal Porridge', 'dal': 'AN_dal_tadka', 'rasam': 'AN_rasam_tomato', 'rajma': 'Kidney bean curry',
       'chana': 'AN_chole', 'sundal': 'AN_sundal', 'sprouts': 'AN_sprouts_salad', 'sabzi': 'AN_veg_kurma',
       'palak': 'Spinach paneer', 'paneer': 'IFL003', 'curd': 'AN_curd_plain', 'buttermilk': 'AN_neer_mor',
       'milk': 'IFL002', 'tea': 'Hot tea', 'coffee': 'AN_filter_coffee', 'egg': 'IFM004', 'omelette': 'IFM007',
       'chickencurry': 'AN_chicken_curry_home', 'grilledchicken': 'AN_grilled_chicken', 'fishcurry': 'AN_meen_kuzhambu',
       'vegbiryani': 'Vegetable biryani/biriyani', 'chickenbiryani': 'AN_chicken_biryani', 'samosa': 'Potato samosa',
       'banana': 'IFE012', 'apple': 'IFE001', 'guava': 'IFE028', 'papaya': 'IFE049', 'mango': 'IFE036',
       'almonds': 'IFH001', 'peanuts': 'IFH012', 'salad': 'IFD043', 'poori': 'Poori', 'bhatura': 'Bhatura',
       'bajji': 'Onion pakora/pakoda', 'bonda': 'Potato bonda', 'appam': 'Appam', 'puttu': 'Rice puttu',
       'kootu': 'AN_kootu', 'poriyal': 'AN_beans_poriyal', 'pulao': 'Mixed vegetable pulao', 'khichdi': 'Plain khitchdi',
       'kesari': 'Semolina halwa', 'payasam': 'AN_paal_payasam', 'muttoncurry': 'AN_mutton_kuzhambu',
       'ghee': 'IFT013', 'oil': 'IFT005', 'parotta': 'Plain parantha/paratha', 'chicken65': 'AN_chicken_chettinad',
       'kachori': 'Kachori', 'bread': None, 'sugar': None}
micro = {}
for cid, ref in REF.items():
    f = byid.get(ref) if ref else None
    if ref and not f:
        f = next((x for n, x in byname.items() if n.startswith(ref.lower())), None) or next((x for n, x in byname.items() if ref.lower() in n), None)
    if f:
        micro[cid] = [round(x, 2) for x in f[8][5:]]
    elif ref:
        print('no ref for', cid, ref)
micro['sugar'] = [99.5] + [0] * 11
micro['bread'] = [4.0, 0.5, 0, 107, 2.4, 80, 250, 450, 1.5, 0, 40, 0]  # whole wheat bread, typical label

data = {'v': 2, 'per': '100 g',
        'nut': ['kcal', 'p', 'c', 'f', 'fi', 'sugar', 'sfa', 'chol', 'ca', 'fe', 'mg', 'k', 'na', 'zn', 'vitc', 'fol', 'vita'],
        'sources': {'annam': 'Annam recipe calculations from IFCT 2017 ingredients (cooked weight)',
                    'ifct': 'Indian Food Composition Tables 2017, ICMR-NIN (raw foods), via @ifct2017/compositions',
                    'indb': 'Indian Nutrient Databank (Vijayakumar et al. 2024, CC BY 4.0), corrected for frying oil and cooked weight'},
        'micro': micro, 'foods': foods}
s = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
open(OUT, 'w').write(s)
from collections import Counter
print(len(foods), 'foods', Counter(f[5] for f in foods), round(len(s.encode()) / 1024), 'KB', 'micro refs', len(micro))
