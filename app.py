import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import os
import datetime
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
        (position) => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            const input = document.createElement("input");
            input.type = "hidden";
            input.id = "geo";
            input.value = lat + "," + lon;
            document.body.appendChild(input);
        }
    );
    </script>
    """,
    height=0,
)

geo = st.text_input("📍 Location (auto-fetched)", key="geo", disabled=True)

# -------------------------------
# CAMERA INPUT
# -------------------------------
camera_image = st.camera_input("Click a photo")

if camera_image is not None:

    # Convert image
    image_bytes = camera_image.getvalue()
    base_image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

    # Get date & time
    now = datetime.datetime.now()
    date_str = now.strftime("%d %b %Y")
    time_str = now.strftime("%I:%M %p")

    # Parse location
    if geo:
        latitude, longitude = geo.split(",")
    else:
        latitude, longitude = "N/A", "N/A"

    # -------------------------------
    # DRAW LOCATION TEXT
    # -------------------------------
    draw = ImageDraw.Draw(base_image)

    text = (
        f"Date: {date_str}\n"
        f"Time: {time_str}\n"
        f"Latitude: {latitude}\n"
        f"Longitude: {longitude}"
    )

    # Text position
    draw.rectangle((0, base_image.height - 150, base_image.width, base_image.height), fill="white")
    draw.text((20, base_image.height - 130), text, fill="black")

    st.subheader("📍 Geo Information")
    st.write(text)

    # -------------------------------
    # LOGO UPLOAD (AS YOU ASKED)
    # -------------------------------
    st.subheader("Upload Logo")
    logo_file = st.file_uploader("Upload logo (PNG preferred)", type=["png", "jpg", "jpeg"])

    if logo_file is not None:
        logo = Image.open(logo_file).convert("RGBA")

        # -------- LOGO SETTINGS (UNCHANGED) --------
        logo = logo.resize((150, 150))
        img_w, img_h = base_image.size
        logo_x = img_w - 170
        logo_y = 20

        base_image.paste(logo, (logo_x, logo_y), logo)

        # -------------------------------
        # SAVE IMAGE
        # -------------------------------
        os.makedirs("output_images", exist_ok=True)
        output_path = "output_images/final_image.png"
        base_image.save(output_path)

        st.subheader("✅ Final Image")
        st.image(base_image, use_container_width=True)

        with open(output_path, "rb") as f:
            st.download_button(
                "⬇ Download Final Image",
                f,
                file_name="geotag_image.png",
                mime="image/png"
            )
