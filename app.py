from flask import Flask, jsonify, request, send_from_directory
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
app = Flask(__name__, static_folder="static")

# Sample records are deliberately labelled demo data.
opportunities = [
    {"id": 1, "title": "Frontend Developer Intern", "organisation": "PixelSpring Labs", "type": "Internship", "mode": "Hybrid · Chennai", "stipend": "₹12,000/month", "deadline": "2026-11-05", "skills": ["HTML", "CSS", "JavaScript"], "match": 86, "risk": "Needs verification", "description": "Build accessible web interfaces with a product team.", "eligibility": "Students with basic web development skills.", "source": "https://example.com/opportunities/frontend-intern"},
    {"id": 2, "title": "Data Analyst Intern", "organisation": "Northstar Analytics", "type": "Internship", "mode": "Remote", "stipend": "₹10,000/month", "deadline": "2026-11-12", "skills": ["Python", "SQL", "Excel"], "match": 78, "risk": "Needs verification", "description": "Explore datasets, prepare reports and communicate insights.", "eligibility": "Undergraduate students comfortable with spreadsheets.", "source": "https://example.com/opportunities/data-analyst"},
    {"id": 3, "title": "Smart City Hackathon 2026", "organisation": "CivicTech Collective", "type": "Hackathon", "mode": "Online", "stipend": "Prizes listed by organiser", "deadline": "2026-11-18", "skills": ["Python", "AI", "Problem solving"], "match": 81, "risk": "Insufficient evidence", "description": "Prototype practical ideas for safer, more connected cities.", "eligibility": "Student teams of 2–5 members.", "source": "https://example.com/events/smart-city-hackathon"},
    {"id": 4, "title": "Women in STEM Scholarship", "organisation": "FutureBridge Foundation", "type": "Scholarship", "mode": "India", "stipend": "Funding varies", "deadline": "2026-11-30", "skills": ["STEM", "Academics"], "match": 74, "risk": "Needs verification", "description": "A sample listing for students pursuing STEM degrees.", "eligibility": "Check the official criteria before applying.", "source": "https://example.com/scholarships/women-in-stem"}
]
posts = [
    {"id": 1, "name": "Ananya Rao", "meta": "CSE · 2nd year · 2h ago", "initials": "AR", "content": "Just finished my first responsive portfolio website! I learned a lot about CSS Grid and accessibility along the way.", "tags": ["#WebDevelopment", "#LearningInPublic"], "likes": 24, "comments": 6, "kind": "Projects"},
    {"id": 2, "name": "Rahul Menon", "meta": "AI/ML Club · 5h ago", "initials": "RM", "content": "Our team is exploring ways to make internship discovery safer for students. What warning signs do you check before applying?", "tags": ["#StudentSafety", "#AI"], "likes": 18, "comments": 9, "kind": "Learning"},
    {"id": 3, "name": "Meera Iyer", "meta": "Electronics · 1d ago", "initials": "MI", "content": "Small progress update: completed a sensor-based mini project and documented the circuit, testing notes and lessons learned.", "tags": ["#Engineering", "#Projects"], "likes": 31, "comments": 4, "kind": "Colleges"}
]
saved = set()
applications = {}

@app.get("/")
def home():
    return send_from_directory(ROOT, "index.html")

@app.get("/api/dashboard")
def dashboard():
    return jsonify({"demo": True, "student": {"name": "Vikas Kumar", "degree": "B.Tech Computer Science · 3rd year", "profile_strength": 78}, "stats": {"skills_learned": 12, "projects_completed": 5, "saved_opportunities": len(saved) or 3, "learning_progress": 64}, "deadlines": opportunities[:4]})

@app.get("/api/opportunities")
def get_opportunities():
    q = request.args.get("q", "").lower().strip()
    kind = request.args.get("type", "All")
    results = [o for o in opportunities if (not q or q in (o["title"] + " " + o["organisation"] + " " + " ".join(o["skills"])).lower()) and (kind == "All" or o["type"] == kind)]
    return jsonify({"demo": True, "items": results})

@app.post("/api/save/<int:opp_id>")
def save_opportunity(opp_id):
    if not any(o["id"] == opp_id for o in opportunities):
        return jsonify({"error": "Opportunity not found"}), 404
    if opp_id in saved:
        saved.remove(opp_id)
        return jsonify({"saved": False, "message": "Removed from saved opportunities"})
    saved.add(opp_id)
    return jsonify({"saved": True, "message": "Opportunity saved"})

@app.get("/api/posts")
def get_posts():
    return jsonify({"demo": True, "items": posts})

@app.post("/api/posts")
def create_post():
    data = request.get_json(silent=True) or {}
    content = str(data.get("content", "")).strip()
    if len(content) < 3:
        return jsonify({"error": "Write a little more before posting."}), 400
    post = {"id": max([p["id"] for p in posts] + [0]) + 1, "name": "Vikas Kumar", "meta": "You · just now", "initials": "VK", "content": content[:1200], "tags": ["#StudentCommunity"], "likes": 0, "comments": 0, "kind": "For You"}
    posts.insert(0, post)
    return jsonify({"item": post, "message": "Post published"})

@app.post("/api/scamsense")
def scamsense():
    data = request.get_json(silent=True) or {}
    description = str(data.get("description", "")).strip()
    source_url = str(data.get("url", "")).strip()
    if len(description) < 8:
        return jsonify({"error": "Paste an opportunity description (at least 8 characters)."}), 400
    checks = [
        (r"registration fee|processing fee|pay\s*₹?|upfront fee|deposit", "Requests an upfront payment", "Legitimate opportunities generally should not require applicants to pay a fee to apply."),
        (r"guaranteed job|100% placement|earn\s*₹?\s*\d+\s*(lakh|crore)", "Potentially unrealistic promise", "Promises that sound guaranteed or unusually high should be checked carefully."),
        (r"urgent|limited slots|apply immediately|within \d+ hours", "Urgency or pressure language", "Pressure tactics can discourage independent verification."),
        (r"bank details|card number|otp|password|upi pin", "Sensitive information request", "Do not share passwords, OTPs, UPI PINs or unnecessary financial details."),
        (r"gmail\.com|bit\.ly|tinyurl\.com|t\.me", "Personal or shortened contact/link", "Confirm the contact and destination through an official organisation website.")
    ]
    findings = [{"signal": title, "explanation": explanation} for pattern, title, explanation in checks if re.search(pattern, description + " " + source_url, re.I)]
    if not source_url or not re.match(r"^https?://", source_url, re.I):
        findings.append({"signal": "Source not independently established", "explanation": "No valid source URL was supplied. This demo cannot verify the employer or domain."})
    if any("upfront payment" in f["signal"].lower() or "sensitive information" in f["signal"].lower() for f in findings):
        risk = "High risk"
    elif findings:
        risk = "Needs verification"
    else:
        risk = "Insufficient evidence"
    return jsonify({"demo": True, "risk": risk, "findings": findings, "checked": ["Upfront fees", "Pressure language", "Sensitive information", "Source URL format"], "note": "This is a rule-based demonstration, not a fraud determination. Verify the opportunity through official channels."})

@app.post("/api/applications")
def update_application():
    data = request.get_json(silent=True) or {}
    try: opp_id = int(data.get("id"))
    except (TypeError, ValueError): return jsonify({"error": "Invalid opportunity id"}), 400
    status = data.get("status", "Saved")
    allowed = ["Saved", "Planning to Apply", "Applied", "Interview", "Completed", "Rejected"]
    if status not in allowed: return jsonify({"error": "Invalid status"}), 400
    applications[opp_id] = status
    return jsonify({"id": opp_id, "status": status})

@app.get("/api/applications")
def get_applications():
    return jsonify({"demo": True, "items": [{"id": o["id"], "title": o["title"], "organisation": o["organisation"], "status": applications.get(o["id"], "Saved" if o["id"] in saved else "Planning to Apply")} for o in opportunities]})

@app.post("/api/skillpath")
def skillpath():
    data = request.get_json(silent=True) or {}
    role = str(data.get("role", "Frontend Developer"))
    skills = [s.strip() for s in str(data.get("skills", "HTML, Python, SQL")).split(",") if s.strip()]
    suggestions = {"Frontend Developer": ["JavaScript", "React", "Git"], "Data Analyst": ["Pandas", "SQL joins", "Data visualisation"], "AI/ML Engineer": ["NumPy", "Statistics", "Model evaluation"], "Cybersecurity Analyst": ["Networking basics", "Linux", "Threat modelling"]}
    return jsonify({"demo": True, "role": role, "current_skills": skills, "next_skills": suggestions.get(role, ["Communication", "Project planning", "Git"]), "projects": ["Build a small portfolio project", "Document your work on GitHub", "Explain your project in a short case study"], "match_note": "Illustrative recommendations — no real AI model is connected."})

@app.get("/<path:path>")
def static_files(path):
    if path.startswith("api/"):
        return jsonify({"error": "Endpoint not found"}), 404
    return send_from_directory(ROOT, path)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
