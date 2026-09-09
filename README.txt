Kundali 5Y — Swiss Ephemeris + Automatic Birth Place edition

RUN:
1. Install Python 3.10+.
2. In this folder run: pip install -r requirements.txt
3. Run: python server.py
4. Open: http://127.0.0.1:8000

NEW:
- Search birth place by city/area name.
- Select a result.
- Latitude and longitude are filled automatically.
- Timezone is detected automatically from the selected coordinates.
- Real Swiss Ephemeris calculations use the resolved coordinates/timezone.

The place search uses OpenStreetMap Nominatim when the app is running online.
Review Nominatim usage policy before commercial/high-volume deployment.

Swiss Ephemeris is by Astrodienst AG. Review its licensing terms before commercial deployment.
