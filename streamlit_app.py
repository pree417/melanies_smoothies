import streamlit as st
from snowflake.snowpark.functions import col
import requests
import pandas as pd

# Streamlit UI
st.title(":cup_with_straw: Customize Your Smoothie :cup_with_straw:")
st.write("Choose the fruits you want in your custom smoothie")

# Input for smoothie order name
name_on_order = st.text_input("Name on Smoothie:").strip()  # Preserve case
st.write("The name on your smoothie will be:", name_on_order)

# Connect to Snowflake
cnx = st.experimental_connection("snowflake", type="snowflake")
session = cnx.session()

# Fetch fruit options
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON'))
pd_df = my_dataframe.to_pandas()

# Multi-select for ingredients
ingredients_list = st.multiselect("Choose up to 5 ingredients", pd_df['FRUIT_NAME'].tolist(), max_selections=5)

# Limit selection
if len(ingredients_list) > 5:
    st.warning("You can select only up to 5 ingredients.")

st.write('')
if ingredients_list:
    # 🛠️ Ensure ingredients match expected format
    normalized_ingredients = " ".join([fruit.capitalize() for fruit in ingredients_list])  # Correct capitalization
    st.write(f"Final Ingredients String: `{normalized_ingredients}`")  # Debugging

    # Fetch nutrition info
    for fruit_chosen in ingredients_list:
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0] if not pd_df[pd_df['FRUIT_NAME'] == fruit_chosen].empty else None
        if search_on:
            st.subheader(f"{fruit_chosen} Nutrition Information")
            try:
                response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{search_on}")
                if response.status_code == 200:
                    fruit_data = response.json()
                    st.write(fruit_data)  # Show full data or first few rows
                else:
                    st.warning(f"Could not fetch nutrition data for {fruit_chosen}")
            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching data: {e}")

    # Submit Order
    time_to_insert = st.button("Submit Order")

    if time_to_insert:
        # Safe SQL Insertion
        try:
            my_insert_stmt = "INSERT INTO smoothies.public.orders (ingredients, name_on_order) VALUES (?, ?)"
            session.sql(my_insert_stmt, params=[normalized_ingredients, name_on_order]).collect()
            st.success(f"Your Smoothie is ordered, {name_on_order}!", icon="✅")
        except Exception as e:
            st.error(f"Error placing your order: {e}")

        # **DEBUG: Check Hashing Values**
        hash_check_query = """
        SELECT ingredients, 
               HASH(ingredients) AS HASH_ORIGINAL,
               HASH(TRIM(ingredients)) AS HASH_TRIMMED,
               HASH(UPPER(TRIM(ingredients))) AS HASH_UPPER_TRIMMED
        FROM smoothies.public.orders 
        WHERE name_on_order = ?;
        """
        hash_results = session.sql(hash_check_query, params=[name_on_order]).collect()
        st.write("🔍 Hash Debugging Results:")
        for row in hash_results:
            st.write(f"Original: {row['HASH_ORIGINAL']}, Trimmed: {row['HASH_TRIMMED']}, Upper Trimmed: {row['HASH_UPPER_TRIMMED']}")
