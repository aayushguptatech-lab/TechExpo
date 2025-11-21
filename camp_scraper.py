import feedparser
from datetime import datetime

def clean_text(text):
    """Remove weird characters and newlines"""
    return " ".join(text.replace("\n", " ").replace("\xa0", " ").split())

def detect_camp_details(title):
    """Infer the camp type and services from the title."""
    title_lower = title.lower()
    camp_type = "General Health Camp"
    services = []

    # Detect specific camp types
    if "blood" in title_lower:
        camp_type = "Blood Donation Camp"
        services = ["Blood Donation", "Hemoglobin Check"]
    elif "eye" in title_lower:
        camp_type = "Eye Checkup Camp"
        services = ["Eye Testing", "Vision Screening"]
    elif "dental" in title_lower:
        camp_type = "Dental Health Camp"
        services = ["Oral Checkup", "Free Dental Consultation"]
    elif "vaccination" in title_lower or "immunization" in title_lower:
        camp_type = "Vaccination Drive"
        services = ["Immunization", "COVID / Flu / Routine Vaccines"]
    elif "yoga" in title_lower:
        camp_type = "Yoga & Wellness Camp"
        services = ["Yoga Sessions", "Meditation", "Wellness Talk"]
    elif "women" in title_lower:
        camp_type = "Women's Health Camp"
        services = ["Gynecology", "Cancer Screening", "Nutrition"]
    elif "child" in title_lower:
        camp_type = "Child Health Camp"
        services = ["Pediatric Checkup", "Nutrition Awareness"]
    elif "medical" in title_lower or "health" in title_lower:
        camp_type = "General Health Checkup"
        services = ["Blood Pressure", "Sugar Test", "BMI", "Consultation"]

    # Detect NGO or organizer name
    ngo = "Local Health Organization"
    keywords = ["ngo", "foundation", "society", "trust", "hospital", "clinic"]
    for word in keywords:
        if word in title_lower:
            parts = title.split()
            for i, w in enumerate(parts):
                if word in w.lower() and i > 0:
                    ngo = " ".join(parts[max(0, i-2):i+2]).strip().title()
                    break
            break

    return camp_type, services, ngo


def fetch_city_camps(city):
    """
    Fetches health camp announcements (title + date + map link + type + NGO info)
    """
    city = city.strip().title()
    print(f"🔍 Fetching camps for {city}")
    results = []

    try:
        query = f"{city} health camp OR medical camp OR NGO OR blood donation OR vaccination drive"
        rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}+India&hl=en-IN&gl=IN&ceid=IN:en"
        feed = feedparser.parse(rss_url)

        for entry in feed.entries[:10]:
            title = clean_text(entry.title)
            link = entry.link
            published = getattr(entry, "published", "Recently")

            camp_type, services, ngo = detect_camp_details(title)
            map_link = f"https://www.google.com/maps/search/?api=1&query={city}+health+camp"

            results.append({
                "title": title,
                "date": published,
                "camp_type": camp_type,
                "services": ", ".join(services) if services else "General Checkup",
                "ngo": ngo,
                "map_link": map_link,
                "news_link": link
            })
    except Exception as e:
        print("⚠️ Error fetching feed:", e)

    if not results:
        results = [{
            "title": f"No live or upcoming camps found in {city}.",
            "date": datetime.now().strftime("%d %b %Y"),
            "camp_type": "General Health Camp",
            "services": "Blood Test, Sugar Test, General Checkup",
            "ngo": "SevaKendra Foundation",
            "map_link": f"https://www.google.com/maps/search/?api=1&query={city}+hospital",
            "news_link": "#"
        }]

    return results
