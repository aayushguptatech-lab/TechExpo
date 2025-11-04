from flask import Flask, request, render_template, redirect, url_for
from concurrent.futures import ThreadPoolExecutor, as_completed
from Utils.Agent import Cardiologist, Psychologist, Pulmonologist, MultidisciplinaryTeam
import os
from PyPDF2 import PdfReader


app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
RESULT_PATH = 'results/final_diagnosis.txt'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.dirname(RESULT_PATH), exist_ok=True)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['report']
        if file:
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)

            medical_report=""
            if file.filename.endswith('.txt'):
                with open(filepath,'r',encoding='utf-8') as f:
                    medical_report=f.read()
            elif file.filename.endswith('.pdf'):
                reader = PdfReader(filepath)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        medical_report += text

            else:
                return "Unsupported file format. Please upload a .txt or .pdf file."

            # Run individual specialists
            agents = {
                "Cardiologist": Cardiologist(medical_report),
                "Psychologist": Psychologist(medical_report),
                "Pulmonologist": Pulmonologist(medical_report)
            }

            responses = {}
            with ThreadPoolExecutor() as executor:
                futures = {executor.submit(agent.run): name for name, agent in agents.items()}
                for future in as_completed(futures):
                    agent_name = futures[future]
                    responses[agent_name] = future.result()

            # Run multidisciplinary agent
            team_agent = MultidisciplinaryTeam(
                cardiologist_report=responses["Cardiologist"],
                psychologist_report=responses["Psychologist"],
                pulmonologist_report=responses["Pulmonologist"]
            )
            final_diagnosis = team_agent.run()
            print("Team agent output:", final_diagnosis)


            # Save the diagnosis
            final_diagnosis_text = "### Final Diagnosis:\n\n" + str(final_diagnosis or "No diagnosis generated.")

            with open(RESULT_PATH, 'w') as result_file:
                result_file.write(final_diagnosis_text)

            return render_template("upload_report.html", diagnosis=final_diagnosis_text)

        return render_template("upload_report.html", error="Please upload a valid .txt file.")

    return render_template("upload_report.html")


if __name__ == '__main__':
    app.run(debug=True)
