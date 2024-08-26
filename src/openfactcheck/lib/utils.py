def detect_streamlit() -> bool:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        if get_script_run_ctx() is not None:
            return True
        else:
            return False
        
    except ImportError:
        return False
    
    except Exception:
        return False
    