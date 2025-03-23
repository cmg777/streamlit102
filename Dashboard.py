# Description: This script creates a Streamlit dashboard for exploratory data analysis (EDA) of Superstore sales data.
# The dashboard allows users to upload their own dataset or use the default Superstore dataset.
# Users can filter the data by date, region, state, and city to analyze sales patterns.
# The dashboard includes visualizations, time series analysis, hierarchical analysis, and data download options.

# ======= SUPERSTORE EDA DASHBOARD =======
# This Streamlit app performs exploratory data analysis on Superstore sales data
# with interactive filters and visualizations to identify sales patterns.

import streamlit as st
import plotly.express as px
import pandas as pd
import plotly.figure_factory as ff
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Configure page layout and title
st.set_page_config(page_title="Superstore EDA", page_icon=":bar_chart:", layout="wide")
st.title(" :bar_chart: Sample SuperStore EDA")

# ===== DATA LOADING SECTION =====
# Users can upload their own data or use the default dataset
fl = st.file_uploader(":file_folder: Upload a file", type=(["csv", "txt", "xlsx", "xls"]))
if fl is not None:
    filename = fl.name
    st.write(f"Analyzing: {filename}")
    df = pd.read_csv(filename, encoding="ISO-8859-1")
else:
    # Default dataset loads if no file is uploaded
    df = pd.read_csv("Superstore.csv", encoding="ISO-8859-1")

# ===== DATE FILTERING SECTION =====
# Create date range selector with two columns layout
col1, col2 = st.columns((2))

# Convert and extract date range from dataset
df["Order Date"] = pd.to_datetime(df["Order Date"])
startDate = pd.to_datetime(df["Order Date"]).min()
endDate = pd.to_datetime(df["Order Date"]).max()

# Date input widgets for time period selection
with col1:
    date1 = pd.to_datetime(st.date_input("Start Date", startDate))
with col2:
    date2 = pd.to_datetime(st.date_input("End Date", endDate))

# Filter dataset to selected date range
df = df[(df["Order Date"] >= date1) & (df["Order Date"] <= date2)].copy()

# ===== SIDEBAR FILTERS SECTION =====
# Hierarchical filtering: Region → State → City
st.sidebar.header("Choose your filter: ")

# Region filter - first level of hierarchy
region = st.sidebar.multiselect("Pick your Region", df["Region"].unique())
df2 = df[df["Region"].isin(region)] if region else df.copy()

# State filter - second level (depends on selected regions)
state = st.sidebar.multiselect("Pick the State", df2["State"].unique())
df3 = df2[df2["State"].isin(state)] if state else df2.copy()

# City filter - third level (depends on selected states)
city = st.sidebar.multiselect("Pick the City", df3["City"].unique())

# Apply all filters to create final filtered dataframe
# This logic handles all possible combinations of filter selections
if not region and not state and not city:
    filtered_df = df
elif not state and not city:
    filtered_df = df[df["Region"].isin(region)]
elif not region and not city:
    filtered_df = df[df["State"].isin(state)]
elif state and city:
    filtered_df = df3[df["State"].isin(state) & df3["City"].isin(city)]
elif region and city:
    filtered_df = df3[df["Region"].isin(region) & df3["City"].isin(city)]
elif region and state:
    filtered_df = df3[df["Region"].isin(region) & df3["State"].isin(state)]
elif city:
    filtered_df = df3[df3["City"].isin(city)]
else:
    filtered_df = df3[df3["Region"].isin(region) & df3["State"].isin(state) & df3["City"].isin(city)]

# ===== TOP VISUALIZATION SECTION =====
# Aggregate sales by category for visualization
category_df = filtered_df.groupby(by=["Category"], as_index=False)["Sales"].sum()

# Two-column layout for main visualizations
with col1:
    st.subheader("Category wise Sales")
    # Bar chart showing sales by category with formatted currency values
    fig = px.bar(category_df, x="Category", y="Sales", 
                 text=[f'${x:,.2f}' for x in category_df["Sales"]],
                 template="seaborn")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Region wise Sales")
    # Donut chart showing regional sales distribution
    fig = px.pie(filtered_df, values="Sales", names="Region", hole=0.5)
    fig.update_traces(text=filtered_df["Region"], textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

# ===== DATA VIEW SECTION =====
# Expandable data viewers with download options
cl1, cl2 = st.columns((2))

with cl1:
    with st.expander("Category_ViewData"):
        # Display category data with heat map styling for easy identification of patterns
        st.write(category_df.style.background_gradient(cmap="Blues"))
        csv = category_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Data", data=csv, file_name="Category.csv", 
                          mime="text/csv", help='Click here to download the data as a CSV file')

with cl2:
    with st.expander("Region_ViewData"):
        # Display region data with gradient styling
        region = filtered_df.groupby(by="Region", as_index=False)["Sales"].sum()
        st.write(region.style.background_gradient(cmap="Oranges"))
        csv = region.to_csv(index=False).encode('utf-8')
        st.download_button("Download Data", data=csv, file_name="Region.csv", 
                          mime="text/csv", help='Click here to download the data as a CSV file')

# ===== TIME SERIES ANALYSIS SECTION =====
# Create month-year period column for temporal analysis
filtered_df["month_year"] = filtered_df["Order Date"].dt.to_period("M")
st.subheader('Time Series Analysis')

# Group and visualize sales trends over time
linechart = pd.DataFrame(filtered_df.groupby(filtered_df["month_year"].dt.strftime("%Y : %b"))["Sales"].sum()).reset_index()
fig2 = px.line(linechart, x="month_year", y="Sales", labels={"Sales": "Amount"}, 
              height=500, width=1000, template="gridon")
st.plotly_chart(fig2, use_container_width=True)

with st.expander("View Data of TimeSeries:"):
    st.write(linechart.T.style.background_gradient(cmap="Blues"))
    csv = linechart.to_csv(index=False).encode("utf-8")
    st.download_button('Download Data', data=csv, file_name="TimeSeries.csv", mime='text/csv')

# ===== HIERARCHICAL ANALYSIS SECTION =====
st.subheader("Hierarchical view of Sales using TreeMap")
# TreeMap visualization showing hierarchical sales breakdown with drill-down capability
fig3 = px.treemap(filtered_df, path=["Region", "Category", "Sub-Category"], 
                 values="Sales", hover_data=["Sales"], color="Sub-Category")
fig3.update_layout(width=800, height=650)
st.plotly_chart(fig3, use_container_width=True)

# ===== SEGMENT AND CATEGORY ANALYSIS SECTION =====
chart1, chart2 = st.columns((2))

with chart1:
    st.subheader('Segment wise Sales')
    # Pie chart showing sales distribution by customer segment
    fig = px.pie(filtered_df, values="Sales", names="Segment", template="plotly_dark")
    fig.update_traces(text=filtered_df["Segment"], textposition="inside")
    st.plotly_chart(fig, use_container_width=True)

with chart2:
    st.subheader('Category wise Sales')
    # Pie chart showing sales distribution by product category
    fig = px.pie(filtered_df, values="Sales", names="Category", template="gridon")
    fig.update_traces(text=filtered_df["Category"], textposition="inside")
    st.plotly_chart(fig, use_container_width=True)

# ===== DETAILED SUBCATEGORY ANALYSIS SECTION =====
st.subheader(":point_right: Month wise Sub-Category Sales Summary")

with st.expander("Summary_Table"):
    # Display sample data to show available fields
    df_sample = df[0:5][["Region", "State", "City", "Category", "Sales", "Profit", "Quantity"]]
    fig = ff.create_table(df_sample, colorscale="Cividis")
    st.plotly_chart(fig, use_container_width=True)

    # Create pivot table for month-wise subcategory analysis
    st.markdown("Month wise sub-Category Table")
    filtered_df["month"] = filtered_df["Order Date"].dt.month_name()
    sub_category_Year = pd.pivot_table(data=filtered_df, values="Sales", index=["Sub-Category"], columns="month")
    st.write(sub_category_Year.style.background_gradient(cmap="Blues"))

# ===== SALES vs PROFIT ANALYSIS SECTION =====
# Scatter plot to visualize relationship between sales, profit, and order quantity
data1 = px.scatter(filtered_df, x="Sales", y="Profit", size="Quantity")
data1.update_layout(
    title={"text": "Relationship between Sales and Profits using Scatter Plot.", "font": {"size": 20}},
    xaxis={"title": {"text": "Sales", "font": {"size": 19}}},
    yaxis={"title": {"text": "Profit", "font": {"size": 19}}}
)
st.plotly_chart(data1, use_container_width=True)

# Data viewer for the filtered dataset
with st.expander("View Data"):
    st.write(filtered_df.iloc[:500, 1:20:2].style.background_gradient(cmap="Oranges"))

# ===== DATA DOWNLOAD SECTION =====
# Download option for the complete filtered dataset
csv = df.to_csv(index=False).encode('utf-8')
st.download_button('Download Data', data=csv, file_name="Data.csv", mime="text/csv")
