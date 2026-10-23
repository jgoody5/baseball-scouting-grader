"""Historical grade-profile comparisons. No asking-price or bonus-demand model."""
from __future__ import annotations

from functools import lru_cache
import csv
import json
import math
from pathlib import Path
import re


@lru_cache(maxsize=1)
def load_history():
    root=Path(__file__).parent / 'data/valuation'
    metadata=json.loads((root/'draft_history.json').read_text())
    grade_fields={'Hit','Power','Run','Arm','Field','Overall','Fastball','Curveball','Slider','Sweeper','Cutter','Splitter','Changeup','Control'}
    numeric_fields={'year','player_id','draft_rank','height_inches','weight_lb','pick','slot_value','signing_bonus'}
    records=[]
    with (root/metadata['records_file']).open(newline='') as stream:
        for raw in csv.DictReader(stream):
            grades={k:int(v) for k,v in raw.items() if k in grade_fields and v}
            row={k:(int(v) if v else None) if k in numeric_fields else v for k,v in raw.items() if k not in grade_fields}
            row.update(id=f"{row['year']}-{row['player_id']}", grades=grades, bio_title='draft',
                       relief_context=row['relief_context']=='True',
                       grade_source=metadata['sources'][str(row['year'])]['grades'],
                       outcome_source=metadata['sources'][str(row['year'])]['outcomes'])
            records.append(row)
    return {**metadata,'records':records}


def numeric_round(value):
    if value in ('PPI', 'CB-A', '1C'):
        return 1
    if value in ('CB-B', '2C', 'SUP-2'):
        return 2
    if value == 'SUP-3':
        return 3
    if value == '4C':
        return 4
    return int(value) if value and str(value).isdigit() else None


def reference_features(row):
    g = row['grades']
    if row['kind'] == 'Position Player':
        return {k: g[k] for k in ('Hit', 'Power', 'Run', 'Arm', 'Field') if k in g}
    secondaries = sorted([v for k,v in g.items() if k in
                          ('Slider', 'Sweeper', 'Cutter', 'Curveball', 'Changeup', 'Splitter')], reverse=True)
    f = {k: g[k] for k in ('Fastball', 'Control') if k in g}
    for index, value in enumerate(secondaries[:2]):
        f[f'Secondary {index+1}'] = value
    return f


def position_penalty(query, historical):
    tokens = set(re.split(r'[/, ]+', (historical or '').upper()))
    if query in tokens:
        return 0.0
    if query in ('CF', 'RF', 'LF', 'OF') and 'OF' in tokens:
        return 1.5  # Draft archives often report OF, not an exact defensive position.
    if query in ('SS', '2B', '3B') and 'INF' in tokens:
        return 2.5
    if query == 'C' or 'C' in tokens:
        return None  # Do not price catchers from non-catchers or vice versa.
    if query == 'DH' and ('1B' in tokens or 'OF' in tokens):
        return 4.0
    if query in ('SS', '2B', '3B') and tokens.intersection({'SS', '2B', '3B', 'INF'}):
        return 4.0
    if query in ('1B', 'RF', 'LF', 'OF') and tokens.intersection({'1B', 'RF', 'LF', 'OF'}):
        return 4.0
    return None


def weighted_quantile(values, quantile):
    ordered = sorted(values)
    total = sum(w for _,w in ordered)
    if not ordered or total <= 0:
        return None
    target = total * quantile
    cumulative = 0
    for value, weight in ordered:
        cumulative += weight
        if cumulative >= target:
            return value
    return ordered[-1][0]


def find_comparables(features, kind, target, *, source_type='Any', hand='', height_inches=None,
                     weight_lb=None, exclude_year=None, exclude_id=None, history=None):
    history = history or load_history()
    weights = ({'Hit': .35, 'Power': .30, 'Run': .10, 'Arm': .10, 'Field': .15}
               if kind == 'Position Player' else
               {'Fastball': .30, 'Secondary 1': .30, 'Secondary 2': .15, 'Control': .25})
    required = ['Hit','Power','Run','Arm','Field'] if kind == 'Position Player' else ['Fastball','Secondary 1','Control']
    if kind == 'Pitcher' and target == 'Starter':
        required += ['Secondary 2']
    if any(k not in features for k in required):
        return []
    matches = []
    for row in history['records']:
        if row['kind'] != kind or row['year'] == exclude_year or row['id'] == exclude_id:
            continue
        if not row['pick'] or not numeric_round(row['round']):
            continue
        other = reference_features(row)
        if any(k not in other for k in required):
            continue
        pp = position_penalty(target, row['position']) if kind == 'Position Player' else 0
        if pp is None:
            continue
        # Same-source peers are preferred, but cross-source matches remain visible.
        context_penalty = 0 if source_type in ('Any', row['source_type']) else 4
        hand_penalty = 0 if not hand or hand == row.get('hand') else 1
        active = [k for k in required if k in weights]
        squared = sum(weights[k] * (features[k]-other[k])**2 for k in active) / sum(weights[k] for k in active)
        role_penalty = 0
        if kind == 'Pitcher':
            role_penalty = (0 if row.get('relief_context') else 5) if target == 'Reliever' else (3 if row.get('relief_context') else 0)
        distance = math.sqrt(squared + pp**2 + context_penalty**2 + hand_penalty**2 + role_penalty**2)
        # Size changes ranking only when both draft-time measurements are explicit.
        size_terms = []
        if height_inches is not None and row.get('height_inches') is not None:
            size_terms.append(min(abs(height_inches-row['height_inches'])/2, 3))
        if weight_lb is not None and row.get('weight_lb') is not None:
            size_terms.append(min(abs(weight_lb-row['weight_lb'])/20, 3))
        if distance > 10:
            continue  # Do not force distant or out-of-distribution comparisons.
        size_distance = sum(size_terms) / len(size_terms) if size_terms else 0
        # Size may reorder near peers, but never increases a player's value directly.
        match = {**row, 'features': other, 'grade_distance': round(distance,3),
                 'size_distance': round(size_distance,3), 'size_matched': bool(size_terms),
                 'distance': round(distance + .15 * size_distance,3)}
        match['similarity_weight'] = math.exp(-.5 * (match['distance']/5)**2)
        matches.append(match)
    ordered = sorted(matches, key=lambda r:(r['distance'],r['id']))
    unique = {}
    for row in ordered:
        unique.setdefault(row['player_id'],row)
    return list(unique.values())[:12]


def profile_label(features, kind, target):
    if kind == 'Pitcher':
        if target == 'Reliever':
            return 'Power relief profile' if features.get('Fastball',0)>=60 else 'Relief profile with secondary weapon'
        if features.get('Fastball',0)>=65 and features.get('Secondary 1',0)>=60:
            return 'Power starter profile'
        if features.get('Control',0)>=55:
            return 'Strike-throwing starter profile'
        return 'Starter profile with command development'
    if target == 'C':
        return 'Defense-led catcher' if features.get('Field',0)>features.get('Hit',0) else 'Offense-led catcher'
    if target in ('SS','CF','2B'):
        if features.get('Run',0)>=65 and features.get('Power',0)<=45:
            return 'Speed / defense at a premium position'
        if features.get('Power',0)>=60:
            return 'Power at a premium position'
        return 'Contact / balanced premium-position profile'
    if features.get('Power',0)>=60:
        return 'Bat-first power profile'
    return 'Contact / balanced corner profile'


def summarize_matches(matches, reference_year, risk_width, adjustment_points=0, history=None):
    history = history or load_history()
    if len(matches) < 4:
        return None
    # These factors are policy assumptions; they are not learned historical coefficients.
    multiplier = max(.85,min(1.15,1+.03*adjustment_points))
    qlo,qhi = (.25,.75) if risk_width == 0 else (.15,.85) if risk_width <=2 else (.10,.90)
    weighted_rounds = [(numeric_round(r['round']),r['similarity_weight']) for r in matches]
    weighted_picks = [(r['pick'],r['similarity_weight']) for r in matches]
    slots = []
    # Annual dollars normalized by the same first-pick slot index, not by actual bonuses.
    ref_slot = 11350600 if reference_year == 2026 else float(history['first_pick_slots'][str(reference_year)])
    for r in matches:
        if r.get('slot_value'):
            amount = r['slot_value'] * ref_slot / float(history['first_pick_slots'][str(r['year'])])
            slots.append((amount, r['similarity_weight']))
    low = high = None
    if len(slots) >= 4 and len(slots)/len(matches) >= .75:
        low = int(math.floor(weighted_quantile(slots,qlo)*multiplier/10000)*10000)
        high = int(math.ceil(weighted_quantile(slots,qhi)*multiplier/10000)*10000)
    rlo,rhi = int(weighted_quantile(weighted_rounds,qlo)),int(weighted_quantile(weighted_rounds,qhi))
    return {'round_low':rlo,'round_high':rhi,'round':f'Rounds {rlo}-{rhi} value',
            'pick_low':int(weighted_quantile(weighted_picks,qlo)),
            'pick_high':int(weighted_quantile(weighted_picks,qhi)),
            'median_pick':int(weighted_quantile(weighted_picks,.5)),
            'bonus_low':low,'bonus_high':high,'slot_sample_count':len(slots),
            'sample_count':len(matches),'effective_sample_count':round(sum(r['similarity_weight'] for r in matches)**2/sum(r['similarity_weight']**2 for r in matches),2),'historical_years':sorted({r['year'] for r in matches}),
            'adjustment_multiplier':multiplier, 'quantiles':[qlo,qhi],
            'money_basis':'Historical pick slot values indexed to '+str(reference_year)+
              ' dollars. Actual signing bonuses are displayed as context only. Trait/physical-fit adjustments are discretionary.',
            'valuation_method':'Historical grade-profile comparables',
            'comparables':matches}


def parse_height(value):
    text = str(value or '').strip()
    match = re.fullmatch(r'(\d)\s*(?:\x27|ft|-|foot)\s*(\d{1,2})\s*(?:\x22|in)?',text)
    if match:
        feet,inches = map(int,match.groups())
        return feet*12+inches if 4<=feet<=7 and 0<=inches<12 else None
    return None
