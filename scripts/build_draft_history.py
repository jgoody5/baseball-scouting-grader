"""Rebuild factual draft reference rows from official archived MLB pages/APIs.

No scouting prose is distributed. Grade reports are from the draft-specific
archive, never the player's current team prospect page.
"""
import csv
import concurrent.futures
import datetime
import html
import json
import re
from pathlib import Path
from urllib.request import urlopen, Request

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'tmp' / 'draft_history'
YEARS = (2022, 2023, 2024, 2025)


def fetch(url, name):
    path = CACHE / name
    if path.exists():
        return path.read_text()
    request = Request(url, headers={'User-Agent': 'BaseballScoutingGrader/0.2 (public draft reference research)'})
    with urlopen(request, timeout=60) as response:
        text = response.read().decode('utf-8', errors='replace')
    path.write_text(text)
    return text


def year_data(year):
    archive = f'https://www.mlb.com/milb/prospects/{year}/draft/'
    outcome_url = f'https://statsapi.mlb.com/api/v1/draft/{year}'
    page = fetch(archive, f'grades-{year}.html')
    match = re.search(r'<span data-init-state="([^"]+)"', page)
    if not match:
        raise ValueError(f'Missing archive state: {year}')
    state = json.loads(html.unescape(match[1]))
    if str(state['context']['year']) != str(year) or state['context']['list'] != 'draft':
        raise ValueError(f'Wrong archive: {year}')
    data = state['payload']
    ranked = [item for key, batch in data['ROOT_QUERY'].items()
              if key.startswith('getPlayerRankingsFromSelection(') for item in batch]
    draft = json.loads(fetch(outcome_url, f'outcomes-{year}.json'))['drafts']
    if draft['draftYear'] != year:
        raise ValueError('Wrong draft outcomes')
    picks = {p['person']['id']: p for r in draft['rounds'] for p in r['picks'] if p.get('person')}
    records = []
    for item in ranked:
        entity = item['playerEntity']
        person = data[entity['player']['__ref']]
        pid = int(entity['player']['__ref'].split(':')[-1])
        draft_bios = [part for part in entity.get('prospectBio', []) if str(part.get('contentTitle', '')).strip().lower() == 'draft']
        if not draft_bios:
            continue
        bio = ' '.join((part.get('contentText') or '') for part in draft_bios)
        # Capture only numerical grades from the explicitly headed scouting-grade paragraph.
        text = html.unescape(re.sub('<[^>]+>', ' ', bio))
        report = re.search(r'Scouting grades\s*:\s*(.*?)(?:\n|$)', text, re.I)
        grade_paragraphs = [html.unescape(re.sub('<[^>]+>', ' ', p)) for p in re.findall(r'<p[^>]*>(.*?)</p>', bio, re.S) if re.search(r'Scouting\s+grades', re.sub('<[^>]+>', ' ',p), re.I)]
        if grade_paragraphs:
            report = re.search(r'Scouting grades\s*:\s*(.*?)(?:\n|$)', grade_paragraphs[0], re.I)
        if not report:
            continue
        values = dict((k.strip(), int(v)) for k,v in re.findall(
            r'(Hit|Power|Run|Arm|Field|Overall|Fastball|Curveball|Slider|Sweeper|Cutter|Splitter|Changeup|Control)\s*:\s*(\d{2})',
            report[1]))
        if not values:
            continue
        pick = picks.get(pid)
        def amount(key):
            value = pick.get(key) if pick else None
            return int(value) if value and str(value).isdigit() and int(value) > 0 else None
        school = (pick or {}).get('school', {})
        school_class = school.get('schoolClass', '')
        source_type = ('High school' if school_class.startswith('HS') else
                       'Junior college' if school_class.startswith('JC') else
                       'College' if school_class.startswith('4YR') else 'Unknown')
        is_pitcher = 'Fastball' in values and 'Hit' not in values
        # Restrict physical observations to report-time text; no current roster body measurements.
        heights = re.findall(r'\b(\d)-foot-(\d{1,2})\b', text)
        height = int(heights[0][0])*12+int(heights[0][1]) if heights else None
        weights = re.findall(r'\b(\d{3})[- ]pound\b', text)
        weight = int(weights[0]) if weights else None
        records.append({'id': f'{year}-{pid}', 'player_id': pid, 'year': year,
            'name': person.get('useName', '')+' '+person.get('useLastName', '') if person.get('useName') else person.get('fullName', str(pid)),
            'position': entity.get('position', ''), 'kind': 'Pitcher' if is_pitcher else 'Position Player',
            'grades': values, 'draft_rank': item['rank'], 'source_type': source_type,
            'school_class': school_class, 'height_inches': height, 'weight_lb': weight,
            'bio_title': 'draft', 'relief_context': bool(re.search(r'\b(?:closer|reliever|bullpen)\b', text, re.I)), 'size_source': 'Explicit draft scouting narrative only; missing otherwise',
            'pick': pick.get('pickNumber') if pick else None,
            'round': str(pick.get('pickRound')) if pick else None,
            'slot_value': amount('pickValue'), 'signing_bonus': amount('signingBonus'),
            'hand': person.get('pitchHandCode') if is_pitcher else person.get('batSideCode'),
            'grade_source': archive, 'outcome_source': outcome_url})
    return records


if __name__ == '__main__':
    CACHE.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        records = [row for batch in pool.map(year_data, YEARS) for row in batch]
    dataset = {'version': 'mlb-draft-2022-2025-v2', 'retrieved_at': datetime.date.today().isoformat(),
        'years': list(YEARS), 'grade_basis': 'MLB Pipeline draft-specific archive grades',
        'coverage': 'Ranked draft prospects only; not the full population of eligible players',
        'records': records, 'first_pick_slots': {str(y): json.loads((CACHE/f'outcomes-{y}.json').read_text())['drafts']['rounds'][0]['picks'][0]['pickValue'] for y in YEARS}}
    grades = ['Hit','Power','Run','Arm','Field','Overall','Fastball','Curveball','Slider','Sweeper','Cutter','Splitter','Changeup','Control']
    fields = ['year','player_id','name','position','kind','draft_rank','source_type','school_class',
              'height_inches','weight_lb','relief_context','hand','pick','round','slot_value','signing_bonus']
    target=ROOT/'data/valuation/draft_records.csv'
    with target.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields+grades)
        writer.writeheader()
        for row in records:
            writer.writerow({**{k:row.get(k) for k in fields},**row['grades']})
    dataset.pop('records')
    dataset['records_file']='draft_records.csv'
    dataset['record_count']=len(records)
    dataset['sources']={str(y):{'grades':f'https://www.mlb.com/milb/prospects/{y}/draft/',
        'outcomes':f'https://statsapi.mlb.com/api/v1/draft/{y}'} for y in YEARS}
    path = ROOT/'data/valuation/draft_history.json'
    path.write_text(json.dumps(dataset, indent=2)+'\n')
    from collections import Counter
    print('Records:', len(records), 'years:', Counter(r['year'] for r in records))
    print('By kind:',Counter(r['kind'] for r in records))
    print('Drafted:',sum(r['pick'] is not None for r in records), 'with slots:',sum(r['slot_value'] is not None for r in records), 'with bonuses:',sum(r['signing_bonus'] is not None for r in records))
    print('Explicit report size:',sum(r['height_inches'] is not None for r in records),sum(r['weight_lb'] is not None for r in records))
