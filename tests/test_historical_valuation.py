import unittest
from copy import deepcopy

from draft_valuation import apply_override, evaluate, money_range
from historical_valuation import (load_history, find_comparables, reference_features,
                                   summarize_matches, numeric_round, parse_height)
from valuation_profiles import EXAMPLES, example_value


class HistoricalValuationTests(unittest.TestCase):
    def test_archived_draft_grades_not_later_development(self):
        records = load_history()['records']
        jones = next(r for r in records if r['year']==2022 and r['name']=='Druw Jones')
        self.assertEqual(jones['grades']['Overall'],65)
        self.assertEqual(jones['grades']['Hit'],55)
        skenes = next(r for r in records if r['year']==2023 and r['name']=='Paul Skenes')
        self.assertEqual(skenes['grades']['Fastball'],80)
        self.assertEqual(skenes['pick'],1)
        self.assertTrue(all(r['bio_title']=='draft' for r in records))
        self.assertEqual(len({r['id'] for r in records}),len(records))

    def test_actual_bonus_never_sets_investment_value(self):
        ex = EXAMPLES[0]
        matches = find_comparables(ex[3],ex[1],ex[2])
        first = summarize_matches(matches,2026,2)
        changed = deepcopy(matches)
        for row in changed: row['signing_bonus']=999999999
        after = summarize_matches(changed,2026,2)
        for key in ('bonus_low','bonus_high','round_low','round_high'):
            self.assertEqual(first[key],after[key])

    def test_no_false_dollar_estimate_when_slots_missing(self):
        ex=EXAMPLES[0]; matches=find_comparables(ex[3],ex[1],ex[2])
        for row in matches: row['slot_value']=None
        result=summarize_matches(matches,2026,2)
        self.assertIsNone(result['bonus_low'])
        self.assertIn('Insufficient',money_range(result))

    def test_sparse_profiles_are_not_forced(self):
        self.assertEqual(find_comparables(dict(Hit=20,Power=20,Run=20,Arm=20,Field=20),'Position Player','SS'),[])
        self.assertIsNone(summarize_matches([],2026,2))

    def test_year_holdout_and_player_deduplication(self):
        ex=EXAMPLES[0]
        matches=find_comparables(ex[3],ex[1],ex[2],exclude_year=2024)
        self.assertTrue(all(r['year']!=2024 for r in matches))
        self.assertEqual(len({r['player_id'] for r in matches}),len(matches))

    def test_size_is_used_only_with_historical_measurement(self):
        ex=EXAMPLES[0]
        history=deepcopy(load_history())
        for r in history['records']: r['height_inches']=None; r['weight_lb']=None
        m=find_comparables(ex[3],ex[1],ex[2],height_inches=80,weight_lb=300,history=history)
        self.assertTrue(all(not r['size_matched'] and r['size_distance']==0 for r in m))
        self.assertEqual(parse_height("6'2\""),74)
        self.assertIsNone(parse_height('6 feet approximately'))

    def test_scout_override_without_supported_suggestion(self):
        result=apply_override({'ready':False,'missing':['Not enough comparable profiles']},7,12,300000,450000,'My evaluation')
        self.assertTrue(result['ready'])
        self.assertEqual(result['basis'],'Scout override')
        self.assertFalse(result['model_suggestion']['ready'])

    def test_round_labels_and_examples(self):
        self.assertEqual(numeric_round('CB-A'),1)
        self.assertEqual(numeric_round('CB-B'),2)
        for example in EXAMPLES:
            result=example_value(example)
            if result:
                self.assertLessEqual(result['round_low'],result['round_high'])
                if result['bonus_low'] is not None:
                    self.assertLessEqual(result['bonus_low'],result['bonus_high'])
                self.assertGreaterEqual(result['sample_count'],4)

    def test_raw_power_and_command_not_invented_in_public_profiles(self):
        for row in load_history()['records']:
            f=reference_features(row)
            self.assertNotIn('Command',f)
            self.assertNotIn('Raw Power',f)


if __name__ == '__main__':
    unittest.main()
