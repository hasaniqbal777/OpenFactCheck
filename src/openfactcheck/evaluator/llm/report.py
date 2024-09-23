import os
import subprocess
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from importlib import resources as pkg_resources

from openfactcheck.utils.logging import get_logger
from openfactcheck.templates import report as report_dir

# Get the logger
logger = get_logger(__name__)

# Import latex template
report_template_path = str(pkg_resources.files(report_dir) / "llm_evaluation_report.tex")

def create_latex_report(model_name, report_path):
    """
    Fill data in tex templates.
    """

    loader = FileSystemLoader(os.path.dirname(report_template_path))
    env = Environment(loader=loader)
    data = {
        "model_name": model_name.replace("_", " "),
        "snowballing_barplot": "snowballing_barplot.png",
        "snowballing_cm": "snowballing_cm.png",
        "selfaware_barplot": "selfaware_barplot.png",
        "selfaware_cm": "selfaware_cm.png",
        "freshqa_barplot": "freshqa_barplot.png",
        "freetext_barplot": "freetext_barplot.png",
    }
    template = env.get_template(os.path.basename(report_template_path))
    latex = template.render(data)
    with open(Path(report_path) / ("main.tex"), "w", encoding="utf-8") as f:
        f.write(latex)

    return None


def compile_pdf(report_path):
    """
    Compile the latex file to pdf.
    """

    # Change the directory to the report path
    original_directory = os.getcwd()
    os.chdir(report_path)

    try:
        try:
            # Compile the latex file
            subprocess.run(["pdflatex", "main.tex"], timeout=60)
        except subprocess.TimeoutExpired:
            logger.error("Compilation of the report timed out.")
            raise Exception("Compilation of the report timed out.")
        

        # Rename the pdf file
        Path("main.pdf").replace("report.pdf")

        # Remove the auxiliary files
        for file in Path(".").glob("main*"):
            file.unlink()
        
        # Change the directory back to the original
        os.chdir(original_directory)

    except Exception as e:
        logger.error(f"Error compiling the report: {e}")
        raise Exception(f"Error compiling the report: {e}")


def create_report(model_name, report_path):
    """
    Create a pdf report.
    """

    logger.debug("Creating the report...")
    create_latex_report(model_name, report_path)

    logger.debug("Compiling the report...")
    compile_pdf(report_path)

    return Path(report_path) / "report.pdf"