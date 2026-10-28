// Mixed: hardcoded database password and configuration concerns.
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

class DatabaseConnector {
    private static final String PASSWORD = "demo-password-123";

    public Connection connect() throws SQLException {
        return DriverManager.getConnection(
            "jdbc:postgresql://localhost:5432/app",
            "app_user",
            PASSWORD
        );
    }
}
