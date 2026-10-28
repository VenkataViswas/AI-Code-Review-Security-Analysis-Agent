// Clean example: parameterized query.
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

class UserRepository {
    public List<String> findUsernames(Connection connection, int userId) throws SQLException {
        String sql = "SELECT username FROM users WHERE id = ?";
        List<String> usernames = new ArrayList<>();
        try (PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setInt(1, userId);
            try (ResultSet results = statement.executeQuery()) {
                while (results.next()) {
                    usernames.add(results.getString("username"));
                }
            }
        }
        return usernames;
    }
}
