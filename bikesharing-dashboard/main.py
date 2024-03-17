'''
This is a project to create an interactive streamlit app to visualize
bike-sharing dataset analysis.
Est. 2024
@arthad
'''

import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

sns.set_style("dark")
st.header('Bike-Sharing Dashboard :bike:', divider="rainbow")

# ============= Helper Function (Creating Dataframes for viz from universal df) =============
def create_season_df(df):
  season_df = (df.groupby('season')['cnt']
                .sum()
                .sort_values(ascending=False)
                .reset_index()
  )
  return season_df

def create_weather_df(df):
  weather_df = (df.groupby('weathersit')['cnt']
                .sum()
                .sort_values(ascending=False)
                .reset_index()
  )
  return weather_df

def create_holiday_df(df):
  holiday_df = (df.groupby('holiday')['cnt']
                .sum()
                .sort_values(ascending=False)
                .reset_index()
  )
  return holiday_df

def create_workingday_df(df):
  workingday_df = (df.groupby('workingday')['cnt']
                .sum()
                .sort_values(ascending=False)
                .reset_index()
  )
  return workingday_df

def create_corr_df(df):
  kolom_numerik = ['temp', 'atemp', 'hum', 'windspeed', 'cnt']
  corr_df = df[kolom_numerik].corr()
  return corr_df


# ============= Data Import =============
# Memuat data penyewaan sepeda harian dari github
daily_df = pd.read_csv("Bike-sharing-dataset/day.csv")
# Memuat data penyewaan sepeda perjam dari github
hourly_df = pd.read_csv("Bike-sharing-dataset/hour.csv")
# Melakukan reset index karena data diimport dari file csv
daily_df.reset_index(inplace=True)
hourly_df.reset_index(inplace=True)
# Mengkonversi tipe data kolom dteday menjadi datetime
daily_df['dteday'] = pd.to_datetime(daily_df['dteday'])
hourly_df['dteday'] = pd.to_datetime(hourly_df['dteday'])


# ============= Value Mapping =============
season_mapping = {
    1: 'Semi',
    2: 'Panas',
    3: 'Gugur',
    4: 'Dingin'
}
weathersit_mapping = {
    1: 'Cerah',
    2: 'Mendung',
    3: 'Hujan Ringan',
    4: 'Badai Petir'
}
holiday_mapping = {
    0: 'Bukan Hari Libur',
    1: 'Hari Libur',
}
workingday_mapping = {
    0: 'Bukan Hari Kerja',
    1: 'Hari Kerja',
}
mnth_mapping = {
    1: 'Jan',
    2: 'Feb',
    3: 'Mar',
    4: 'Apr',
    5: 'Mei',
    6: 'Jun',
    7: 'Jul',
    8: 'Agu',
    9: 'Sep',
    10: 'Okt',
    11: 'Nov',
    12: 'Des'
}
yr_mapping = {
    0: 2011,
    1: 2012,
}
weekday_mapping = {
    0: 'Senin',
    1: 'Selasa',
    2: 'Rabu',
    3: 'Kamis',
    4: 'Jumat',
    5: 'Sabtu',
    6: 'Minggu'
}
daily_df['season'] = daily_df['season'].map(season_mapping)
daily_df['weathersit'] = daily_df['weathersit'].map(weathersit_mapping)
daily_df['holiday'] = daily_df['holiday'].map(holiday_mapping)
daily_df['workingday'] = daily_df['workingday'].map(workingday_mapping)
daily_df['mnth'] = daily_df['mnth'].map(mnth_mapping)
daily_df['weekday'] = daily_df['weekday'].map(weekday_mapping)
hourly_df['season'] = hourly_df['season'].map(season_mapping)
hourly_df['weathersit'] = hourly_df['weathersit'].map(weathersit_mapping)
hourly_df['holiday'] = hourly_df['holiday'].map(holiday_mapping)
hourly_df['workingday'] = hourly_df['workingday'].map(workingday_mapping)


# ============= Section: Sidebar =============
# Menyediakan sebuah filter rentang tanggal
with st.sidebar:
    st.image('logo_bikeshare.png')
    min_date = daily_df["dteday"].dt.date.min()
    max_date = daily_df["dteday"].dt.date.max()
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

daily_df = daily_df[(daily_df['dteday'].dt.date >= start_date) & (daily_df['dteday'].dt.date <= end_date)]
season_daily_df = create_season_df(daily_df)
weather_daily_df = create_weather_df(daily_df)
holiday_df = create_holiday_df(daily_df)
workingday_df = create_workingday_df(daily_df)
corr_df = create_corr_df(daily_df)


# ============= Dashboard: Daily Rent =============
st.subheader("Penyewaan Harian")
col_1, col_2, col_3, col_4 = st.columns(4)
with col_1:
    st.metric("Min", daily_df['cnt'].min())  
with col_2: 
    st.metric("Max", daily_df['cnt'].max())     
with col_3: 
    st.metric("Avg", round(daily_df['cnt'].mean()))   
with col_4: 
    st.metric("Total Orders", daily_df['cnt'].sum())
# Line chart untuk memvisualisasi jumlah penyewaan harian             
fig, ax = plt.subplots(figsize=(20,10))
ax.plot(
   daily_df['dteday'],
   daily_df['cnt'],
   color='plum',
   marker='.'
)
st.pyplot(fig)
# Stacked area chart untuk memvisualisasi komposisi jumlah penyewaan harian
fig, ax = plt.subplots(figsize=(20,10))
ax.stackplot(
   daily_df['dteday'],
   daily_df['registered'],
   daily_df['casual'],
   labels=['casual', 'registered']
)
ax.legend(loc='upper left')
st.pyplot(fig)
st.write("")
st.write("")


# ============= Dashboard: Correlation Matrix =============
# Membuat heatmap untuk memvisualisasi korelasi antar variabel numerik pada dataset
st.subheader("Korelasi Variabel Numerik")
fig, ax = plt.subplots(figsize=(20, 10))
sns.heatmap(
   corr_df,
   annot=True,
   ax=ax
)
st.pyplot(fig)
# Membuat 2 scatter plot untuk memvisualisasi korelasi variabel-variabel yang paling kuat dengan variabel cnt,
# yaitu antara variabel temp & atemp.
fig, axes= plt.subplots(figsize=(20, 10), nrows=1, ncols=2)
sns.regplot(
    x='temp',
    y='cnt',
    data=daily_df,
    ax=axes[0]
)
axes[0].set_title("Suhu")
sns.regplot(
    x='temp',
    y='cnt',
    data=daily_df,
    ax=axes[1]
)
axes[1].set_title("Suhu Semu")
st.pyplot(fig)
st.write("")
st.write("")


# ============= Dashboard: Jumlah Penyewaan Pada Setiap Musim/Cuaca =============
# Membuat barchart untuk memvisualisasi jumlah penyewaan pada setiap musim ataupun cuaca (Harian)
st.subheader("Jumlah Penyewaan Pada Setiap Musim/Cuaca")
colors_1 = ['#4FFB55', '#D3D3D3', '#D3D3D3', '#D3D3D3']
colors_2 = ['#4FFB55', '#D3D3D3', '#D3D3D3']
fig, axes = plt.subplots(figsize=(20,6), nrows=1, ncols=2)
# First chart: season
sns.barplot(
    x='season',
    y='cnt',
    hue='season',
    data=season_daily_df,
    palette=colors_1,
    ax=axes[0]
)
tallest_value = season_daily_df['cnt'].max()
axes[0].bar_label(
    axes[0].containers[0],
    labels=['{:,}'.format(tallest_value)],
    label_type='edge'
)
axes[0].margins(y=0.1)
axes[0].set_xlabel(None)
axes[0].set_ylabel(None)
axes[0].set_title("Musim")
# Second chart: weather
sns.barplot(
    x='weathersit',
    y='cnt',
    hue='weathersit',
    data=weather_daily_df,
    palette=colors_2,
    ax=axes[1]
)
tallest_value = weather_daily_df['cnt'].max()
axes[1].bar_label(
    axes[1].containers[0],
    labels=['{:,}'.format(tallest_value)],
    label_type='edge'
)
axes[1].margins(y=0.1)
axes[1].set_xlabel(None)
axes[1].set_ylabel(None)
axes[1].set_title("Cuaca")
st.pyplot(fig)
st.write("")
# Membuat pie chart untuk memvisualisasi jumlah penyewaan pada setiap musim ataupun cuaca (harian)
num_categories_1 = len(season_daily_df['cnt'])
num_categories_2 = len(weather_daily_df['cnt'])
explode_1 = [0] * num_categories_1
explode_2 = [0] * num_categories_2
if num_categories_1 > 1:
   explode_1[0] = 0.2
if num_categories_2 > 1:
   explode_2[0] = 0.2
fig, axes = plt.subplots(figsize=(20,6), nrows=1, ncols=2)
# First chart: season
axes[0].pie(
    x=season_daily_df['cnt'],
    labels=season_daily_df['season'],
    colors=sns.color_palette("pastel"),
    explode=explode_1,
    autopct='%.2f%%'
)
axes[0].set_xlabel(None)
axes[0].set_ylabel(None)
axes[0].set_title("Musim")
# Second chart: weather
axes[1].pie(
    x=weather_daily_df['cnt'],
    labels=weather_daily_df['weathersit'],
    colors=sns.color_palette("pastel"),
    explode=explode_2,
    autopct='%.2f%%'
)
axes[1].set_xlabel(None)
axes[1].set_ylabel(None)
axes[1].set_title("Cuaca")
st.pyplot(fig)
st.write("")
st.write("")


# ============= Dashboard: Jumlah Penyewaan Pada Setiap Hari Libur/Hari Kerja =============
# Membuat barchart untuk memvisualisasi jumlah penyewaan pada setiap hari libur/kerja
st.subheader("Jumlah Penyewaan Menurut Hari Libur/Hari Kerja")
colors_1 = ['#4FFB55', '#D3D3D3']
colors_2 = ['#4FFB55', '#D3D3D3']
holiday_df = create_holiday_df(daily_df)
workingday_df = create_workingday_df(daily_df)
fig, axes = plt.subplots(figsize=(20,6), nrows=1, ncols=2)
# First chart: holiday
sns.barplot(
    x='holiday',
    y='cnt',
    hue='holiday',
    data=holiday_df,
    palette=colors_1,
    ax=axes[0]
)
tallest_value = holiday_df['cnt'].max()
axes[0].bar_label(
    axes[0].containers[0],
    labels=['{:,}'.format(tallest_value)],
    label_type='edge'
)
axes[0].margins(y=0.1)
axes[0].set_xlabel(None)
axes[0].set_ylabel(None)
axes[0].set_title("Hari Libur")
# Second chart: workingday
sns.barplot(
    x='workingday',
    y='cnt',
    hue='workingday',
    data=workingday_df,
    palette=colors_2,
    ax=axes[1]
)
tallest_value = workingday_df['cnt'].max()
axes[1].bar_label(
    axes[1].containers[0],
    labels=['{:,}'.format(tallest_value)],
    label_type='edge'
)
axes[1].margins(y=0.1)
axes[1].set_xlabel(None)
axes[1].set_ylabel(None)
axes[1].set_title("Hari Kerja")
st.pyplot(fig)
st.write("")
# Membuat pie chart untuk memvisualisasi jumlah penyewaan pada setiap hari libur/hari kerja
num_categories = len(holiday_df['cnt'])
explode = [0] * num_categories
if num_categories > 1:
   explode[0] = 0.2
fig, axes = plt.subplots(figsize=(20,6), nrows=1, ncols=2)
# First chart: holiday
axes[0].pie(
    x=holiday_df['cnt'],
    labels=holiday_df['holiday'],
    colors=sns.color_palette("pastel"),
    explode=explode,
    autopct='%.2f%%'
)
axes[0].set_xlabel(None)
axes[0].set_ylabel(None)
axes[0].set_title("Hari Libur")
# Second chart: workingday
axes[1].pie(
    x=workingday_df['cnt'],
    labels=workingday_df['workingday'],
    colors=sns.color_palette("pastel"),
    explode=explode,
    autopct='%.2f%%'
)
axes[1].set_xlabel(None)
axes[1].set_ylabel(None)
axes[1].set_title("Hari Kerja")
st.pyplot(fig)
st.write("")
st.write("")
st.divider()
st.caption("Copyright (c) Dicoding x Artha 2024")
