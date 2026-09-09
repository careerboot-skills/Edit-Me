
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
import json, os, math
from datetime import datetime, timedelta, timezone

import swisseph as swe

BASE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(BASE, "static")
PORT = 8000

PLANETS = [
    ("Sun", "सूर्य", swe.SUN, "☉"),
    ("Moon", "चंद्र", swe.MOON, "☽"),
    ("Mars", "मंगल", swe.MARS, "♂"),
    ("Mercury", "बुध", swe.MERCURY, "☿"),
    ("Jupiter", "गुरु", swe.JUPITER, "♃"),
    ("Venus", "शुक्र", swe.VENUS, "♀"),
    ("Saturn", "शनि", swe.SATURN, "♄"),
    ("Rahu", "राहु", swe.MEAN_NODE, "☊"),
]
SIGNS_EN = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
SIGNS_HI = ["मेष","वृषभ","मिथुन","कर्क","सिंह","कन्या","तुला","वृश्चिक","धनु","मकर","कुंभ","मीन"]
NAK = [
    "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu","Pushya","Ashlesha",
    "Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati","Vishakha","Anuradha",
    "Jyeshtha","Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishta","Shatabhisha",
    "Purva Bhadrapada","Uttara Bhadrapada","Revati"
]
NAK_HI = [
    "अश्विनी","भरणी","कृत्तिका","रोहिणी","मृगशिरा","आर्द्रा","पुनर्वसु","पुष्य","आश्लेषा",
    "मघा","पूर्व फाल्गुनी","उत्तर फाल्गुनी","हस्त","चित्रा","स्वाती","विशाखा","अनुराधा",
    "ज्येष्ठा","मूल","पूर्वाषाढ़ा","उत्तराषाढ़ा","श्रवण","धनिष्ठा","शतभिषा",
    "पूर्व भाद्रपद","उत्तर भाद्रपद","रेवती"
]

def norm(x):
    return x % 360.0

def sign_index(lon):
    return int(norm(lon) // 30)

def deg_text(lon):
    lon = norm(lon)
    d = int(lon % 30)
    m = int((lon % 1) * 60)
    return f"{d}° {m:02d}'"

def nakshatra(lon):
    x = norm(lon)
    n = int(x / (360/27))
    pada = int((x % (360/27)) / (360/108)) + 1
    return {"name": NAK[n], "name_hi": NAK_HI[n], "pada": pada}

def jd_from_local(year, month, day, hour, minute, tz_offset):
    # local civil time -> UTC decimal hour
    local_hour = hour + minute/60.0
    ut_hour = local_hour - float(tz_offset)
    return swe.julday(year, month, day, ut_hour)

def planet_positions(jd):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    out = []
    for en, hi, pid, sym in PLANETS:
        vals, _ = swe.calc_ut(jd, pid, flags)
        lon = norm(vals[0])
        # Rahu is mean ascending node; Ketu is opposite.
        out.append({
            "name": en, "name_hi": hi, "symbol": sym,
            "longitude": lon, "degree": deg_text(lon),
            "sign": SIGNS_EN[sign_index(lon)],
            "sign_hi": SIGNS_HI[sign_index(lon)],
            "nakshatra": nakshatra(lon),
            "retrograde": vals[3] < 0
        })
    rahu = next(x for x in out if x["name"] == "Rahu")
    ketu_lon = norm(rahu["longitude"] + 180)
    out.append({
        "name":"Ketu","name_hi":"केतु","symbol":"☋","longitude":ketu_lon,
        "degree":deg_text(ketu_lon),"sign":SIGNS_EN[sign_index(ketu_lon)],
        "sign_hi":SIGNS_HI[sign_index(ketu_lon)],"nakshatra":nakshatra(ketu_lon),
        "retrograde":True
    })
    return out

def ascendant(jd, lat, lon):
    # Swiss Ephemeris houses_ex returns tropical cusps/ascendant.
    cusps, ascmc = swe.houses_ex(jd, float(lat), float(lon), b'P', 0)
    tropical_asc = norm(ascmc[0])
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayan = swe.get_ayanamsa_ut(jd)
    sid_asc = norm(tropical_asc - ayan)
    return sid_asc, ayan, cusps

def whole_sign_houses(asc):
    first = sign_index(asc)
    houses = []
    for i in range(12):
        s = (first+i) % 12
        houses.append({"house":i+1,"sign":SIGNS_EN[s],"sign_hi":SIGNS_HI[s],"start":s*30})
    return houses

def transit_summary(natal, birth_jd, lat, lon):
    # Astrology guidance layer: uses actual Swiss Ephemeris transit positions,
    # then turns the Jupiter/Saturn relationship to natal Moon/Lagna into themes.
    moon = next(p for p in natal if p["name"]=="Moon")
    asc, _, _ = ascendant(birth_jd, lat, lon)
    moon_sign = sign_index(moon["longitude"])
    asc_sign = sign_index(asc)
    now = datetime.now(timezone.utc)
    base_year = now.year
    result=[]
    for i in range(5):
        y=base_year+i
        # Jan 1 12:00 UTC gives a stable annual snapshot.
        jd=swe.julday(y,1,1,12.0)
        tp=planet_positions(jd)
        j=next(p for p in tp if p["name"]=="Jupiter")
        s=next(p for p in tp if p["name"]=="Saturn")
        j_from_moon=(sign_index(j["longitude"])-moon_sign)%12+1
        s_from_moon=(sign_index(s["longitude"])-moon_sign)%12+1
        j_from_asc=(sign_index(j["longitude"])-asc_sign)%12+1
        career = "Growth through learning, mentors and opportunity; avoid rushing."
        money = "Prefer planned saving and measured risk; review commitments carefully."
        relation = "Communication and consistency matter more than assumptions."
        if j_from_moon in (1,2,5,7,9,11):
            career = "A comparatively supportive Jupiter pattern for learning, visibility and new opportunities."
        if j_from_asc in (2,5,9,10,11):
            money = "A comparatively constructive period for building income skills and long-term financial structure."
        if s_from_moon in (3,6,10,11):
            career = "Saturn-style results favor disciplined work, responsibility and durable progress."
        if s_from_moon in (4,8,12):
            relation = "Give relationships patience and clear boundaries; avoid reacting to temporary pressure."
        result.append({
            "year":y,
            "jupiter":j["sign_hi"],
            "saturn":s["sign_hi"],
            "career":career,
            "money":money,
            "relation":relation,
            "note":"Astrology-based guidance, not a factual prediction or financial advice."
        })
    return result

def calculate(payload):
    year=int(payload["year"]); month=int(payload["month"]); day=int(payload["day"])
    hour=int(payload["hour"]); minute=int(payload["minute"])
    tz=float(payload.get("timezone",5.5))
    lat=float(payload["latitude"]); lon=float(payload["longitude"])
    name=payload.get("name","Guest").strip() or "Guest"
    place=payload.get("place","").strip() or "Birth place"

    jd=jd_from_local(year,month,day,hour,minute,tz)
    planets=planet_positions(jd)
    asc, ayan, _ = ascendant(jd,lat,lon)
    houses=whole_sign_houses(asc)

    for p in planets:
        p["house"]=(sign_index(p["longitude"])-sign_index(asc))%12+1
    chart=[{"house":h["house"],"sign":h["sign"],"sign_hi":h["sign_hi"],
            "planets":[p["name"] for p in planets if p["house"]==h["house"]]} for h in houses]

    return {
        "name":name,"place":place,
        "birth":{"year":year,"month":month,"day":day,"hour":hour,"minute":minute,"timezone":tz,
                 "latitude":lat,"longitude":lon},
        "ayanamsa":ayan,
        "ascendant":{"longitude":asc,"degree":deg_text(asc),"sign":SIGNS_EN[sign_index(asc)],
                     "sign_hi":SIGNS_HI[sign_index(asc)],"nakshatra":nakshatra(asc)},
        "planets":planets,"houses":houses,"chart":chart,
        "five_years":transit_summary(planets,jd,lat,lon)
    }

class Handler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/api/kundali":
            self.send_error(404); return
        try:
            n=int(self.headers.get("Content-Length","0"))
            payload=json.loads(self.rfile.read(n).decode("utf-8"))
            data=calculate(payload)
            body=json.dumps(data,ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type","application/json; charset=utf-8")
            self.send_header("Content-Length",str(len(body)))
            self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            body=json.dumps({"error":str(e)},ensure_ascii=False).encode("utf-8")
            self.send_response(400)
            self.send_header("Content-Type","application/json; charset=utf-8")
            self.send_header("Content-Length",str(len(body)))
            self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            self.path="/index.html"
        return super().do_GET()

if __name__ == "__main__":
    os.chdir(STATIC)
    print(f"Kundali 5Y running at http://127.0.0.1:{PORT}")
    ThreadingHTTPServer(("127.0.0.1",PORT),Handler).serve_forever()
