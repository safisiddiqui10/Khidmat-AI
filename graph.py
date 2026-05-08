import json
import os
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from typing import TypedDict
from langgraph.graph import StateGraph

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)


class State(TypedDict):
    user_input: str
    data: dict
    missing: list


def extract(state):
    prompt = f"""
Extract beneficiary details.
Return ONLY valid JSON.
Do not use markdown.
Do not wrap in ```json.
Do not add explanation.

Fields:
name
phone
location
need
family_members

If missing, set null.

Example:
{{
    "name": null,
    "phone": null,
    "location": null,
    "need": null,
    "family_members": null
}}

Text:
{state['user_input']}
"""


    response = llm.invoke(prompt)
    content = response.content.strip()
    content = re.sub(r"```json|```", "", content).strip()
    print("LLM Output:", content)

    try:
        extracted = json.loads(content)
    except Exception as e:
        print("JSON Error:", e)
        extracted = {}
        
    data = state.get("data", {}).copy()

    for key, value in extracted.items():
        if value is not None and value != "":
            data[key] = str(value)

    required = ["name", "phone", "need"]

    missing = [
        field for field in required
        if data.get(field) is None
            ]

    return {
        "data": data,
        "missing": missing
    }




graph = StateGraph(State)
graph.add_node("extract", extract)
graph.set_entry_point("extract")
graph = graph.compile()
























# import os
# import json
# from dotenv import load_dotenv
# from langchain_groq import ChatGroq
# from langgraph.graph import StateGraph, END
# from typing import TypedDict
# from db import engine
# from sqlalchemy import text

# load_dotenv()

# llm = ChatGroq(
#     model="llama-3.3-70b-versatile",
#     api_key=os.getenv("GROQ_API_KEY")
# )


# class State(TypedDict):
#     user_input: str
#     data: dict
#     missing: list


# # ---------------- EXTRACT NODE ----------------
# def extract(state):
#     prompt = f"""
# Extract name, phone, location, need, family_members.

# Return only JSON.

# Text: {state["user_input"]}
# """

#     response = llm.invoke(prompt)
#     extracted = json.loads(response.content)

#     data = state.get("data", {})
#     data.update({k: v for k, v in extracted.items() if v})

#     return {"data": data}


# # ---------------- VALIDATE NODE ----------------
# def validate(state):
#     data = state["data"]

#     required = ["name", "phone", "need"]

#     missing = [field for field in required if field not in data]

#     return {"missing": missing}


# # ---------------- SAVE NODE ----------------
# def save(state):
#     with engine.connect() as conn:
#         conn.execute(
#             text("""
#             INSERT INTO beneficiaries
#             (name, phone, location, need, family_members)
#             VALUES (:name, :phone, :location, :need, :family_members)
#             """),
#             {
#                 "name": state["data"].get("name"),
#                 "phone": state["data"].get("phone"),
#                 "location": state["data"].get("location"),
#                 "need": state["data"].get("need"),
#                 "family_members": state["data"].get("family_members")
#             }
#         )
#         conn.commit()

#     print("Saved successfully")

#     return state


# # ---------------- ROUTER ----------------
# def route(state):
#     if state["missing"]:
#         return END
#     return "save"


# # ---------------- GRAPH ----------------
# builder = StateGraph(State)

# builder.add_node("extract", extract)
# builder.add_node("validate", validate)
# builder.add_node("save", save)

# builder.set_entry_point("extract")

# builder.add_edge("extract", "validate")
# builder.add_conditional_edges("validate", route)
# builder.add_edge("save", END)

# graph = builder.compile()