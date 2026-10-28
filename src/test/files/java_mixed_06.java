// Mixed: unsafe path resolution and swallowed errors.
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

class UserFileReader {
    public String read(String root, String requestedName) {
        try {
            Path path = Path.of(root, requestedName);
            return Files.readString(path);
        } catch (Exception exception) {
            return "";
        }
    }
}
