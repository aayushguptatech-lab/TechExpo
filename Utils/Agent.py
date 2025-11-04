from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq


class Agent:
    def __init__(self, medical_report = None, role = None, extra_info = None):
        self.medical_report = medical_report
        self.role = role
        self.extra_info = extra_info
        self.prompt_template = self.create_prompt_template()

        self.model = ChatGroq(
            api_key = "API_KEY",
            model = "llama-3.3-70b-versatile",
            temperature=0.0
        )
    
    def create_prompt_template(self):
        if self.role == "MultidisciplinaryTeam":
            templates = f"""Act as a multidisciplinary medical team analyzing a full health test report.
            For each test in the report:
            1. Mention the **Test Name**
            2. Give its **Normal Range**
            3. Mention the **Reported Value**
            4. Add an **Interpretation** — whether it’s LOW, NORMAL, or HIGH.
            5. Write a short **Explanation** in plain language.
            6. Add a **Suggestion** — practical advice to help bring it back to the normal range.
            Example Output:
            - Test: Hemoglobin  
            • Normal Range: 13–17 g/dL  
            • Reported Value: 10 g/dL  
            • Interpretation: LOW  
            • Explanation: Indicates anemia or iron deficiency.  
            • Suggestion: Eat iron-rich foods like spinach, red meat, or supplements (under guidance).
            Now analyze the following report and respond in the same format:

                Cardiologist Report: {self.extra_info.get('cardiologist_report', '')}
                Psychologist Report: {self.extra_info.get('psychologist_report', '')}
                Pulmonologist Report: {self.extra_info.get('pulmonologist_report', '')}"""
            return PromptTemplate.from_template(templates)

        else:
            templates = {
                "Cardiologist": """
                   Act as a professional cardiologist analyzing a patient's medical test report.
                   For every heart-related test you find (e.g., cholesterol, LDL, HDL, triglycerides, ECG, blood pressure, etc.), give a detailed but simple summary.
                   For each test, include:
                   1. **Test Name**
                   2. **Normal Range**
                   3. **Reported Value**
                   4. **Interpretation** — Clearly mention if the result is LOW, NORMAL, or HIGH.
                   5. **Explanation** — Describe what this could mean for heart health.
                   6. **Suggestion** — Suggest what the person can do (diet, lifestyle, exercise) to improve it.Example Output:
                   - Test: Cholesterol  
                   • Normal Range: 125–200 mg/dL  
                   • Reported Value: 240 mg/dL  
                   • Interpretation: HIGH  
                   • Explanation: Indicates elevated cholesterol, which can increase the risk of heart disease.  
                   • Suggestion: Avoid fried food, increase fiber intake, and exercise regularly.
                   Now, analyze this report and return structured, human-readable output:
                    Medical Report: {medical_report}
                """,
                "Psychologist": """
                   Act as a professional psychologist analyzing a patient's medical test report.
                   Your goal is to interpret the report in terms of **mental health, mood, and emotional well-being**. 
                   Focus on biomarkers that may be linked to stress, depression, anxiety, sleep disturbance, or cognitive function 
                   (e.g., cortisol, thyroid levels, vitamin B12, vitamin D, blood sugar, etc.).
                   For each relevant test found:
                   1. **Test Name**
                   2. **Normal Range**
                   3. **Reported Value**
                   4. **Interpretation** — LOW / NORMAL / HIGH
                   5. **Explanation** — What this result may indicate about the person's mental or emotional health.
                   6. **Suggestion** — Simple, science-backed lifestyle, diet, or behavioral tips to improve or maintain balance.
                   Example Output:
                   - Test: Cortisol  
                   • Normal Range: 6–18 µg/dL (morning)  
                   • Reported Value: 22 µg/dL  
                   • Interpretation: HIGH  
                   • Explanation: Suggests elevated stress levels that might be impacting mood or sleep.  
                   • Suggestion: Try mindfulness, deep breathing, and balanced sleep patterns.
                   Now, analyze this medical report in the same structured format:
                    Patient's Report: {medical_report}
                """,
                "Pulmonologist": """
                    Act as an expert pulmonologist analyzing a patient's test report.
                    For each lung-related test (e.g., oxygen saturation, FEV1, FVC, spirometry, etc.), provide a detailed summary.
                    For each test, include:
                    1. **Test Name**
                    2. **Normal Range**
                    3. **Reported Value**
                    4. **Interpretation** — LOW / NORMAL / HIGH
                    5. **Explanation** — Describe what this means for respiratory health.
                    6. **Suggestion** — Steps to improve or maintain lung function.
                    Example Output:
                    Test: Oxygen Saturation  
                    • Normal Range: 95–100%  
                    • Reported Value: 89%  
                    • Interpretation: LOW  
                    • Explanation: May indicate mild respiratory distress or lung inefficiency.  
                    • Suggestion: Practice deep breathing, consult a doctor if persistent.
                    Now analyze this report and present it in the same structured format:               
                    
                    Patient's Report: {medical_report}"""
            }

            selected_templates = templates[self.role]
            return PromptTemplate.from_template(selected_templates)
        
    def run(self):
        print(f"{self.role} is running.....")
        prompt = self.prompt_template.format(medical_report=self.medical_report)

        try:
            response = self.model.invoke(prompt)
            return response.content
        except Exception as e:
            print(f"Error Occurred: ", e)
            return None
    
class Cardiologist(Agent):
    def __init__(self, medical_report):
        super().__init__(medical_report, "Cardiologist")

    
class Psychologist(Agent):
    def __init__(self, medical_report):
        super().__init__(medical_report, "Psychologist")

        
class Pulmonologist(Agent):
    def __init__(self, medical_report):
        super().__init__(medical_report, "Pulmonologist")

    
class MultidisciplinaryTeam(Agent):
    def __init__(self, cardiologist_report, psychologist_report, pulmonologist_report):
        extra_info = {
            "cardiologist_report": cardiologist_report,
            "psychologist_report": psychologist_report,
            "pulmonologist_report": pulmonologist_report
        }
        super().__init__(role="MultidisciplinaryTeam", extra_info=extra_info)

    def run(self):
        print("Multidisciplinary team is generating the final diagnosis...")
        try:
            # Use the extra_info dictionary to fill in the prompt
            prompt = self.prompt_template.format(
                cardiologist_report=self.extra_info.get("cardiologist_report", ""),
                psychologist_report=self.extra_info.get("psychologist_report", ""),
                pulmonologist_report=self.extra_info.get("pulmonologist_report", "")
            )

            response = self.model.invoke(prompt)
            if response and hasattr(response, "content"):
                print(" Final multidisciplinary diagnosis generated successfully.")
                return response.content
            else:
                print("Model returned empty response.")
                return "No diagnosis generated."
        except Exception as e:
            print("Error while generating multidisciplinary diagnosis:", e)
            return "No diagnosis generated."
