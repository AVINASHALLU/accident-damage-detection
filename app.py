import streamlit as st
import config
import config_local
import mysql.connector as connector
import os
from ultralytics import YOLO
from collections import Counter
from dotenv import load_dotenv
from PIL import Image
import tempfile
import sys

load_dotenv()

# ---------------- PAGE CONFIG ---------------- #

st.set_page_config(
    page_title="Vehicle Damage Detection",
    page_icon="🚗",
    layout="centered"
)

# ---------------- SIMPLE ACCESSIBLE UI ---------------- #

st.markdown("""
<style>

/* Main Background */
.stApp {
    background-color: #f4f6f9;
}

/* Main Container 
.main-box {
    background-color: white;
    padding: 25px;
    border: 1px solid #d1d5db;
    border-radius: 12px;
    margin-top: 20px;
}*/

/* Title */
.title {
    text-align: center;
    color: #1e3a8a;
    font-size: 36px;
    font-weight: bold;
    margin-bottom: 5px;
}

/* Subtitle */
.subtitle {
    text-align: center;
    color: #4b5563;
    margin-bottom: 25px;
}

/* Section Box 
.section-box {
    background-color: #ffffff;
    padding: 18px;
    border: 1px solid #d1d5db;
    border-radius: 10px;
    margin-bottom: 20px;
}
*/
/* Button */
.stButton > button {
    width: 100%;
    height: 45px;
    border-radius: 8px;
    border: none;
    background-color: #2563eb;
    color: white;
    font-size: 16px;
    font-weight: 600;
}

/* Input Labels */
label {
    font-weight: 600 !important;
    color: #111827 !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: white;
    border-right: 1px solid #d1d5db;
}

</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ---------------- #

st.markdown(
    '<div class="title">🚗 Vehicle Damage Detection</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">AI-powered vehicle inspection and repair estimation</div>',
    unsafe_allow_html=True
)

# ---------------- LOAD MODEL ---------------- #

file_path = os.path.dirname(os.path.abspath(sys.argv[0]))

model_path = f"{file_path}/models/model weights/best.pt"

model = YOLO(model_path)

# ---------------- DATABASE ---------------- #

def connect_to_db():

    try:
        connection = connector.connect(**config.mysql_credentials)  #cloud config
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

    class_names = [
        'Bonnet',
        'Bumper',
        'Dickey',
        'Door',
        'Fender',
        'Light',
        'Windshield'
    ]

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
                    """
                    SELECT price
                    FROM car_models
                    WHERE brand=%s AND model=%s AND part=%s
                    """,
                    (car_brand, car_model, part_name)
                )

                price_data = cursor.fetchone()

                if price_data:
                    prices[part_name] = price_data['price']

    return prices

# ---------------- SIDEBAR ---------------- #

with st.sidebar:

    st.title("Menu")

    st.write("✔ Upload Vehicle Image")
    st.write("✔ Detect Damages")
    st.write("✔ Estimate Repair Cost")

    st.info("YOLOv26 AI Detection System")

# ---------------- MAIN CONTENT ---------------- #

st.markdown('<div class="main-box">', unsafe_allow_html=True)

brands = get_brands()

brand_models = get_brand_models()

# ---------------- BRAND SELECTION ---------------- #

#st.markdown('<div class="section-box">', unsafe_allow_html=True)

selected_brand = st.selectbox(
    "Select Car Brand",
    brands
)

models = [
    m['model']
    for m in brand_models
    if m['brand'] == selected_brand
]

selected_model = st.selectbox(
    "Select Car Model",
    models
)

st.markdown('</div>', unsafe_allow_html=True)

# ---------------- FILE UPLOAD ---------------- #

#st.markdown('<div class="section-box">', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Upload Vehicle Image",
    type=["jpg", "jpeg", "png"]
)

st.markdown('</div>', unsafe_allow_html=True)

# ---------------- IMAGE DISPLAY ---------------- #

if uploaded_file:

    image = Image.open(uploaded_file)

   # st.markdown('<div class="section-box">', unsafe_allow_html=True)

    st.subheader("Uploaded Image")

    st.image(
        image,
        use_container_width=True
    )

    st.markdown('</div>', unsafe_allow_html=True)

    # ---------------- DETECTION BUTTON ---------------- #

    if st.button("Detect Damage"):

        with st.spinner("Analyzing image..."):

            # Save Temporary File
            temp_file = tempfile.NamedTemporaryFile(
                suffix=".jpg",
                delete=False
            )

            image.save(temp_file.name)

            # Run YOLO Model
            result = model(temp_file.name)

            detected_objects = result[0].boxes

            class_ids = [
                box.cls.item()
                for box in detected_objects
            ]

            class_counts = Counter(class_ids)

            # ---------------- NO DAMAGE ---------------- #

            if not class_counts:

                st.warning("No damage detected")

            else:

                # Save Detection Image
                result[0].save("detected.jpg")

                st.subheader("Detected Damage")

                st.image(
                    "detected.jpg",
                    use_container_width=True
                )

                st.markdown(
                    '</div>',
                    unsafe_allow_html=True
                )

                # ---------------- COST ESTIMATION ---------------- #

                part_prices = get_part_prices(
                    class_counts,
                    selected_brand,
                    selected_model
                )

                total_cost = 0

                st.markdown(
                    '<div class="section-box">',
                    unsafe_allow_html=True
                )

                st.subheader("Damage Estimate")

                for part, price in part_prices.items():

                    st.write(f"🔧 {part} : ₹{price}")

                    total_cost += price

                st.success(
                    f"Estimated Repair Cost: ₹{total_cost}"
                )

                st.markdown(
                    '</div>',
                    unsafe_allow_html=True
                )

st.markdown('</div>', unsafe_allow_html=True)
