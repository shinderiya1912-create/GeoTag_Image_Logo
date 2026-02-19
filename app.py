import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import os
import datetime
import numpy as np
import streamlit.components.v1 as components

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="GeoTag Logo Camera App", layout="centered")
st.title("📸 GeoTag Camera with Logo")
st.info("Please allow camera and location access when prompted.")

# -------------------------------
# GET LOCATION FROM BROWSER
# -------------------------------
components.html(
    """
    <script>
    navigator.geolocation.getCurrentPosition(
        function(position) {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            const inputLat = document.createElement("input");
            inputLat.type = "hidden";
            inputLat.id = "lat";
            inputLat.value = lat;
            document.body.appendChild(inputLat);

            const inputLon = document.createElement("input");
            inputLon.type = "hidden";
            inputLon.id = "lon";
            inputLon.value = lon;
            document.body.appendChild(inputLon);
        }
    );
    </script>
    """,
    height=0,
)

lat = st.text_input("Latitude (auto)", key="lat", disabled=True)
lon = st.text_input("Longitude (auto)", key="lon", disabled=True)

# -------------------------------
# CAMERA INPUT
# -------------------------------
camera_image = st.camera_input("Click a photo")

if camera_image is not None:
    # Convert to PIL
    image_bytes = camera_image.getvalue()
    base_image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

    # -------------------------------
    # GET DATE & TIME
    # -------------------------------
    now = datetime.datetime.now()
    date_str = now.strftime("%d %b %Y")
    time_str = now.strftime("%I:%M %p")

    # -------------------------------
    # DRAW TEXT (LOCATION + DATE/TIME)
    # -------------------------------
    draw = ImageDraw.Draw(base_image)
    lat_text = lat if lat else "N/A"
    lon_text = lon if lon else "N/A"

    text = f"Date: {date_str}\nTime: {time_str}\nLatitude: {lat_text}\nLongitude: {lon_text}"

    # Draw a white rectangle for text
    draw.rectangle((0, base_image.height - 130, base_image.width, base_image.height), fill="white")
    draw.text((20, base_image.height - 120), text, fill="black")

    st.subheader("📍 Geo Information")
    st.write(text)

    # -------------------------------
    # LOGO UPLOAD
    # -------------------------------
    st.subheader("Upload Logo")
    logo_file = st.file_uploader("Upload logo (PNG recommended)", type=["png", "jpg", "jpeg"])

    if logo_file is not None:
        logo = Image.open(logo_file).convert("RGBA")

        # -------------------------------
        # LOGO ADJUSTMENTS
        # -------------------------------
        st.sidebar.subheader("Logo Adjustments")
        # Size slider
        size = st.sidebar.slider("Logo size", 50, 300, 150)
        logo = logo.resize((size, size))

        # Position sliders
        max_x = base_image.width - size
        max_y = base_image.height - size
        x_pos = st.sidebar.slider("Logo X Position", 0, max_x, max_x - 20)
        y_pos = st.sidebar.slider("Logo Y Position", 0, max_y, 20)

        # Circle option
        circle_logo = st.sidebar.checkbox("Circle-shaped logo", value=True)
        if circle_logo:
            logo_np = np.array(logo)
            h, w = logo_np.shape[:2]
            mask = np.zeros((h, w), dtype=np.uint8)
            import cv2  # OpenCV for circle mask
            cv2.circle(mask, (w // 2, h // 2), w // 2, 255, -1)
            if logo_np.shape[2] == 4:
                logo_np[:, :, 3] = cv2.bitwise_and(logo_np[:, :, 3], mask)
            logo = Image.fromarray(logo_np)

        # -------------------------------
        # PASTE LOGO
        # -------------------------------
        base_image.paste(logo, (x_pos, y_pos), logo)

        # -------------------------------
        # SAVE IMAGE
        # -------------------------------
        os.makedirs("output_images", exist_ok=True)
        output_path = "output_images/final_image.png"
        base_image.save(output_path)

        # -------------------------------
        # SHOW FINAL IMAGE
        # -------------------------------
        st.subheader("✅ Final Image")
        st.image(base_image, use_container_width=True)

        with open(output_path, "rb") as f:
            st.download_button(
                "⬇ Download Final Image",
                f,
                file_name="geotag_image.png",
                mime="image/png"
            )
