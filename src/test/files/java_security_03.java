// Security issue: unsafe use of a user-controlled path.
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

class FileDownload {
    public byte[] readFile(String baseDirectory, String requestedFile) throws IOException {
        Path target = Path.of(baseDirectory, requestedFile);
        return Files.readAllBytes(target);
    }
}
