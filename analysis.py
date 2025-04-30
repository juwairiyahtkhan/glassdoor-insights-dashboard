import pandas as pd
import ast
from functools import reduce
from itertools import combinations
from collections import Counter

#Define categories
empat_categories = [
    "Economic Value", "Interest Value", "Social Value", "Development Value", "Application Value", "No Value"
]
display_categories = empat_categories[:-1]  #For prediction output

# ===== OVERVIEW PANEL =====
#Bar Chart for Average overall_rating, recommendation %, and outlook % by Firm
df_reviews = pd.read_csv("./source/CSV/df_reviews.csv")

def percent_positive(col):
    return col.apply(lambda x: 1 if str(x).lower() in ['positive', 'yes'] else 0)

df_reviews['recommend_bin'] = percent_positive(df_reviews['recommend'])
df_reviews['outlook_bin'] = percent_positive(df_reviews['outlook'])

df_firm_summary = df_reviews.groupby('firm').agg({
    'overall_rating': lambda x: round(x.mean(), 2),
    'recommend_bin': lambda x: round(x.mean() * 100, 2),
    'outlook_bin': lambda x: round(x.mean() * 100, 2)
}).reset_index().rename(columns={
    'recommend_bin': 'recommend_percent',
    'outlook_bin': 'outlook_percent'
})

df_firm_summary.to_csv('./source/CSV/firm-averages.csv', index=False) # --> Bar chart

#Radar Chart for average empat categories per firm
#Flatten and average category scores for each firm
#Expand categories into binary flags for each review
def extract_prob_vector(category_dict):
    vector = {cat: 0 for cat in display_categories}
    if isinstance(category_dict, dict):
        for cat in display_categories:
            vector[cat] = category_dict.get(cat, 0)
    return vector

#Convert stringified dicts to real dicts
df_reviews['pros_cat'] = df_reviews['pros_cat'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
df_reviews['cons_cat'] = df_reviews['cons_cat'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
#Add binary columns to df for pros and cons
for cat in display_categories:
    df_reviews[f'pros_{cat}'] = df_reviews['pros_cat'].apply(lambda x: extract_prob_vector(x).get(cat, 0))
    df_reviews[f'cons_{cat}'] = df_reviews['cons_cat'].apply(lambda x: extract_prob_vector(x).get(cat, 0))

#Average by firm
firm_empat_profile = df_reviews.groupby('firm')[
    [f'pros_{cat}' for cat in display_categories] + [f'cons_{cat}' for cat in display_categories]
].mean().multiply(100).round(2).reset_index()

firm_empat_profile.to_csv('./source/CSV/firm_empat_profile.csv', index=False)# --> Radar-chart

# ===== TEMPORAL TRENDS PANEL =====
#Tracking Rated categories over time
df_reviews['year_month'] = pd.to_datetime(df_reviews['year_month'], errors='coerce')
df_reviews['year'] = df_reviews['year_month'].dt.year
rating_cols = ['overall_rating', 'work_life_balance', 'culture_values', 'career_opp', 'comp_benefits', 'senior_mgmt']

yearly_ratings = (
    df_reviews
    .groupby(['firm', 'year'])[rating_cols]
    .mean()
    .reset_index()
)

yearly_ratings = yearly_ratings.round(1)
yearly_ratings.to_csv('./source/CSV/yearly_ratings.csv', index=False) # --> Multi-line plot

#Tracking EmpAt category count changes over time
def monthly_empat_count(df, col):
  return (
      df[df[col].notna()].groupby(['year_month', col]).size().reset_index(name='count')
  )

pros_time = monthly_empat_count(df_reviews, 'top_pros_category')
cons_time = monthly_empat_count(df_reviews, 'top_cons_category')
category_col = 'top_category'
pros_time = pros_time.rename(columns={'top_pros_category': category_col}) #Rename for before merging
cons_time = cons_time.rename(columns={'top_cons_category': category_col})

#Combine and sum counts per category
empat_time_series = (
    pd.concat([pros_time, cons_time])
    .groupby(['year_month', category_col])
    .sum()
    .reset_index()
    .pivot(index='year_month', columns=category_col, values='count')
    .fillna(0)
)

empat_time_series.to_csv('./source/CSV/empat_time_series.csv') # --> Stacked-line plot 

# ===== EMPAT PANEL =====
#Rank firms by how frequently each EmpAt value is tagged in pros
firm_profile_fit = []

for cat in display_categories:
    df_cat = df_reviews.groupby('firm').agg({
        f'pros_{cat}': 'sum',
        'pros_cat': 'count'  #counts total reviews per firm
    }).reset_index()
    df_cat[f'{cat}_fit'] = round((df_cat[f'pros_{cat}'] / df_cat['pros_cat']) * 100, 2)
    df_cat = df_cat[['firm', f'{cat}_fit']]
    firm_profile_fit.append(df_cat)

df_profile_fit = reduce(lambda left, right: pd.merge(left, right, on='firm'), firm_profile_fit)
df_profile_fit.to_csv('./source/CSV/profile_fit.csv', index=False) # --> Horizontal bar graph

#EmpAt sentiment polarity distribution
#Tracks how often each value is praised (in pros) vs. criticised (in cons)
empat_sentiment = []

for cat in display_categories:
    pros_count = df_reviews[f'pros_{cat}'].sum()
    cons_count = df_reviews[f'cons_{cat}'].sum()
    total = pros_count + cons_count
    sentiment_ratio = round((pros_count / total) * 100, 2) if total else 0
    empat_sentiment.append({
        'EmpAt Value': cat,
        'Positive Mentions': int(pros_count),
        'Negative Mentions': int(cons_count),
        'Positive %': sentiment_ratio,
        'Negative %': round(100 - sentiment_ratio, 2)
    })

df_empat_sentiment = pd.DataFrame(empat_sentiment)
df_empat_sentiment.to_csv('./source/CSV/empat_sentdistrib.csv', index=False)  # --> Diverging bar chart

#Tracks how often EmpAt categories co-occur in the same review
cooccurrence_counter = Counter()
for idx, row in df_reviews.iterrows():
    mentioned_cats = []
    for cat in display_categories:
        if row.get(f'pros_{cat}', 0) > 0 or row.get(f'cons_{cat}', 0) > 0:
            mentioned_cats.append(cat)   
    if mentioned_cats:
        for combo in combinations(sorted(set(mentioned_cats)), 2):  #Count unique pair combinations of categories
            cooccurrence_counter[combo] += 1

cooccurrence_records = []
for combo, count in cooccurrence_counter.items():
    cooccurrence_records.append({'Parent': combo[0], 'Child': combo[1], 'Count': count})

df_cooccurrence = pd.DataFrame(cooccurrence_records)
df_cooccurrence.to_csv('./source/CSV/cooccurrence_network.csv', index=False)  # --> Network diagram

#Track which EmpAt values are rarely mentioned in either pros or cons
neglect_data = []

for cat in display_categories:
    pros_count = df_reviews[f'pros_{cat}'].sum()
    cons_count = df_reviews[f'cons_{cat}'].sum()
    total = pros_count + cons_count
    neglect_data.append({
        'EmpAt Value': cat,
        'Total Mentions': int(total)
    })

df_neglect = pd.DataFrame(neglect_data).sort_values(by='Total Mentions', ascending=True)
df_neglect.to_csv('./source/CSV/neglect_index.csv', index=False)  # --> Radial Column Chart

