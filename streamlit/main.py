'''
This is a project to create an interactive streamlit app to visualize
Dicoding Collection company.
Est. 2024
'''


import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from babel.numbers import format_currency
sns.set_style("dark")
st.header('Dicoding Collection Dashboard (Artha) :dragon:', divider="rainbow")

# ============= Helper Function (Creating Dataframes for viz from universal df) =============
def create_daily_orders_df(df):
    daily_orders_df = df.resample(rule='D', on='order_date').agg({
        "order_id":"nunique",
        "total_price":"sum"
    })
    daily_orders_df.reset_index(inplace=True)
    daily_orders_df.rename(columns={
        "order_id":"order_count",
        "total_price":"revenue"
    }, inplace=True)
    return daily_orders_df

def create_sum_order_items_df(df):
    sum_order_items_df = (df.groupby('product_name')['quantity_y']
                          .sum()
                          .sort_values()
                          .reset_index()
    )
    return sum_order_items_df

def create_gender_df(df):
    gender_df = df.groupby('gender')['customer_id'].nunique().reset_index()
    gender_df.rename(columns={'customer_id':'customer_count'}, inplace=True)
    return gender_df

def create_age_df(df):
    age_df = df.groupby('age_group')['customer_id'].nunique().reset_index()
    age_df.rename(columns={'customer_id':'customer_count'}, inplace=True)    
    return age_df

def create_states_df(df):
    states_df = df.groupby('state')['customer_id'].nunique().reset_index()
    states_df.rename(columns={'customer_id':'customer_count'}, inplace=True)    
    return states_df    

def create_rfm_df(df):
    rfm_df = df.groupby(by='customer_id', as_index=False).agg({
        'order_id':'nunique',
        'order_date':'max',
        'total_price':'sum'
    })
    latest_date = df['order_date'].max()
    rfm_df['order_date'] = rfm_df['order_date'].apply(lambda x: (latest_date - x).days)
    rfm_df.rename(
        columns={
            'order_id':'frequency',
            'order_date':'recency',
            'total_price':'monetary'
        },
        inplace=True
    )
    return rfm_df


# ============= Data Import =============
all_df = pd.read_csv('streamlit/all_df.csv')
# Sorting rows based on order_date
all_df.sort_values(by="order_date", inplace=True)
# Reset index because it was imported from csv
all_df.reset_index(inplace=True)
# Ensuring order_date and delivery_date to be datetime
datetime_columns = ['order_date', 'delivery_date']
for col in datetime_columns:
    all_df[col] = pd.to_datetime(all_df[col])


# ============= Section: Sidebar =============
# Providing a date filter input (range).
with st.sidebar:
    st.image('streamlit/logo_dicoding_collection.png')
    min_date = all_df["order_date"].dt.date.min()
    max_date = all_df["order_date"].dt.date.max()
    start_date = min_date
    end_date = max_date
    val = st.date_input(
        label="Rentang waktu",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    # Workaround to prevent Streamlit from showing ValueError
    try:
        start_date, end_date = val
    except ValueError:
        st.error("You must pick both the start and the end date")
        st.stop() # Pausing the script's execution

# Filter df to only include rows within the specified date range.
main_df = all_df[(all_df['order_date'].dt.date >= start_date) & (all_df['order_date'].dt.date <= end_date)]
# Creating derivatives df
daily_order_df = create_daily_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
gender_df = create_gender_df(main_df)
age_df = create_age_df(main_df)
state_df = create_states_df(main_df)
rfm_df = create_rfm_df(main_df)   


# ============= Dashboard: Daily Orders =============
st.subheader("Daily Orders")
col_order, col_revenue = st.columns(2)
with col_order:
    total_orders = daily_order_df['order_count'].sum()
    st.metric("Total Orders", total_orders)
with col_revenue: 
    total_revenue = format_currency(daily_order_df['revenue'].sum(), "AUD", locale='es_CO')
    st.metric("Total Revenue", total_revenue)    

# x-axis -> month (%Y-%M); y-axis -> daily order count
fig, ax = plt.subplots(figsize=(12,5))
ax.plot(
    daily_order_df['order_date'],
    daily_order_df['order_count'],
    color='plum',
    marker='o'
)
ax.tick_params(axis='y', which='major', labelsize=12)
st.pyplot(fig)


# ============= Dashboard: Best & Worst Performing Products =============
st.write("") #Empty line
st.subheader("Best & Worst Performing Products")
fig, ax = plt.subplots(figsize=(12,5), nrows=1, ncols=2)
colors_1 = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
# The first subplot
sns.barplot(
    x='quantity_y',
    y='product_name',
    hue='product_name',
    data=sum_order_items_df.head(5),
    palette=colors_1,
    ax=ax[0]
)
ax[0].set_ylabel(None)
ax[0].set_xlabel(None)
ax[0].tick_params(axis='y', labelsize=12)
ax[0].set_title("Worst Performing Product (Bottom 5)", loc="center", fontsize=15)
# The second subplot
sns.barplot(
    x='quantity_y',
    y='product_name',
    hue='product_name',
    data=sum_order_items_df.sort_values(by='quantity_y', ascending=False).head(5),
    palette=colors_1,
    ax=ax[1]
)
ax[1].set_ylabel(None)
ax[1].set_xlabel(None)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].tick_params(axis='y', labelsize=12)
ax[1].set_title("Best Performing Product (Top 5)", loc="center", fontsize=15)
st.pyplot(fig)


# ============= Dashboard: Best & Worst Performing Products =============
st.write("") #Empty line
st.subheader("Customer Demographics")
colors_2 = ["#72BCD4", "#D3D3D3", "#D3D3D3"]
colors_3 = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
# The first & second plot
fig, ax = plt.subplots(figsize=(12,5), nrows=1, ncols=2)
sns.barplot(
    x='gender',
    y='customer_count',
    data=gender_df.sort_values(by='customer_count',ascending=False),
    hue='gender',
    palette=colors_2,
    ax=ax[0]
)
ax[0].set_ylabel(None)
ax[0].set_xlabel(None)
ax[0].tick_params(axis='y', labelsize=12)
ax[0].set_title("Number of Customer by Gender", loc="center", fontsize=15)
sns.barplot(
    x='age_group',
    y='customer_count',
    data=age_df,
    hue='age_group',
    palette=colors_2,
    ax=ax[1]
)
ax[1].set_ylabel(None)
ax[1].set_xlabel(None)
ax[1].tick_params(axis='y', labelsize=12)
ax[1].set_title("Number of Customer by Age", loc="center", fontsize=15)
st.pyplot(fig)
# The third plot
fig, ax = plt.subplots(figsize=(12,5))
sns.barplot(
    x='customer_count',
    y='state',
    data=state_df.sort_values(by='customer_count', ascending=False),
    hue='state',
    palette=colors_3,
    ax=ax
)
ax.set_ylabel(None)
ax.set_xlabel(None)
ax.tick_params(axis='y', labelsize=12)
ax.set_title("Number of Customer by States", loc="center", fontsize=15)
st.pyplot(fig)


# ============= Dashboard: Best Customer Based on RFM Parameters =============
st.write("")
st.subheader("Best Customer Based on RFM Parameters")
col_recency, col_frequency, col_monetary = st.columns(3)
colors_4 = ["#72BCD4"] * 5
with col_recency:
    avg_recency = round(rfm_df['recency'].mean(), 2)
    st.metric("Average Recency (days)", avg_recency)    
with col_frequency:
    avg_frequency = round(rfm_df['frequency'].mean(), 2)
    st.metric("Average Frequency", avg_frequency)
with col_monetary:
    avg_monetary = format_currency(rfm_df['monetary'].mean(), "AUD", locale='es_CO')
    st.metric("Average Monetary", avg_monetary)
fig, ax = plt.subplots(figsize=(12,5), nrows=1, ncols=3)
# The first plot
sns.barplot(
    x='customer_id',
    y='recency',
    data=rfm_df.sort_values(by='recency').head(5),
    hue='customer_id',
    palette=colors_4,
    legend=None,
    ax=ax[0]
)
ax[0].set_xlabel("customer_id")
ax[0].set_ylabel(None)
ax[0].tick_params(axis='y', labelsize=12)
ax[0].set_title("By Recency (days)", loc='center', fontsize=15)
# The second plot
sns.barplot(
    x='customer_id',
    y='frequency',
    data=rfm_df.sort_values(by='frequency', ascending=False).head(5),
    hue='customer_id',
    palette=colors_4,
    legend=None,
    ax=ax[1]
)
ax[1].set_xlabel("customer_id")
ax[1].set_ylabel(None)
ax[1].tick_params(axis='y', labelsize=12)
ax[1].set_title("By Frequency", loc='center', fontsize=15)
# The third plot
sns.barplot(
    x='customer_id',
    y='monetary',
    data=rfm_df.sort_values(by='monetary', ascending=False).head(5),
    hue='customer_id',
    palette=colors_4,
    legend=None,
    ax=ax[2]
)
ax[2].set_xlabel("customer_id")
ax[2].set_ylabel(None)
ax[2].tick_params(axis='y', labelsize=12)
ax[2].set_title("By Monetary", loc='center', fontsize=15)
st.pyplot(fig)

st.write("")
st.write("")
st.divider()
st.caption("Copyright (c) Dicoding x Artha 2024")

