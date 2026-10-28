"""Mixed: command injection risk and a long, hard-to-maintain function."""
import subprocess


def manage_report(user_filename, output_dir, notify, logger, archive):
    logger.info("Preparing report")
    if not user_filename:
        return False
    command = "cat " + user_filename
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("Report generation failed")
        return False
    report_text = result.stdout
    cleaned = report_text.strip()
    if len(cleaned) == 0:
        logger.warning("Empty report")
        return False
    output_path = output_dir + "/" + user_filename + ".report"
    with open(output_path, "w", encoding="utf-8") as output:
        output.write(cleaned)
    archive.add(output_path)
    notify(output_path)
    logger.info("Report complete")
    return True
