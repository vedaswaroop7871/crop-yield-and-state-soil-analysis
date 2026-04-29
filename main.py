import pandas as pd
import streamlit as st
import plotly.express as px

# Load Data
df = pd.read_csv('crop_yield.csv')

st.title("Hello , welcome to the Crop Yield Analysis App! Let's start by exploring the data.")
st.title("the original dataset:")

from st_aggrid import AgGrid, GridOptionsBuilder

st.header("📊 Interactive Data Explorer")

# 1. Setup the Grid Options
gb = GridOptionsBuilder.from_dataframe(df)

# 2. This enables the 'Three Dots' (Filter & Sort) for every column
gb.configure_default_column(
    filterable=True, 
    sortable=True, 
    editable=False,
    groupable=True
)

# 3. This ensures all rows are "selected" and interactive
gb.configure_selection(selection_mode="multiple", use_checkbox=True)

# 4. Build the options and display
gridOptions = gb.build()

# The 'UpdateMode' ensures that if you filter in the table, 
# you can use that filtered data for other things.
response = AgGrid(
    df, 
    gridOptions=gridOptions,
    height=500, 
    width='100%',
    theme='alpine', # Professional 'Excel' look
    enable_enterprise_modules=False
)

# If you want your CHARTS to update based on the 'Three Dots' filters:
filtered_data = pd.DataFrame(response['data'])


# Method: Fill missing Production based on the average of that specific Crop
st.title("### Data Summary")
st.dataframe(df.describe())

st.title("checking for missing values:")
st.write(df.isnull().sum())
import io

st.title("### DataFrame Information")
buffer = io.StringIO()
df.info(buf=buffer)
s = buffer.getvalue()
st.text(s)

st.write(f"**Shape of the dataset:** {df.shape}")

st.title("Step 2: Exploratory Data Analysis (EDA)")

# 1. Correlation Matrix (Heatmap)
st.subheader("How variables relate to each other")
numeric_df = df.select_dtypes(include=['float64', 'int64'])
corr = numeric_df.corr()
fig_corr = px.imshow(corr, text_auto=True, aspect="auto", 
                     color_continuous_scale='Viridis',
                     title="Correlation Heatmap")
st.plotly_chart(fig_corr)

# 2. Yield vs Fertilizer (Interactive Scatter)
st.subheader("Fertilizer vs Yield Impact")
# Let's filter for one crop to make it readable
crop_list = df['crop'].unique()
selected_crop = st.selectbox("Pick a crop to visualize:", crop_list)
filtered_df = df[df['crop'] == selected_crop]
st.subheader("Fertilizer vs Yield Impact")

# Using the columns we KNOW you have
fig_scatter = px.scatter(filtered_df, 
                         x="fertilizer", # Changed from Annual_Rainfall
                         y="yield", 
                         color="season", 
                         size="area",
                         hover_data=['pesticide', 'state'],
                         title=f"Fertilizer usage vs Yield for {selected_crop}",
                         template="plotly_white")
st.plotly_chart(fig_scatter)


st.header("Visual Summaries for Presentation")

# Pie Chart: Top 5 Crops by Total Production
st.subheader("📊 Production Distribution by Crop")

# 1. Aggregate the data
crop_production = df.groupby('crop')['production'].sum().reset_index()
top_5_crops = crop_production.sort_values(by='production', ascending=False).head(5)

# 2. Create the Plotly Pie Chart
fig_pie = px.pie(top_5_crops, 
                 values='production', 
                 names='crop', 
                 title='Top 5 Crops Contributing to Total Production',
                 hole=0.4, # This makes it a "Donut" chart, which looks more modern
                 color_discrete_sequence=px.colors.qualitative.Pastel)
fig_pie.update_traces(textposition='inside', textinfo='percent+label')

st.plotly_chart(fig_pie)


# Bar Graph: Average Yield per State
st.subheader("📈 Top 10 States by Average Yield Efficiency")

# 1. Aggregate average yield per state
state_yield = df.groupby('state')['yield'].mean().reset_index()
top_10_states = state_yield.sort_values(by='yield', ascending=False).head(10)

# 2. Create the Plotly Bar Chart
fig_bar = px.bar(top_10_states, 
                 x='state', 
                 y='yield',
                 text_auto='.2s', # Shows the value on top of the bar
                 title='Top 10 States with Highest Average Yield',
                 color='yield', # This creates a gradient color effect
                 color_continuous_scale='Greens')

st.plotly_chart(fig_bar)


st.header(" Relative Efficiency Analysis")

# 1. Apply Min-Max Normalization per Crop group
# This ensures each crop has its own 0-to-1 scale
df['relative_yield'] = df.groupby('crop')['yield'].transform(
    lambda x: (x - x.min()) / (x.max() - x.min()) if (x.max() - x.min()) != 0 else 0
)

st.write("### Normalized Data Preview")
st.write("Now, every crop's 'Best' yield is 1.0 and its 'Worst' is 0.0.")
st.dataframe(df[['state', 'crop', 'yield', 'relative_yield']].head(10))

# 2. Visualizing the 'Fair' Comparison
st.subheader("Top States by Relative Yield Efficiency")
st.write("This chart shows which states are reaching the maximum potential for their selected crops.")

# Average of the normalized scores
state_efficiency = df.groupby('state')['relative_yield'].mean().reset_index()

fig_norm = px.bar(state_efficiency.sort_values('relative_yield', ascending=False),
    x='relative_yield', 
    y='state', 
    orientation='h',
    title="Overall State Efficiency (Normalized 0-1)",
    color='relative_yield',
    color_continuous_scale='Viridis')

st.plotly_chart(fig_norm, use_container_width=True)


year_max=df['year'].max()
year_min=df['year'].min()
st.write(f"year range is {year_max} -{year_min} years")



#ritesh
st.header("Time-Series Analysis (1997 - 2020)")

# 1. Prepare the data: Filter years and Group by Year
# We ensure we are only looking at the requested range
df_years = df[(df['year'] >= 1997) & (df['year'] <= 2020)]
yearly_summary = df_years.groupby('year').sum().reset_index()

# --- Visual 1: Crop Production Trend ---
st.subheader("1. Total Crop Production Over the Years")

fig_prod = px.line(yearly_summary, 
    x='year', 
                   y='production', 
                   title='Total Production Trend (1997-2020)',
                   markers=True, # Adds dots on each year
                   line_shape='spline', # Makes the line smooth/curvy
                   render_mode='svg')

# Add a range slider for a "Pro" look
fig_prod.update_xaxes(rangeslider_visible=True)
fig_prod.update_traces(line_color='#2ca02c') # Green for production

st.plotly_chart(fig_prod)

# --- Visual 2: Fertilizer and Pesticide Usage ---
st.subheader("2. Fertilizer & Pesticide Usage Trends")

# We use 'melt' to put Fertilizer and Pesticide in the same chart for comparison
usage_data = yearly_summary.melt(id_vars='year', 
                                 value_vars=['fertilizer', 'pesticide'],
                                 var_name='Input Type', 
                                 value_name='Usage Amount')

fig_usage = px.line(usage_data, 
                    x='year', 
                    y='Usage Amount', 
                    color='Input Type',
                    title='Comparison: Fertilizer vs Pesticide Use',
                    markers=True,
                    color_discrete_map={
                        "fertilizer": "#ff7f0e", # Orange
                        "pesticide": "#d62728"   # Red
                    })

st.plotly_chart(fig_usage)

df['Calculated_Yield'] = df['production'] / df['area']
st.dataframe(df)
st.write("Calculated Yield (production/area) added to the dataset for outlier analysis.")

st.subheader("Identifying Yield Outliers by Season")

fig_box = px.box(df, 
                 x="season", 
                 y="Calculated_Yield", 
                 color="season",
                 title="Yield Distribution across Seasons",
                 points="outliers") # This highlights the weird data points

st.plotly_chart(fig_box)


# STATE_SOIL_DATA
soil_df = pd.read_csv('state_soil_data.csv')
soil_df.columns = soil_df.columns.str.lower().str.strip()
st.title("Lets also analyze the soil data to see if it has any impact on yield.")
st.title("the original dataset:")

from st_aggrid import AgGrid, GridOptionsBuilder

st.header("🧪 State Soil Composition Database")

# 1. Setup the Grid Options specifically for soil_df
gb_soil = GridOptionsBuilder.from_dataframe(soil_df)

# 2. Enable the 'Three Dots' (Filter & Sort) for every soil column (N, P, K, pH)
gb_soil.configure_default_column(
    filterable=True, 
    sortable=True, 
    groupable=True
)

# 3. Optional: Make the pH column specific (e.g., filter by number ranges)
gb_soil.configure_column("ph", type=["numericColumn","numberColumnFilter"])

# 4. Build and Display
gridOptions_soil = gb_soil.build()

response_soil = AgGrid(
    soil_df, 
    gridOptions=gridOptions_soil,
    height=400, 
    theme='balham', # 'balham' is a slightly tighter, more professional Excel look
    enable_enterprise_modules=False
)


st.title("### Data Summary")
st.dataframe(soil_df.describe())

st.title("checking for missing values:")
st.write(soil_df.isnull().sum())
import io

st.title("### DataFrame Information")
buffer = io.StringIO()
soil_df.info(buf=buffer)
s = buffer.getvalue()
st.text(s)

st.write(f"**Shape of the dataset:** {soil_df.shape}")






state_soil = soil_df.groupby('state')[['n', 'p', 'k','ph']].mean().reset_index()
merged_df = pd.merge(df, state_soil, on='state', how='left')
print(state_soil)
st.subheader("State-wise Nutrient Profile (N-P-K)")
fig_soil_heat = px.imshow(state_soil.set_index('state'), #to create heatmap
                          text_auto=True, 
                          color_continuous_scale='YlGn',
                          height=800,
                          title="Average Nitrogen, Phosphorus, and Potassium by State")
                          
st.plotly_chart(fig_soil_heat, use_container_width=True)



st.subheader("Soil pH Distribution by Category")
# 1. Create a category column for better EDA
# Acidic: < 6.5, Neutral: 6.5 to 7.5, Alkaline: > 7.5
def categorize_ph(ph):
    if ph < 6.6: return "Acidic"
    elif 6.5 <= ph <= 7.5: return "Neutral"
    else: return "Alkaline"

soil_df['ph_category'] = soil_df['ph'].apply(categorize_ph)

# 2. Plot with color assigned to the category
fig_ph = px.histogram(soil_df, 
                      x="ph", 
                      color="ph_category", # This gives different colors
                      nbins=20, 
                      histnorm='percent',
                      title="Distribution of Soil pH Levels",
                      # We can manually set the colors: Red for Acid, Green for Neutral, Blue for Alkaline
                      color_discrete_map={
                          "Acidic": "#e74c3c", 
                          "Neutral": "#2ecc71", 
                          "Alkaline": "#3498db"
                      },
                      category_orders={"ph_category": ["Acidic", "Neutral", "Alkaline"]})

# Add a line for "Neutral" pH (7.0)
fig_ph.add_vline(x=7.0, line_dash="dash", line_color="black", annotation_text="Ideal Neutral")

st.plotly_chart(fig_ph, use_container_width=True)


st.header("🧪 Crop-Soil Dependency Analysis")

# Group by crop to see the average soil nutrients they grow in
crop_soil_deps = merged_df.groupby('crop')[['n', 'p', 'k']].mean().reset_index()

# Melt the data for a grouped bar chart
melted_deps = crop_soil_deps.melt(id_vars='crop', var_name='Nutrient', value_name='Average_Soil_Level')

fig_deps = px.bar(melted_deps, 
                  x='crop', 
                  y='Average_Soil_Level', 
                  color='Nutrient',
                  barmode='group',
                  title="Average Soil Nutrient Levels by Crop Type",
                  color_discrete_map={'n': '#2ecc71', 'p': '#3498db', 'k': '#9b59b6'})

st.plotly_chart(fig_deps, use_container_width=True)

