"""IFCT 2017 basic foods + Annam's recipe-calculated South Indian / everyday dishes.

Nutrient order (per 100 g) for every food in Annam:
 0 kcal, 1 protein g, 2 carbs g, 3 fat g, 4 fibre g, 5 free sugar g, 6 sat fat g,
 7 cholesterol mg, 8 calcium mg, 9 iron mg, 10 magnesium mg, 11 potassium mg,
 12 sodium mg, 13 zinc mg, 14 vitamin C mg, 15 folate ug, 16 vitamin A ug
"""
import csv, json, re, sys

CSV = sys.argv[1]
rows = list(csv.reader(open(CSV)))
H = [x.split(';')[-1].strip() for x in rows[0]]
IF = {}
for r in rows[1:]:
    d = dict(zip(H, r))
    f = lambda k, m=1.0: float(d[k] or 0) * m
    p, fa, c, fi = f('protcnt'), f('fatce'), f('choavldf'), f('fibtg')
    kcal = f('enerc') / 4.184
    atw = 4 * p + 4 * c + 9 * fa + 2 * fi
    if atw and abs(kcal - atw) / atw > 0.15:
        kcal = atw  # a few IFCT energy values (e.g. chicken leg) disagree with their own macros
    IF[d['code']] = dict(code=d['code'], name=d['name'], lang=d['lang'], grup=d['grup'], v=[
        kcal, p, c, fa, fi, f('fsugar'), f('fasat'), f('cholc', 1000), f('ca', 1000), f('fe', 1000),
        f('mg', 1000), f('k', 1000), f('na', 1000), f('zn', 1000), f('vitc', 1000),
        f('folsum', 1e6), f('vita', 1e6)])

# a few staples IFCT 2017 does not list (values per 100 g; NIN / UK CoFID typical)
EXTRA = {
    'SALT': [0] * 12 + [38758, 0, 0, 0, 0],
    'SUGAR': [398, 0, 99.5, 0, 0, 99.5] + [0] * 11,
    'CURD': [60, 3.1, 3.0, 4.0, 0, 0, 2.5, 11, 149, 0.2, 11, 130, 32, 0.5, 1, 7, 31],
    'BUTTER': [729, 0.6, 0.1, 81, 0, 0, 51, 215, 15, 0.2, 2, 24, 576, 0.1, 0, 3, 684],
    'CREAM': [250, 2.5, 3.5, 25, 0, 0, 15.6, 80, 85, 0.1, 8, 110, 35, 0.3, 1, 5, 230],
    'WATER': [0] * 17, 'COFFEE': [2, 0.1, 0, 0, 0, 0, 0, 0, 2, 0, 3, 50, 2, 0, 0, 0, 0],
}
def nut(code):
    return EXTRA[code] if code in EXTRA else IF[code]['v']

def lang_names(s):
    out = {}
    for seg in s.rstrip('.').split(';'):
        seg = seg.strip()
        m = re.match(r'^((?:[A-Z][a-z]*\.,?\s*)+)(.+)$', seg)
        if not m: continue
        for pre in re.findall(r'([A-Z][a-z]*)\.', m.group(1)):
            out.setdefault(pre, m.group(2).strip())
    return out

RAW_SUFFIX = {'Cereals and Millets', 'Grain Legumes', 'Animal Meat', 'Poultry', 'Marine Fish',
              'Fresh Water Fish and Shellfish', 'Marine Shellfish', 'Marine Mollusks'}
FRUIT_PIECE = [(r'apple', 150), (r'banana', 100), (r'orange', 130), (r'guava', 100), (r'mango, ripe', 200),
               (r'sapota', 100), (r'pear', 180), (r'peach', 150), (r'plum', 60), (r'fig', 50), (r'litchi', 10),
               (r'strawberry', 12), (r'custard apple', 100), (r'dates', 8), (r'goosberry', 30), (r'lime, sweet', 150),
               (r'pummelo', 150), (r'avocado', 150), (r'kiwi', 70), (r'jambu', 5), (r'zizyphus', 15), (r'rambutan', 30),
               (r'mangosteen', 40), (r'wood apple', 100), (r'bael', 100), (r'star fruit', 90), (r'apricot', 10)]
FRUIT_CUP = [(r'papaya|melon|pineapple|grapes|pomegranate|jack fruit|black berry|cherries|phalsa|currants|karonda|soursop|palm', 150)]
VEG_PIECE = [(r'potato', 150), (r'carrot', 70), (r'onion, big', 100), (r'onion, small', 10), (r'beet', 120),
             (r'sweet potato', 150), (r'tomato', 100), (r'cucumber', 200), (r'radish', 100), (r'capsicum', 120),
             (r'drumstick$', 70), (r'brinjal', 80), (r'chillies, green', 3), (r'garlic', 4), (r'ginger', 10),
             (r'lemon', 15), (r'curry leaves', 2), (r'corn, baby', 10), (r'maize, tender', 150)]

def raw_units(f):
    n, g = f['name'].lower(), f['grup']
    u = []
    def first(table):
        for rx, gg in table:
            if re.search(rx, n): return gg
    if g == 'Fruits':
        pc = first(FRUIT_PIECE)
        if 'juice' in n: u.append(['tablespoon', 15])
        elif pc: u.append(['piece', pc])
        u.append(['cup', first(FRUIT_CUP) or 150])
    elif g in ('Other Vegetables', 'Roots and Tubers', 'Condiments and Spices'):
        pc = first(VEG_PIECE)
        if pc: u.append(['piece', pc])
        if g == 'Condiments and Spices' and not pc: u.append(['teaspoon', 3])
        elif g != 'Condiments and Spices': u.append(['cup', 100])
    elif g == 'Green Leafy Vegetables': u.append(['cup', 30])
    elif g == 'Nuts and Oil Seeds':
        u += [['handful', 30], ['tablespoon', 10]]
    elif g in ('Cereals and Millets', 'Grain Legumes'):
        u += [['tablespoon', 12], ['cup', 180]]
        if 'flakes' in n or 'puffed' in n: u = [['cup', 30 if 'puffed' in n else 60]]
    elif g in RAW_SUFFIX:
        u.append(['serving', 150])
    elif g == 'Egg and Egg Products':
        u.append(['egg', 10 if 'quial' in n else 70 if 'duck' in n else 33 if 'white' in n else 17 if 'yolk' in n else 50])
    elif g == 'Milk and Milk Products':
        u += [['small bowl', 100], ['tablespoon', 15]] if re.search('paneer|khoa', n) else [['glass', 200], ['cup', 150]]
    elif g == 'Edible Oils and Fats': u += [['teaspoon', 5], ['tablespoon', 14]]
    elif g == 'Sugars': u += [['glass', 250]] if 'juice' in n else [['tablespoon', 15], ['piece', 20]]
    elif g == 'Mushrooms': u.append(['cup', 70])
    elif g == 'Miscellaneous Foods': u.append(['glass', 250])
    u.append(['100 g', 100])
    return u

def rnd(v):
    return [round(x, 2 if i in (9, 13) else 1) for i, x in enumerate(v)]

raw = []
for code, f in IF.items():
    L = lang_names(f['lang'])
    nm = f['name'] + (', raw' if f['grup'] in RAW_SUFFIX and 'raw' not in f['name'].lower() else '')
    raw.append({'id': 'IF' + code, 'n': nm, 'ta': L.get('Tam', ''), 'hi': L.get('H', ''), 'grp': f['grup'],
                'u': raw_units(f), 'v': rnd(f['v'])})

# ---------------- recipe-calculated dishes ----------------
# each: id, English, Tamil, Hindi, veg, ingredients {code: grams}, yield (cooked/raw total), units
B = [['small bowl', 100], ['bowl', 150], ['large bowl', 250]]
P = [['small plate', 150], ['plate', 250]]
G = [['glass', 200], ['tall glass', 300]]
T = [['tablespoon', 15], ['small bowl', 50]]
def pc(label, g): return [[label, g]]
SAMBAR_POWDER = {'G024': 6, 'G022': 4, 'B001': 3, 'G026': 1}
TEMPER = {'H013': 2, 'G010': 2, 'G019': 0.5}
DISHES = [
 ('ven_pongal', 'Ven pongal', 'வெண் பொங்கல்', 'वेन पोंगल', 1, {'A015': 100, 'B010': 50, 'T013': 20, 'G031': 2, 'G025': 2, 'G014': 5, 'H005': 10, 'G010': 2, 'SALT': 4, 'WATER': 500}, .85, B),
 ('sakkarai_pongal', 'Sakkarai pongal (sweet)', 'சர்க்கரைப் பொங்கல்', 'मीठा पोंगल', 1, {'A015': 100, 'B010': 25, 'I001': 150, 'T013': 30, 'H005': 10, 'E057': 10, 'G020': 1, 'L002': 100, 'WATER': 400}, .75, B),
 ('sambar_home', 'Sambar (home style)', 'சாம்பார்', 'सांभर', 1, {'B021': 75, 'E064': 15, **SAMBAR_POWDER, 'D046': 50, 'D031': 50, 'G018': 50, 'D076': 50, 'D066': 50, 'T005': 15, **TEMPER, 'G033': 1, 'SALT': 8, 'WATER': 900}, .8, B),
 ('rasam_tomato', 'Tomato rasam', 'தக்காளி ரசம்', 'टमाटर रसम', 1, {'D076': 150, 'E064': 10, 'B021': 15, 'G031': 2, 'G025': 2, 'G011': 5, 'T013': 5, **TEMPER, 'G009': 3, 'SALT': 6, 'WATER': 700}, .85, B),
 ('mor_kuzhambu', 'Mor kuzhambu', 'மோர்க் குழம்பு', 'मोर कुलंबु (छाछ करी)', 1, {'CURD': 300, 'H007': 40, 'G008': 5, 'G014': 5, 'G025': 2, 'B021': 5, 'D001': 100, 'T001': 10, **TEMPER, 'G033': 1, 'SALT': 5, 'WATER': 150}, .9, B),
 ('vatha_kuzhambu', 'Vatha kuzhambu', 'வத்தக் குழம்பு', 'वत्त कुलंबु', 1, {'E064': 40, 'G018': 80, 'G011': 20, 'T004': 30, **SAMBAR_POWDER, 'I001': 5, **TEMPER, 'SALT': 8, 'WATER': 400}, .7, B),
 ('kara_kuzhambu', 'Kara kuzhambu (brinjal)', 'கத்தரிக்காய் காரக் குழம்பு', 'बैंगन कारा कुलंबु', 1, {'D031': 150, 'E064': 30, 'G018': 60, 'G011': 15, 'T004': 25, **SAMBAR_POWDER, 'H007': 20, **TEMPER, 'SALT': 8, 'WATER': 400}, .72, B),
 ('kootu', 'Chow chow kootu', 'சௌசௌ கூட்டு', 'चौचौ कूटू', 1, {'B010': 50, 'D038': 250, 'H007': 30, 'G025': 2, 'G008': 5, 'T005': 5, **TEMPER, 'SALT': 5, 'G033': 1, 'WATER': 300}, .8, B),
 ('avial', 'Avial', 'அவியல்', 'अवियल', 1, {'D046': 50, 'F002': 50, 'D049': 50, 'D063': 50, 'F017': 50, 'D001': 50, 'H007': 60, 'CURD': 50, 'G008': 5, 'G025': 2, 'T001': 15, 'G010': 2, 'SALT': 5, 'WATER': 80}, .85, B),
 ('beans_poriyal', 'Beans poriyal', 'பீன்ஸ் பொரியல்', 'बीन्स पोरियल', 1, {'D049': 250, 'H007': 25, 'T005': 10, 'H013': 2, 'B003': 3, 'G010': 1, 'G022': 2, 'SALT': 4, 'WATER': 30}, .85, B),
 ('cabbage_poriyal', 'Cabbage poriyal', 'முட்டைக்கோஸ் பொரியல்', 'पत्तागोभी पोरियल', 1, {'C015': 300, 'H007': 25, 'T005': 10, 'H013': 2, 'B003': 3, 'B001': 3, 'G008': 4, 'SALT': 4}, .8, B),
 ('potato_roast', 'Potato roast (urulai varuval)', 'உருளைக்கிழங்கு வறுவல்', 'आलू रोस्ट', 1, {'F006': 300, 'T005': 30, 'G022': 5, 'G033': 1, 'H013': 1, 'G010': 1, 'SALT': 5}, .8, B),
 ('keerai_masiyal', 'Keerai masiyal (greens)', 'கீரை மசியல்', 'साग (कीरै मसियल)', 1, {'C002': 250, 'B010': 30, 'T005': 5, 'G011': 5, 'G025': 1, 'G008': 3, 'SALT': 3, 'WATER': 50}, .75, B),
 ('vendakkai_poriyal', 'Okra fry (vendakkai poriyal)', 'வெண்டைக்காய் பொரியல்', 'भिंडी फ्राई', 1, {'D056': 300, 'T005': 25, 'G017': 40, 'G022': 4, 'SALT': 4}, .75, B),
 ('idiyappam', 'Idiyappam', 'இடியாப்பம்', 'इडियप्पम', 1, {'A015': 200, 'WATER': 300, 'SALT': 2, 'T001': 5}, .95, pc('idiyappam', 40)),
 ('adai', 'Adai (lentil dosa)', 'அடை', 'अड़ई (दाल डोसा)', 1, {'A015': 100, 'B001': 50, 'B021': 50, 'B003': 25, 'G022': 4, 'G017': 50, 'G010': 2, 'G014': 5, 'SALT': 5, 'WATER': 200, 'T005': 30}, .85, pc('adai', 90)),
 ('pesarattu', 'Pesarattu (green moong dosa)', 'பெசரட்டு', 'पेसरट्टू', 1, {'B011': 200, 'A015': 30, 'G008': 8, 'G014': 10, 'G017': 50, 'G025': 2, 'SALT': 4, 'WATER': 250, 'T005': 25}, .85, pc('pesarattu', 90)),
 ('paniyaram', 'Kuzhi paniyaram', 'குழிப் பணியாரம்', 'कुझी पनियारम', 1, {'A014': 150, 'B003': 40, 'G017': 50, 'G008': 5, 'G010': 2, 'H013': 2, 'T005': 25, 'SALT': 5, 'WATER': 250}, .8, pc('paniyaram', 20)),
 ('ragi_dosa', 'Ragi dosa', 'கேழ்வரகு தோசை', 'रागी डोसा', 1, {'A010': 100, 'A015': 30, 'A022': 20, 'G017': 40, 'G008': 5, 'CURD': 30, 'WATER': 300, 'T005': 20, 'SALT': 4}, .8, pc('dosa', 70)),
 ('wheat_dosa', 'Wheat dosa', 'கோதுமை தோசை', 'गेहूं का डोसा', 1, {'A019': 150, 'A015': 20, 'G017': 30, 'G008': 3, 'WATER': 300, 'T005': 20, 'SALT': 3}, .8, pc('dosa', 70)),
 ('ghee_roast', 'Ghee roast dosa', 'நெய் ரோஸ்ட்', 'घी रोस्ट डोसा', 1, {'A014': 100, 'B003': 30, 'WATER': 150, 'T013': 15, 'SALT': 3}, .8, pc('dosa', 90)),
 ('ragi_kali', 'Ragi kali / mudde', 'கேழ்வரகு களி', 'रागी मुद्दे', 1, {'A010': 100, 'WATER': 300, 'SALT': 2}, .85, pc('ball', 150)),
 ('ragi_koozh', 'Ragi koozh (with buttermilk)', 'கேழ்வரகு கூழ்', 'रागी अंबली', 1, {'A010': 30, 'CURD': 100, 'WATER': 300, 'G017': 20, 'SALT': 3}, 1.0, G),
 ('kambu_koozh', 'Kambu koozh (bajra)', 'கம்பங் கூழ்', 'बाजरा अंबली', 1, {'A003': 40, 'CURD': 100, 'WATER': 300, 'G017': 20, 'SALT': 3}, 1.0, G),
 ('ragi_malt', 'Ragi malt with milk', 'ராகி மால்ட்', 'रागी माल्ट', 1, {'A010': 20, 'L002': 150, 'WATER': 50, 'I001': 10}, .9, G),
 ('bisibelebath', 'Bisibelebath', 'பிசிபேளாபாத்', 'बिसी बेले भात', 1, {'A015': 100, 'B021': 60, 'E064': 15, 'F002': 50, 'D049': 50, 'D061': 50, 'T013': 20, 'T005': 10, **SAMBAR_POWDER, 'H006': 8, 'H005': 10, 'SALT': 8, 'WATER': 800}, .8, P),
 ('puliyodharai', 'Puliyodharai (temple style)', 'புளியோதரை', 'पुलियोदरई (इमली चावल)', 1, {'A015': 150, 'WATER': 400, 'E064': 40, 'T004': 40, 'H012': 20, 'B001': 10, 'B003': 5, 'G022': 6, 'I001': 10, 'H011': 5, 'G010': 2, 'SALT': 8, 'G033': 1, 'G019': 1}, .9, P),
 ('tomato_rice', 'Tomato rice', 'தக்காளி சாதம்', 'टमाटर चावल', 1, {'A015': 150, 'WATER': 350, 'D076': 200, 'G017': 80, 'T005': 25, 'G014': 5, 'G011': 5, 'G022': 4, 'G033': 1, 'G016': 5, 'SALT': 6}, .9, P),
 ('coconut_rice', 'Coconut rice', 'தேங்காய் சாதம்', 'नारियल चावल', 1, {'A015': 150, 'WATER': 350, 'H007': 80, 'T001': 20, 'B001': 5, 'B003': 5, 'H005': 10, 'G008': 5, 'G010': 2, 'SALT': 5}, .92, P),
 ('jeera_rice', 'Jeera rice', 'சீரக சாதம்', 'जीरा राइस', 1, {'A015': 150, 'WATER': 300, 'T013': 15, 'G025': 3, 'SALT': 3}, .95, P),
 ('white_rice', 'Cooked white rice (sadam)', 'சாதம்', 'पका हुआ चावल', 1, {'A015': 100, 'WATER': 190}, .95, [['cup', 150]] + P),
 ('parboiled_rice', 'Cooked boiled rice (puzhungal arisi)', 'புழுங்கல் அரிசி சாதம்', 'उबला चावल (सेला)', 1, {'A014': 100, 'WATER': 210}, .95, [['cup', 150]] + P),
 ('brown_rice', 'Cooked brown rice', 'கைக்குத்தல் அரிசி சாதம்', 'ब्राउन राइस', 1, {'A013': 100, 'WATER': 230}, .95, [['cup', 150]] + P),
 ('samai_rice', 'Cooked little millet (samai)', 'சாமை சாதம்', 'कुटकी (सामा) चावल', 1, {'A016': 100, 'WATER': 250}, .95, [['cup', 150]] + P),
 ('varagu_rice', 'Cooked kodo millet (varagu)', 'வரகு சாதம்', 'कोदो चावल', 1, {'A017': 100, 'WATER': 250}, .95, [['cup', 150]] + P),
 ('toor_dal_plain', 'Plain toor dal (paruppu)', 'பருப்பு', 'सादी अरहर दाल', 1, {'B021': 100, 'WATER': 400, 'SALT': 2, 'G033': 1}, .85, B),
 ('dal_tadka', 'Dal tadka', 'தால் தட்கா', 'दाल तड़का', 1, {'B021': 100, 'G017': 50, 'D076': 60, 'T013': 15, 'G025': 2, 'G011': 8, 'G022': 2, 'G033': 1, 'SALT': 5, 'WATER': 600}, .8, B),
 ('veg_kurma', 'Vegetable kurma', 'காய்கறி குருமா', 'वेज कुरमा', 1, {'F006': 100, 'F002': 70, 'D049': 70, 'D061': 60, 'G017': 80, 'D076': 80, 'H007': 60, 'H005': 10, 'T005': 25, 'G014': 5, 'G011': 5, 'G022': 4, 'SALT': 6, 'WATER': 250}, .8, B),
 ('chole', 'Chole (chickpea curry)', 'சன்னா மசாலா', 'छोले', 1, {'B002': 150, 'G017': 120, 'D076': 150, 'T005': 25, 'G014': 8, 'G011': 7, 'G022': 5, 'G024': 5, 'G025': 2, 'SALT': 6, 'WATER': 700}, .75, B),
 ('paneer_butter_masala', 'Paneer butter masala', 'பனீர் பட்டர் மசாலா', 'पनीर बटर मसाला', 1, {'L003': 200, 'D076': 300, 'G017': 80, 'H005': 25, 'BUTTER': 30, 'CREAM': 50, 'G014': 5, 'G011': 5, 'G022': 4, 'SUGAR': 5, 'SALT': 5, 'WATER': 150}, .8, B),
 ('aloo_gobi', 'Aloo gobi', 'உருளை காலிஃப்ளவர்', 'आलू गोभी', 1, {'F006': 200, 'D036': 250, 'G017': 60, 'D076': 60, 'T005': 25, 'G014': 5, 'G024': 3, 'G022': 3, 'G033': 1, 'SALT': 5}, .8, B),
 ('chicken_chettinad', 'Chettinad chicken', 'செட்டிநாடு சிக்கன்', 'चेट्टिनाड चिकन', 0, {'N001': 500, 'G017': 150, 'D076': 100, 'T005': 40, 'H006': 20, 'G031': 6, 'G024': 8, 'G022': 6, 'G025': 3, 'G014': 10, 'G011': 10, 'G010': 2, 'SALT': 8, 'WATER': 150}, .75, B),
 ('chicken_curry_home', 'Chicken curry (home style)', 'கோழிக் குழம்பு', 'चिकन करी', 0, {'N001': 500, 'G017': 150, 'D076': 150, 'T005': 30, 'G014': 10, 'G011': 10, 'G022': 8, 'G024': 6, 'G033': 1, 'SALT': 8, 'WATER': 250}, .75, B),
 ('mutton_kuzhambu', 'Mutton kuzhambu', 'ஆட்டுக்கறி குழம்பு', 'मटन करी', 0, {'O001': 500, 'G017': 150, 'D076': 100, 'T005': 35, 'H007': 40, 'G024': 8, 'G022': 7, 'G014': 10, 'G011': 10, 'SALT': 8, 'WATER': 400}, .7, B),
 ('meen_kuzhambu', 'Fish curry (meen kuzhambu)', 'மீன் குழம்பு', 'मछली करी', 0, {'P034': 400, 'E064': 30, 'G018': 100, 'D076': 100, 'T004': 30, 'G022': 10, 'G024': 8, 'G033': 1, 'G011': 15, 'G026': 1, 'SALT': 8, 'WATER': 400}, .8, B),
 ('meen_varuval', 'Fish fry (meen varuval)', 'மீன் வறுவல்', 'मछली फ्राई', 0, {'P034': 400, 'G022': 10, 'G033': 1, 'G014': 8, 'G011': 7, 'E033': 10, 'SALT': 5, 'T005': 25}, .8, pc('piece', 60)),
 ('egg_curry_home', 'Egg curry (muttai kuzhambu)', 'முட்டைக் குழம்பு', 'अंडा करी', 0, {'M004': 300, 'G017': 120, 'D076': 120, 'T005': 25, 'H007': 30, 'G014': 5, 'G011': 5, 'G022': 6, 'G024': 5, 'G033': 1, 'SALT': 6, 'WATER': 200}, .8, B),
 ('egg_podimas', 'Egg podimas (bhurji)', 'முட்டை பொடிமாஸ்', 'अंडा भुर्जी', 0, {'M001': 150, 'G017': 40, 'G008': 4, 'T005': 8, 'SALT': 2, 'G033': 0.5}, .85, [['small bowl', 100]]),
 ('kothu_parotta', 'Kothu parotta (egg)', 'கொத்து பரோட்டா', 'कोथु परोटा', 0, {'A018': 150, 'T005': 45, 'WATER': 80, 'M001': 100, 'G017': 80, 'D076': 60, 'G022': 4, 'SALT': 4}, .85, P),
 ('chicken_biryani', 'Chicken biryani', 'சிக்கன் பிரியாணி', 'चिकन बिरयानी', 0, {'A015': 300, 'N001': 500, 'G017': 150, 'D076': 100, 'CURD': 100, 'T005': 40, 'T013': 20, 'G014': 15, 'G011': 15, 'G016': 10, 'G009': 10, 'G022': 8, 'G020': 2, 'G023': 1, 'SALT': 12, 'WATER': 600}, .85, P),
 ('grilled_chicken', 'Grilled chicken breast', 'கிரில் சிக்கன்', 'ग्रिल्ड चिकन', 0, {'N003': 200, 'T005': 5, 'G022': 2, 'G031': 1, 'SALT': 2}, .72, pc('piece', 120)),
 ('semiya_payasam', 'Semiya payasam', 'சேமியா பாயசம்', 'सेवइयां खीर', 1, {'A023': 50, 'L002': 500, 'SUGAR': 80, 'T013': 10, 'H005': 10, 'E057': 10, 'G020': 1}, .8, [['small bowl', 100], ['bowl', 150]]),
 ('paal_payasam', 'Paal payasam (rice kheer)', 'பால் பாயசம்', 'चावल की खीर', 1, {'A015': 40, 'L002': 800, 'SUGAR': 80, 'G020': 1}, .65, [['small bowl', 100], ['bowl', 150]]),
 ('kozhukattai', 'Sweet kozhukattai (modak)', 'இனிப்பு கொழுக்கட்டை', 'मोदक', 1, {'A015': 150, 'WATER': 250, 'I001': 100, 'H007': 100, 'G020': 1, 'T013': 5, 'SALT': 1}, .9, pc('piece', 35)),
 ('murukku', 'Murukku', 'முறுக்கு', 'मुरुक्कु (चकली)', 1, {'A015': 200, 'B003': 40, 'BUTTER': 20, 'H011': 5, 'G025': 3, 'SALT': 4, 'WATER': 120}, .7, pc('piece', 15), 70),
 ('medu_vada', 'Medu vada (ulundu vadai)', 'உளுந்து வடை', 'मेदु वड़ा', 1, {'B003': 200, 'G017': 40, 'G008': 5, 'G014': 5, 'G010': 2, 'G031': 2, 'SALT': 5, 'WATER': 120}, .85, pc('vada', 45), 50),
 ('paruppu_vadai', 'Masala vadai (paruppu vadai)', 'பருப்பு வடை', 'मसाला वड़ा (दाल वड़ा)', 1, {'B001': 200, 'G017': 60, 'G008': 5, 'G025': 2, 'G010': 2, 'G014': 5, 'SALT': 5, 'WATER': 40}, .9, pc('vada', 35), 50),
 ('sundal', 'Chana sundal', 'கொண்டைக்கடலை சுண்டல்', 'चना सुंडल', 1, {'B002': 100, 'WATER': 120, 'H007': 20, 'T005': 5, **TEMPER, 'G022': 1, 'SALT': 3}, 1.0, [['small bowl', 100]]),
 ('neer_mor', 'Buttermilk (neer mor)', 'நீர் மோர்', 'छाछ', 1, {'CURD': 100, 'WATER': 200, 'SALT': 2, 'G014': 2, 'G010': 1}, 1.0, G),
 ('filter_coffee', 'Filter coffee (with milk & sugar)', 'ஃபில்டர் காபி', 'फ़िल्टर कॉफ़ी', 1, {'L002': 120, 'COFFEE': 30, 'SUGAR': 8}, 1.0, pc('tumbler', 150)),
 ('coconut_chutney_home', 'Coconut chutney (home style)', 'தேங்காய் சட்னி', 'नारियल चटनी', 1, {'H007': 100, 'B001': 20, 'G008': 8, 'G014': 3, 'SALT': 3, 'WATER': 120, 'T005': 5, 'H013': 1, 'B003': 2, 'G010': 1}, 1.0, T),
 ('tomato_chutney', 'Tomato chutney (thakkali)', 'தக்காளி சட்னி', 'टमाटर चटनी', 1, {'D076': 300, 'G017': 60, 'T004': 20, 'G022': 6, 'G011': 5, 'SALT': 4}, .6, T),
 ('aval_upma', 'Poha / aval upma', 'அவல் உப்புமா', 'पोहा', 1, {'A011': 100, 'WATER': 100, 'G017': 50, 'H012': 15, 'T005': 12, 'H013': 1, 'G010': 1, 'G008': 3, 'G033': 1, 'E033': 5, 'SALT': 3}, .95, B),
 ('ragi_roti', 'Ragi roti', 'கேழ்வரகு ரொட்டி', 'रागी रोटी', 1, {'A010': 150, 'G017': 40, 'G008': 4, 'G009': 5, 'WATER': 130, 'T005': 15, 'SALT': 3}, .85, pc('roti', 60)),
 ('sprouts_salad', 'Sprouts salad (moong)', 'முளைகட்டிய பயறு சாலட்', 'अंकुरित मूंग सलाद', 1, {'B011': 50, 'WATER': 60, 'G017': 30, 'D076': 30, 'D043': 30, 'E033': 5, 'SALT': 1}, 1.0, [['small bowl', 100], ['bowl', 150]]),
 ('curd_plain', 'Curd / thayir (plain)', 'தயிர்', 'दही', 1, {'CURD': 100}, 1.0, [['small bowl', 100], ['bowl', 150], ['tablespoon', 15]]),
]

# ---- 2026-11-28: samba wheat (broken wheat) dishes, more sambar types, regional rice, seeraga samba biryani ----
# Same method: home recipes, IFCT 2017 ingredient values, cooked-weight yield. Regional rice types use the
# nearest IFCT rice (raw milled, parboiled milled or brown), because IFCT does not list them separately.
def sambar(veg, dal=None, oil=15, water=900, extra=None):
    ing = dict(dal if dal is not None else {'B021': 75})
    ing.update({'E064': 15, **SAMBAR_POWDER, 'G018': 50, 'D076': 50, **veg})
    if oil: ing['T005'] = oil
    ing.update({**TEMPER, 'G033': 1, 'G009': 5, 'SALT': 8, 'WATER': water, **(extra or {})})
    return ing
UPMA_BASE = {'T005': 15, 'G017': 60, 'G008': 5, 'G014': 3, 'H013': 1, 'B003': 3, 'G010': 2, 'SALT': 4}
BIRYANI = {'G017': 150, 'D076': 100, 'CURD': 120, 'T005': 40, 'T013': 20, 'G014': 15, 'G011': 15, 'G016': 10,
           'G009': 10, 'G022': 8, 'G031': 3, 'G020': 2, 'G023': 1, 'SALT': 12, 'WATER': 600}
RICE_U = [['cup', 150]] + P
DISHES += [
 ('samba_rava', 'Samba wheat rava / broken wheat (dry)', 'சம்பா கோதுமை ரவை', 'दलिया (टूटा गेहूं, सूखा)', 1, {'A021': 100}, 1.0, [['tablespoon', 12], ['cup', 170]]),
 ('samba_rava_upma', 'Samba rava upma (broken wheat upma)', 'சம்பா ரவை உப்புமா', 'दलिया उपमा', 1, {'A021': 100, **UPMA_BASE, 'WATER': 300}, .85, B),
 ('samba_rava_upma_veg', 'Samba rava upma with vegetables (peas, carrot)', 'காய்கறி சம்பா ரவை உப்புமா', 'सब्ज़ी वाला दलिया उपमा', 1, {'A021': 100, 'D061': 40, 'F002': 40, 'D049': 30, **UPMA_BASE, 'G017': 50, 'SALT': 5, 'WATER': 320}, .85, B),
 ('samba_rava_pongal', 'Samba rava pongal / khichdi (with moong dal)', 'சம்பா ரவை பொங்கல்', 'दलिया खिचड़ी', 1, {'A021': 100, 'B010': 40, 'T013': 15, 'G031': 2, 'G025': 2, 'G014': 3, 'H005': 8, 'G010': 2, 'SALT': 5, 'WATER': 500}, .85, B),
 ('samba_rava_kanji', 'Samba rava kanji (salt, with buttermilk)', 'சம்பா ரவை கஞ்சி', 'नमकीन दलिया कांजी', 1, {'A021': 40, 'WATER': 400, 'CURD': 80, 'G018': 10, 'SALT': 3}, .9, G),
 ('samba_rava_kanji_milk', 'Samba rava porridge with milk (sweet)', 'பால் சம்பா ரவை கஞ்சி', 'मीठा दलिया (दूध वाला)', 1, {'A021': 40, 'L002': 250, 'WATER': 200, 'SUGAR': 15, 'G020': 0.5}, .85, B),
 ('samba_rava_dosa', 'Samba rava dosa', 'சம்பா ரவை தோசை', 'दलिया डोसा', 1, {'A021': 100, 'A015': 25, 'B003': 10, 'G017': 30, 'G008': 4, 'G025': 1, 'SALT': 3, 'WATER': 220, 'T005': 20}, .8, pc('dosa', 80)),
 ('samba_rava_payasam', 'Samba rava payasam (broken wheat kheer)', 'சம்பா ரவை பாயசம்', 'दलिया खीर', 1, {'A021': 40, 'L002': 400, 'I001': 60, 'T013': 10, 'H005': 8, 'G020': 1}, .75, [['small bowl', 100], ['bowl', 150]]),
 ('sambar_drumstick', 'Drumstick sambar (murungakkai)', 'முருங்கைக்காய் சாம்பார்', 'सहजन (ड्रमस्टिक) सांबर', 1, sambar({'D046': 150}), .8, B),
 ('sambar_brinjal', 'Brinjal sambar (kathirikkai)', 'கத்தரிக்காய் சாம்பார்', 'बैंगन सांबर', 1, sambar({'D031': 150}), .8, B),
 ('sambar_lauki', 'Bottle gourd sambar (sorakkai / lauki)', 'சுரைக்காய் சாம்பார்', 'लौकी सांबर', 1, sambar({'D007': 200}), .8, B),
 ('sambar_ash_gourd', 'White pumpkin sambar (poosanikai / ash gourd)', 'வெண்பூசணி சாம்பார்', 'सफ़ेद कद्दू (पेठा) सांबर', 1, sambar({'D001': 200}), .8, B),
 ('sambar_pumpkin', 'Yellow pumpkin sambar (parangikai)', 'பரங்கிக்காய் சாம்பார்', 'पीला कद्दू सांबर', 1, sambar({'D066': 200}), .8, B),
 ('sambar_radish', 'Radish sambar (mullangi)', 'முள்ளங்கி சாம்பார்', 'मूली सांबर', 1, sambar({'F010': 150}), .8, B),
 ('sambar_okra', 'Okra sambar (vendakkai)', 'வெண்டைக்காய் சாம்பார்', 'भिंडी सांबर', 1, sambar({'D056': 150}), .8, B),
 ('sambar_onion', 'Small onion sambar (chinna vengaya)', 'சின்ன வெங்காய சாம்பார்', 'छोटे प्याज़ का सांबर', 1, sambar({'G018': 170}), .8, B),
 ('sambar_mixed_veg', 'Mixed vegetable sambar', 'கலவை காய்கறி சாம்பார்', 'मिक्स सब्ज़ी सांबर', 1, sambar({'D046': 40, 'D031': 40, 'F002': 40, 'D049': 40, 'D066': 40}), .8, B),
 ('sambar_tiffin', 'Tiffin sambar (for idli, dosa)', 'டிஃபன் சாம்பார் (இட்லி சாம்பார்)', 'इडली सांबर (टिफ़िन सांबर)', 1, sambar({'G018': 60, 'D076': 60}, dal={'B021': 40, 'B010': 30}, water=1000), .82, B),
 ('sambar_no_oil', 'Sambar without oil', 'எண்ணெய் இல்லாத சாம்பார்', 'बिना तेल का सांबर', 1, sambar({'D046': 50, 'D031': 50, 'D066': 50}, oil=0), .8, B),
 ('sambar_no_dal', 'Sambar without dal (vegetable kuzhambu)', 'பருப்பு இல்லாத சாம்பார்', 'बिना दाल का सांबर', 1, sambar({'D046': 80, 'D031': 80, 'D066': 80}, dal={}, oil=12, water=600, extra={'E064': 20}), .8, B),
 ('sambar_arachuvitta', 'Arachuvitta sambar (ground coconut)', 'அரைச்சுவிட்ட சாம்பார்', 'नारियल मसाला सांबर', 1, sambar({'D046': 80, 'D031': 50}, extra={'H007': 40}), .8, B),
 ('seeraga_samba_rice', 'Cooked seeraga samba rice', 'சீரக சம்பா சாதம்', 'जीरा सांबा चावल (पका)', 1, {'A015': 100, 'WATER': 180}, .95, RICE_U),
 ('ponni_rice', 'Cooked ponni rice', 'பொன்னி அரிசி சாதம்', 'पोन्नी चावल (पका)', 1, {'A014': 100, 'WATER': 210}, .95, RICE_U),
 ('sona_masoori_rice', 'Cooked sona masoori rice', 'சோனா மசூரி சாதம்', 'सोना मसूरी चावल (पका)', 1, {'A015': 100, 'WATER': 200}, .95, RICE_U),
 ('basmati_rice', 'Cooked basmati rice', 'பாஸ்மதி சாதம்', 'बासमती चावल (पका)', 1, {'A015': 100, 'WATER': 180}, .95, RICE_U),
 ('matta_rice', 'Cooked matta rice (Kerala red rice)', 'மட்டை அரிசி சாதம்', 'मट्टा चावल (लाल चावल, पका)', 1, {'A013': 100, 'WATER': 250}, .95, RICE_U),
 ('mappillai_samba_rice', 'Cooked mappillai samba (red rice)', 'மாப்பிள்ளை சம்பா சாதம்', 'मप्पिल्लई सांबा लाल चावल (पका)', 1, {'A013': 100, 'WATER': 250}, .95, RICE_U),
 ('kavuni_rice', 'Cooked karuppu kavuni (black rice)', 'கருப்பு கவுனி சாதம்', 'काला चावल (पका)', 1, {'A013': 100, 'WATER': 250}, .95, RICE_U),
 ('ss_chicken_biryani', 'Seeraga samba chicken biryani', 'சீரக சம்பா சிக்கன் பிரியாணி', 'जीरा सांबा चिकन बिरयानी', 0, {'A015': 300, 'N001': 500, **BIRYANI}, .85, P),
 ('ss_mutton_biryani', 'Seeraga samba mutton biryani', 'சீரக சம்பா மட்டன் பிரியாணி', 'जीरा सांबा मटन बिरयानी', 0, {'A015': 300, 'O001': 500, **BIRYANI, 'WATER': 700}, .85, P),
 ('ss_egg_biryani', 'Seeraga samba egg biryani', 'சீரக சம்பா முட்டை பிரியாணி', 'जीरा सांबा अंडा बिरयानी', 0, {'A015': 300, 'M004': 300, **BIRYANI}, .85, P),
 ('ss_veg_biryani', 'Seeraga samba vegetable biryani', 'சீரக சம்பா காய்கறி பிரியாணி', 'जीरा सांबा वेज बिरयानी', 1, {'A015': 300, 'F006': 100, 'F002': 80, 'D049': 80, 'D061': 60, **BIRYANI}, .85, P),
]
# other names people type (separated by |), used only for search
ALIAS = {
 'samba_rava': 'samba rava|samba wheat|samba godumai|samba godhumai rava|godumai rava|broken wheat|dalia|daliya|cracked wheat|emmer wheat|bulgur|lapsi',
 'samba_rava_upma': 'samba wheat upma|samba godumai upma|godhumai rava upma|godumai upma|broken wheat upma|dalia upma|daliya upma',
 'samba_rava_upma_veg': 'samba wheat upma vegetables|samba rava upma peas carrot|vegetable dalia|broken wheat vegetable upma|godumai rava kichadi',
 'samba_rava_pongal': 'samba rava khichdi|samba wheat pongal|godhumai pongal|godumai rava pongal|broken wheat khichdi|dalia khichdi|broken wheat pongal',
 'samba_rava_kanji': 'samba wheat kanji|godhumai kanji|godumai kanji|broken wheat kanji|dalia kanji|samba rava koozh',
 'samba_rava_kanji_milk': 'samba rava kanji milk|sweet dalia|dalia porridge|broken wheat porridge|godhumai paal kanji',
 'samba_rava_dosa': 'samba wheat dosa|godhumai rava dosa|godumai rava dosai|broken wheat dosa|dalia dosa',
 'samba_rava_payasam': 'samba wheat payasam|godhumai payasam|godumai rava payasam|broken wheat payasam|dalia kheer|lapsi kheer',
 'sambar_drumstick': 'murungakkai sambar|drumstick sambar|sahjan sambar',
 'sambar_brinjal': 'kathirikkai sambar|kathirikai sambar|eggplant sambar|baingan sambar',
 'sambar_lauki': 'sorakkai sambar|suraikkai sambar|lauki sambar|sambar with lauki|bottle gourd sambar|dudhi sambar',
 'sambar_ash_gourd': 'poosanikai sambar|vellai poosanikai sambar|white pumpkin sambar|ash gourd sambar|petha sambar',
 'sambar_pumpkin': 'parangikai sambar|parangikkai sambar|yellow pumpkin sambar|kaddu sambar|pumpkin sambar',
 'sambar_radish': 'mullangi sambar|radish sambar|mooli sambar',
 'sambar_okra': 'vendakkai sambar|vendaikai sambar|okra sambar|bhindi sambar|ladies finger sambar',
 'sambar_onion': 'vengaya sambar|chinna vengaya sambar|small onion sambar|shallot sambar|onion sambar',
 'sambar_mixed_veg': 'sambar with vegetables|vegetable sambar|kalavai kai sambar|mix veg sambar',
 'sambar_tiffin': 'idli sambar|tiffin sambar|hotel sambar|dosa sambar|moong dal sambar',
 'sambar_no_oil': 'sambar without oil|oil free sambar|no oil sambar|zero oil sambar',
 'sambar_no_dal': 'sambar without dal|no dal sambar|kai kuzhambu|vegetable kuzhambu',
 'sambar_arachuvitta': 'arachu vitta sambar|arachuvitta sambar|coconut sambar|kerala sambar',
 'seeraga_samba_rice': 'seeraga samba|jeeraga samba|jeera samba rice|seeraga samba arisi|seeraga samba sadam',
 'ponni_rice': 'ponni arisi|ponni boiled rice|ponni sadam',
 'sona_masoori_rice': 'sona masuri|sona masoori|sona masoori sadam',
 'basmati_rice': 'basmathi rice|basmati chawal|basmati sadam',
 'matta_rice': 'kerala matta|rose matta|palakkadan matta|red rice|matta arisi|kerala red rice',
 'mappillai_samba_rice': 'mappillai samba|mapillai samba|maappillai samba|red rice|mappillai samba arisi',
 'kavuni_rice': 'karuppu kavuni|kavuni arisi|black rice|kala chawal',
 'ss_chicken_biryani': 'dindigul biryani|seeraga samba biryani|jeeraga samba biryani|dindigul chicken biryani',
 'ss_mutton_biryani': 'dindigul mutton biryani|seeraga samba mutton biryani|mutton biryani',
 'ss_egg_biryani': 'egg biryani|muttai biryani|seeraga samba egg biryani',
 'ss_veg_biryani': 'veg biryani seeraga samba|vegetable biryani|kaikari biryani',
}

dishes = []
for d in DISHES:
    did, en, ta, hi, veg, ing, y, units = d[:8]
    fry_oil = d[8] if len(d) > 8 else 0  # grams of frying oil absorbed by the batch
    tot = [0.0] * 17; W = 0.0
    for code, g in ing.items():
        v = nut(code); W += g
        for i in range(17): tot[i] += v[i] * g / 100
    if fry_oil:
        for i, x in enumerate(nut('T005')): tot[i] += x * fry_oil / 100
    cooked = W * y + fry_oil
    per = [x / cooked * 100 for x in tot]
    dishes.append({'id': 'AN_' + did, 'n': en, 'ta': ta, 'hi': hi, 'veg': veg,
                   'u': units + [['100 g', 100]], 'v': rnd(per), **({'a': ALIAS[did]} if did in ALIAS else {})})
    print(f"{en[:34]:34} {per[0]:6.0f} kcal/100g  " + ', '.join(f"{u[0]} {u[1]}g={per[0]*u[1]/100:.0f}" for u in units[:2]))

json.dump(raw, open('ifct_raw.json', 'w'), ensure_ascii=False)
json.dump(dishes, open('dishes.json', 'w'), ensure_ascii=False)
print(len(raw), 'raw foods;', len(dishes), 'dishes')
