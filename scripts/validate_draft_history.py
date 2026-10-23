"""Leave-one-draft-year-out check. Outcomes only; no career-success claim."""
import json
from pathlib import Path
import statistics
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from historical_valuation import load_history, reference_features, find_comparables, summarize_matches, numeric_round

history=load_history()
results=[]
for row in history['records']:
    if not row['pick'] or not numeric_round(row['round']):
        continue
    f=reference_features(row)
    if row['kind']=='Pitcher':
        target='Reliever' if row.get('relief_context') and f.get('Secondary 2',0)<=45 else 'Starter'
    else:
        pos=(row.get('position') or '').split('/')[0]
        target=pos if pos in ('C','1B','2B','3B','SS','CF','RF','LF','OF') else 'SS' if pos=='INF' else ''
    if not target:
        continue
    matches=find_comparables(f,row['kind'],target,source_type=row['source_type'],hand=row.get('hand',''),exclude_year=row['year'],exclude_id=row['id'])
    result=summarize_matches(matches,2026,2)
    results.append({'id':row['id'],'year':row['year'],'kind':row['kind'],'ready':result is not None,
                    'absolute_pick_error':abs(result['median_pick']-row['pick']) if result else None,
                    'round_in_range':result['round_low']<=numeric_round(row['round'])<=result['round_high'] if result else None,
                    'pick_in_range':result['pick_low']<=row['pick']<=result['pick_high'] if result else None})

def summary(rows):
    ready=[r for r in rows if r['ready']]
    return {'eligible_rows':len(rows),'supported_rows':len(ready),
            'support_rate':round(len(ready)/len(rows),3) if rows else None,
            'median_absolute_pick_error':statistics.median(r['absolute_pick_error'] for r in ready) if ready else None,
            'round_interval_coverage':round(sum(r['round_in_range'] for r in ready)/len(ready),3) if ready else None,
            'pick_interval_coverage':round(sum(r['pick_in_range'] for r in ready)/len(ready),3) if ready else None}
report={'method':'Leave-one-draft-year-out; no same-year peers; ranked/drafted population only',
        'limitations':'Comparison guide only. Reported coverage is descriptive, not calibrated confidence. Missing undrafted/lower-ranked coverage and subjective role proxies limit generalization.',
        'overall':summary(results),
        'by_kind':{k:summary([r for r in results if r['kind']==k]) for k in ('Pitcher','Position Player')},
        'by_year':{str(y):summary([r for r in results if r['year']==y]) for y in history['years']}}
(ROOT/'data/valuation/validation_report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
