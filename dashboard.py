import streamlit as st
import pandas as pd
import altair as alt
import json
# Import Gemini API client (replace with the actual Gemini SDK or HTTP client)
import google.generativeai as genai

# Conversion rate: 1 USD = 35 THB
USD_TO_THB = 35

def df_to_json(df, name_metrics):
    """
    Convert a DataFrame to JSON format.

    Args:
        df (pd.DataFrame): The DataFrame to convert.

    Returns:
        str: JSON string representation of the DataFrame.
    """
    return df.to_json(f"/Users/trungtran/Documents/VNS/MD/data/{name_metrics}.json",indent=4, date_format='iso')

# Load data
def load_data():
    df = pd.read_csv("sample_data_fishery_thailand.csv", delimiter=",")
    df['date'] = pd.to_datetime(df['date'])  # Ensure 'date' is in datetime format
    df['province'] = df['province'].astype('category')
    df['type'] = df['type'].astype('category')
    
    # Convert values from 1000 USD to THB
    df['total_value_product'] = df['total_value_product'] * 1000 * USD_TO_THB
    df['unit_value'] = df['unit_value'] * 1000 * USD_TO_THB
    return df

df = load_data()

# Streamlit page settings
st.set_page_config(layout="wide")
st.title("Thailand Fishery Dashboard")
st.write("This dashboard provides insights into fishery production, economic trends, and geospatial distribution.")

# --- Auto-Generate Insights ---
st.markdown("### Insights and Summary")


# Configure the API key (or use service account if running on GCP)
genai.configure(api_key="AIzaSyBZGtJP6DCh9PReRA8-fiJNTLKyVXvxjlc")

# Load Gemini model
model = genai.GenerativeModel("gemini-2.0-flash")

def generate_insights(filtered_df):
    """
    Generate insights and key takeaways using Google's Gemini model.

    Args:
        filtered_df (pd.DataFrame): The DataFrame containing filtered fishery data.

    Returns:
        str: A textual insight generated by Gemini.
    """
    summary = f"""
    The dataset contains {len(filtered_df)} records after applying filters. 
    The total production is {filtered_df['total_quant_of_product'].sum():,.2f} tonnes, 
    with a total value of {filtered_df['total_value_product'].sum():,.2f} THB. 
    The average unit value is {filtered_df['unit_value'].mean():,.2f} THB.
    """

    prompt = f"Based on the following summary, generate insights and key takeaways:\n\n{summary}"

    response = model.generate_content(prompt)

    return response.text.strip()
  # Adjust based on Gemini's response format

# --- Header with Filters ---
with st.container():
    st.markdown("### Filters")
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    # Date Range Filter
    with col1:
        start_date = st.date_input("Start Date", df['date'].min())
        end_date = st.date_input("End Date", df['date'].max())

    # Province Filter (List-Box)
    with col2:
        province = st.selectbox("Select Province", options=["All"] + list(df['province'].unique()))
        if province != "All":
            df = df[df['province'] == province]

    # Type Filter (List-Box)
    with col3:
        type_filter = st.selectbox("Select Type", options=["All"] + list(df['type'].unique()))
        if type_filter != "All":
            df = df[df['type'] == type_filter]

    # Pieaces Filter (List-Box)
    with col4:
        pieace_filter = st.selectbox("Select Pieace", options=["All"] + list(df['pieaces'].unique()))
        if pieace_filter != "All":
            df = df[df['pieaces'] == pieace_filter]

# Apply Date Range Filter
filtered_df = df[(df['date'] >= pd.to_datetime(start_date)) & 
                 (df['date'] <= pd.to_datetime(end_date))]

# Display insights
if not filtered_df.empty:
    try:
        insights = generate_insights(filtered_df)
        st.write(insights)
    except Exception as e:
        st.write(f"Error generating insights: {e}")
else:
    st.write("No data available for the selected filters.")

# --- Layout: Geomap on the left, charts on the right ---
col1, col2 = st.columns([1, 3])

# LEFT: Geomap
with col1:
    st.markdown("### Geospatial View")
    st.components.v1.html(
        """
        <div style="min-height:400px" id="datawrapper-vis-FPm38"><script type="text/javascript" defer src="https://datawrapper.dwcdn.net/FPm38/embed.js" charset="utf-8" data-target="#datawrapper-vis-FPm38"></script><noscript><img src="https://datawrapper.dwcdn.net/FPm38/full.png" alt="" /></noscript></div>
        """,
        height=100000
    )

# RIGHT: Charts and Metrics
with col2:
    # Key Metrics
    st.markdown("### Key Metrics")
    total_production = filtered_df['total_quant_of_product'].sum()
    total_value = filtered_df['total_value_product'].sum()
    average_unit_value = filtered_df['unit_value'].mean()
    total_employment = filtered_df['total_emp'].sum()
    

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Production (Tonnes)", f"{total_production:,.2f}")
    col2.metric("Total Value (THB)", f"{total_value:,.2f}")
    col3.metric("Average Unit Value (THB)", f"{average_unit_value:,.2f}")
    col4.metric("Total Employment", f"{total_employment:,.0f}")

    # Production by Type (Pie Chart)
    st.markdown("### Production by Type")
    production_by_type = filtered_df.groupby('type')['total_quant_of_product'].sum().reset_index()
    pie_chart_production = alt.Chart(production_by_type).mark_arc().encode(
        theta=alt.Theta(field="total_quant_of_product", type="quantitative"),
        color=alt.Color(field="type", type="nominal"),
        tooltip=["type", alt.Tooltip("total_quant_of_product", format=",.2f", title="Production (Tonnes)")]
    ).properties(
        title="Total Production by Fishery Type"
    )
    st.altair_chart(pie_chart_production, use_container_width=True)

    # Value by Type (Pie Chart)
    st.markdown("### Value by Type")
    value_by_type = filtered_df.groupby('type')['total_value_product'].sum().reset_index()
    pie_chart_value = alt.Chart(value_by_type).mark_arc().encode(
        theta=alt.Theta(field="total_value_product", type="quantitative"),
        color=alt.Color(field="type", type="nominal"),
        tooltip=["type", alt.Tooltip("total_value_product", format=",.2f", title="Value (THB)")]
    ).properties(
        title="Total Value by Fishery Type"
    )
    st.altair_chart(pie_chart_value, use_container_width=True)

    # Production Over Time (Line Chart)
    st.markdown("### Production Over Time")
    production_over_time = filtered_df.groupby('date')['total_quant_of_product'].sum().reset_index()
    line_chart_production = alt.Chart(production_over_time).mark_line().encode(
        x=alt.X('date:T', title='Date'),
        y=alt.Y('total_quant_of_product:Q', title='Production (Tonnes)'),
        tooltip=['date:T', alt.Tooltip('total_quant_of_product', format=",.2f", title="Production (Tonnes)")]
    ).properties(
        title="Total Production Over Time"
    )
    st.altair_chart(line_chart_production, use_container_width=True)

    # Value Over Time (Line Chart)
    st.markdown("### Value Over Time")
    value_over_time = filtered_df.groupby('date')['total_value_product'].sum().reset_index()
    line_chart_value = alt.Chart(value_over_time).mark_line().encode(
        x=alt.X('date:T', title='Date'),
        y=alt.Y('total_value_product:Q', title='Value (THB)'),
        tooltip=['date:T', alt.Tooltip('total_value_product', format=",.2f", title="Value (THB)")]
    ).properties(
        title="Total Value Over Time"
    )
    st.altair_chart(line_chart_value, use_container_width=True)

    # Average Unit Value Over Time of Catfishes (Line Chart)
    st.markdown("### Average Unit Value Over Time of Catfishes")
    unit_value_over_time = filtered_df[filtered_df['pieaces'] == 'Catfishes'].groupby('date')['unit_value'].mean().reset_index()
    line_chart_unit_value = alt.Chart(unit_value_over_time).mark_line().encode(
        x=alt.X('date:T', title='Date'),
        y=alt.Y('unit_value:Q', title='Average Unit Value (THB)'),
        tooltip=['date:T', alt.Tooltip('unit_value', format=",.2f", title="Unit Value (THB)")]
    ).properties(
        title="Average Unit Value Over Time of Catfishes"
    )
    st.altair_chart(line_chart_unit_value, use_container_width=True)

    # Top Provinces by Production (Bar Chart)
    st.markdown("### Top Provinces by Production")
    top_production_provinces = filtered_df.groupby('province')['total_quant_of_product'].sum().sort_values(ascending=False).reset_index().head(5)
    bar_chart_production = alt.Chart(top_production_provinces).mark_bar().encode(
        x=alt.X('total_quant_of_product:Q', title='Production (Tonnes)'),
        y=alt.Y('province:N', sort='-x', title='Province'),
        tooltip=['province', alt.Tooltip('total_quant_of_product', format=",.2f", title="Production (Tonnes)")]
    ).properties(
        title="Top 5 Provinces by Production"
    )
    st.altair_chart(bar_chart_production, use_container_width=True)

    # Top Provinces by Value (Bar Chart)
    st.markdown("### Top Provinces by Value")
    top_value_provinces = filtered_df.groupby('province')['total_value_product'].sum().sort_values(ascending=False).reset_index().head(5)
    bar_chart_value = alt.Chart(top_value_provinces).mark_bar().encode(
        x=alt.X('total_value_product:Q', title='Value (THB)'),
        y=alt.Y('province:N', sort='-x', title='Province'),
        tooltip=['province', alt.Tooltip('total_value_product', format=",.2f", title="Value (THB)")]
    ).properties(
        title="Top 5 Provinces by Value"
    )
    st.altair_chart(bar_chart_value, use_container_width=True)

    # Monthly Comparison of Top 3 Pieaces
    st.markdown("### Monthly Comparison of Top 3 Pieaces")
    top_3_pieaces = filtered_df.groupby('pieaces')['total_quant_of_product'].sum().nlargest(3).index.tolist()
    filtered_df['month'] = filtered_df['date'].dt.to_period('M')  # Extract month-year for grouping
    monthly_pieaces = filtered_df[filtered_df['pieaces'].isin(top_3_pieaces)].copy().groupby(['month', 'pieaces'])['total_quant_of_product'].sum().reset_index()
    monthly_pieaces['month'] = monthly_pieaces['month'].dt.to_timestamp()  # Convert period to timestamp for Altair

    # Create a line chart for monthly comparison
    monthly_pieaces_chart = alt.Chart(monthly_pieaces).mark_line(point=True).encode(
        x=alt.X('month:T', title='Month'),
        y=alt.Y('total_quant_of_product:Q', title='Total Production (Tonnes)'),
        color=alt.Color('pieaces:N', title='Pieaces'),
        tooltip=['month:T', 'pieaces:N', alt.Tooltip('total_quant_of_product:Q', format=",.2f", title="Production (Tonnes)")]
    ).properties(
        title="Monthly Comparison of Top 3 Pieaces"
    )

    st.altair_chart(monthly_pieaces_chart, use_container_width=True)
    
    # Monthly Comparison of Top 3 Provinces
    st.markdown("### Monthly Comparison of Top 3 Provinces")
    top_3_provinces = filtered_df.groupby('province')['total_quant_of_product'].sum().nlargest(3).index.tolist()
    filtered_df['month'] = filtered_df['date'].dt.to_period('M')  # Extract month-year for grouping
    monthly_provinces = filtered_df[filtered_df['province'].isin(top_3_provinces)].copy().groupby(['month', 'province'])['total_quant_of_product'].sum().reset_index()
    monthly_provinces['month'] = monthly_provinces['month'].dt.to_timestamp()  # Convert period to timestamp for Altair

    # Create a line chart for monthly comparison
    monthly_provinces_chart = alt.Chart(monthly_provinces).mark_line(point=True).encode(
        x=alt.X('month:T', title='Month'),
        y=alt.Y('total_quant_of_product:Q', title='Total Production (Tonnes)'),
        color=alt.Color('province:N', title='Province'),
        tooltip=['month:T', 'province:N', alt.Tooltip('total_quant_of_product:Q', format=",.2f", title="Production (Tonnes)")]
    ).properties(
        title="Monthly Comparison of Top 3 Provinces"
    )

    st.altair_chart(monthly_provinces_chart, use_container_width=True)

    # Export and Import Value Over Time (Line Chart)
    st.markdown("### Export and Import Value Over Time")
    st.write("This chart shows the trends of export and import values over time.")

    # Group data by date for export and import values
    export_import_over_time = filtered_df.groupby('date')[['export_value', 'import_value']].sum().reset_index()

    print(export_import_over_time)
    
    # Create a line chart for export and import values
    export_import_chart = alt.Chart(export_import_over_time).transform_fold(
        ['export_value', 'import_value'],  # Columns to fold
        as_=['Type', 'Value']  # Rename folded columns
    ).mark_line(point=True).encode(
        x=alt.X('date:T', title='Date'),
        y=alt.Y('Value:Q', title='Value (THB)'),
        color=alt.Color('Type:N', title='Type', scale=alt.Scale(scheme='set1')),
        tooltip=['date:T', 'Type:N', alt.Tooltip('Value:Q', format=",.2f", title="Value (THB)")]
    ).properties(
        title="Export and Import Value Over Time"
    )

    st.altair_chart(export_import_chart, use_container_width=True)

    # Net Trade Value Over Time (Line Chart)
    st.markdown("### Net Trade Value Over Time")
    st.write("This chart shows the net trade value (export - import) over time.")

    # Group data by date for net trade value
    net_trade_over_time = filtered_df.groupby('date')['net_trade_value'].sum().reset_index()

    print(net_trade_over_time)
    
    # Create a line chart for net trade value
    net_trade_chart = alt.Chart(net_trade_over_time).mark_line(point=True).encode(
        x=alt.X('date:T', title='Date'),
        y=alt.Y('net_trade_value:Q', title='Net Trade Value (THB)'),
        tooltip=['date:T', alt.Tooltip('net_trade_value:Q', format=",.2f", title="Net Trade Value (THB)")]
    ).properties(
        title="Net Trade Value Over Time"
    )

    st.altair_chart(net_trade_chart, use_container_width=True)

    # Top Provinces by Net Trade Value (Bar Chart)
    st.markdown("### Top Provinces by Net Trade Value")
    st.write("This bar chart shows the top provinces by net trade value.")

    # Group data by province for net trade value
    top_net_trade_provinces = filtered_df.groupby('province')['net_trade_value'].sum().sort_values(ascending=False).reset_index().head(5)

    # Create a bar chart for top provinces by net trade value
    top_net_trade_chart = alt.Chart(top_net_trade_provinces).mark_bar().encode(
        x=alt.X('net_trade_value:Q', title='Net Trade Value (THB)'),
        y=alt.Y('province:N', sort='-x', title='Province'),
        color=alt.Color('province:N', title='Province', scale=alt.Scale(scheme='set2')),
        tooltip=['province', alt.Tooltip('net_trade_value:Q', format=",.2f", title="Net Trade Value (THB)")]
    ).properties(
        title="Top 5 Provinces by Net Trade Value"
    )

    st.altair_chart(top_net_trade_chart, use_container_width=True)

# Function to export chart data to JSON
def export_chart_to_json(data, chart_name, chart_type, number_chart):
    """
    Export chart data to a JSON file in the specified format.

    Args:
        data (list): List of dictionaries containing chart data.
        chart_name (str): Name of the chart.
        file_path (str): Path to save the JSON file.
    """
    # Convert Timestamp objects to strings
    
    PATH_JSON = f"/Users/trungtran/Documents/VNS/MD/data/metrics_data/FISHERY_{chart_type}_{number_chart}.json"
    
    data_dict = data.to_dict(orient="records")
    
    for record in data_dict:
        for key, value in record.items():
            if isinstance(value, pd.Timestamp):
                record[key] = value.isoformat()  # Convert to ISO 8601 string

    json_data = {
        "value": data_dict,
        "chart_name": chart_name
    }
    with open(PATH_JSON, "w") as json_file:
        json.dump(json_data, json_file, indent=4)
    print(f"Chart data exported to {PATH_JSON}")
    
def export_metrics_to_json(data, chart_name, number_chart):
    """
    Export chart data to a JSON file in the specified format.

    Args:
        data (list): List of dictionaries containing chart data.
        chart_name (str): Name of the chart.
        file_path (str): Path to save the JSON file.
    """
    
    PATH_JSON = f"/Users/trungtran/Documents/VNS/MD/data/metrics_data/FISHERY_BIGNUMBER_{number_chart}.json"

    json_data = {
        "value": data,
        "chart_name": chart_name
    }
    with open(PATH_JSON, "w") as json_file:
        json.dump(json_data, json_file, indent=4)
    print(f"Chart data exported to {PATH_JSON}")

SCENARIO = "FISHERY"
CHART_MAPPING = {
    "production_by_type": {"Chart": "Production by Type", "Type": "PIECHART", "Number": "1"},
    "value_by_type": {"Chart": "Value by Type", "Type": "PIECHART", "Number": "2"},
    "production_over_time": {"Chart": "Production Over Time", "Type": "LINECHART", "Number": "1"},
    "value_over_time": {"Chart": "Value Over Time", "Type": "LINECHART", "Number": "2"},
    "average_unit_value_over_time": {"Chart": "Average Unit Value Over Time of Catfishes", "Type": "LINECHART", "Number": "3"},
    "top_production_provinces": {"Chart": "Top Provinces by Production", "Type": "BARCHART", "Number": "1"},
    "top_value_provinces": {"Chart": "Top Provinces by Value", "Type": "BARCHART", "Number": "2"},
    "monthly_pieaces": {"Chart": "Monthly Comparison of Top 3 Pieaces", "Type": "LINECHART", "Number": "4"},
    "monthly_provinces": {"Chart": "Monthly Comparison of Top 3 Provinces", "Type": "LINECHART", "Number": "5"},
    "export_import_over_time": {"Chart": "Export and Import Value Over Time", "Type": "LINECHART", "Number": "6"},
    "net_trade_over_time": {"Chart": "Net Trade Value Over Time", "Type": "LINECHART", "Number": "7"},
    "top_net_trade_provinces": {"Chart": "Top Provinces by Net Trade Value", "Type": "BARCHART", "Number": "3"},
}

METRICS_MAPPING = {
    "total_production": {"Chart": "Total Production", "Type": "BIGNUMBER", "Number": "1"},
    "total_value": {"Chart": "Total Value", "Type": "BIGNUMBER", "Number": "2"},
    "average_unit_value": {"Chart": "Average Unit Value", "Type": "BIGNUMBER", "Number": "3"},
    "total_employment": {"Chart": "Total Employment", "Type": "BIGNUMBER", "Number": "4"},
}


# export_chart_to_json(
#     data=production_by_type,
#     chart_name=CHART_MAPPING["production_by_type"]["Chart"],
#     chart_type=CHART_MAPPING["production_by_type"]["Type"],
#     number_chart=CHART_MAPPING["production_by_type"]["Number"]
# )

# export_chart_to_json(
#     data=value_by_type,
#     chart_name=CHART_MAPPING["value_by_type"]["Chart"],
#     chart_type=CHART_MAPPING["value_by_type"]["Type"],
#     number_chart=CHART_MAPPING["value_by_type"]["Number"]
# )

# export_chart_to_json(
#     data=production_over_time,
#     chart_name=CHART_MAPPING["production_over_time"]["Chart"],
#     chart_type=CHART_MAPPING["production_over_time"]["Type"],
#     number_chart=CHART_MAPPING["production_over_time"]["Number"]
# )

# export_chart_to_json(
#     data=value_over_time,
#     chart_name=CHART_MAPPING["value_over_time"]["Chart"],
#     chart_type=CHART_MAPPING["value_over_time"]["Type"],
#     number_chart=CHART_MAPPING["value_over_time"]["Number"]
# )

# export_chart_to_json(
#     data=unit_value_over_time,
#     chart_name=CHART_MAPPING["average_unit_value_over_time"]["Chart"],
#     chart_type=CHART_MAPPING["average_unit_value_over_time"]["Type"],
#     number_chart=CHART_MAPPING["average_unit_value_over_time"]["Number"]
# )
# export_chart_to_json(
#     data=top_production_provinces,
#     chart_name=CHART_MAPPING["top_production_provinces"]["Chart"],
#     chart_type=CHART_MAPPING["top_production_provinces"]["Type"],
#     number_chart=CHART_MAPPING["top_production_provinces"]["Number"]
# )

# export_chart_to_json(
#     data=top_value_provinces,
#     chart_name=CHART_MAPPING["top_value_provinces"]["Chart"],
#     chart_type=CHART_MAPPING["top_value_provinces"]["Type"],
#     number_chart=CHART_MAPPING["top_value_provinces"]["Number"]
# )

# export_chart_to_json(
#     data=monthly_pieaces,
#     chart_name=CHART_MAPPING["monthly_pieaces"]["Chart"],
#     chart_type=CHART_MAPPING["monthly_pieaces"]["Type"],
#     number_chart=CHART_MAPPING["monthly_pieaces"]["Number"]
# )

# export_chart_to_json(
#     data=monthly_provinces,
#     chart_name=CHART_MAPPING["monthly_provinces"]["Chart"],
#     chart_type=CHART_MAPPING["monthly_provinces"]["Type"],
#     number_chart=CHART_MAPPING["monthly_provinces"]["Number"]
# )

# export_chart_to_json(
#     data=export_import_over_time,
#     chart_name=CHART_MAPPING["export_import_over_time"]["Chart"],
#     chart_type=CHART_MAPPING["export_import_over_time"]["Type"],
#     number_chart=CHART_MAPPING["export_import_over_time"]["Number"]
# )

# export_chart_to_json(
#     data=net_trade_over_time,
#     chart_name=CHART_MAPPING["net_trade_over_time"]["Chart"],
#     chart_type=CHART_MAPPING["net_trade_over_time"]["Type"],
#     number_chart=CHART_MAPPING["net_trade_over_time"]["Number"]
# )

# export_chart_to_json(
#     data=top_net_trade_provinces,
#     chart_name=CHART_MAPPING["top_net_trade_provinces"]["Chart"],
#     chart_type=CHART_MAPPING["top_net_trade_provinces"]["Type"],
#     number_chart=CHART_MAPPING["top_net_trade_provinces"]["Number"]
# )
# # Export metrics to JSON

# export_metrics_to_json(
#     data=total_production,
#     chart_name=METRICS_MAPPING["total_production"]["Chart"],
#     number_chart=METRICS_MAPPING["total_production"]["Number"],
# )

# export_metrics_to_json(
#     data=total_value,
#     chart_name=METRICS_MAPPING["total_value"]["Chart"],
#     number_chart=METRICS_MAPPING["total_value"]["Number"],
# )

# export_metrics_to_json(
#     data=average_unit_value,
#     chart_name=METRICS_MAPPING["average_unit_value"]["Chart"],
#     number_chart=METRICS_MAPPING["average_unit_value"]["Number"],
# )

# export_metrics_to_json(
#     data=total_employment,
#     chart_name=METRICS_MAPPING["total_employment"]["Chart"],
#     number_chart=METRICS_MAPPING["total_employment"]["Number"],
# )

# Export geos map
geomaps_df = df.groupby('province').agg({'total_quant_of_product': 'sum'}).reset_index()
geomaps_df['total_quant_of_product'] = geomaps_df['total_quant_of_product'].astype(float)
geomaps_df['total_quant_of_product'] = geomaps_df['total_quant_of_product'].apply(lambda x: "{:,.2f}".format(x))

# export_chart_to_json(
#     data=geomaps_df,
#     chart_name="Total Production by Province",
#     chart_type="GEOMAP",
#     number_chart="1"
# )
