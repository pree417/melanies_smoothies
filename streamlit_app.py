# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col
import requests
import pandas as pd

# Streamlit app UI
st.title(":cup_with_straw: Customize Your Smoothie :cup_with_straw:")
st.write("Choose your fruits you want in your custom smoothie")

# Input for smoothie order name
name_on_order = st.text_input("Name on Smoothie:")
st.write("The name on your smoothie will be:", name_on_order)

# Connect to Snowflake
cnx = st.connection("snowflake")
session = cnx.session()

# Fetch available fruit options
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON'))
pd_df = my_dataframe.to_pandas()

# Multiselect for fruit choices
ingredients_list = st.multiselect("Choose up to 5 ingredients", pd_df['FRUIT_NAME'].tolist(), max_selections=5)

# Limit selection warning
if len(ingredients_list) > 5:
    st.warning("You can select only up to 5 ingredients.")

st.write('')
if ingredients_list:
    ingredients_string = " ".join(ingredients_list)  # Join fruits into a string

    for fruit_chosen in ingredients_list:
        if not pd_df[pd_df['FRUIT_NAME'] == fruit_chosen].empty:
            search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]

            st.subheader(f"{fruit_chosen} Nutrition Information")
            
            # Fetch nutrition information safely
            try:
                response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{search_on}")
                if response.status_code == 200:
                    fruit_data = response.json()
                    st.dataframe(data=fruit_data, use_container_width=True)
                else:
                    st.warning(f"Could not fetch nutrition data for {fruit_chosen}")
            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching data: {e}")

    # Button to submit order
    time_to_insert = st.button("Submit Order")

    if time_to_insert:
        # Secure SQL insert query
        my_insert_stmt = "INSERT INTO smoothies.public.orders (ingredients, name_on_order) VALUES (?, ?)"
        session.sql(my_insert_stmt, params=[ingredients_string.strip(), name_on_order]).collect()

        st.success(f"Your Smoothie is ordered, {name_on_order}!", icon="✅")
