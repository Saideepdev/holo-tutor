import os
from flask import Flask, request, jsonify
from simple_salesforce import Salesforce
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Initialize Flask
app = Flask(__name__)

# Salesforce Login
try:
    sf = Salesforce(
        username=os.getenv("SF_USERNAME"),
        password=os.getenv("SF_PASSWORD"),
        security_token=os.getenv("SF_SECURITY_TOKEN"),
        domain=os.getenv("SF_DOMAIN")
    )
except Exception as e:
    print("Salesforce login error:", str(e))
    sf = None

# Endpoint for student question
@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    question = data.get("question")
    student_id = data.get("student_id")
    lesson_id = data.get("lesson_id")

    if not question or not student_id or not lesson_id:
        return jsonify({"error": "Missing one or more required fields"}), 400

    # Call Ollama locally
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
               "model": "gemma:2b",
                "prompt": question,
                "stream": False
            }
        )
        result = response.json()
        answer = result.get("response", "").strip()
    except Exception as e:
        return jsonify({"error": f"Ollama error: {str(e)}"}), 500

    # Log into Salesforce
    try:
        sf.LearningActivity__c.create({
            "Student__c": student_id,
            "Lesson__c": lesson_id,
            "Question__c": question,
            "Answer__c": answer
        })
    except Exception as e:
        return jsonify({"error": f"Salesforce logging error: {str(e)}"}), 500

    return jsonify({"answer": answer})

if __name__ == "__main__":
   app.run(host='0.0.0.0', port=10000)

