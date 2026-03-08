import streamlit as st
import config
import mysql.connector as connector
import os
from ultralytics import YOLO
from collections import Counter
from dotenv import load_dotenv
from PIL import Image
import tempfile
import sys

load_dotenv()

# Page title
st.set_page_config(page_title="Vehicle Damage Detection", layout="centered")
st.title("🚗 AI Vehicle Damage Detection System")

file_path = os.path.dirname(os.path.abspath(sys.argv[0]))
# Load YOLO model
model_path = f"{file_path}/models/model weights/best_yolo_v11.pt"
model = YOLO(model_path)


# ---------------- DATABASE ---------------- #

def connect_to_db():
    try:
        connection = connector.connect(**config.mysql_credentials)
        return connection
    except connector.Error as e:
        st.error(f"Database connection error: {e}")
        return None


def get_brands():
    connection = connect_to_db()
    brands_list = []
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT brand FROM car_models")
        brands = cursor.fetchall()

        for brand in brands:
            brands_list.append(brand['brand'])

    return brands_list


def get_brand_models():
    connection = connect_to_db()

    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT brand,model FROM car_models")
        brand_models = cursor.fetchall()
        return brand_models

    return []


def get_part_name_from_id(class_id):
    class_names = ['Bonnet', 'Bumper', 'Dickey', 'Door', 'Fender', 'Light', 'Windshield']

    if 0 <= class_id < len(class_names):
        return class_names[int(class_id)]

    return None


def get_part_prices(class_counts, car_brand, car_model):

    connection = connect_to_db()
    prices = {}

    if connection:
        cursor = connection.cursor(dictionary=True)
        for class_id, count in class_counts.items():
            part_name = get_part_name_from_id(class_id)

            if part_name:
                cursor.execute(
                    "SELECT price FROM car_models WHERE brand=%s AND model=%s AND part=%s",
                    (car_brand, car_model, part_name)
                )
                price_data = cursor.fetchone()

                if price_data:
                    prices[part_name] = price_data['price']

    return prices


# ---------------- UI ---------------- #

brands = get_brands()
brand_models = get_brand_models()

selected_brand = st.selectbox("Select Car Brand", brands)

models = [m['model'] for m in brand_models if m['brand'] == selected_brand]

selected_model = st.selectbox("Select Car Model", models)


uploaded_file = st.file_uploader("Upload Vehicle Image", type=["jpg", "jpeg", "png"])


if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_container_width=True)

    if st.button("Detect Damage"):
        with st.spinner("Analyzing image..."):
            # Save image temporarily
            temp_file = tempfile.NamedTemporaryFile(suffix=".jpg",delete=False)
            image.save(temp_file.name)
            # Run YOLO detection
            result = model(temp_file.name)
            detected_objects = result[0].boxes
            class_ids = [box.cls.item() for box in detected_objects]
            class_counts = Counter(class_ids)

            if not class_counts:
                st.warning("No damage detected")

            else:
                # Show detected image
                result[0].save("detected.jpg")
                st.image("detected.jpg", caption="Detected Damage", use_container_width=True)
                # Get part prices
                part_prices = get_part_prices(class_counts, selected_brand, selected_model)
                st.subheader("Damage Estimate")
                total_cost = 0

                for part, price in part_prices.items():
                    st.write(f"{part} : ₹{price}")
                    total_cost += price

                st.success(f"Estimated Repair Cost: ₹{total_cost}")
