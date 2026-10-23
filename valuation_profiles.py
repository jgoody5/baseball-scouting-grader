"""Illustrative grade combinations priced from the historical reference set."""
import streamlit as st
from historical_valuation import find_comparables, summarize_matches

# These are explicitly synthetic grade inputs, never attributed to real players.
EXAMPLES = [
 ('Impact shortstop','Position Player','SS',dict(Hit=60,Power=60,Run=60,Arm=60,Field=60)),
 ('Contact shortstop','Position Player','SS',dict(Hit=55,Power=40,Run=55,Arm=55,Field=55)),
 ('Glove-first shortstop','Position Player','SS',dict(Hit=45,Power=40,Run=55,Arm=60,Field=65)),
 ('Speed-first center fielder','Position Player','CF',dict(Hit=50,Power=40,Run=70,Arm=50,Field=60)),
 ('Power center fielder','Position Player','CF',dict(Hit=50,Power=60,Run=60,Arm=55,Field=55)),
 ('Defense-first catcher','Position Player','C',dict(Hit=45,Power=45,Run=30,Arm=60,Field=60)),
 ('Offense-first catcher','Position Player','C',dict(Hit=55,Power=55,Run=35,Arm=55,Field=45)),
 ('Power first baseman','Position Player','1B',dict(Hit=50,Power=65,Run=30,Arm=50,Field=45)),
 ('Hit-first first baseman','Position Player','1B',dict(Hit=60,Power=50,Run=40,Arm=45,Field=50)),
 ('Corner bat with hit risk','Position Player','RF',dict(Hit=40,Power=60,Run=45,Arm=55,Field=45)),
 ('Top-end power starter','Pitcher','Starter',{'Fastball':70,'Secondary 1':65,'Secondary 2':55,'Control':55}),
 ('Balanced starter','Pitcher','Starter',{'Fastball':55,'Secondary 1':55,'Secondary 2':50,'Control':50}),
 ('Pitchability starter','Pitcher','Starter',{'Fastball':45,'Secondary 1':55,'Secondary 2':50,'Control':60}),
 ('Power starter with strike risk','Pitcher','Starter',{'Fastball':65,'Secondary 1':60,'Secondary 2':45,'Control':40}),
 ('Two-weapon power reliever','Pitcher','Reliever',{'Fastball':65,'Secondary 1':65,'Control':40}),
 ('Strike-throwing reliever','Pitcher','Reliever',{'Fastball':55,'Secondary 1':55,'Control':55}),
]


def example_value(example):
    name,kind,target,features = example
    matches = find_comparables(features,kind,target)
    result = summarize_matches(matches,2026,2)
    return result


def render_profile_examples(kind,prefix):
    with st.expander('Explore grade profiles'):
        st.caption('Illustrative inputs, not real player grades. Each example runs through the same historical comparisons. Exploring does not change your report.')
        options = [x for x in EXAMPLES if x[1]==kind]
        name = st.selectbox('Example profile',[x[0] for x in options],key=f'{prefix}_example')
        example = next(x for x in options if x[0]==name)
        st.write('Projected position / role: '+example[2])
        st.write(example[3])
        result = example_value(example)
        if not result:
            st.info('Insufficient similar historical profiles; no automatic value for this example.')
        else:
            from draft_valuation import money_range
            st.write(result['round']+' | '+money_range(result))
            st.caption(f"{result['sample_count']} comparisons; {result['slot_sample_count']} have slot values.")
            st.dataframe([{'Player':r['name'],'Year':r['year'],'Pick':r['pick'],
                           'Round':r['round'],'Grades':str(r['grades'])} for r in result['comparables']],
                          hide_index=True,use_container_width=True)
