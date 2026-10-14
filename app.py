
import sqlite3
import streamlit as st
from tools.task_tools import get_connection
from agent import agent

st.set_page_config(
    page_title="Personal Productivity Agent",
    page_icon="📋",
    layout="wide",
)

st.title("📋 Personal Productivity Agent")
st.write("Manage your tasks and work with your AI assistant.")

# -----------------------------------------
# DASHBOARD: READ TASKS FROM SQLITE
# -----------------------------------------
with get_connection() as connection:
    connection.row_factory = sqlite3.Row

    rows = connection.execute("""
        SELECT id, title, description, priority, deadline, status
        FROM tasks
        ORDER BY id DESC
    """).fetchall()

total_tasks = len(rows)
pending_tasks = sum(row["status"] == "pending" for row in rows)
completed_tasks = sum(row["status"] == "completed" for row in rows)

st.subheader("Your Dashboard")

col1, col2, col3 = st.columns(3)
col1.metric("Total Tasks", total_tasks)
col2.metric("Pending Tasks", pending_tasks)
col3.metric("Completed Tasks", completed_tasks)

st.divider()

# -----------------------------------------
# AI CHAT INTERFACE
# -----------------------------------------
st.subheader("🤖 Chat with Your Productivity Agent")

st.caption(
    "Ask the agent to create tasks, list your tasks, "
    "or mark tasks as completed."
)

# Keep conversation history during Streamlit reruns
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display previous messages
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept a new user message
user_input = st.chat_input(
    "For example: List all my pending tasks"
)

if user_input:
    # Display and save the user's message
    st.session_state.chat_history.append(
        {"role": "user", "content": user_input}
    )

    with st.chat_message("user"):
        st.markdown(user_input)

    # Ask the existing LangChain agent
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result = agent.invoke(
                    {
                        "messages": [
                            {
                                "role": "user",
                                "content": user_input,
                            }
                        ]
                    }
                )

                # Find the final AI response
                answer = None

                for message in reversed(result["messages"]):
                    if (
                        getattr(message, "type", None) == "ai"
                        and message.content
                    ):
                        answer = message.content
                        break

                if answer is None:
                    answer = "I couldn't find a response. Please try again."

                st.markdown(answer)

                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": answer,
                    }
                )

            except Exception as error:
                answer = (
                    f"Sorry, the agent encountered an error: "
                    f"{type(error).__name__}: {str(error)[:300]}"
                )

                st.error(answer)

                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": answer,
                    }
                )

# Button to clear conversation history
if st.button("Clear chat"):
    st.session_state.chat_history = []
    st.rerun()

st.divider()

# -----------------------------------------
# TASK LIST AND FILTERS
# -----------------------------------------
st.subheader("Your Tasks")

col1, col2 = st.columns(2)

with col1:
    status_filter = st.selectbox(
        "Filter by status",
        ["All", "Pending", "Completed"],
    )

with col2:
    priority_filter = st.selectbox(
        "Filter by priority",
        ["All", "High", "Medium", "Low"],
    )

filtered_rows = rows

if status_filter != "All":
    filtered_rows = [
        row
        for row in filtered_rows
        if row["status"] == status_filter.lower()
    ]

if priority_filter != "All":
    filtered_rows = [
        row
        for row in filtered_rows
        if row["priority"] == priority_filter.lower()
    ]

if not filtered_rows:
    st.info("No tasks match your selected filters.")
else:
    for row in filtered_rows:
        with st.container(border=True):
            st.markdown(
                f"### Task {row['id']}: {row['title']}"
            )

            col1, col2, col3 = st.columns(3)

            col1.write(
                f"**Status:** {row['status'].title()}"
            )
            col2.write(
                f"**Priority:** {row['priority'].title()}"
            )
            col3.write(
                f"**Deadline:** {row['deadline'] or 'Not set'}"
            )

            if row["description"]:
                st.write(
                    f"**Description:** {row['description']}"
                )

st.divider()

st.caption(
    "Personal Productivity Agent | "
    "LangChain + OpenRouter + SQLite + Streamlit"
)
