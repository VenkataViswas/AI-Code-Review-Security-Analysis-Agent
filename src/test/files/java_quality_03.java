// Code quality issue: catching and suppressing every exception.
import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;

class ConfigLoader {
    public String load(String path) {
        try (BufferedReader reader = new BufferedReader(new FileReader(path))) {
            return reader.readLine();
        } catch (Exception exception) {
            return null;
        }
    }
}
