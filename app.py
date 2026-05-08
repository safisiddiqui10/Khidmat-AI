import streamlit as st
from graph import graph, llm ,extract
from database import engine
from sqlalchemy import text
import uuid
from constant import QUESTIONS, REQUIRED_FIELDS
from database import save_or_update_beneficiary

st.set_page_config(page_title="Khidmat AI")
st.title("Khidmat-AI")

if "state" not in st.session_state:
    st.session_state.state = {
        "data": {
            "name": None,
            "phone": None,
            "location": None,
            "need": None,
            "family_members": None
        },
        "user_input": None,
        "missing": ["name"]
    }

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": QUESTIONS["name"]
        }
    ]

if "row_id" not in st.session_state:
    st.session_state.row_id = None

if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())


st.sidebar.title("Debug Panel")
st.sidebar.subheader("Extracted Data")
st.sidebar.json(st.session_state.state["data"])
st.sidebar.subheader("Missing Fields")
st.sidebar.write(st.session_state.state["missing"])
st.sidebar.subheader("Row ID")
st.sidebar.write(st.session_state.row_id)

def build_chat_history():
    history = ""
    recent_messages = st.session_state.messages[-10:]

    for msg in recent_messages:
        role = msg["role"]
        content = msg["content"]
        history += f"{role}: {content}\n"

    return history

def get_latest_data():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT * FROM beneficiaries
            ORDER BY id DESC
            LIMIT 10
        """))

        return [dict(row._mapping) for row in result.fetchall()]

st.sidebar.subheader("Database")
st.sidebar.dataframe(get_latest_data())


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])


prompt = st.chat_input("Type your response")


# main business logic
if prompt:

    if prompt.lower() == "/new":

        st.session_state.state = {
            "data": {
                "name": None,
                "phone": None,
                "location": None,
                "need": None,
                "family_members": None
            },
            "user_input": None,
            "missing": ["name"]
        }

        st.session_state.messages = [
            {
                "role": "assistant",
                "content": QUESTIONS["name"]
            }
        ]

        st.session_state.row_id = None
        st.session_state.submitted = False

        st.rerun()

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.write(prompt)

    previous_data = st.session_state.state["data"].copy()

    st.session_state.state["user_input"] = prompt
    result = graph.invoke(st.session_state.state)

    st.session_state.state["data"] = result["data"]
    st.session_state.state["missing"] = result["missing"]
    current_data = result["data"]

    new_data_found = current_data != previous_data

    data = {
        k: str(v) if v is not None else None
        for k, v in current_data.items()
    }


    with engine.connect() as conn:

        if st.session_state.row_id is None:

            query = text("""
                INSERT INTO beneficiaries
                (name, phone, location, need, family_members)
                VALUES (:name, :phone, :location, :need, :family_members)
                RETURNING id
            """)

            res = conn.execute(query, data)
            st.session_state.row_id = res.fetchone()[0]
            conn.commit()

        # UPDATE SAME ROW
        else:

            query = text("""
                UPDATE beneficiaries
                SET
                    name = COALESCE(:name, name),
                    phone = COALESCE(:phone, phone),
                    location = COALESCE(:location, location),
                    need = COALESCE(:need, need),
                    family_members = COALESCE(:family_members, family_members)
                WHERE id = :id
            """)

            conn.execute(query, {
                "id": st.session_state.row_id,
                **data
            })

            conn.commit()

    missing = result["missing"]

    if missing:

        next_question = QUESTIONS[missing[0]]

        if not new_data_found:

            chat_history = build_chat_history()

            response = llm.invoke(
            f"""
            You are Khidmat-AI assistant.

            Conversation history:
            {chat_history}

            Current user message:
            {prompt}

            Reply naturally and shortly.
            """
        )

            bot_reply = (
                f"{response.content}\n\n"
                f"{next_question}"
            )

        else:
            bot_reply = next_question

    else:

        if not new_data_found:

            chat_history = build_chat_history()

            response = llm.invoke(
            f"""
            You are Khidmat-AI assistant.

            Conversation history:
            {chat_history}

            Current user message:
            {prompt}

            Reply naturally and shortly.
            """
        )

            bot_reply = (
                f"{response.content}\n\n"
                "You can still provide optional details "
                "before submitting."
            )
        else:

            bot_reply = (
                "Details updated successfully.\n\n"
                "You can still provide optional details "
                "before submitting."
            )

    st.session_state.messages.append({
        "role": "assistant",
        "content": bot_reply
    })

    with st.chat_message("assistant"):
        st.write(bot_reply)


#submit and add another person logic
all_required_done = all(
    st.session_state.state["data"].get(field)
    for field in REQUIRED_FIELDS
)
actions = []

actions.append({
    "label": "✅ Submit",
    "key": "submit"
})

actions.append({
    "label": "➕ Add Person",
    "key": "new_person"
})

# Future buttons can easily be added
# actions.append({
#     "label": "🗑 Delete",
#     "key": "delete"
# })

cols = st.columns(len(actions))

for col, action in zip(cols, actions):
    with col:
        if action["key"] == "submit":
            if all_required_done:
                if st.button(
                    action["label"],
                    use_container_width=True
                ):

                    st.session_state.submitted = True
                    st.success(
                        "Form submitted successfully!"
                    )

            else:
                st.button(
                    action["label"],
                    disabled=True,
                    use_container_width=True
                )

        elif action["key"] == "new_person":
            if st.button(
                action["label"],
                use_container_width=True
            ):

                st.session_state.state = {
                    "data": {
                        "name": None,
                        "phone": None,
                        "location": None,
                        "need": None,
                        "family_members": None
                    },
                    "user_input": None,
                    "missing": ["name"]
                }

                st.session_state.messages = [
                    {
                        "role": "assistant",
                        "content": QUESTIONS["name"]
                    }
                ]

                st.session_state.row_id = None
                st.session_state.submitted = False
                st.session_state.session_id = str(uuid.uuid4())
                st.rerun()