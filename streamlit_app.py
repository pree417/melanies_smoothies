# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col
import requests
import pandas as pd

# Streamlit app UI
st.title(":cup_with_straw: Customize Your Smoothie :cup_with_straw:")
st.write("Choose the fruits you want in your custom smoothie")

# Input for smoothie order name
name_on_order = st.text_input("Name on Smoothie:").strip().upper()  # Normalize input
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
    # Normalize ingredients list
    normalized_ingredients = " ".join([fruit.upper().strip() for fruit in ingredients_list])  

    for fruit_chosen in ingredients_list:
        # Fetch search key for fruit
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0] if not pd_df[pd_df['FRUIT_NAME'] == fruit_chosen].empty else None

        if search_on:
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
        # Insert order into Snowflake with normalized ingredients
        my_insert_stmt = "INSERT INTO smoothies.public.orders (ingredients, name_on_order) VALUES (?, ?)"
        session.sql(my_insert_stmt, params=[normalized_ingredients, name_on_order]).collect()

        st.success(f"Your Smoothie is ordered, {name_on_order}!", icon="✅")

        # Debugging: Check inserted data
        hash_check_query = f"""
        SELECT ingredients, HASH(UPPER(TRIM(ingredients))), HASH(UPPER(TRIM(name_on_order))) 
        FROM smoothies.public.orders 
        WHERE name_on_order = ?;
        """
        hash_results = session.sql(hash_check_query, params=[name_on_order]).collect()
        st.write("Debugging Hash Values:", hash_results)
