# 🌍 TravoMate – AI Travel Planning Chatbot

TravoMate is an AI-powered travel planning chatbot that generates personalized itineraries and budget-friendly travel plans through natural language interaction. It simplifies trip planning by converting user queries into structured travel suggestions using Large Language Models (LLMs).

---
**[Live Demo](https://travomate-travel-planning-chatbot-v2.streamlit.app/)**
---
## 🚀 Features
- Conversational travel planning  
- Personalized itineraries based on user input  
- Budget estimation with visual breakdown (charts)  
- Interactive and user-friendly web interface  
- Session-based memory for refining plans  

---

## 🛠️ Tech Stack
- **Programming Language:** Python  
- **Frontend:** Streamlit  
- **AI Engine:** Large Language Model (LLM via API)  
- **Visualization:** Plotly  
- **Environment Management:** python-dotenv  

---

## ⚙️ How It Works
1. User enters a travel query (destination, budget, duration, etc.).  
2. The chatbot processes the input using an LLM.  
3. A personalized travel plan and budget breakdown are generated.  
4. Results are displayed with interactive charts.  
5. The user can refine the plan through follow-up queries.

---

## 📂 Project Structure
- **app.py** (Main Streamlit application)
- **openrouter_chat.py** (LLM API integration)
- **prompt_template.py** (System prompt for chatbot)
- **requirements.txt**   (Project dependencies)
- **.env**  (API key configuration)


---

## ▶️ Setup & Run Locally

###  Clone the repository and run
```bash
git clone https://github.com/devvsingh/TravoMate-Travel-planning-chatbot.git
cd travomate

pip install -r requirements.txt

streamlit run app.py

