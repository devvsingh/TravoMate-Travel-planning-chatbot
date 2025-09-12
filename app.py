# app.py
import streamlit as st
from openrouter_chat import chat_with_openrouter
from prompt_template import TRAVEL_ASSISTANT_PROMPT
import os
from dotenv import load_dotenv
import plotly.express as px
import plotly.graph_objects as go
import re
import json

load_dotenv()

# Budget extraction and visualization functions
def extract_budget_from_response(response_text, user_input=""):
    """Extract budget breakdown from AI response with improved patterns"""
    budget_data = {}
    
    # First, try to get the main budget from user input (most reliable)
    user_budget = None
    user_budget_match = re.search(r'₹\s*(\d+(?:,\d+)*)', user_input)
    if user_budget_match:
        user_budget = int(user_budget_match.group(1).replace(',', ''))
    
    # Enhanced patterns for specific category costs in response
    patterns = {
        'accommodation': [
            r'accommodation[:\s-]*₹?\s*(\d+(?:,\d+)*)',
            r'₹\s*(\d+(?:,\d+)*)\s*(?:for|per|\/)\s*accommodation',
        ],
        'transport': [
            r'transport(?:ation)?[:\s-]*₹?\s*(\d+(?:,\d+)*)',
            r'₹\s*(\d+(?:,\d+)*)\s*(?:\()?(?:bike|car|train|bus|flight)',
        ],
        'food': [
            r'food[:\s-]*₹?\s*(\d+(?:,\d+)*)',
            r'₹\s*(\d+(?:,\d+)*)\s*(?:for|per|\/)\s*food',
        ],
        'activities': [
            r'(?:sightseeing and )?activities[:\s-]*₹?\s*(\d+(?:,\d+)*)',
            r'₹\s*(\d+(?:,\d+)*)\s*(?:\()?(?:entrance|water sports|sightseeing)',
        ],
        'miscellaneous': [
            r'(?:miscellaneous|misc|other)[:\s-]*₹?\s*(\d+(?:,\d+)*)',
            r'₹\s*(\d+(?:,\d+)*)\s*(?:for|per|\/)\s*(?:misc|other)',
        ]
    }
    
    # Try to extract specific amounts from response
    response_breakdown = {}
    for category, pattern_list in patterns.items():
        for pattern in pattern_list:
            matches = re.finditer(pattern, response_text.lower())
            for match in matches:
                amount = int(match.group(1).replace(',', ''))
                # Only consider reasonable amounts (not too small)
                if amount >= 500:  # Minimum threshold
                    if category not in response_breakdown or amount > response_breakdown[category]:
                        response_breakdown[category] = amount
    
    # If we have user budget, always prioritize it
    if user_budget:
        # Check if response has specific breakdown
        if response_breakdown:
            response_total = sum(response_breakdown.values())
            
            # If response total is significantly different from user budget,
            # scale the breakdown to match user's budget
            if abs(response_total - user_budget) > user_budget * 0.1:  # More than 10% difference
                # Scale the breakdown to match user's total budget
                scale_factor = user_budget / response_total
                budget_data = {
                    category: int(amount * scale_factor) 
                    for category, amount in response_breakdown.items()
                }
                return budget_data, user_budget, "scaled"
            else:
                # Use response breakdown as-is if close to user budget
                return response_breakdown, response_total, "specific"
        else:
            # No specific breakdown found, create estimated breakdown
            budget_data = {
                'accommodation': int(user_budget * 0.35),  # 35%
                'transport': int(user_budget * 0.25),     # 25%
                'food': int(user_budget * 0.20),          # 20%
                'activities': int(user_budget * 0.15),    # 15%
                'miscellaneous': int(user_budget * 0.05)  # 5%
            }
            return budget_data, user_budget, "estimated"
    
    # If no user budget but we found specific breakdown, return it
    elif response_breakdown:
        total_found = sum(response_breakdown.values())
        return response_breakdown, total_found, "specific"
    
    return None, None, None

def create_budget_visualization(budget_data):
    """Create beautiful budget breakdown charts"""
    if not budget_data:
        return None, None
    
    categories = list(budget_data.keys())
    amounts = list(budget_data.values())
    
    # Create pie chart
    colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe']
    
    pie_fig = go.Figure(data=[go.Pie(
        labels=[cat.title() for cat in categories],
        values=amounts,
        hole=0.4,
        marker=dict(colors=colors[:len(categories)]),
        textinfo='label+percent',
        textfont=dict(color='white', size=12),
        hovertemplate='<b>%{label}</b><br>₹%{value:,}<br>%{percent}<extra></extra>'
    )])
    
    pie_fig.update_layout(
        title=dict(text="Budget Breakdown", font=dict(size=20, color='white')),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        showlegend=True,
        legend=dict(font=dict(color='white')),
        height=400
    )
    
    # Create bar chart
    bar_fig = go.Figure(data=[go.Bar(
        x=[cat.title() for cat in categories],
        y=amounts,
        marker=dict(
            color=colors[:len(categories)],
            line=dict(color='rgba(255,255,255,0.3)', width=2)
        ),
        text=[f'₹{amount:,}' for amount in amounts],
        textposition='auto',
        textfont=dict(color='white', size=12),
        hovertemplate='<b>%{x}</b><br>₹%{y:,}<extra></extra>'
    )])
    
    bar_fig.update_layout(
        title=dict(text="Category-wise Expenses", font=dict(size=20, color='white')),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(tickfont=dict(color='white'), gridcolor='rgba(255,255,255,0.2)'),
        yaxis=dict(tickfont=dict(color='white'), gridcolor='rgba(255,255,255,0.2)'),
        height=400
    )
    
    return pie_fig, bar_fig

# Enhanced page config
st.set_page_config(
    page_title="TravoMate - AI Travel Planner", 
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for glassmorphism design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styles */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Main container glassmorphism */
    .main .block-container {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
    }
    
    /* Header glassmorphism */
    .main-header {
        text-align: center;
        padding: 2rem;
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(25px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: white;
        border-radius: 25px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.2);
    }
    
    .main-header h1 {
        font-weight: 700;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
        margin-bottom: 0.5rem;
    }
    
    .main-header p {
        font-weight: 400;
        opacity: 0.9;
    }
    
    /* Sidebar glassmorphism */
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Chat messages glassmorphism */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 15px;
        margin: 0.5rem 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    /* Welcome message glassmorphism */
    .quick-tip {
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(25px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: white;
        padding: 2rem;
        margin: 1rem 0;
        border-radius: 20px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
    }
    
    .quick-tip h4 {
        color: white !important;
        margin-bottom: 0.5rem;
        font-weight: 600;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
    }
    
    .quick-tip p {
        color: rgba(255, 255, 255, 0.95) !important;
        margin-bottom: 0;
        font-weight: 400;
    }
    
    /* Button glassmorphism */
    .stButton > button {
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: white;
        border-radius: 25px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: rgba(255, 255, 255, 0.3);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
    }
    
    /* Input glassmorphism */
    .stChatInput > div > div > input {
        background: rgba(255, 255, 255, 0.15) !important;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 25px !important;
        color: white !important;
        padding: 1rem 1.5rem !important;
    }
    
    .stChatInput > div > div > input::placeholder {
        color: rgba(255, 255, 255, 0.7) !important;
    }
    
    /* Metric cards glassmorphism */
    .metric-card {
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        color: white;
    }
    
    /* Selectbox and slider glassmorphism */
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.15) !important;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 15px !important;
        color: white !important;
    }
    
    .stSlider > div > div > div {
        background: rgba(255, 255, 255, 0.2) !important;
    }
    
    /* Text styling */
    .stMarkdown {
        color: white;
    }
    
    /* Expander glassmorphism */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 15px !important;
        color: white !important;
    }
    
    .streamlit-expanderContent {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 15px !important;
    }
    
    # Link styling
    a {
        color: rgba(255, 255, 255, 0.9) !important;
        text-decoration: none !important;
    }
    
    a:hover {
        color: white !important;
        text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
    }
    
    # Plotly charts styling for glassmorphism
    .js-plotly-plot {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 20px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
    }
    
    /* Budget summary cards */
    .budget-summary {
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        color: white;
        text-align: center;
    }
    
    .budget-summary h2 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(45deg, #fff, #f093fb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .budget-summary p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown("""
<div class="main-header">
    <h1>🌍 TravoMate - Your AI Travel Planner</h1>
    <p>Plan your next adventure with the power of AI ✈️</p>
</div>
""", unsafe_allow_html=True)

# Sidebar with quick actions and tips
with st.sidebar:
    st.markdown("### 🚀 Quick Start")
    
    # Sample prompts
    st.markdown("**Try these prompts:**")
    sample_prompts = [
        "Plan a 5-day trip to Goa for ₹25,000",
        "Weekend getaway to Manali under ₹15,000",
        "Family vacation to Kerala with kids",
        "Solo backpacking through Himachal Pradesh",
        "7-day Rajasthan heritage tour for ₹40,000",
        "Beach vacation in Andaman for ₹50,000"
    ]
    
    for prompt in sample_prompts:
        if st.button(f"💡 {prompt}", key=prompt, use_container_width=True):
            st.session_state.selected_prompt = prompt
    
    st.divider()
    
    # Travel preferences
    # st.markdown("### ⚙️ Travel Preferences")
    # with st.expander("Set your preferences"):
    #     budget_range = st.select_slider(
    #         "Budget Range",
    #         options=["Budget (₹)", "Mid-range (₹₹)", "Luxury (₹₹₹)"],
    #         value="Mid-range (₹₹)"
    #     )
        
    #     travel_style = st.selectbox(
    #         "Travel Style",
    #         ["Adventure", "Relaxation", "Cultural", "Food & Drink", "Family-friendly"]
    #     )
        
    #     duration = st.slider("Trip Duration (days)", 1, 30, 7)
    
    # st.divider()
    
    # Tips section
    st.markdown("""
    ### 💡 Tips for Better Planning
    - Be specific about your budget in ₹
    - Mention travel dates for seasonal recommendations
    - Include group size and ages
    - Specify interests (food, culture, adventure, spirituality)
    - Ask about local transport and accommodation
    - Consider monsoon seasons for outdoor activities
    """)
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History", type="secondary", use_container_width=True):
        st.session_state.messages = [
            {"role": "system", "content": TRAVEL_ASSISTANT_PROMPT}
        ]
        st.rerun()

# Main chat area
col1, col2 = st.columns([3, 1])

with col1:
    # Initialize session memory
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": TRAVEL_ASSISTANT_PROMPT}
        ]
    
    # Welcome message for new users
    if len(st.session_state.messages) == 1:
        with st.container():
            st.markdown("""
            <div class="quick-tip">
                <h4>👋 Welcome to TravoMate!</h4>
                <p>I'm your AI travel assistant. Tell me where you'd like to go, your budget, 
                travel dates, and interests - I'll help create the perfect itinerary for you!</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Chat container
    chat_container = st.container()
    with chat_container:
        # Show chat history (skip system message)
        for msg in st.session_state.messages[1:]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
    
    # Handle selected prompt from sidebar
    if "selected_prompt" in st.session_state:
        user_input = st.session_state.selected_prompt
        del st.session_state.selected_prompt
    else:
        user_input = st.chat_input("✈️ Where would you like to go? Tell me about your dream trip...")
    
    if user_input:
        # Add user message
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Get and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Planning your perfect trip..."):
                try:
                    reply = chat_with_openrouter(st.session_state.messages)
                    st.markdown(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    
                    # Extract and visualize budget if present
                    budget_data, total_budget, budget_type = extract_budget_from_response(reply, user_input)
                    if budget_data:
                        st.session_state.latest_budget = budget_data
                        st.session_state.budget_total = total_budget
                        
                        # Show budget visualization in an expander
                        with st.expander("💰 Budget Breakdown Visualization", expanded=True):
                            # Show budget type indicator
                            if budget_type == "estimated":
                                st.info("📊 **Estimated breakdown** based on your budget of ₹{:,}. Percentages based on typical Indian travel costs.".format(total_budget))
                            elif budget_type == "specific":
                                st.success("🎯 **Specific breakdown** extracted from the travel plan.")
                            elif budget_type == "scaled":
                                st.warning("⚖️ **Adjusted breakdown** - AI suggested amounts scaled to match your budget of ₹{:,}.".format(total_budget))
                            
                            col1, col2 = st.columns(2)
                            
                            pie_fig, bar_fig = create_budget_visualization(budget_data)
                            
                            with col1:
                                st.plotly_chart(pie_fig, use_container_width=True)
                            
                            with col2:
                                st.plotly_chart(bar_fig, use_container_width=True)
                            
                            # Budget summary
                            actual_total = sum(budget_data.values())
                            st.markdown(f"""
                            <div class="budget-summary">
                                <h2>₹{actual_total:,}</h2>
                                <p>Total Estimated Budget</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Detailed breakdown
                            st.markdown("### 📊 Detailed Breakdown")
                            for category, amount in budget_data.items():
                                percentage = (amount / actual_total) * 100
                                st.markdown(f"""
                                <div style="background: rgba(255, 255, 255, 0.1); padding: 0.5rem 1rem; border-radius: 10px; margin: 0.5rem 0;">
                                    **{category.title()}:** ₹{amount:,} ({percentage:.1f}%)
                                </div>
                                """, unsafe_allow_html=True)
                    
                    # If no budget detected, offer manual budget input
                    else:
                        if st.button("💰 Add Budget Breakdown", key="manual_budget"):
                            st.session_state.show_budget_input = True
                    
                    # Manual budget input
                    if st.session_state.get('show_budget_input', False):
                        with st.expander("🔧 Manual Budget Input", expanded=True):
                            st.markdown("**Enter your budget breakdown:**")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                accommodation = st.number_input("🏨 Accommodation", min_value=0, step=500, key="acc_input")
                                food = st.number_input("🍽️ Food", min_value=0, step=500, key="food_input")
                                misc = st.number_input("🛍️ Miscellaneous", min_value=0, step=500, key="misc_input")
                            
                            with col2:
                                transport = st.number_input("🚗 Transport", min_value=0, step=500, key="trans_input")
                                activities = st.number_input("🎯 Activities", min_value=0, step=500, key="act_input")
                                
                                if st.button("📊 Generate Visualization", type="primary"):
                                    manual_budget = {
                                        'accommodation': accommodation,
                                        'transport': transport,
                                        'food': food,
                                        'activities': activities,
                                        'miscellaneous': misc
                                    }
                                    # Remove zero values
                                    manual_budget = {k: v for k, v in manual_budget.items() if v > 0}
                                    
                                    if manual_budget:
                                        st.session_state.latest_budget = manual_budget
                                        st.session_state.show_budget_input = False
                                        st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Oops! Something went wrong: {e}")
                    st.info("💡 Try rephrasing your question or check your internet connection.")

with col2:
    # Budget visualization in sidebar if available
    if "latest_budget" in st.session_state and st.session_state.latest_budget:
        st.markdown("""
        <div class="metric-card">
            <h3>💰 Current Budget</h3>
        </div>
        """, unsafe_allow_html=True)
        
        total = sum(st.session_state.latest_budget.values())
        st.markdown(f"""
        <div class="metric-card">
            <h2 style="margin: 0; font-size: 1.8rem; color: #f093fb;">₹{total:,}</h2>
            <p style="margin: 0; opacity: 0.8;">Total Budget</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show top 3 categories
        sorted_budget = sorted(st.session_state.latest_budget.items(), key=lambda x: x[1], reverse=True)[:3]
        for category, amount in sorted_budget:
            percentage = (amount / total) * 100
            st.markdown(f"""
            <div class="metric-card" style="background: rgba(255, 255, 255, 0.08); padding: 0.8rem;">
                <strong>{category.title()}</strong><br>
                <span style="font-size: 1.2rem;">₹{amount:,}</span>
                <span style="opacity: 0.7;"> ({percentage:.0f}%)</span>
            </div>
            """, unsafe_allow_html=True)
    
    # Quick stats with glassmorphism
    st.markdown("""
    <div class="metric-card">
        <h3>📊 Chat Stats</h3>
    </div>
    """, unsafe_allow_html=True)
    
    total_messages = len(st.session_state.messages) - 1  # Exclude system message
    st.markdown(f"""
    <div class="metric-card">
        <h2 style="margin: 0; font-size: 2rem;">{total_messages}</h2>
        <p style="margin: 0; opacity: 0.8;">Messages</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="metric-card">
        <h3>🔗 Helpful Links</h3>
        <ul style="list-style: none; padding: 0;">
            <li>• <a href="https://www.irctc.co.in/" target="_blank">Indian Railways</a></li>
            <li>• <a href="https://weather.com/" target="_blank">Weather Forecast</a></li>
            <li>• <a href="https://xe.com/" target="_blank">Currency Converter</a></li>
            <li>• <a href="https://www.mea.gov.in/" target="_blank">Travel Advisories</a></li>
            <li>• <a href="https://www.makemytrip.com/" target="_blank">Hotel Bookings</a></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Fun travel fact with glassmorphism
    st.markdown("""
    <div class="metric-card">
        <h3>🌟 Did You Know?</h3>
    </div>
    """, unsafe_allow_html=True)
    
    travel_facts = [
        "India has the world's highest motorable road - Khardung La in Ladakh at 17,582 feet",
        "The Golden Temple in Amritsar serves free meals to over 100,000 people daily",
        "Meghalaya receives the highest rainfall in the world - Mawsynram gets 467 inches annually",
        "India is home to 6 seasons according to the Hindu calendar",
        "The Kumbh Mela is the largest peaceful gathering of people on Earth",
        "India has more than 1,600 spoken languages and 22 official languages"
    ]
    
    import random
    if st.button("🎲 Random Travel Fact"):
        selected_fact = random.choice(travel_facts)
        st.markdown(f"""
        <div class="metric-card" style="background: rgba(255, 255, 255, 0.2); margin-top: 1rem;">
            <p style="margin: 0; font-style: italic;">{selected_fact}</p>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: white; padding: 1rem;'>
    TravoMate v1.0 | Happy Travels! 🌟
</div>
""", unsafe_allow_html=True)