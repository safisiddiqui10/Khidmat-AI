from graph import graph
from database import engine
from sqlalchemy import text


state = {
    "data": {
        "name": None,
        "phone": None,
        "location": None,
        "need": None,
        "family_members": None
    },
    "user_input": None
}

questions = {
    "name": "What is your full name?",
    "phone": "What is your phone number?",
    "location": "Which city do you live in?",
    "need": "What kind of help do you need?",
    "family_members": "How many family members are there?"
}

print("AI Khidmat Bot")
print("Bot:", questions["name"])


while True:
    user_input = input("You: ")
    
    if user_input.lower() in ["exit", "quit"]:
        break

    state["user_input"] = user_input

    result = graph.invoke(state)
    
    state["data"] = result["data"]
    state["missing"] = result["missing"]    
    print("LLM Output:", state["data"])

    # for key, value in result.get("data", {}).items():
    #     if value is not None:
    #         state["data"][key] = value
    
    # state["missing"] = result.get("missing", [])
    print("Current State:", state["data"])
    
    
    # if result["missing"]:
    #     print("Please provide:", ", ".join(result["missing"]))
    if state["missing"]:
        next_field = state["missing"][0]
        print("Bot:", questions[state["missing"][0]])
    
    else:
        with engine.connect() as conn:
            query = text("""
            INSERT INTO beneficiaries
            (name, phone, location, need, family_members)
            VALUES (:name, :phone, :location, :need, :family_members)
        """)

            conn.execute(query, state["data"])
            conn.commit()

        print("Bot: Information saved successfully.")
        print("Bot: You can continue chatting with me.")
            # this can be optimized by moving it to the save node in graph.py krlunga next   
            # reset only after successful save

        # break