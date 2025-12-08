"""Streamlit dashboard for Workout Tracker.

A user-friendly interface for managing workout exercises through the FastAPI backend.
Features include listing exercises, adding new ones, filtering by weight, and viewing statistics.
"""

import pandas as pd
import streamlit as st

from services.frontend.src.client import (
    list_exercises,
    create_exercise,
    update_exercise,
    delete_exercise,
    get_exercise,
)

# Page configuration
st.set_page_config(
    page_title="Workout Tracker Dashboard",
    page_icon="🏋",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Workout Tracker Dashboard")
st.caption(
    "View, create, and manage your workout exercises"
)


@st.cache_data(ttl=30)
def cached_exercises() -> list[dict]:
    """Fetch exercises with 30-second cache.

    Returns:
        list[dict]: List of all exercises from the API.
    """
    return list_exercises()


# Sidebar for actions
with st.sidebar:
    st.header("Actions")

    if st.button("Refresh Data", use_container_width=True):
        cached_exercises.clear()
        st.rerun()

    st.divider()
    st.caption("Tip: Data refreshes automatically every 30 seconds")


# Main content
try:
    with st.spinner("Loading exercises..."):
        exercises = cached_exercises()

    # Display metrics
    if exercises:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Exercises", len(exercises))

        with col2:
            total_sets = sum(ex.get("sets", 0) for ex in exercises)
            st.metric("Total Sets", total_sets)

        with col3:
            total_volume = sum(
                ex.get("sets", 0) * ex.get("reps", 0) * ex.get("weight", 0)
                for ex in exercises
                if ex.get("weight") is not None
            )
            st.metric("Total Volume", f"{total_volume:.1f} kg")

        with col4:
            weighted_exercises = sum(1 for ex in exercises if ex.get("weight") is not None)
            st.metric("Weighted Exercises", weighted_exercises)

        st.divider()

        # Filter section
        st.subheader("Exercise List")

        col_filter1, col_filter2 = st.columns(2)

        with col_filter1:
            filter_weighted = st.selectbox(
                "Filter by type",
                ["All", "Weighted Only", "Bodyweight Only"],
                key="filter_type"
            )

        with col_filter2:
            search_term = st.text_input(
                "Search exercises",
                placeholder="Type exercise name...",
                key="search"
            )

        # Apply filters
        filtered_exercises = exercises

        if filter_weighted == "Weighted Only":
            filtered_exercises = [ex for ex in filtered_exercises if ex.get("weight") is not None]
        elif filter_weighted == "Bodyweight Only":
            filtered_exercises = [ex for ex in filtered_exercises if ex.get("weight") is None]

        if search_term:
            filtered_exercises = [
                ex for ex in filtered_exercises
                if search_term.lower() in ex.get("name", "").lower()
            ]

        # Display exercises
        if filtered_exercises:
            st.caption(f"Showing {len(filtered_exercises)} of {len(exercises)} exercises")

            # Convert to DataFrame for better display
            df = pd.DataFrame(filtered_exercises)
            df["weight"] = df["weight"].fillna("Bodyweight")

            # Reorder columns
            column_order = ["id", "name", "sets", "reps", "weight"]
            df = df[column_order]

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": st.column_config.NumberColumn("ID", width="small"),
                    "name": st.column_config.TextColumn("Exercise", width="medium"),
                    "sets": st.column_config.NumberColumn("Sets", width="small"),
                    "reps": st.column_config.NumberColumn("Reps", width="small"),
                    "weight": st.column_config.TextColumn("Weight", width="small"),
                }
            )
        else:
            st.info("No exercises match your filters.")


        st.divider()

        # Update exercise section
        st.subheader("Update Exercise")

        # Create exercise_names dictionary for use in update and delete sections
        exercise_names = {f"{ex['id']} - {ex['name']}": ex['id'] for ex in exercises}

        col_upd1, col_upd2 = st.columns([3, 1])

        with col_upd1:
            selected_to_update = st.selectbox(
                "Select exercise to update",
                options=list(exercise_names.keys()),
                key="update_select"
            )

        with col_upd2:
            st.write("")  # Spacer
            st.write("")  # Spacer
            if st.button("Load Exercise", type="secondary", use_container_width=True):
                st.session_state.update_mode = True
                st.session_state.update_id = exercise_names[selected_to_update]

        if st.session_state.get("update_mode", False):
            try:
                current_exercise = get_exercise(st.session_state.update_id)

                with st.form("update_exercise", clear_on_submit=False):
                    st.info(f"Updating: **{current_exercise['name']}** (ID: {current_exercise['id']})")

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        updated_name = st.text_input(
                            "Exercise Name *",
                            value=current_exercise['name'],
                            help="The name of the exercise"
                        )

                    with col2:
                        updated_sets = st.number_input(
                            "Sets *",
                            min_value=1,
                            max_value=20,
                            value=current_exercise['sets'],
                            help="Number of sets"
                        )

                    with col3:
                        updated_reps = st.number_input(
                            "Reps *",
                            min_value=1,
                            max_value=100,
                            value=current_exercise['reps'],
                            help="Repetitions per set"
                        )

                    with col4:
                        # Use text input for weight to allow empty string for bodyweight
                        current_weight = current_exercise.get('weight')
                        weight_display = "" if current_weight is None else str(current_weight)
                        updated_weight_str = st.text_input(
                            "Weight (kg)",
                            value=weight_display,
                            placeholder="Leave empty for bodyweight",
                            help="Weight in kg, or leave empty for bodyweight exercises"
                        )

                    col_btn1, col_btn2 = st.columns(2)

                    with col_btn1:
                        update_submitted = st.form_submit_button("Update Exercise", type="primary", use_container_width=True)

                    with col_btn2:
                        cancel_update = st.form_submit_button("Cancel", use_container_width=True)

                    if cancel_update:
                        st.session_state.update_mode = False
                        st.session_state.update_id = None
                        st.rerun()

                    if update_submitted:
                        if not updated_name or not updated_name.strip():
                            st.error("Exercise name is required!")
                        else:
                            try:
                                # Parse weight: empty string = None (bodyweight)
                                weight_value = None
                                weight_is_valid = True

                                if updated_weight_str and updated_weight_str.strip():
                                    try:
                                        weight_value = float(updated_weight_str.strip())
                                        if weight_value <= 0:
                                            weight_value = None
                                    except ValueError:
                                        st.error("Weight must be a valid number or empty for bodyweight")
                                        weight_is_valid = False

                                if not weight_is_valid:
                                    st.stop()

                                # Always send all parameters to ensure proper update
                                updated_exercise = update_exercise(
                                    st.session_state.update_id,
                                    name=updated_name.strip(),
                                    sets=updated_sets,
                                    reps=updated_reps,
                                    weight=weight_value
                                )
                                cached_exercises.clear()
                                st.session_state.update_mode = False
                                st.session_state.update_id = None
                                weight_display = f"{updated_exercise.get('weight')} kg" if updated_exercise.get('weight') else "Bodyweight"
                                st.success(
                                    f"Updated exercise: {updated_exercise['name']} "
                                    f"({updated_exercise['sets']} sets × {updated_exercise['reps']} reps, {weight_display})"
                                )
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Failed to update exercise: {exc}")

            except Exception as exc:
                st.error(f"Failed to load exercise: {exc}")
                st.session_state.update_mode = False
                st.session_state.update_id = None

    else:
        st.info("No exercises yet. Add your first exercise below!")

    st.divider()

    # Create exercise section
    st.subheader("Add New Exercise")

    with st.form("create_exercise", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            name = st.text_input(
                "Exercise Name *",
                placeholder="e.g., Bench Press",
                help="The name of the exercise"
            )

        with col2:
            sets = st.number_input(
                "Sets *",
                min_value=1,
                max_value=20,
                value=3,
                help="Number of sets"
            )

        with col3:
            reps = st.number_input(
                "Reps *",
                min_value=1,
                max_value=100,
                value=10,
                help="Repetitions per set"
            )

        with col4:
            weight_str = st.text_input(
                "Weight (kg)",
                value="",
                placeholder="Leave empty for bodyweight",
                help="Weight in kg, or leave empty for bodyweight exercises"
            )

        submitted = st.form_submit_button("Create Exercise", type="primary", use_container_width=True)

        if submitted:
            if not name or not name.strip():
                st.error("Exercise name is required!")
            else:
                try:
                    # Parse weight: empty string or invalid = None (bodyweight)
                    weight_value = None
                    if weight_str and weight_str.strip():
                        try:
                            weight_value = float(weight_str.strip())
                            if weight_value <= 0:
                                weight_value = None
                        except ValueError:
                            st.error("Weight must be a valid number or empty for bodyweight")
                            st.stop()

                    exercise = create_exercise(
                        name=name.strip(),
                        sets=sets,
                        reps=reps,
                        weight=weight_value
                    )
                    cached_exercises.clear()
                    weight_display = f"{exercise.get('weight')} kg" if exercise.get('weight') else "Bodyweight"
                    st.success(
                        f"Created exercise: {exercise['name']} "
                        f"({exercise['sets']} sets × {exercise['reps']} reps, {weight_display})"
                    )
                    st.rerun()
                except Exception as exc:
                    st.error(f"Failed to create exercise: {exc}")

    st.divider()

    # Delete exercise section (moved to end)
    if exercises:
        st.subheader("Delete Exercise")
        col_del1, col_del2 = st.columns([3, 1])

        with col_del1:
            selected_to_delete = st.selectbox(
                "Select exercise to delete",
                options=list(exercise_names.keys()),
                key="delete_select"
            )

        with col_del2:
            st.write("")  # Spacer
            st.write("")  # Spacer
            if st.button("Delete", type="secondary", use_container_width=True):
                try:
                    exercise_id = exercise_names[selected_to_delete]
                    delete_exercise(exercise_id)
                    cached_exercises.clear()
                    st.success(f"Deleted exercise: {selected_to_delete}")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Failed to delete: {exc}")

except Exception as e:
    st.error(f"Failed to connect to the API. Is the backend running?")
    st.exception(e)
    st.info(
        "Make sure the FastAPI server is running:\n\n"
        "```bash\n"
        "uvicorn services.api.src.api:app --reload\n"
        "```"
    )

