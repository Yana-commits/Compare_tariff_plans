import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats as st
import seaborn as sns

calls = pd.read_csv('calls.csv')
internet = pd.read_csv('internet.csv')
messages = pd.read_csv('messages.csv')
tariffs = pd.read_csv('tariffs.csv')
users = pd.read_csv('users.csv')

pd.set_option('display.max_columns', None)

calls['call_date'] = pd.to_datetime(calls['call_date'], format='ISO8601')

internet['session_date'] = pd.to_datetime(internet['session_date'], format='ISO8601')
internet.drop(columns=['Unnamed: 0'], inplace=True)
internet.rename(columns={"mb_per_month_included": "gb_per_month_included"}, inplace=True)

messages['message_date'] = pd.to_datetime(messages['message_date'], format='ISO8601')

users['reg_date'] = pd.to_datetime(users['reg_date'], format='ISO8601')
users['churn_date'] = users['churn_date'].fillna(pd.to_datetime('today').date())

tariffs.rename(columns={"mb_per_month_included": "gb_per_month_included"}, inplace=True)

def to_gig(num):
    if num == 0:
        return 0
    elif num < 1024:
        return 1
    elif num%1024 == 0:
        return num//1024
    else:
        return num//1024 +1

tariffs["gb_per_month_included"] = tariffs["gb_per_month_included"].apply(to_gig)

calls['year_month'] = calls['call_date'].dt.to_period('M')
messages['year_month'] = messages['message_date'].dt.to_period('M')
internet['year_month'] = internet['session_date'].dt.to_period('M')

calls['duration'] = np.ceil(calls['duration'])

#print('calls',calls.info())
#print('internet',internet.info())
#print('messages',messages.info())
#print('tariffs',tariffs.info())
#print('users',users.info())

calls_per_month = calls.groupby(['user_id','year_month'])['duration'].agg(['sum','count']).reset_index()
calls_per_month.rename(columns={'sum': 'minutes', 'count': 'calls'}, inplace=True)
messages_per_month = messages.groupby(['user_id','year_month']).id.agg(messeges ='count').reset_index()
internet_per_month = internet.groupby(['user_id','year_month']).mb_used.agg('sum').reset_index()

internet_per_month['mb_used'] = internet_per_month['mb_used'].apply(to_gig)
internet_per_month.rename(columns={'mb_used': 'gb_used'}, inplace=True)

#print(calls_per_month)
#print(messages_per_month)
#print(internet_per_month)

res_temp = calls_per_month.merge(messages_per_month, on=['user_id','year_month'])\
.merge(internet_per_month, on=['user_id','year_month'])

user_t = users[['user_id','tariff']]

res_temp = res_temp.merge(user_t, on='user_id')
res_temp = res_temp.merge(tariffs,left_on='tariff',right_on ='tariff_name')
res_temp.drop(columns=['tariff_name'], inplace=True)

def includes(users,include,tariff):
    if users > include:
       users =  users - include
    else: 
        users = 0

    return users * tariff

def revenue(row):
   
   rev_min = includes(row['minutes'],row['minutes_included'],row['rub_per_minute'])
   rev_mess = includes(row['messeges'],row['messages_included'],row['rub_per_message'])
   rev_net = includes(row['gb_used'],row['gb_per_month_included'],row['rub_per_gb'])

   return rev_min +rev_mess +rev_net +row['rub_monthly_fee']

res_temp['revenue_per_month'] = res_temp.apply(revenue, axis=1)

users_needs = res_temp.groupby(["user_id","tariff"])[['minutes','messeges','gb_used']].agg(
    avg_minutes = ('minutes', 'mean'),
    avg_messeges = ('messeges', 'mean'),
    avg_gb_used = ('gb_used', 'mean')                                                                                           
    ).reset_index()

#print(users_needs)
#print(res_temp)

users_needs_t = users_needs.groupby("tariff")[['avg_minutes','avg_messeges','avg_gb_used']].agg(
    avg_minutes = ('avg_minutes', 'mean'),
    avg_messeges = ('avg_messeges', 'mean'),
    avg_gb_used = ('avg_gb_used', 'mean'), 
    std_minutes = ('avg_minutes', 'std'),
    std_messeges = ('avg_messeges', 'std'),
    std_gb_used = ('avg_gb_used', 'std')

    ).reset_index()

#print(users_needs_t)


# visualiation with phython

#ax = users_needs.query('tariff == "smart"').plot(
#    kind = 'hist',
#    y = 'avg_minutes',
#    histtype = 'step',
#    linewidth =5,
#    alpha = 0.7,
#    label = 'smart',
#    )

#users_needs.query('tariff == "ultra"').plot(
#    kind = 'hist',
#    y = 'avg_minutes',
#    histtype = 'step',
#    linewidth =5,
#    alpha = 0.7,
#    label = 'ultra',
#    ax = ax,
#    grid = True,
#    legend = True,
#    )

#plt.title('minutes')
#plt.show()

#ax = users_needs.query('tariff == "smart"').plot(
#    kind = 'hist',
#    y = 'avg_messeges',
#    histtype = 'step',
#    linewidth =5,
#    alpha = 0.7,
#    label = 'smart',
#    )

#users_needs.query('tariff == "ultra"').plot(
#    kind = 'hist',
#    y = 'avg_messeges',
#    histtype = 'step',
#    linewidth =5,
#    alpha = 0.7,
#    label = 'ultra',
#    ax = ax,
#    grid = True,
#    legend = True,
#    )

#plt.title('messeges')
#plt.show()

#ax = users_needs.query('tariff == "smart"').plot(
#    kind = 'hist',
#    y = 'avg_gb_used',
#    histtype = 'step',
#    linewidth =5,
#    alpha = 0.7,
#    label = 'smart',
#    )

#users_needs.query('tariff == "ultra"').plot(
#    kind = 'hist',
#    y = 'avg_gb_used',
#    histtype = 'step',
#    linewidth =5,
#    alpha = 0.7,
#    label = 'ultra',
#    ax = ax,
#    grid = True,
#    legend = True,
#    )

#plt.title('gb_used')
#plt.show()

user_revenue = res_temp.groupby(["user_id","tariff"])['revenue_per_month'].agg(['mean','sum'])

user_revenue_final = user_revenue.groupby("tariff").agg(
        total_sum = ('sum','sum'),
        user_num = ('sum','count'),
        mean_rev = ('mean','mean'),
        median_rev = ('mean','median')
        )

#print(user_revenue_final)

total_smart = user_revenue.query('tariff == "smart"')['mean']
total_ultra = user_revenue.query('tariff =="ultra"')['mean']

result = st.ttest_ind(total_smart,total_ultra)

#print(result.pvalue)

ARPU_smart = user_revenue_final.query('tariff == "smart"')['total_sum']/user_revenue_final\
    .query('tariff == "smart"')['user_num']

ARPU_ultra = user_revenue_final.query('tariff == "ultra"')['total_sum']/user_revenue_final\
    .query('tariff == "ultra"')['user_num']

#print('ARPU_smart', ARPU_smart)
#print('ARPU_ultra', ARPU_ultra)

def over_limit(row,colmn_name = "minutes"):
    item = row['minutes']
    item_included = row['minutes_included']
    rub_per_item = row['rub_per_minute']

    if colmn_name == "messeges":
        item = row['messeges']
        item_included = row['messages_included']
        rub_per_item = row['rub_per_message']
    elif colmn_name == "gb_used":
        item = row['gb_used']
        item_included = row['gb_per_month_included']
        rub_per_item = row['rub_per_gb']

    res = includes(item, item_included, rub_per_item)

    if res == 0:
        return 0
    else: return 1

res_temp['overlim_minutes'] = res_temp.apply(over_limit, axis=1, colmn_name = "minutes")
res_temp['overlim_messeges'] = res_temp.apply(over_limit, axis=1, colmn_name = "messeges")
res_temp['overlim_gb_used'] = res_temp.apply(over_limit, axis=1, colmn_name = "gb_used")

res_temp_overlim = res_temp\
    .groupby(['user_id','tariff'])[['overlim_minutes','overlim_messeges','overlim_gb_used']].mean()\
    .groupby("tariff").agg('mean')*100

#print(res_temp_overlim)

traffic_for_tableu = res_temp.groupby(['user_id','tariff'])\
    [['minutes','messeges','gb_used','revenue_per_month','overlim_minutes','overlim_messeges','overlim_gb_used']].mean().round(2).reset_index()

cols_to_multiply = ['overlim_minutes','overlim_messeges','overlim_gb_used']
traffic_for_tableu[cols_to_multiply] *= 100
print(traffic_for_tableu)

#traffic_for_tableu.to_csv('traffic_for_tableu.csv', index=False)

print("ok")