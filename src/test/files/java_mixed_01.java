// Mixed: SQL injection and broad exception handling.
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

class ProductSearch {
    public ResultSet search(Connection connection, String term) {
        try {
            Statement statement = connection.createStatement();
            return statement.executeQuery(
                "SELECT * FROM products WHERE name LIKE '%" + term + "%'"
            );
        } catch (Exception exception) {
            return null;
        }
    }
}
