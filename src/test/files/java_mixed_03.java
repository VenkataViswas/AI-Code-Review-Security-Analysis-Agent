// Mixed: command injection risk and an overly long method.
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;

class ReportRunner {
    public String runReport(String userInput) throws IOException, InterruptedException {
        System.out.println("Starting report");
        if (userInput == null || userInput.isBlank()) {
            return "INVALID";
        }
        Process process = Runtime.getRuntime().exec(new String[] {"sh", "-c", "cat " + userInput});
        BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
        StringBuilder output = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) {
            output.append(line).append("\n");
        }
        int exitCode = process.waitFor();
        if (exitCode != 0) {
            System.err.println("Report failed");
            return "FAILED";
        }
        String report = output.toString().trim();
        System.out.println("Report length: " + report.length());
        System.out.println("Archiving report");
        System.out.println("Sending notification");
        System.out.println("Writing audit event");
        return report;
    }
}
