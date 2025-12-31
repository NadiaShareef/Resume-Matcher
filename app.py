import streamlit as st

# Try to import PDF library
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# Define the classes and functions
class JobDescription:
    def __init__(self, title, required_skills, required_experience_years, required_qualification):
        self.title = title
        self.required_skills = required_skills
        self.required_experience_years = required_experience_years
        self.required_qualification = required_qualification

class Resume:
    def __init__(self, candidate_name, skills, experience_years, qualification):
        self.candidate_name = candidate_name
        self.skills = skills
        self.experience_years = experience_years
        self.qualification = qualification

def match_skills(resume, job_description):
    resume_skills = set(skill.lower() for skill in resume.skills)
    required_skills = set(skill.lower() for skill in job_description.required_skills)
    common_skills = len(resume_skills.intersection(required_skills))
    
    if not required_skills:
        return 1.0
    score = common_skills / len(required_skills)
    return score

def match_experience(resume, job_description):
    required_exp = job_description.required_experience_years
    candidate_exp = resume.experience_years
    if required_exp == 0:
        return 1.0
    elif candidate_exp >= required_exp:
        return 1.0
    else:
        return candidate_exp / required_exp

def match_qualification(resume, job_description):
    qualification_levels = {
        "none": 0,
        "high school": 1,
        "associate's degree": 2,
        "bachelor's degree": 3,
        "master's degree": 4,
        "phd": 5
    }
    
    candidate_qual = resume.qualification.lower() if resume.qualification else "none"
    required_qual = job_description.required_qualification.lower() if job_description.required_qualification else "none"
    
    candidate_level = qualification_levels.get(candidate_qual, 0)
    required_level = qualification_levels.get(required_qual, 0)
    
    if (required_level == 0 or required_qual in ["none", "high school"]) and candidate_level > 0:
        return 1.0
    if required_level == 0 and candidate_level == 0:
        return 1.0
    if candidate_level >= required_level:
        return 1.0
    elif required_level > 0:
        return candidate_level / required_level
    else:
        return 0.0

def calculate_overall_score(resume, job_description):
    skill_weight = 0.5
    experience_weight = 0.3
    qualification_weight = 0.2
    
    total_weight = skill_weight + experience_weight + qualification_weight
    if total_weight != 1.0:
        skill_weight /= total_weight
        experience_weight /= total_weight
        qualification_weight /= total_weight
    
    skill_score = match_skills(resume, job_description)
    experience_score = match_experience(resume, job_description)
    qualification_score = match_qualification(resume, job_description)
    
    overall_score = (
        skill_score * skill_weight +
        experience_score * experience_weight +
        qualification_score * qualification_weight
    )
    return overall_score, skill_score, experience_score, qualification_score

def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

def extract_skills_from_text(text):
    """Extract skills from resume text using keyword matching"""
    # Common skills database
    skill_keywords = {
        "Programming": ["python", "java", "javascript", "c++", "c#", "ruby", "php", "swift", "kotlin", "go", "rust"],
        "Web Dev": ["html", "css", "react", "angular", "vue", "node.js", "django", "flask", "spring", "express"],
        "Databases": ["sql", "mysql", "postgresql", "mongodb", "redis", "oracle", "sqlite"],
        "Cloud/DevOps": ["aws", "azure", "google cloud", "docker", "kubernetes", "jenkins", "terraform", "ansible"],
        "Data Science": ["pandas", "numpy", "tensorflow", "pytorch", "scikit-learn", "r", "tableau", "power bi"],
        "Tools": ["git", "github", "gitlab", "jira", "confluence", "slack", "trello", "figma", "photoshop"]
    }
    
    text_lower = text.lower()
    detected_skills = []
    
    # Check for each skill
    for category, skills in skill_keywords.items():
        for skill in skills:
            if skill in text_lower:
                detected_skills.append(skill)
    
    return list(set(detected_skills))  # Remove duplicates

# Streamlit UI
st.set_page_config(page_title="Resume Matcher with PDF Parser", page_icon="📄", layout="wide")
st.title("📄 Resume Matcher with PDF Parser")
st.markdown("---")

# Check for PDF support
if not PDF_SUPPORT:
    st.warning("⚠️ **PDF parsing is disabled.** To enable PDF upload, add `PyPDF2` to requirements.txt and redeploy.")
    st.code("Add this to requirements.txt: PyPDF2==3.0.1")

# Create two columns
col1, col2 = st.columns(2)

with col1:
    st.header("Job Description")
    job_title = st.text_input("Job Title", "Software Engineer")
    
    skills_input = st.text_area("Required Skills (comma-separated)", "Python, Java, SQL, Django")
    required_skills = [skill.strip() for skill in skills_input.split(",")]
    
    required_exp = st.slider("Required Experience (years)", 0, 10, 3)
    
    qualification_options = ["none", "high school", "associate's degree", "bachelor's degree", "master's degree", "phd"]
    required_qual = st.selectbox("Required Qualification", qualification_options, index=3)
    
    job = JobDescription(job_title, required_skills, required_exp, required_qual)

with col2:
    st.header("Candidate Resume")
    
    # PDF Upload Section
    st.subheader("📁 Upload PDF Resume (Optional)")
    pdf_file = st.file_uploader("Choose a PDF file", type=['pdf'], label_visibility="collapsed")
    
    if pdf_file and PDF_SUPPORT:
        with st.spinner("Extracting text from PDF..."):
            pdf_text = extract_text_from_pdf(pdf_file)
            
            if pdf_text:
                st.success("✅ PDF processed successfully!")
                
                # Extract skills automatically
                auto_skills = extract_skills_from_text(pdf_text)
                
                # Display extracted text preview
                with st.expander("View extracted text from PDF"):
                    st.text(pdf_text[:1000] + "..." if len(pdf_text) > 1000 else pdf_text)
                
                if auto_skills:
                    st.info(f"🔍 **Auto-detected skills:** {', '.join(auto_skills)}")
                    
                    # Use auto-detected skills as default
                    skills_default = ", ".join(auto_skills)
                    candidate_name_default = "Extracted from PDF"
                    
                    # Try to extract name (simple heuristic)
                    lines = pdf_text.split('\n')
                    if lines:
                        candidate_name_default = lines[0][:50]  # First line as name
                    
                else:
                    skills_default = "Python, SQL, C++, Django"
                    candidate_name_default = "Candidate from PDF"
                    st.warning("No skills detected automatically. Please enter manually.")
            else:
                skills_default = "Python, SQL, C++, Django"
                candidate_name_default = "Candidate"
                st.error("Could not extract text from PDF. Please enter details manually.")
    else:
        skills_default = "Python, SQL, C++, Django"
        candidate_name_default = "Alice Smith"
    
    # Manual input fields (will be auto-filled if PDF uploaded)
    candidate_name = st.text_input("Candidate Name", candidate_name_default)
    
    candidate_skills_input = st.text_area("Candidate Skills (comma-separated)", skills_default)
    candidate_skills = [skill.strip() for skill in candidate_skills_input.split(",")]
    
    candidate_exp = st.slider("Candidate Experience (years)", 0, 15, 4)
    
    candidate_qual = st.selectbox("Candidate Qualification", qualification_options, index=4)
    
    resume = Resume(candidate_name, candidate_skills, candidate_exp, candidate_qual)

st.markdown("---")
st.header("📊 Match Results")

if st.button("Calculate Match Score", type="primary"):
    overall, skill_score, exp_score, qual_score = calculate_overall_score(resume, job)
    
    # Display scores
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Skill Match", f"{skill_score:.2f}")
    with col2:
        st.metric("Experience Match", f"{exp_score:.2f}")
    with col3:
        st.metric("Qualification Match", f"{qual_score:.2f}")
    with col4:
        st.metric("Overall Match", f"{overall:.2f}", f"{(overall*100):.0f}%")
    
    # Progress bars
    st.subheader("Detailed Breakdown")
    st.progress(skill_score, text=f"Skills: {skill_score:.1%}")
    st.progress(exp_score, text=f"Experience: {exp_score:.1%}")
    st.progress(qual_score, text=f"Qualification: {qual_score:.1%}")
    
    # Matched skills
    matched_skills = set([s.lower() for s in resume.skills]).intersection(set([s.lower() for s in job.required_skills]))
    missing_skills = set([s.lower() for s in job.required_skills]).difference(set([s.lower() for s in resume.skills]))
    
    if matched_skills:
        st.success(f"✅ **Matched Skills:** {', '.join(matched_skills)}")
    if missing_skills:
        st.warning(f"⚠️ **Missing Skills:** {', '.join(missing_skills)}")

# Instructions for PDF support
st.markdown("---")
with st.expander("ℹ️ How to enable PDF parsing"):
    st.markdown("""
    **To enable PDF upload feature:**
    
    1. **Update requirements.txt** with:
    ```
    streamlit==1.28.0
    PyPDF2==3.0.1
    ```
    
    2. **Redeploy on Streamlit Cloud:**
       - Go to [share.streamlit.io](https://share.streamlit.io)
       - Select your app
       - Click "⋮" → "Redeploy"
    
    3. **Wait 1-2 minutes** for updates
    
    **Note:** PDF parsing works best with text-based PDFs (not scanned images).
    """)

# Footer
st.markdown("---")
st.caption("Resume Matcher with PDF Parser | Deployed on Streamlit Cloud")