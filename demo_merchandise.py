import gradio as gr
import pandas as pd
import random
import os
import base64

import re

# --- Constants & Configuration ---
LOGO_PATH = "/root/health_week_demo/hcw_demo/deep_logo.png"
BANNER_IMAGE_PATH = "/root/health_week_demo/hcw_demo/hcw_banner.png"
### --- MODIFIED --- ###
# Corrected the file path to use forward slashes.
WELCOME_BANNER_PATH = "/root/health_week_demo/hcw_demo/prize_banner.png"
QUIZ_FILE_PATH = "/root/health_week_demo/hcw_demo/test_bank_200.jsonl"
CHOICES = ["A", "B", "C", "D"]
NUM_QUESTIONS = 10

# --- Color Palette ---
COLOR_BLUE_LIGHTEST = "#00aeef"
COLOR_BLUE_BRIGHT = "#00a1e4"
COLOR_BLUE_MID_2 = "#007dc5"
COLOR_BLUE_DARK = "#006cb7"
COLOR_BLUE_DARKEST = "#005baa"

# --- Terms and Conditions Text ---
TERMS_AND_CONDITIONS_TEXT = """
## Terms and Conditions for the AI Quiz Challenge
###### **1. Eligibility:** This quiz is open to all attendees of the event.
###### **2. How to Enter:** To enter, complete the registration form accurately and answer all 15 questions.
###### **3. Prize:** The prize is a Microsoft Surface Tablet, non-transferable with no cash alternative. The winner will be drawn randomly from all eligible entries after the event.
###### **4. Data Privacy:** By participating, you agree to the collection of your personal data for quiz administration and winner notification.
###### **5. General Conditions:** The organizers' decision is final. By ticking the box, you agree to these terms.
"""

# --- Utility Functions & HTML Generation ---
def convert_image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"Warning: Image not found at {image_path}.")
        return None

logo_data = convert_image_to_base64(LOGO_PATH)
LOGO_HTML = f'<div id="logo-container"><img id="logo-image" src="data:image/png;base64,{logo_data}" alt="Deep by POST Group Logo"></div>' if logo_data else '<div id="logo-container"><div id="logo-fallback">Deep by POST Group</div></div>'

banner_data = convert_image_to_base64(BANNER_IMAGE_PATH)
BANNER_HTML = f'<div id="banner-container"><img id="banner-image" src="data:image/png;base64,{banner_data}" alt="AI Quiz Challenge Banner"></div>' if banner_data else '<h1>🧠 AI Quiz Challenge</h1>'

welcome_banner_data = convert_image_to_base64(WELCOME_BANNER_PATH)
WELCOME_BANNER_HTML = f'<div id="welcome-banner-container"><img id="welcome-banner-image" src="data:image/png;base64,{welcome_banner_data}" alt="Welcome to the AI Challenge"></div>' if welcome_banner_data else ''


os.environ['HTTP_PROXY'], os.environ['HTTPS_PROXY'] = '', ''

def is_valid_email(email):
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email or "") is not None

def load_questions_from_jsonl(file_path=QUIZ_FILE_PATH):
    try:
        return pd.read_json(file_path, lines=True).to_dict(orient='records')
    except (FileNotFoundError, ValueError) as e:
        print(f"Error loading questions: {e}")
        return []

full_question_bank = load_questions_from_jsonl(QUIZ_FILE_PATH)

def save_results_to_csv(name, email, company, job_title, user_score, ai_score, ai_model):
    new_data = pd.DataFrame([[name, email, company, job_title, user_score, ai_score, ai_model]],
                            columns=['Name', 'Email', 'Company', 'JobTitle', 'UserScore', 'AIScore', 'AIModel'])
    new_data.to_csv('quiz_results.csv', mode='a', header=not os.path.isfile('quiz_results.csv'), index=False)

# --- Gradio Core Functions ---
def show_login_form():
    return {welcome_row: gr.update(visible=False), login_row: gr.update(visible=True)}

def start_quiz(name, email, company, job_title, ai_model, terms_agreed):
    error_messages = []
    if not name.strip(): error_messages.append("Name is required.")
    if not email.strip(): error_messages.append("Email is required.")
    elif not is_valid_email(email): error_messages.append("Please enter a valid email address.")
    if not company.strip(): error_messages.append("Company Name is required.")
    if not job_title.strip(): error_messages.append("Job Title is required.")
    if not terms_agreed: error_messages.append("You must agree to the terms and conditions.")

    if error_messages:
        return {
            login_row: gr.update(visible=True),
            start_error_msg: gr.update(value="<br>".join(error_messages), visible=True),
            quiz_row: gr.update(visible=False), score_display_row: gr.update(visible=False),
            main_banner_row: gr.update(visible=False) # Keep banner hidden on error
        }
    if not full_question_bank:
        return {
            login_row: gr.update(visible=True),
            start_error_msg: gr.update(value="Error: No questions loaded.", visible=True),
            quiz_row: gr.update(visible=False), score_display_row: gr.update(visible=False),
            main_banner_row: gr.update(visible=False) # Keep banner hidden on error
        }

    quiz_questions = random.sample(full_question_bank, min(NUM_QUESTIONS, len(full_question_bank)))
    first_question = quiz_questions[0]
    options = [first_question['opa'], first_question['opb'], first_question['opc'], first_question['opd']]

    percentage = (1 / len(quiz_questions)) * 100
    question_title_html = f'''
        <div class="progress-container">
            <div class="progress-bar-fill" style="width: {percentage}%;"></div>
            <div class="progress-text">Question 1 / {len(quiz_questions)}</div>
        </div>
    '''
    question_display_html = f'<div id="question-card"><span>{first_question["question"]}</span></div>'

    return {
        login_row: gr.update(visible=False), score_display_row: gr.update(visible=True),
        start_error_msg: gr.update(value="", visible=False), quiz_row: gr.update(visible=True),
        question_title: gr.update(value=question_title_html),
        question_display: gr.update(value=question_display_html),
        choice_a_button: gr.update(value=options[0], visible=True), choice_b_button: gr.update(value=options[1], visible=True),
        choice_c_button: gr.update(value=options[2], visible=True), choice_d_button: gr.update(value=options[3], visible=True),
        question_state: quiz_questions, user_score_state: 0, ai_score_state: 0, q_index_state: 0,
        user_name_state: name, user_email_state: email, company_name_state: company, job_title_state: job_title,
        ai_model_state: ai_model,
        user_score_display: gr.update(value='<div class="score-card" id="user-score-card">Human<br><span class="score-value">0</span></div>'),
        ai_score_display: gr.update(value='<div class="score-card" id="ai-score-card">AI<br><span class="score-value">0</span></div>'),
        reset_button: gr.update(visible=False),
        main_banner_row: gr.update(visible=True), # Show main banner when quiz starts
    }

def process_answer(user_answer, q_index, user_score, ai_score, questions, name, email, company, job_title, ai_model):
    current_question, num_questions = questions[q_index], len(questions)
    options = [current_question['opa'], current_question['opb'], current_question['opc'], current_question['opd']]
    correct_answer_index, ai_answer_index = current_question['cop'], current_question.get(ai_model, 0)

    try:
        user_choice_index = options.index(user_answer)
        user_correct = (user_choice_index == correct_answer_index)
        if user_correct: user_score += 1
    except ValueError:
        user_choice_index, user_correct = -1, False

    if ai_answer_index == correct_answer_index: ai_score += 1

    feedback = (f"Your answer: **{CHOICES[user_choice_index] if user_choice_index != -1 else 'N/A'}** ({'✅ Correct' if user_correct else '❌ Incorrect'}).\n"
                f"AI's answer: **{CHOICES[ai_answer_index]}** ({'✅ Correct' if ai_answer_index == correct_answer_index else '❌ Incorrect'}).\n"
                f"The correct answer was: **{CHOICES[correct_answer_index]}**.")

    q_index += 1
    user_score_html = f'<div class="score-card" id="user-score-card">Human<br><span class="score-value">{user_score}</span></div>'
    ai_score_html = f'<div class="score-card" id="ai-score-card">AI<br><span class="score-value">{ai_score}</span></div>'

    if q_index >= num_questions:
        save_results_to_csv(name, email, company, job_title, user_score, ai_score, ai_model)
        winner_text = f"🤝 It's a draw! {user_score} to {ai_score}."
        if user_score > ai_score: winner_text = f"🎉 Congratulations, {name}! You won {user_score} to {ai_score}."
        elif ai_score > user_score: winner_text = f"🤖 The AI won {ai_score} to {user_score}. Better luck next time!"
        winner_html = f'<div id="final-result-banner">{winner_text}</div>'
        return {
            quiz_row: gr.update(visible=False), feedback_row: gr.update(visible=False), end_row: gr.update(visible=True),
            final_result_text: gr.update(value=winner_html), user_score_display: user_score_html, ai_score_display: ai_score_html,
            choice_a_button: gr.update(visible=False), choice_b_button: gr.update(visible=False),
            choice_c_button: gr.update(visible=False), choice_d_button: gr.update(visible=False),
            reset_button: gr.update(visible=True)
        }
    else:
        next_question = questions[q_index]
        next_options = [next_question['opa'], next_question['opb'], next_question['opc'], next_question['opd']]
        percentage = ((q_index + 1) / num_questions) * 100
        question_title_html = f'''
            <div class="progress-container">
                <div class="progress-bar-fill" style="width: {percentage}%;"></div>
                <div class="progress-text">Question {q_index + 1} / {num_questions}</div>
            </div>
        '''
        question_display_html = f'<div id="question-card"><span>{next_question["question"]}</span></div>'
        return {
            q_index_state: q_index, user_score_state: user_score, ai_score_state: ai_score,
            question_title: gr.update(value=question_title_html), question_display: gr.update(value=question_display_html),
            choice_a_button: gr.update(value=next_options[0]), choice_b_button: gr.update(value=next_options[1]),
            choice_c_button: gr.update(value=next_options[2]), choice_d_button: gr.update(value=next_options[3]),
            feedback_row: gr.update(visible=True), feedback_text: gr.update(value=feedback),
            user_score_display: user_score_html, ai_score_display: ai_score_html,
            quiz_row: gr.update(visible=True), end_row: gr.update(visible=False),
        }

def reset_quiz():
    return {
        welcome_row: gr.update(visible=True), login_row: gr.update(visible=False), score_display_row: gr.update(visible=False),
        name_box: gr.update(value=""), email_box: gr.update(value=""), company_box: gr.update(value=""), job_title_box: gr.update(value=""),
        ai_model_dropdown: gr.update(value="gpt-4.1-nano"),
        terms_checkbox: gr.update(value=False),
        start_error_msg: gr.update(value="", visible=False), quiz_row: gr.update(visible=False),
        feedback_row: gr.update(visible=False), end_row: gr.update(visible=False),
        user_score_display: gr.update(value='<div class="score-card" id="user-score-card">Human<br><span class="score-value">0</span></div>'),
        ai_score_display: gr.update(value='<div class="score-card" id="ai-score-card">AI<br><span class="score-value">0</span></div>'),
        choice_a_button: gr.update(visible=False), choice_b_button: gr.update(visible=False),
        choice_c_button: gr.update(visible=False), choice_d_button: gr.update(visible=False),
        feedback_text: gr.update(value=""), reset_button: gr.update(visible=False),
        q_index_state: 0, user_score_state: 0, ai_score_state: 0, question_state: [],
        user_name_state: "", user_email_state: "", company_name_state: "", job_title_state: "",
        ai_model_state: "gpt-4.1-nano",
        main_banner_row: gr.update(visible=False), # Hide main banner on reset
    }

# --- Gradio UI Layout & Custom CSS ---
custom_css = f"""
:root {{ --body-background-fill: #f0f4f8; }}
body {{ background-color: var(--body-background-fill); font-family: 'Inter', sans-serif; }}
.gradio-container {{ max-width: 900px !important; margin: auto; padding: 2rem; background-color: #ffffff; border-radius: 16px; box-shadow: 0 8px 30px rgba(0,0,0,0.12); }}
h1, .markdown h1 {{ text-align: center; color: {COLOR_BLUE_DARK}; font-weight: 800; font-size: 2.8rem; margin-bottom: 1rem; }}
#logo-container {{ text-align: center; margin-bottom: 1rem; }}
#logo-image {{ max-width: 250px; max-height: 100px; }}
.prize-text {{ color: #f1c40f; font-weight: 700; }}
#tc-popup-row {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0, 0, 0, 0.6); z-index: 1000; display: flex; align-items: center; justify-content: center; }}
#tc-popup-group {{ background: white; padding: 2rem; border-radius: 12px; max-width: 700px; box-shadow: 0 5px 25px rgba(0,0,0,0.3); }}

#banner-container {{
    text-align: center;
    margin: 0.5rem 0 1.5rem 0;
}}
#banner-image {{
    width: 100%;
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}}

#welcome-banner-container {{
    text-align: center;
    margin-bottom: 1.5rem;
}}
#welcome-banner-image {{
    width: 100%;
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}}

/* --- Animated Progress Bar --- */
.progress-container {{
    position: relative; height: 50px; background-color: #e9ecef;
    border-radius: 25px; margin: 1rem auto 2rem auto; overflow: hidden;
    box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
}}
.progress-bar-fill {{
    height: 100%;
    background: linear-gradient(45deg, {COLOR_BLUE_BRIGHT}, {COLOR_BLUE_DARK});
    border-radius: 25px;
    transition: width 0.5s ease-in-out;
}}
.progress-text {{
    position: absolute; top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    color: white; font-size: 1.4rem; font-weight: 600;
    text-shadow: 1px 1px 3px rgba(0,0,0,0.5);
    white-space: nowrap;
}}

/* --- Professional Question Card Design --- */
#question-card {{
    display: flex; align-items: center; justify-content: center;
    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
    border: 1px solid #dee2e6;
    border-top: 4px solid {COLOR_BLUE_BRIGHT};
    border-radius: 16px;
    padding: 2.5rem;
    margin: 1rem 0;
    min-height: 200px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    transition: all 0.3s ease;
}}
#question-card span {{
    font-size: 1.8rem;
    font-weight: 600;
    text-align: center;
    line-height: 1.5;
    color: {COLOR_BLUE_DARK};
}}

/* --- BUTTON STYLES --- */
.gr-button {{ border-radius: 8px !important; font-weight: 600 !important; transition: all 0.2s ease !important; }}
.primary {{ background: {COLOR_BLUE_BRIGHT} !important; color: white !important; border: none !important; }}
.primary:hover {{ background: {COLOR_BLUE_DARKEST} !important; transform: translateY(-2px); box-shadow: 0 4px 10px rgba(0,0,0,0.15); }}
.secondary {{ background: #ffffff !important; border: 2px solid {COLOR_BLUE_DARK} !important; color: {COLOR_BLUE_DARK} !important; }}
.secondary:hover {{ background: {COLOR_BLUE_DARK} !important; color: white !important; transform: translateY(-2px); }}
.choice-button {{ background: #ffffff !important; border: 2px solid {COLOR_BLUE_DARK} !important; color: {COLOR_BLUE_DARK} !important; font-size: 1.1rem !important; min-height: 60px; }}
.choice-button:hover {{ background: {COLOR_BLUE_DARKEST} !important; color: white !important; border-color: {COLOR_BLUE_DARKEST} !important; transform: translateY(-2px); box-shadow: 0 4px 10px rgba(0,0,0,0.1); }}

.score-card {{ text-align: center; font-size: 1.5rem; font-weight: 700; color: #ffffff; padding: 1rem; border-radius: 12px; line-height: 1.4; }}
#user-score-card {{ background-color: {COLOR_BLUE_MID_2}; }}
#ai-score-card {{ background-color: {COLOR_BLUE_DARK}; }}
.score-value {{ font-size: 3.5rem; color: #ffffff; font-weight: 700; display: block; line-height: 1; }}

#error-msg .markdown {{ color: #e74c3c; font-weight: bold; text-align: center; }}

@keyframes pulse-glow {{ 0%, 100% {{ box-shadow: 0 0 5px rgba(0, 174, 239, 0.3); }} 50% {{ box-shadow: 0 0 25px rgba(0, 174, 239, 0.7); }} }}
#final-result-banner {{
    font-size: 2.5rem; font-weight: 700; text-align: center; padding: 2.5rem; margin: 1rem 0;
    border: 2px solid {COLOR_BLUE_LIGHTEST}; border-radius: 16px;
    background: linear-gradient(45deg, {COLOR_BLUE_BRIGHT}, {COLOR_BLUE_DARK});
    -webkit-background-clip: text; background-clip: text; color: transparent;
    animation: pulse-glow 3s infinite ease-in-out;
}}
"""

with gr.Blocks(css=custom_css, title="AI Quiz Challenge") as demo:
    state_vars = [gr.State(v) for v in [[], 0, 0, 0, "", "", "", "", "gpt-4.1-nano"]]
    question_state, user_score_state, ai_score_state, q_index_state, user_name_state, user_email_state, company_name_state, job_title_state, ai_model_state = state_vars

    gr.HTML(LOGO_HTML)
    
    ### --- MODIFIED --- ###
    # 1. Wrap the main banner in a Row to control its visibility. Start with visible=False.
    with gr.Row(visible=False) as main_banner_row:
        gr.HTML(BANNER_HTML)

    with gr.Row(visible=False) as score_display_row:
        user_score_display = gr.HTML(value='<div class="score-card" id="user-score-card">Human<br><span class="score-value">0</span></div>')
        ai_score_display = gr.HTML(value='<div class="score-card" id="ai-score-card">AI<br><span class="score-value">0</span></div>')

    with gr.Row(visible=True, variant="panel") as welcome_row:
        with gr.Column():
            # Only the welcome banner and the start button are here.
            gr.HTML(WELCOME_BANNER_HTML)
            show_login_button = gr.Button("Start Quiz 🚀", elem_classes="primary")

    with gr.Row(visible=False, variant="panel") as login_row:
        with gr.Column(scale=1):
            name_box = gr.Textbox(label="Your Name", placeholder="Enter your full name...")
            email_box = gr.Textbox(label="Email", placeholder="Enter your work email...")
            company_box = gr.Textbox(label="Company Name", placeholder="Enter your company name...")
            job_title_box = gr.Textbox(label="Job Title", placeholder="Enter your job title...")
            
            ai_model_dropdown = gr.Dropdown(
                label="Choose AI Difficulty",
                choices=[("Easy (gpt-4.1-nano)", "gpt-4.1-nano"), ("Medium (gpt-4.1)", "gpt-4.1"), ("Hard (gpt-5)", "gpt-5")],
                value="gpt-4.1-nano"
            )
            
            with gr.Row():
                terms_checkbox = gr.Checkbox(label="I agree to the terms and conditions.", value=False)
                view_tc_button = gr.Button("View T&C", elem_classes="secondary", size="sm")
            start_button = gr.Button("Confirm Details & Begin 🚀", elem_classes="primary")
            start_error_msg = gr.Markdown(visible=False, value="", elem_id="error-msg")

    with gr.Row(visible=False, elem_id="tc-popup-row") as tc_popup_row:
        with gr.Group(elem_id="tc-popup-group"):
            gr.Markdown(TERMS_AND_CONDITIONS_TEXT)
            close_tc_button = gr.Button("Close", elem_classes="secondary")

    with gr.Row(visible=False, variant="panel") as quiz_row:
        with gr.Column(scale=1):
            question_title = gr.HTML()
            question_display = gr.HTML()
            with gr.Row():
                choice_a_button, choice_b_button = [gr.Button(visible=False, elem_classes="choice-button") for _ in range(2)]
            with gr.Row():
                choice_c_button, choice_d_button = [gr.Button(visible=False, elem_classes="choice-button") for _ in range(2)]

    with gr.Row(visible=False, variant="panel", elem_id="feedback-row") as feedback_row:
        feedback_text = gr.Markdown("")

    with gr.Row(visible=False, variant="panel", elem_id="end-row") as end_row:
        with gr.Column(scale=1):
            final_result_text = gr.HTML()
            reset_button = gr.Button("Reset Quiz", elem_classes="secondary", visible=False)

    # --- Logic Bindings ---
    show_login_button.click(fn=show_login_form, outputs=[welcome_row, login_row])
    view_tc_button.click(lambda: gr.update(visible=True), outputs=[tc_popup_row])
    close_tc_button.click(lambda: gr.update(visible=False), outputs=[tc_popup_row])

    start_inputs = [name_box, email_box, company_box, job_title_box, ai_model_dropdown, terms_checkbox]
    ### --- MODIFIED --- ###
    # 2. Add main_banner_row to the outputs of the start button.
    start_outputs = [login_row, score_display_row, start_error_msg, quiz_row, question_title, question_display,
                     choice_a_button, choice_b_button, choice_c_button, choice_d_button,
                     *state_vars, user_score_display, ai_score_display, reset_button, main_banner_row]
    start_button.click(fn=start_quiz, inputs=start_inputs, outputs=start_outputs)

    answer_inputs = [q_index_state, user_score_state, ai_score_state, question_state, user_name_state,
                     user_email_state, company_name_state, job_title_state, ai_model_state]
    answer_outputs = [q_index_state, user_score_state, ai_score_state, question_title, question_display,
                      choice_a_button, choice_b_button, choice_c_button, choice_d_button, feedback_row,
                      feedback_text, user_score_display, ai_score_display, quiz_row, end_row, final_result_text, reset_button]

    for btn in [choice_a_button, choice_b_button, choice_c_button, choice_d_button]:
        btn.click(fn=process_answer, inputs=[btn] + answer_inputs, outputs=answer_outputs)

    ### --- MODIFIED --- ###
    # 3. Add main_banner_row to the reset logic.
    reset_outputs_map = {
        welcome_row: gr.update(visible=True), login_row: gr.update(visible=False),
        score_display_row: gr.update(visible=False), name_box: gr.update(value=""), email_box: gr.update(value=""),
        company_box: gr.update(value=""), job_title_box: gr.update(value=""), ai_model_dropdown: gr.update(value="gpt-4.1-nano"),
        terms_checkbox: gr.update(value=False), start_error_msg: gr.update(value="", visible=False),
        quiz_row: gr.update(visible=False), feedback_row: gr.update(visible=False), end_row: gr.update(visible=False),
        user_score_display: gr.update(value='<div class="score-card" id="user-score-card">Human<br><span class="score-value">0</span></div>'),
        ai_score_display: gr.update(value='<div class="score-card" id="ai-score-card">AI<br><span class="score-value">0</span></div>'),
        choice_a_button: gr.update(visible=False), choice_b_button: gr.update(visible=False),
        choice_c_button: gr.update(visible=False), choice_d_button: gr.update(visible=False),
        feedback_text: gr.update(value=""), reset_button: gr.update(visible=False),
        q_index_state: 0, user_score_state: 0, ai_score_state: 0, question_state: [],
        user_name_state: "", user_email_state: "", company_name_state: "", job_title_state: "",
        ai_model_state: "gpt-4.1-nano",
        main_banner_row: gr.update(visible=False)
    }
    reset_button.click(lambda: list(reset_outputs_map.values()), outputs=list(reset_outputs_map.keys()))

if __name__ == "__main__":

    demo.launch(share=True)