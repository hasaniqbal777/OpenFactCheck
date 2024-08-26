import streamlit as st

def metric_card(
        background_color: str = "#FFF",
        border_size_px: int = 1,
        border_color: str = "#CCC",
        border_radius_px: int = 5,
        border_left_color: str = "#9AD8E1",
        label: str = "Label",
        value: str = "Value",
    ) -> None:
        
    html_str = f"""
    <div>
        <p style='font-size: 14px;
                  color: rgb(49, 51, 63);
                  height: auto;
                  min-height: 1.5rem;
                  vertical-align: middle;
                  flex-direction: row;
                  -webkit-box-align: center;
                  align-items: center;
                  margin-bottom: 0px;
                  display: grid;
                  background-color: {background_color};
                  border: {border_size_px}px solid {border_color};
                  padding: 5% 5% 5% 10%;
                  border-radius: {border_radius_px}px;
                  border-left: 0.5rem solid {border_left_color};'>
            {label}
            <br>
            <span style='font-size: 2.25rem;
                         padding-bottom: 0.25rem;'>
                {value}
            </span>
        </p>
    </div>
    """
    st.markdown(html_str, unsafe_allow_html=True)
    st.markdown('######')