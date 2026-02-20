import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import os
import datetime
from streamlit_js_eval import get_geolocation, streamlit_js_eval
from geopy.distance import geodesic
import textwrap
import time
import googlemaps

# -------------------------------
# PAGE CONFIG & CSS
# -------------------------------
st.set_page_config(page_title="GeoTag Camera", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .main { background-color: #f7f7f7; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    .snap-header { font-weight: 800; color: #000; font-size: 2.2rem; text-align: center; margin-top: 1rem; letter-spacing: -1px; }
    .snap-subheader { color: #888; text-align: center; font-size: 0.9rem; margin-bottom: 1.5rem; }
    .stVerticalBlock { gap: 1rem !important; }
    .info-card { background: white; padding: 15px; border-radius: 18px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 1rem; }
    .place-item { background: #fff; padding: 12px 15px; border-radius: 12px; margin-bottom: 8px; border-left: 6px solid #FFFC00; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
    .place-name { font-weight: bold; font-size: 1.05rem; color: #000; margin: 0; }
    .place-address { font-size: 0.8rem; color: #777; margin: 0; }
    .place-dist { font-size: 0.75rem; color: #000; font-weight: 600; background: #FFFC00; padding: 2px 6px; border-radius: 6px; }
    .stButton > button { border-radius: 20px; width: 100%; font-weight: 600; background-color: #FFFC00; color: #000; border: none; transition: transform 0.1s; }
    .stButton > button:active { transform: scale(0.98); }
    .stImage img { border-radius: 15px; }
    </style>
""", unsafe_allow_html=True)

# -------------------------------
# STATE MANAGEMENT
# -------------------------------
if "lat" not in st.session_state: st.session_state.lat = None
if "lon" not in st.session_state: st.session_state.lon = None
if "selected_venue" not in st.session_state: st.session_state.selected_venue = "Detecting..."
if "full_address" not in st.session_state: st.session_state.full_address = "Wait for GPS..."
if "local_time" not in st.session_state: st.session_state.local_time = None
if "nearby_places" not in st.session_state: st.session_state.nearby_places = []
if "time_fetch_attempts" not in st.session_state: st.session_state.time_fetch_attempts = 0

# -------------------------------
# GOOGLE MAPS SETUP
# -------------------------------
GMAPS_API_KEY = "AIzaSyBOCNcRazxdoae9jf3sROu5v2QWkiFzPLo"  # <-- Replace with your Google Maps API Key
gmaps = googlemaps.Client(key=GMAPS_API_KEY)

# -------------------------------
# HEADER
# -------------------------------
st.markdown('<div class="snap-header">GeoTag Camera</div>', unsafe_allow_html=True)
st.markdown('<div class="snap-subheader">Snap with location & time labels</div>', unsafe_allow_html=True)

# -------------------------------
# BROWSER DATA FETCH
# -------------------------------
loc_data = get_geolocation()
if loc_data and "coords" in loc_data:
    new_lat = loc_data["coords"].get("latitude")
    new_lon = loc_data["coords"].get("longitude")

    if st.session_state.lat is None:
        st.session_state.lat = new_lat
        st.session_state.lon = new_lon

        # Auto-Discover Nearby Places using Google Maps
        with st.spinner("Finding nearby places..."):
            try:
                # Reverse Geocoding
                rev_result = gmaps.reverse_geocode((new_lat, new_lon))
                if rev_result:
                    st.session_state.full_address = rev_result[0]['formatted_address']
                    st.session_state.selected_venue = rev_result[0]['address_components'][0]['long_name']

                # Nearby Places
                places_result = gmaps.places_nearby(
                    location=(new_lat, new_lon),
                    radius=500,  # meters
                    type='establishment'
                )
                if places_result.get("results"):
                    st.session_state.nearby_places = places_result["results"]
                else:
                    st.session_state.nearby_places = [{'name': st.session_state.selected_venue,
                                                       'vicinity': st.session_state.full_address,
                                                       'geometry': {'location': {'lat': new_lat, 'lng': new_lon}}}]
            except Exception as e:
                st.error(f"Google Maps fetch failed: {e}")

# Fetch Browser Time
b_time = streamlit_js_eval(code='new Date().toLocaleString()', key='time_comp_v4')
if b_time:
    st.session_state.local_time = b_time
elif st.session_state.local_time is None:
    st.session_state.local_time = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

# -------------------------------
# STATUS CARD
# -------------------------------
with st.container():
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.caption("🕒 Time")
        show_time = st.session_state.local_time.split(", ")[-1] if st.session_state.local_time and "," in st.session_state.local_time else "Detecting..."
        st.subheader(show_time)
    with c2:
        st.caption("📍 GPS")
        st.subheader(f"{round(st.session_state.lat, 4) if st.session_state.lat else '...'}")
    
    st.caption("🏢 Selected Venue")
    st.write(f"**{st.session_state.selected_venue}**")
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------
# PLACES & SEARCH
# -------------------------------
st.markdown("### 📍 Places Near You")
search_q = st.text_input("Not right? Search for a place:", placeholder="e.g. Cafe, Park, Office...")

if st.button("Search Places"):
    if search_q:
        with st.spinner("Searching..."):
            try:
                res = gmaps.places(query=search_q, location=(st.session_state.lat, st.session_state.lon), radius=1000)
                if res.get("results"):
                    st.session_state.nearby_places = res["results"]
                    st.toast("Updated place list!", icon="✅")
                else:
                    st.error("No places found.")
            except Exception as e:
                st.error(f"Search failed: {e}")

# Scrollable Selection List
if st.session_state.nearby_places:
    for idx, p in enumerate(st.session_state.nearby_places):
        name = p.get('name', 'Unknown')
        addr_short = p.get('vicinity', '')
        dist = ""
        if st.session_state.lat and st.session_state.lon:
            d = geodesic(
                (st.session_state.lat, st.session_state.lon),
                (p['geometry']['location']['lat'], p['geometry']['location']['lng'])
            ).m
            dist = f"{int(d)}m" if d < 1000 else f"{round(d/1000,1)}km"

        col_txt, col_sel = st.columns([4, 1])
        with col_txt:
            st.markdown(f"""
                <div class="place-item">
                    <p class="place-name">{name} <span class="place-dist">{dist}</span></p>
                    <p class="place-address">{addr_short}</p>
                </div>
            """, unsafe_allow_html=True)
        with col_sel:
            if st.button("Use", key=f"sel_{idx}"):
                st.session_state.selected_venue = name
                st.session_state.full_address = addr_short
                st.session_state.lat = p['geometry']['location']['lat']
                st.session_state.lon = p['geometry']['location']['lng']
                st.rerun()

# -------------------------------
# CAMERA / UPLOAD
# -------------------------------
st.markdown("---")
choice = st.radio("Choose Input:", ["Camera 📸", "Upload 📁"], horizontal=True, label_visibility="collapsed")

captured = None
if "Camera" in choice:
    captured = st.camera_input("Take a Snap")
else:
    captured = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])

if captured:
    raw_img = Image.open(io.BytesIO(captured.getvalue())).convert("RGBA")
    draw = ImageDraw.Draw(raw_img)
    
    venue_name = st.session_state.selected_venue.upper()
    timestamp = st.session_state.local_time if st.session_state.local_time else "Unknown Time"
    gps_str = f"GPS: {st.session_state.lat}, {st.session_state.lon}"
    addr_wrapped = textwrap.fill(st.session_state.full_address, width=40)
    
    overlay = f"{venue_name}\n{'─'*20}\n{timestamp}\n{gps_str}\n{addr_wrapped}"
    
    lines = overlay.count("\n") + 1
    box_h = 80 + (lines * 32)
    draw.rectangle([0, raw_img.height - box_h, raw_img.width, raw_img.height], fill=(0,0,0, 170))
    draw.text((35, raw_img.height - box_h + 30), overlay, fill="white")
    
    st.markdown("### ✨ Preview")
    st.image(raw_img, use_container_width=True)
    
    col_dl, col_logo = st.columns(2)
    with col_logo:
        logo_up = st.file_uploader("Add Logo?", type=["png", "jpg"])
        if logo_up:
            l_img = Image.open(logo_up).convert("RGBA").resize((160, 160))
            raw_img.paste(l_img, (raw_img.width - 190, 40), l_img)
            st.info("Logo added! Download to see final.")
            
    with col_dl:
        buf = io.BytesIO()
        raw_img.save(buf, format="PNG")
        st.download_button("⬇️ Save Snapshot", buf.getvalue(), f"Snap_{int(time.time())}.png", "image/png")

# -------------------------------
# FOOTER / REFRESH
# -------------------------------
if st.button("🔄 Reset Location & Time"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

if st.session_state.lat is None:
    st.warning("⚠️ **Location not found.** Please ensure GPS is ON and you allowed browser access. Try reloading the page.")