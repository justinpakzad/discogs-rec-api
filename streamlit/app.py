import streamlit as st
import re
import requests


def validate_url(url: str) -> bool:
    """Check if URL matches Discogs release pattern."""
    pattern = r"https?://www\.discogs\.com/release/\d+(-[a-zA-Z0-9\-]+)?"
    return bool(re.match(pattern, url))


def display_recommendations(recs: list[dict]) -> None:
    """Render recommendation links with custom styling."""
    for rec in recs:
        st.markdown(
            f"<a href='{rec.get('url')}' class='custom-font'>{rec.get('artist_name')} - {rec.get('release_title')}</a>",
            unsafe_allow_html=True,
        )


def get_recomendation(url: str, n_recs: int) -> dict:
    """Fetch recommendations from API endpoint."""
    try:
        response = requests.post(
            "http://discogs_rec_api:8000/recommend",
            json={"url": url, "n_recs": n_recs},
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error: {e}")


def main():
    st.title("Discogs Rec")

    url = st.text_input(
        "Enter a Discogs URL", placeholder="https://www.discogs.com/release/123456"
    )

    is_valid = validate_url(url)
    n_recs = st.slider("Number of Recommendations", 1, 20, 5)
    if url:
        if not is_valid:
            st.error(
                "Invalid URL, please make sure it takes "
                "the form https://www.discogs.com/release/<release_id>"
            )

        recs = get_recomendation(url=url, n_recs=n_recs)

        if "recommendations" not in recs:
            st.error(recs.get("detail"))

        display_recommendations(recs=recs.get("recommendations"))


main()
