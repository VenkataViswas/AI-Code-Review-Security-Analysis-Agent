// Mixed: predictable random token and duplicated validation.
import java.util.Random;

class ResetCodeService {
    private final Random random = new Random();

    public String createResetCode(String userId) {
        if (userId == null || userId.isBlank()) {
            throw new IllegalArgumentException("userId required");
        }
        return String.valueOf(100000 + random.nextInt(900000));
    }

    public String createLoginCode(String userId) {
        if (userId == null || userId.isBlank()) {
            throw new IllegalArgumentException("userId required");
        }
        return String.valueOf(100000 + random.nextInt(900000));
    }
}
